from __future__ import annotations

from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from bookings.models import Booking
from core.mixins import (
    ChainOwnerRequiredMixin,
    HotelAdminRequiredMixin,
    HotelScopedQuerysetMixin,
)
from core.models import get_user_hotels
from core.scopes import get_current_hotel
from enquiries.forms import EnquiryForm
from enquiries.models import Enquiry
from django.db import transaction


class EnquiryListView(HotelAdminRequiredMixin, HotelScopedQuerysetMixin, ListView):
    """
    List enquiries scoped to current hotel or all for chain owners.
    """

    model = Enquiry
    template_name = "enquiries/enquiry_list.html"
    context_object_name = "enquiries"
    require_current_hotel_for_admins = True

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("hotel", "room_category", "created_by")
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


class EnquiryCreateView(HotelAdminRequiredMixin, CreateView):
    """
    Create a new enquiry for the current hotel scope.
    """

    model = Enquiry
    form_class = EnquiryForm
    template_name = "enquiries/enquiry_form.html"
    success_url = reverse_lazy("enquiries:enquiry_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form: EnquiryForm) -> HttpResponse:
        form.instance.created_by = self.request.user
        messages.success(self.request, "Enquiry saved successfully.")
        return super().form_valid(form)


class EnquiryUpdateView(HotelAdminRequiredMixin, HotelScopedQuerysetMixin, UpdateView):
    """
    Update an enquiry within the user's hotel scope.
    """

    model = Enquiry
    form_class = EnquiryForm
    template_name = "enquiries/enquiry_form.html"
    success_url = reverse_lazy("enquiries:enquiry_list")
    require_current_hotel_for_admins = True

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form: EnquiryForm) -> HttpResponse:
        messages.success(self.request, "Enquiry updated successfully.")
        return super().form_valid(form)


class EnquiryDeleteView(ChainOwnerRequiredMixin, DeleteView):
    """
    Allow chain owners to delete enquiries if needed.
    """

    model = Enquiry
    template_name = "enquiries/enquiry_confirm_delete.html"
    success_url = reverse_lazy("enquiries:enquiry_list")

    def delete(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        messages.success(request, "Enquiry deleted.")
        return super().delete(request, *args, **kwargs)


@login_required
@transaction.atomic
def convert_enquiry_to_booking(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Convert an enquiry to a booking.
    Marks the enquiry as CONVERTED and creates a new Booking record.
    """
    enquiry = get_object_or_404(Enquiry, pk=pk)
    # Security: Check user has access to this enquiry's hotel
    from core.models import get_user_hotels
    user_hotels = get_user_hotels(request.user)
    if enquiry.hotel not in user_hotels:
        messages.error(request, "You don't have access to this enquiry.")
        return redirect("enquiries:enquiry_list")
    # Prevent duplicate conversion
    if enquiry.status == Enquiry.Status.CONVERTED:
        messages.warning(request, "This enquiry has already been converted.")
        return redirect("enquiries:enquiry_list")
    try:
        # Get the payload from enquiry
        booking_data = enquiry.to_booking_payload()
        
        # Create the booking with the payload data
        # Note: We don't pass hotel separately since it's already in booking_data
        booking = Booking.objects.create(
            **booking_data,
            created_by=request.user,
        )
        # Mark enquiry as converted
        enquiry.status = Enquiry.Status.CONVERTED
        enquiry.save(update_fields=["status", "updated_at"])
        messages.success(
            request,
            f"Enquiry converted to booking successfully. Booking ID: {booking.id}",
        )
        return redirect("bookings:booking_detail", pk=booking.pk)
    except Exception as e:
        messages.error(request, f"Error converting enquiry: {str(e)}")
        return redirect("enquiries:enquiry_list")