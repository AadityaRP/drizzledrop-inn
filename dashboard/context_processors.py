from __future__ import annotations

from typing import Dict, List

from django.urls import NoReverseMatch, reverse

from core.models import get_user_hotels
from core.scopes import get_current_hotel


def _safe_reverse(name: str) -> str:
    """
    Attempt to reverse a URL name, falling back to "#" if not configured yet.
    """

    try:
        return reverse(name)
    except NoReverseMatch:
        return "#"


def sidebar_menu(request) -> Dict[str, object]:
    """
    Provide sidebar items and hotel context to templates.
    """

    user = getattr(request, "user", None)
    if not getattr(user, "is_authenticated", False):
        return {
            "sidebar_menu": [],
            "current_hotel": None,
            "accessible_hotels": get_user_hotels(user),
        }

    is_chain_owner = getattr(user, "is_chain_owner", False)
    dashboard_url = (
        _safe_reverse("dashboard:chain_owner_dashboard")
        if is_chain_owner
        else _safe_reverse("dashboard:hotel_admin_dashboard")
    )

    items: List[Dict[str, object]] = [
        {
            "label": "Dashboard",
            "icon": "bi-speedometer2",
            "url": dashboard_url,
            "section": "main",
        },
        {
            "label": "Bookings",
            "icon": "bi-journal-check",
            "url": _safe_reverse("bookings:booking_list"),
            "section": "main",
        },
        {
            "label": "Enquiries",
            "icon": "bi-chat-dots",
            "url": _safe_reverse("enquiries:enquiry_list"),
            "section": "main",
        },
        {
            "label": "Invoices",
            "icon": "bi-receipt",
            "url": _safe_reverse("invoicing:invoice_list"),
            "section": "main",
        },
        {
            "label": "Rooms",
            "icon": "bi-door-closed",
            "url": _safe_reverse("hotels:room_list"),
            "section": "main",
        },
        {
            "label": "Room Categories",
            "icon": "bi-grid-3x3-gap",
            "url": _safe_reverse("hotels:room_category_list"),
            "section": "main",
        },
        {
            "label": "Reports",
            "icon": "bi-graph-up",
            "url": _safe_reverse("reports:revenue_report"),
            "section": "main",
        },
    ]

    if is_chain_owner:
        items.extend(
            [
                {
                    "label": "Hotels",
                    "icon": "bi-buildings",
                    "url": _safe_reverse("hotels:hotel_list"),
                    "section": "admin",
                },
                {
                    "label": "Users",
                    "icon": "bi-people",
                    "url": "#",
                    "section": "admin",
                },
            ]
        )

    items.append(
        {
            "label": "Logout",
            "icon": "bi-box-arrow-right",
            "url": _safe_reverse("admin:logout"),
            "section": "account",
        }
    )

    current_path = request.path
    for item in items:
        url = item.get("url") or "#"
        item["active"] = bool(url != "#" and current_path.startswith(str(url)))

    return {
        "sidebar_menu": items,
        "current_hotel": get_current_hotel(request),
        "accessible_hotels": get_user_hotels(user),
    }
