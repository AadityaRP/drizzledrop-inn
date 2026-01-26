from __future__ import annotations

from typing import Optional

from django.apps import apps
from django.db import models


class TimeStampedModel(models.Model):
    """
    Abstract base model that tracks creation and update timestamps.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


def _user_is_chain_owner(user: models.Model) -> bool:
    """
    Helper to keep chain-owner checks in one place.
    """

    role = getattr(user, "role", None)
    roles = getattr(user.__class__, "Roles", None)
    is_chain_owner = bool(role and roles and role == getattr(roles, "CHAIN_OWNER", None))
    return bool(is_chain_owner or getattr(user, "is_superuser", False))


def get_user_hotels(user: models.Model):
    """
    Return a queryset of hotels the user can access.

    - Chain owners / superusers: all hotels.
    - Hotel admins / staff: hotels linked through HotelUser.
    - Anonymous users: empty queryset.
    """

    Hotel = apps.get_model("hotels", "Hotel")
    HotelUser = apps.get_model("users", "HotelUser")

    if not getattr(user, "is_authenticated", False):
        return Hotel.objects.none()

    if _user_is_chain_owner(user):
        return Hotel.objects.all()

    return Hotel.objects.filter(
        id__in=HotelUser.objects.filter(user=user).values_list("hotel_id", flat=True)
    )


class HotelScopedQuerySet(models.QuerySet):
    """
    QuerySet with helpers to enforce hotel-level isolation.
    """

    def for_user(self, user: models.Model) -> "HotelScopedQuerySet":
        """
        Restrict records to hotels the user is allowed to see.
        """

        if not getattr(user, "is_authenticated", False):
            return self.none()

        if _user_is_chain_owner(user):
            return self

        return self.filter(hotel__in=get_user_hotels(user))

    def for_hotel(self, hotel: Optional[models.Model]) -> "HotelScopedQuerySet":
        """
        Restrict records to a specific hotel when provided.
        """

        if hotel is None:
            return self.none()
        return self.filter(hotel=hotel)


class HotelScopedManager(models.Manager.from_queryset(HotelScopedQuerySet)):
    """
    Manager that exposes scoped helpers on related lookups as well.
    """

    use_in_migrations = True


class HotelScopedModel(TimeStampedModel):
    """
    Base model for any entity that belongs to a specific hotel.
    """

    hotel = models.ForeignKey(
        "hotels.Hotel",
        on_delete=models.CASCADE,
        related_name="%(class)ss",
        help_text="Hotel this record belongs to.",
    )

    objects = HotelScopedManager()

    class Meta:
        abstract = True
