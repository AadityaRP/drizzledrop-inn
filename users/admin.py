from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import HotelUser, User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "Role & Contact",
            {
                "fields": (
                    "role",
                    "phone",
                )
            },
        ),
    )
    list_display = ("username", "email", "role", "is_staff", "is_superuser")
    list_filter = DjangoUserAdmin.list_filter + ("role",)


@admin.register(HotelUser)
class HotelUserAdmin(admin.ModelAdmin):
    list_display = ("user", "hotel", "is_primary_admin")
    list_filter = ("hotel", "is_primary_admin")
    search_fields = ("user__username", "user__email", "hotel__name", "hotel__code")
