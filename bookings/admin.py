from django.contrib import admin

from bookings.models import Booking, BookingRoom, Payment


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "guest_name",
        "hotel",
        "check_in",
        "check_out",
        "room_category",
        "rooms_count",
        "status",
    )
    list_filter = ("hotel", "status", "room_category")
    search_fields = ("guest_name", "guest_mobile")


@admin.register(BookingRoom)
class BookingRoomAdmin(admin.ModelAdmin):
    list_display = ("booking", "room")
    list_filter = ("room__hotel",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("booking", "amount", "mode", "payment_date", "is_advance")
    list_filter = ("mode", "is_advance")
