from __future__ import annotations

from typing import Any, Dict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView

from core.mixins import ChainOwnerRequiredMixin, HotelAdminRequiredMixin
from core.models import get_user_hotels
from core.scopes import ensure_user_has_hotel_access, get_current_hotel, set_current_hotel


def _redirect_target(request: HttpRequest) -> str:
    """
    Decide where to send the user after switching hotel or login.
    """

    next_url = request.GET.get("next") or request.POST.get("next")
    if next_url:
        return next_url
    referrer = request.META.get("HTTP_REFERER")
    if referrer:
        return referrer
    return reverse("dashboard:dashboard_redirect")


@login_required
def dashboard_redirect_view(request: HttpRequest) -> HttpResponse:
    """
    Route users to the correct dashboard based on their role.
    """

    user = request.user
    if getattr(user, "is_chain_owner", False):
        return redirect("dashboard:chain_owner_dashboard")
    return redirect("dashboard:hotel_admin_dashboard")


class _BaseDashboardView(TemplateView):
    """
    Shared helpers for dashboard templates.
    """

    def _base_context(self) -> Dict[str, Any]:
        user = self.request.user
        return {
            "accessible_hotels": get_user_hotels(user),
            "current_hotel": get_current_hotel(self.request),
        }

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context.update(self._base_context())
        return context


class ChainOwnerDashboardView(ChainOwnerRequiredMixin, _BaseDashboardView):
    """
    Dashboard landing for chain owners / superusers.
    """

    template_name = "dashboard/chain_dashboard.html"


class HotelAdminDashboardView(HotelAdminRequiredMixin, _BaseDashboardView):
    """
    Dashboard landing for hotel admins, ensuring a hotel is selected.
    """

    template_name = "dashboard/hotel_dashboard.html"

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        current_hotel = get_current_hotel(request)
        accessible_hotels = get_user_hotels(request.user)

        if not current_hotel and accessible_hotels.exists():
            default_hotel = accessible_hotels.first()
            if default_hotel:
                set_current_hotel(request, default_hotel.id)
                messages.info(
                    request,
                    f"Switched to {default_hotel.name} as your active hotel.",
                )
                return redirect("dashboard:hotel_admin_dashboard")

        if current_hotel:
            ensure_user_has_hotel_access(request.user, current_hotel)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["current_hotel"] = get_current_hotel(self.request)
        return context


@login_required
def switch_hotel_view(request: HttpRequest) -> HttpResponse:
    """
    Persist the selected hotel into the session for subsequent requests.
    """

    if request.method != "POST":
        return redirect(_redirect_target(request))

    hotel_id = request.POST.get("hotel_id")
    user_hotels = get_user_hotels(request.user)

    if not hotel_id:
        set_current_hotel(request, None)
        messages.info(request, "Cleared current hotel selection.")
        return redirect(_redirect_target(request))

    try:
        hotel_id_int = int(hotel_id)
    except (TypeError, ValueError):
        messages.error(request, "Invalid hotel selection.")
        return redirect(_redirect_target(request))

    hotel = user_hotels.filter(id=hotel_id_int).first()
    if not hotel:
        messages.error(request, "You do not have access to that hotel.")
        return redirect(_redirect_target(request))

    set_current_hotel(request, hotel.id)
    messages.success(request, f"Switched to {hotel.name}.")
    return redirect(_redirect_target(request))
