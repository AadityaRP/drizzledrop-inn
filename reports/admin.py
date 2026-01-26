from django.contrib import admin

from reports.models import DailyRevenueSnapshot, MonthlyRevenueSnapshot


@admin.register(DailyRevenueSnapshot)
class DailyRevenueSnapshotAdmin(admin.ModelAdmin):
    list_display = ("hotel", "snapshot_date", "total_revenue", "gst_amount", "bookings_count")
    list_filter = ("hotel", "snapshot_date")


@admin.register(MonthlyRevenueSnapshot)
class MonthlyRevenueSnapshotAdmin(admin.ModelAdmin):
    list_display = ("hotel", "year", "month", "total_revenue", "gst_amount", "bookings_count")
    list_filter = ("hotel", "year", "month")
