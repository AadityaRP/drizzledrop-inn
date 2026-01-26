from __future__ import annotations

from datetime import date
from typing import Any, Dict

from django.db.models import Count, Sum
from django.views.generic import TemplateView

from core.mixins import HotelAdminRequiredMixin, HotelScopedQuerysetMixin
from core.models import get_user_hotels
from core.scopes import get_current_hotel
from invoicing.models import Invoice


class RevenueReportView(HotelAdminRequiredMixin, HotelScopedQuerysetMixin, TemplateView):
    """
    Revenue and GST report (daily + monthly) for the selected hotel scope.
    """

    template_name = "reports/revenue_report.html"
    require_current_hotel_for_admins = True

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        current_hotel = get_current_hotel(self.request)
        qs = self.get_queryset()
        today = date.today()
        month_qs = qs.filter(issue_date__year=today.year, issue_date__month=today.month)
        daily = qs.filter(issue_date=today).aggregate(
            total=Sum("total_amount"), gst=Sum("gst_amount"), count=Count("id")
        )
        monthly = month_qs.aggregate(
            total=Sum("total_amount"), gst=Sum("gst_amount"), count=Count("id")
        )
        context.update(
            {
                "current_hotel": current_hotel,
                "accessible_hotels": get_user_hotels(self.request.user),
                "is_chain_owner": getattr(self.request.user, "is_chain_owner", False),
                "daily": daily,
                "monthly": monthly,
                "monthly_invoices": month_qs.order_by("-issue_date")[:50],
            }
        )
        return context

    def get_queryset(self):
        qs = Invoice.objects.all().select_related("hotel", "booking")
        hotel_id = self.request.GET.get("hotel")
        if getattr(self.request.user, "is_chain_owner", False) and hotel_id:
            try:
                qs = qs.filter(hotel_id=int(hotel_id))
            except (TypeError, ValueError):
                pass
        else:
            current_hotel = get_current_hotel(self.request)
            if current_hotel:
                qs = qs.filter(hotel=current_hotel)
        return qs
