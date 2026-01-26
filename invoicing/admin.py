from django.contrib import admin

from invoicing.models import Invoice, InvoiceSequence


@admin.register(InvoiceSequence)
class InvoiceSequenceAdmin(admin.ModelAdmin):
    list_display = ("hotel", "prefix", "current_number", "updated_at")


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = (
        "invoice_number",
        "hotel",
        "booking",
        "issue_date",
        "total_amount",
        "payment_status",
    )
    list_filter = ("hotel", "payment_status")
    search_fields = ("invoice_number", "booking__guest_name")
