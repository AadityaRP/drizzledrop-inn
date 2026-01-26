from __future__ import annotations

from typing import Any, Dict

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from core.mixins import (
    ChainOwnerRequiredMixin,
    HotelAdminRequiredMixin,
    HotelScopedQuerysetMixin,
)
from core.models import get_user_hotels
from core.scopes import get_current_hotel
from hotels.forms import HotelForm, RoomCategoryForm, RoomForm
from hotels.models import Hotel, Room, RoomCategory


class HotelListView(HotelAdminRequiredMixin, ListView):
    """
    Display hotels. Chain owners see all; hotel admins see their assigned ones (read-only).
    """

    template_name = "hotels/hotel_list.html"
    model = Hotel
    context_object_name = "hotels"

    def get_queryset(self):
        qs = super().get_queryset().select_related("chain")
        user_hotels = get_user_hotels(self.request.user)
        if getattr(self.request.user, "is_chain_owner", False):
            return qs
        return qs.filter(id__in=user_hotels.values_list("id", flat=True))

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "is_chain_owner": getattr(self.request.user, "is_chain_owner", False),
                "accessible_hotels": get_user_hotels(self.request.user),
            }
        )
        return context


class HotelCreateView(ChainOwnerRequiredMixin, CreateView):
    """
    Create hotels (chain owners / superusers only).
    """

    template_name = "hotels/hotel_form.html"
    form_class = HotelForm
    success_url = reverse_lazy("hotels:hotel_list")

    def form_valid(self, form: HotelForm) -> HttpResponse:
        messages.success(self.request, "Hotel created successfully.")
        return super().form_valid(form)


class HotelUpdateView(ChainOwnerRequiredMixin, UpdateView):
    """
    Update hotels (chain owners / superusers only).
    """

    template_name = "hotels/hotel_form.html"
    form_class = HotelForm
    model = Hotel
    success_url = reverse_lazy("hotels:hotel_list")

    def form_valid(self, form: HotelForm) -> HttpResponse:
        messages.success(self.request, "Hotel updated successfully.")
        return super().form_valid(form)


class HotelDeleteView(ChainOwnerRequiredMixin, DeleteView):
    """
    Delete hotels (chain owners / superusers only).
    """

    template_name = "hotels/hotel_confirm_delete.html"
    model = Hotel
    success_url = reverse_lazy("hotels:hotel_list")

    def delete(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        messages.success(request, "Hotel deleted.")
        return super().delete(request, *args, **kwargs)


class RoomCategoryListView(
    HotelAdminRequiredMixin, HotelScopedQuerysetMixin, ListView
):
    """
    List room categories. Chain owners see all; hotel admins see current hotel only.
    """

    model = RoomCategory
    template_name = "hotels/roomcategory_list.html"
    context_object_name = "categories"
    require_current_hotel_for_admins = True

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("hotel")
            .order_by("hotel__name", "name")
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


class RoomCategoryCreateView(ChainOwnerRequiredMixin, CreateView):
    """
    Create room categories (chain owners / superusers only).
    """

    template_name = "hotels/roomcategory_form.html"
    form_class = RoomCategoryForm
    success_url = reverse_lazy("hotels:room_category_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form: RoomCategoryForm) -> HttpResponse:
        messages.success(self.request, "Room category created.")
        return super().form_valid(form)


class RoomCategoryUpdateView(ChainOwnerRequiredMixin, UpdateView):
    """
    Update room categories (chain owners / superusers only).
    """

    template_name = "hotels/roomcategory_form.html"
    form_class = RoomCategoryForm
    model = RoomCategory
    success_url = reverse_lazy("hotels:room_category_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form: RoomCategoryForm) -> HttpResponse:
        messages.success(self.request, "Room category updated.")
        return super().form_valid(form)


class RoomCategoryDeleteView(ChainOwnerRequiredMixin, DeleteView):
    """
    Delete room categories (chain owners / superusers only).
    """

    template_name = "hotels/roomcategory_confirm_delete.html"
    model = RoomCategory
    success_url = reverse_lazy("hotels:room_category_list")

    def delete(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        messages.success(request, "Room category deleted.")
        return super().delete(request, *args, **kwargs)


class RoomListView(HotelAdminRequiredMixin, HotelScopedQuerysetMixin, ListView):
    """
    List rooms. Chain owners see all; hotel admins see rooms for the selected hotel.
    """

    model = Room
    template_name = "hotels/room_list.html"
    context_object_name = "rooms"
    require_current_hotel_for_admins = True

    def get_queryset(self):
        qs = (
            super()
            .get_queryset()
            .select_related("hotel", "category")
            .order_by("hotel__name", "room_number")
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


class RoomCreateView(ChainOwnerRequiredMixin, CreateView):
    """
    Create rooms (chain owners / superusers only).
    """

    template_name = "hotels/room_form.html"
    form_class = RoomForm
    success_url = reverse_lazy("hotels:room_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form: RoomForm) -> HttpResponse:
        messages.success(self.request, "Room created.")
        return super().form_valid(form)


class RoomUpdateView(ChainOwnerRequiredMixin, UpdateView):
    """
    Update rooms (chain owners / superusers only).
    """

    template_name = "hotels/room_form.html"
    form_class = RoomForm
    model = Room
    success_url = reverse_lazy("hotels:room_list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def form_valid(self, form: RoomForm) -> HttpResponse:
        messages.success(self.request, "Room updated.")
        return super().form_valid(form)


class RoomDeleteView(ChainOwnerRequiredMixin, DeleteView):
    """
    Delete rooms (chain owners / superusers only).
    """

    template_name = "hotels/room_confirm_delete.html"
    model = Room
    success_url = reverse_lazy("hotels:room_list")

    def delete(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        messages.success(request, "Room deleted.")
        return super().delete(request, *args, **kwargs)
