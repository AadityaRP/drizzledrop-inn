from __future__ import annotations

from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, UpdateView

from bookings.forms import BookingForm
from bookings.models import Booking
from core.mixins import (
    HotelAdminRequiredMixin,
    HotelScopedQuerysetMixin,
)
from core.models import get_user_hotels
from core.scopes import ensure_user_has_hotel_access, get_current_hotel
from invoicing.models import Invoice


class BookingListView(HotelAdminRequiredMixin, HotelScopedQuerysetMixin, ListView):
    """
    List bookings for the selected hotel; chain owners can filter by hotel.
    """

    model = Booking
    template_name = "bookings/booking_list.html"
    context_object_name = "bookings"
    require_current_hotel_for_admins = True

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("hotel", "room_category", "enquiry")
            .order_by("-created_at")
        )
        hotel_id = self.request.GET.get("hotel")
        if getattr(self.request.user, "is_chain_owner", False) and hotel_id:
            try:
                qs = qs.filter(hotel_id=int(hotel_id))
            except (TypeError, ValueError):
                pass
        return qs

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "is_chain_owner": getattr(self.request.user, "is_chain_owner", False),
                "current_hotel": get_current_hotel(self.request),
                "accessible_hotels": get_user_hotels(self.request.user),
            }
        )
        return context


class BookingCreateView(HotelAdminRequiredMixin, CreateView):
    """
    Create a booking within hotel scope. Availability validated via form.
    """

    model = Booking
    form_class = BookingForm
    template_name = "bookings/booking_form.html"
    success_url = reverse_lazy("bookings:booking_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form: BookingForm) -> HttpResponse:
        form.instance.created_by = self.request.user
        messages.success(self.request, "Booking created.")
        response = super().form_valid(form)
        return response


class BookingUpdateView(HotelAdminRequiredMixin, HotelScopedQuerysetMixin, UpdateView):
    """
    Update a booking; scope enforced by mixin.
    """

    model = Booking
    form_class = BookingForm
    template_name = "bookings/booking_form.html"
    success_url = reverse_lazy("bookings:booking_list")
    require_current_hotel_for_admins = True

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form: BookingForm) -> HttpResponse:
        form.instance.updated_by = self.request.user
        messages.success(self.request, "Booking updated.")
        return super().form_valid(form)


def _get_booking_for_user(request: HttpRequest, pk: int) -> Booking:
    booking = get_object_or_404(Booking, pk=pk)
    ensure_user_has_hotel_access(request.user, booking.hotel)
    return booking


@login_required
def booking_confirm_view(request: HttpRequest, pk: int) -> HttpResponse:
    booking = _get_booking_for_user(request, pk)
    try:
        booking.confirm()
        messages.success(request, "Booking confirmed and rooms assigned.")
    except ValueError as exc:  # availability or cancellation state
        messages.error(request, str(exc))
    return redirect("bookings:booking_list")


@login_required
def booking_checkin_view(request: HttpRequest, pk: int) -> HttpResponse:
    booking = _get_booking_for_user(request, pk)
    booking.check_in_guests()
    messages.success(request, "Guest checked in.")
    return redirect("bookings:booking_list")


@login_required
def booking_checkout_view(request: HttpRequest, pk: int) -> HttpResponse:
    booking = _get_booking_for_user(request, pk)
    booking.check_out_guests()
    Invoice.generate_for_booking(booking)
    messages.success(request, "Guest checked out and invoice generated.")
    return redirect("bookings:booking_list")
