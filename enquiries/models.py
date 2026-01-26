from __future__ import annotations

from datetime import date
from typing import Dict, Optional

from django.core.validators import MinValueValidator, RegexValidator
from django.db import models

from core.models import HotelScopedModel


class Enquiry(HotelScopedModel):
    """
    Customer enquiry captured before converting to booking.
    """

    class Status(models.TextChoices):
        NEW = "NEW", "New"
        FOLLOW_UP = "FOLLOW_UP", "Follow Up"
        CONVERTED = "CONVERTED", "Converted"
        LOST = "LOST", "Lost"

    EARLY_CHECKIN_OPTIONS = [
        ("5-7", "5:00 AM to 7:00 AM"),
        ("7-9", "Above 7:00 AM to 9:00 AM"),
        ("9-11", "Above 9:00 AM to 11:00 AM"),
    ]
    LATE_CHECKOUT_OPTIONS = [
        ("11-13", "11:00 AM to 1:00 PM"),
        ("13-15", "Above 1:00 PM to 3:00 PM"),
        ("15-17", "Above 3:00 PM to 5:00 PM"),
    ]

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
        related_name="enquiries",
    )
    with_food = models.BooleanField(default=False)
    extra_bed = models.BooleanField(default=False)
    early_check_in_option = models.CharField(
        max_length=16, choices=EARLY_CHECKIN_OPTIONS, blank=True
    )
    late_check_out_option = models.CharField(
        max_length=16, choices=LATE_CHECKOUT_OPTIONS, blank=True
    )
    special_request = models.TextField(blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.NEW,
    )
    created_by = models.ForeignKey(
        "users.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="enquiries_created",
    )

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        super().clean()
        if self.check_in and self.check_out and self.check_in >= self.check_out:
            raise models.ValidationError("Check-out must be after check-in.")

    def default_early_check_in(self) -> str:
        return "Standard after 11:00 AM" if not self.early_check_in_option else ""

    def default_late_check_out(self) -> str:
        return "Standard before 11:00 AM" if not self.late_check_out_option else ""

    def to_booking_payload(self) -> Dict[str, object]:
        """
        Helper to pre-fill booking form from enquiry data.
        """

        return {
            "hotel": self.hotel,
            "check_in": self.check_in,
            "check_out": self.check_out,
            "guest_name": self.guest_name,
            "guest_mobile": self.guest_mobile,
            "adults": self.adults,
            "children": self.children,
            "room_category": self.room_category,
            "with_food": self.with_food,
            "extra_bed": self.extra_bed,
            "early_check_in_option": self.early_check_in_option,
            "late_check_out_option": self.late_check_out_option,
            "special_request": self.special_request,
        }

    def stay_nights(self) -> int:
        if self.check_in and self.check_out:
            return (self.check_out - self.check_in).days
        return 0

    def is_future(self) -> bool:
        return bool(self.check_in and self.check_in >= date.today())

    def __str__(self) -> str:  # pragma: no cover - simple display
        return f"{self.guest_name} ({self.check_in} to {self.check_out})"
