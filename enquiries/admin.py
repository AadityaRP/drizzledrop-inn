from django.contrib import admin

from enquiries.models import Enquiry


@admin.register(Enquiry)
class EnquiryAdmin(admin.ModelAdmin):
    list_display = (
        "guest_name",
        "guest_mobile",
        "hotel",
        "check_in",
        "check_out",
        "room_category",
        "status",
        "created_at",
    )
    list_filter = ("hotel", "status", "room_category")
    search_fields = ("guest_name", "guest_mobile")
