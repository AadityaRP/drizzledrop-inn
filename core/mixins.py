from __future__ import annotations

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.exceptions import PermissionDenied

from core.models import _user_is_chain_owner, get_user_hotels
from core.scopes import get_current_hotel


class ChainOwnerRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Restrict access to chain owners (or superusers).
    """

    def test_func(self) -> bool:  # pragma: no cover - simple predicate
        return _user_is_chain_owner(self.request.user)


class HotelAdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Allow Hotel Admins or Chain Owners.
    """

    def test_func(self) -> bool:  # pragma: no cover - simple predicate
        user = self.request.user
        roles = getattr(user.__class__, "Roles", None)
        is_hotel_admin = getattr(user, "role", None) == getattr(roles, "HOTEL_ADMIN", None)
        return bool(_user_is_chain_owner(user) or is_hotel_admin)


class HotelScopedQuerysetMixin(LoginRequiredMixin):
    """
    Automatically filter querysets to the current user's hotel scope.
    """

    hotel_field = "hotel"
    allow_chain_owner_all = True
    require_current_hotel_for_admins = False

    def get_current_hotel(self):
        return get_current_hotel(self.request)

    def get_queryset(self):
        base_qs = super().get_queryset()
        user = self.request.user
        current_hotel = self.get_current_hotel()

        if not user.is_authenticated:
            return base_qs.none()

        if _user_is_chain_owner(user):
            if self.allow_chain_owner_all:
                return base_qs
            if current_hotel:
                return base_qs.filter(**{self.hotel_field: current_hotel})
            return base_qs.none()

        if current_hotel:
            return base_qs.filter(**{self.hotel_field: current_hotel})

        if self.require_current_hotel_for_admins:
            raise PermissionDenied("Select a hotel to continue.")

        return base_qs.filter(**{f"{self.hotel_field}__in": get_user_hotels(user)})
