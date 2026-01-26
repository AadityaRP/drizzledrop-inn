from __future__ import annotations

import io
from typing import Any, Dict

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView

from bookings.models import Booking
from core.mixins import HotelAdminRequiredMixin, HotelScopedQuerysetMixin
from core.models import get_user_hotels
from core.scopes import get_current_hotel
from invoicing.models import Invoice
from core.scopes import ensure_user_has_hotel_access

try:
    from weasyprint import HTML  # pyright: ignore[reportMissingImports]
except Exception:  # pragma: no cover - optional dependency
    HTML = None


class InvoiceListView(HotelAdminRequiredMixin, HotelScopedQuerysetMixin, ListView):
    """
    List invoices scoped by hotel, with chain owner filter.
    """

    model = Invoice
    template_name = "invoicing/invoice_list.html"
    context_object_name = "invoices"
    require_current_hotel_for_admins = True

    def get_queryset(self):
        qs = super().get_queryset().select_related("hotel", "booking")
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
                "current_hotel": get_current_hotel(self.request),
                "accessible_hotels": get_user_hotels(self.request.user),
                "is_chain_owner": getattr(self.request.user, "is_chain_owner", False),
            }
        )
        return context


class InvoiceDetailView(HotelAdminRequiredMixin, HotelScopedQuerysetMixin, DetailView):
    model = Invoice
    template_name = "invoicing/invoice_detail.html"
    context_object_name = "invoice"
    require_current_hotel_for_admins = True


@login_required
def generate_invoice_view(request: HttpRequest, booking_id: int) -> HttpResponse:
    """
    Generate invoice for a booking and redirect to detail.
    """

    booking = get_object_or_404(Booking, pk=booking_id)
    ensure_user_has_hotel_access(request.user, booking.hotel)
    invoice = Invoice.generate_for_booking(booking)
    messages.success(request, f"Invoice {invoice.invoice_number} generated.")
    return redirect("invoicing:invoice_detail", pk=invoice.pk)


@login_required
def invoice_pdf_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Generate and download invoice as PDF using WeasyPrint.
    """

    invoice = get_object_or_404(Invoice, pk=pk)
    ensure_user_has_hotel_access(request.user, invoice.hotel)

    # Build absolute URLs for images
    # Use local file paths for WeasyPrint to avoid dev server deadlocks
    import os
    from pathlib import Path
    from django.contrib.staticfiles import finders
    
    def get_local_uri(relative_path):
        absolute_path = finders.find(relative_path)
        if absolute_path:
            return Path(absolute_path).as_uri()
        return ""

    logo_url = get_local_uri("assets/images/logo.jpeg")
    gpay_qr_full_url = get_local_uri("assets/images/gpay_scanner.png")

    # Debug info (will appear in server console)
    print(f"DEBUG: Logo URI: {logo_url}")
    print(f"DEBUG: GPay URI: {gpay_qr_full_url}")

    # Render HTML template
    html = render_to_string(
        "invoicing/invoice_pdf.html",
        {
            "invoice": invoice,
            "logo_url": logo_url,
            "gpay_qr_full_url": gpay_qr_full_url,
        },
    )

    # Check if WeasyPrint is available
    if HTML is None:
        # Fallback: return HTML in browser if WeasyPrint not installed
        return HttpResponse(html, content_type="text/html")

    # Generate PDF
    pdf_io = io.BytesIO()
    HTML(
        string=html,
        base_url=request.build_absolute_uri("/")
    ).write_pdf(pdf_io)

    # Create response with PDF
    response = HttpResponse(pdf_io.getvalue(), content_type="application/pdf")
    
    # Force download with proper filename
    response["Content-Disposition"] = (
        f'attachment; filename="{invoice.invoice_number}.pdf"'
    )
    
    return response


@login_required
def invoice_preview_view(request: HttpRequest, pk: int) -> HttpResponse:
    """
    Preview invoice in browser (HTML view) - useful for checking before download.
    """

    invoice = get_object_or_404(Invoice, pk=pk)
    ensure_user_has_hotel_access(request.user, invoice.hotel)

    # For preview (browser), we keep HTTP URLs
    logo_url = request.build_absolute_uri(
        settings.STATIC_URL + "assets/images/logo.jpeg"
    )
    
    gpay_qr_full_url = request.build_absolute_uri(
        settings.STATIC_URL + "assets/images/gpay_scanner.png"
    )

    html = render_to_string(
        "invoicing/invoice_pdf.html",
        {
            "invoice": invoice,
            "logo_url": logo_url,
            "gpay_qr_full_url": gpay_qr_full_url,
        },
    )

    return HttpResponse(html, content_type="text/html")


# @login_required
# def invoice_email_view(request: HttpRequest, pk: int) -> HttpResponse:
#     """
#     Email invoice PDF to guest if email configured.
#     """

#     invoice = get_object_or_404(Invoice, pk=pk)
#     ensure_user_has_hotel_access(request.user, invoice.hotel)
#     booking = invoice.booking
#     recipient = getattr(booking, "guest_email", None) or getattr(settings, "DEFAULT_TO_EMAIL", None)
    
#     if not recipient:
#         messages.error(request, "Guest email not available.")
#         return redirect("invoicing:invoice_detail", pk=pk)

#     # Build absolute URLs
#     logo_url = request.build_absolute_uri(
#         settings.STATIC_URL + "assets/images/logo.jpeg"
#     )
    
#     gpay_qr_full_url = request.build_absolute_uri(
#         settings.STATIC_URL + "assets/images/gpay-qr-full.png"
#     )

#     # Render HTML
#     html = render_to_string(
#         "invoicing/invoice_pdf.html", 
#         {
#             "invoice": invoice,
#             "logo_url": logo_url,
#             "gpay_qr_full_url": gpay_qr_full_url,
#         }
#     )
    
#     # Generate PDF if WeasyPrint available
#     if HTML:
#         pdf_io = io.BytesIO()
#         HTML(
#             string=html, 
#             base_url=request.build_absolute_uri("/")
#         ).write_pdf(pdf_io)
#         attachment = pdf_io.getvalue()
#     else:
#         attachment = None

#     # Create and send email
#     email = EmailMessage(
#         subject=f"Invoice {invoice.invoice_number} - DrizzleDrop Inn",
#         body=f"Dear {booking.guest_name},\n\nPlease find attached your invoice for booking.\n\nThank you for your business.\n\nDrizzleDrop Inn",
#         to=[recipient],
#     )
    
#     if attachment:
#         email.attach(
#             filename=f"{invoice.invoice_number}.pdf", 
#             content=attachment, 
#             mimetype="application/pdf"
#         )
    
#     email.send(fail_silently=False)
#     messages.success(request, f"Invoice emailed to {recipient}")
    
#     return redirect("invoicing:invoice_detail", pk=pk)