from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.db import models, transaction

from core.models import HotelScopedModel, TimeStampedModel


class InvoiceSequence(TimeStampedModel):
    """
    Per-hotel invoice sequence generator.
    """

    hotel = models.OneToOneField(
        "hotels.Hotel",
        on_delete=models.CASCADE,
        related_name="invoice_sequence",
    )
    prefix = models.CharField(max_length=32, default="DDI")
    current_number = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Invoice sequence"
        verbose_name_plural = "Invoice sequences"

    def next_number(self) -> str:
        with transaction.atomic():
            seq = InvoiceSequence.objects.select_for_update().get(pk=self.pk)
            seq.current_number += 1
            seq.save(update_fields=["current_number", "updated_at"])
        return f"{self.prefix}-{self.hotel.code}-{date.today().year}-{seq.current_number:04d}"

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.prefix} {self.hotel.code} ({self.current_number})"


class Invoice(HotelScopedModel):
    """
    GST-compliant invoice linked to a booking.
    """

    class PaymentStatus(models.TextChoices):
        UNPAID = "UNPAID", "Unpaid"
        PARTIAL = "PARTIAL", "Partial"
        PAID = "PAID", "Paid"

    booking = models.OneToOneField(
        "bookings.Booking",
        on_delete=models.CASCADE,
        related_name="invoice",
    )
    invoice_number = models.CharField(max_length=64, unique=True)
    issue_date = models.DateField(default=date.today)
    taxable_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    gst_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    gst_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_status = models.CharField(
        max_length=16,
        choices=PaymentStatus.choices,
        default=PaymentStatus.UNPAID,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-issue_date", "-created_at"]

    @classmethod
    def generate_for_booking(cls, booking) -> "Invoice":
        """
        Create or refresh invoice for a booking with calculated GST.
        """

        seq, _ = InvoiceSequence.objects.get_or_create(hotel=booking.hotel)
        invoice_number = seq.next_number()
        taxable = booking.total_room_charge()
        gst_rate = booking.room_category.tax_rate or Decimal("0.00")
        gst_amount = (taxable * gst_rate) / Decimal("100")
        total = taxable + gst_amount
        invoice, _ = cls.objects.update_or_create(
            booking=booking,
            defaults={
                "hotel": booking.hotel,
                "invoice_number": invoice_number,
                "taxable_amount": taxable,
                "gst_rate": gst_rate,
                "gst_amount": gst_amount,
                "total_amount": total,
            },
        )
        return invoice

    def __str__(self) -> str:  # pragma: no cover
        return self.invoice_number
