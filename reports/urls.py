from django.urls import path

from reports import views

app_name = "reports"

urlpatterns = [
    path("revenue/", views.RevenueReportView.as_view(), name="revenue_report"),
]
