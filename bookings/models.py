from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import List, Optional

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models, transaction

from core.models import HotelScopedModel
from hotels.models import Room


class Booking(HotelScopedModel):
    """
    A room booking scoped to a hotel.
    """

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        CHECKED_IN = "CHECKED_IN", "Checked In"
        CHECKED_OUT = "CHECKED_OUT", "Checked Out"
        CANCELLED = "CANCELLED", "Cancelled"

    enquiry = models.ForeignKey(
        "enquiries.Enquiry",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings",
    )
    check_in = models.DateField()
    check_out = models.DateField()
    guest_name = models.CharField(max_length=255)
    guest_mobile = models.CharField(
        max_length=20,
        validators=[
            RegexValidator(
                regex=r"^[0-9+\-\s]{8,20}$",
                message="Enter a valid mobile number.",
            )
        ],
    )
    adults = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    children = models.PositiveIntegerField(default=0)
    room_category = models.ForeignKey(
        "hotels.RoomCategory",
        on_delete=models.PROTECT,
        related_name="bookings",
    )
    rooms_count = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    with_food = models.BooleanField(default=False)
    extra_bed = models.BooleanField(default=False)
    early_check_in_option = models.CharField(max_length=16, blank=True)
    late_check_out_option = models.CharField(max_length=16, blank=True)
    special_request = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings_created",
    )
    updated_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="bookings_updated",
    )

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        super().clean()
        if self.check_in and self.check_out and self.check_in >= self.check_out:
            raise models.ValidationError("Check-out must be after check-in.")
        if self.check_in and self.check_in < date.today():
            # Allow past dates for updates but warn.
            pass

    def nights(self) -> int:
        return (self.check_out - self.check_in).days if self.check_in and self.check_out else 0

    def assign_rooms(self) -> List[Room]:
        """
        Assign available rooms up to rooms_count. Returns assigned rooms.
        """

        available = get_available_rooms(
            hotel=self.hotel,
            category=self.room_category,
            check_in=self.check_in,
            check_out=self.check_out,
        )[: self.rooms_count]
        if len(available) < self.rooms_count:
            raise ValueError("Not enough rooms available for the requested dates.")

        BookingRoom.objects.bulk_create(
            [BookingRoom(booking=self, room=room) for room in available]
        )
        return available

    @transaction.atomic
    def confirm(self):
        """
        Confirm the booking and assign rooms if not already assigned.
        """

        if self.status == self.Status.CANCELLED:
            raise ValueError("Cannot confirm a cancelled booking.")

        self.status = self.Status.CONFIRMED
        self.save(update_fields=["status", "updated_at"])
        if not self.rooms.exists():
            self.assign_rooms()

    def check_in_guests(self):
        self.status = self.Status.CHECKED_IN
        self.save(update_fields=["status", "updated_at"])

    def check_out_guests(self):
        self.status = self.Status.CHECKED_OUT
        self.save(update_fields=["status", "updated_at"])

    def total_room_charge(self) -> Decimal:
        rate = self.room_category.base_rate or Decimal("0.00")
        nights = self.nights()
        return rate * self.rooms_count * nights

    def __str__(self) -> str:  # pragma: no cover - simple display
        return f"Booking {self.id or ''} - {self.guest_name}"


class BookingRoom(models.Model):
    """
    Mapping of specific rooms assigned to a booking.
    """

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="rooms",
    )
    room = models.ForeignKey(
        "hotels.Room",
        on_delete=models.PROTECT,
        related_name="room_bookings",
    )

    class Meta:
        unique_together = ("booking", "room")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.room} -> booking {self.booking_id}"


class Payment(models.Model):
    """
    Payment linked to a booking (advance or settlement).
    """

    class Mode(models.TextChoices):
        CASH = "CASH", "Cash"
        CARD = "CARD", "Card"
        UPI = "UPI", "UPI"
        BANK = "BANK", "Bank Transfer"

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    mode = models.CharField(max_length=16, choices=Mode.choices, default=Mode.UPI)
    is_advance = models.BooleanField(default=False)
    payment_date = models.DateField(default=date.today)
    notes = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.amount} via {self.mode} on {self.payment_date}"


def get_available_rooms(hotel, category, check_in, check_out):
    """
    Return queryset of rooms available for the given window.
    """

    overlapping = BookingRoom.objects.filter(
        booking__hotel=hotel,
        booking__room_category=category,
        booking__status__in=[
            Booking.Status.CONFIRMED,
            Booking.Status.CHECKED_IN,
        ],
        booking__check_in__lt=check_out,
        booking__check_out__gt=check_in,
    ).values_list("room_id", flat=True)

    return Room.objects.filter(
        hotel=hotel,
        category=category,
        is_active=True,
    ).exclude(id__in=overlapping).order_by("room_number")
