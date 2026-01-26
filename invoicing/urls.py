from django.urls import path
from . import views

app_name = "invoicing"

urlpatterns = [
    path("", views.InvoiceListView.as_view(), name="invoice_list"),
    path("<int:pk>/", views.InvoiceDetailView.as_view(), name="invoice_detail"),
    path("generate/<int:booking_id>/", views.generate_invoice_view, name="generate_invoice"),
    path("<int:pk>/preview/", views.invoice_preview_view, name="invoice_preview"),  # HTML preview
    path("<int:pk>/pdf/", views.invoice_pdf_view, name="invoice_pdf"),  # Download PDF
    # path("<int:pk>/email/", views.invoice_email_view, name="invoice_email"),  # Email PDF
]