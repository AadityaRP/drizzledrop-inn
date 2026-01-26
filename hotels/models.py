from __future__ import annotations

from django.db import models

from core.models import HotelScopedModel, TimeStampedModel


class Chain(TimeStampedModel):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self) -> str:  # pragma: no cover - simple display
        return self.name


class Hotel(TimeStampedModel):
    chain = models.ForeignKey(
        Chain,
        on_delete=models.CASCADE,
        related_name="hotels",
    )
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=32, unique=True)
    address = models.TextField(blank=True)
    gstin = models.CharField(max_length=32, blank=True)
    contact_numbers = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)

    class Meta:
        unique_together = ("chain", "code")
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - simple display
        return f"{self.name} ({self.code})"


class RoomCategory(HotelScopedModel):
    name = models.CharField(max_length=100)
    with_food = models.BooleanField(default=False)
    base_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    extra_bed_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="GST rate percentage for the room category.",
    )
    max_adults = models.PositiveIntegerField(default=2)
    max_children = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("hotel", "name", "with_food")
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - simple display
        suffix = " (with food)" if self.with_food else ""
        return f"{self.name}{suffix} @ {self.hotel.code}"


class Room(HotelScopedModel):
    category = models.ForeignKey(
        RoomCategory,
        on_delete=models.PROTECT,
        related_name="rooms",
    )
    room_number = models.CharField(max_length=20)
    floor = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("hotel", "room_number")
        ordering = ["hotel__name", "room_number"]

    def __str__(self) -> str:  # pragma: no cover - simple display
        return f"{self.room_number} - {self.hotel.code}"
