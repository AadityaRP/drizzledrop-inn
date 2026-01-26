from django.contrib import admin

from .models import Chain, Hotel, Room, RoomCategory


@admin.register(Chain)
class ChainAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)


@admin.register(Hotel)
class HotelAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "chain", "email", "contact_numbers")
    list_filter = ("chain",)
    search_fields = ("name", "code", "email")


@admin.register(RoomCategory)
class RoomCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "hotel", "with_food", "base_rate", "tax_rate")
    list_filter = ("hotel", "with_food")
    search_fields = ("name", "hotel__name", "hotel__code")


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("room_number", "hotel", "category", "is_active")
    list_filter = ("hotel", "category", "is_active")
    search_fields = ("room_number", "hotel__name", "hotel__code")
