from __future__ import annotations

from typing import Optional

from django.core.exceptions import PermissionDenied
from django.http import HttpRequest

from core.models import get_user_hotels

CURRENT_HOTEL_SESSION_KEY = "current_hotel_id"


def get_current_hotel(request: HttpRequest, allow_fallback: bool = True):
    """
    Resolve the current hotel from session or user assignments.
    """

    from hotels.models import Hotel

    hotel_id = request.session.get(CURRENT_HOTEL_SESSION_KEY)
    if hotel_id:
        hotel = Hotel.objects.filter(id=hotel_id).first()
        if hotel:
            return hotel

    if not allow_fallback:
        return None

    user_hotels = get_user_hotels(getattr(request, "user", None))
    return user_hotels.first()


def set_current_hotel(request: HttpRequest, hotel_id: Optional[int]) -> None:
    """
    Persist the current hotel in session for subsequent requests.
    """

    if hotel_id is None:
        request.session.pop(CURRENT_HOTEL_SESSION_KEY, None)
    else:
        request.session[CURRENT_HOTEL_SESSION_KEY] = hotel_id


def ensure_user_has_hotel_access(user, hotel) -> None:
    """
    Raise PermissionDenied if the user cannot access the given hotel.
    """

    if hotel is None:
        raise PermissionDenied("A hotel must be selected.")

    if not get_user_hotels(user).filter(id=getattr(hotel, "id", None)).exists():
        raise PermissionDenied("You do not have access to this hotel.")
