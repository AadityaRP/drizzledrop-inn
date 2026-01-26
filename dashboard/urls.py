from django.urls import path

from dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.dashboard_redirect_view, name="dashboard_redirect"),
    path("chain/", views.ChainOwnerDashboardView.as_view(), name="chain_owner_dashboard"),
    path("hotel/", views.HotelAdminDashboardView.as_view(), name="hotel_admin_dashboard"),
    path("switch-hotel/", views.switch_hotel_view, name="switch_hotel"),
]
