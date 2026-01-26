from django.urls import path

from bookings import views

app_name = "bookings"

urlpatterns = [
    path("", views.BookingListView.as_view(), name="booking_list"),
    path("add/", views.BookingCreateView.as_view(), name="booking_create"),
    path("<int:pk>/edit/", views.BookingUpdateView.as_view(), name="booking_update"),
    path("<int:pk>/confirm/", views.booking_confirm_view, name="booking_confirm"),
    path("<int:pk>/check-in/", views.booking_checkin_view, name="booking_checkin"),
    path("<int:pk>/check-out/", views.booking_checkout_view, name="booking_checkout"),
]
