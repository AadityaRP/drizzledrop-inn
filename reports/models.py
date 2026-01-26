from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db import models

from core.models import HotelScopedModel


class DailyRevenueSnapshot(HotelScopedModel):
    """
    Aggregated daily revenue for performance reporting.
    """

    snapshot_date = models.DateField(default=date.today)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bookings_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("hotel", "snapshot_date")
        ordering = ["-snapshot_date"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.hotel.code} {self.snapshot_date}: {self.total_revenue}"


class MonthlyRevenueSnapshot(HotelScopedModel):
    """
    Monthly revenue summary grouped by hotel.
    """

    year = models.PositiveIntegerField()
    month = models.PositiveIntegerField()
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bookings_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("hotel", "year", "month")
        ordering = ["-year", "-month"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.hotel.code} {self.year}-{self.month}: {self.total_revenue}"
