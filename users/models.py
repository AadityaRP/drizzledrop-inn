from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model for Drizzle Drop Inn chain system.

    Extends Django's AbstractUser to add role and phone fields.
    """

    class Roles(models.TextChoices):
        CHAIN_OWNER = "CHAIN_OWNER", "Chain Owner"
        HOTEL_ADMIN = "HOTEL_ADMIN", "Hotel Admin"
        STAFF = "STAFF", "Staff"

    role = models.CharField(
        max_length=32,
        choices=Roles.choices,
        default=Roles.STAFF,
        help_text="Defines the access level within the Drizzle Drop Inn chain.",
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        help_text="Primary contact number for the user.",
    )

    @property
    def is_chain_owner(self) -> bool:
        return bool(
            self.role == self.Roles.CHAIN_OWNER or getattr(self, "is_superuser", False)
        )

    @property
    def is_hotel_admin(self) -> bool:
        return self.role == self.Roles.HOTEL_ADMIN

    def primary_hotel(self):
        membership = self.hotel_memberships.filter(is_primary_admin=True).first()
        if membership:
            return membership.hotel
        membership = self.hotel_memberships.first()
        return membership.hotel if membership else None

    def __str__(self) -> str:  # type: ignore[override]
        name = self.get_full_name() or self.username
        return f"{name} ({self.get_role_display()})"


class HotelUser(models.Model):
    """
    Link users to hotels with an optional primary assignment flag.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="hotel_memberships",
    )
    hotel = models.ForeignKey(
        "hotels.Hotel",
        on_delete=models.CASCADE,
        related_name="user_memberships",
    )
    is_primary_admin = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "hotel")
        verbose_name = "Hotel assignment"
        verbose_name_plural = "Hotel assignments"

    def __str__(self) -> str:  # pragma: no cover - simple display
        return f"{self.user} @ {self.hotel}"
