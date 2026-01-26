from __future__ import annotations

from datetime import date
from typing import Any, Dict

from django import forms

from bookings.models import Booking
from core.models import get_user_hotels
from hotels.models import RoomCategory


class BookingForm(forms.ModelForm):
    """
    Booking form with hotel-aware dropdowns and availability validation.
    """

    class Meta:
        model = Booking
        fields = [
            "hotel",
            "enquiry",
            "check_in",
            "check_out",
            "guest_name",
            "guest_mobile",
            "adults",
            "children",
            "room_category",
            "rooms_count",
            "with_food",
            "extra_bed",
            "early_check_in_option",
            "late_check_out_option",
            "special_request",
            "status",
        ]
        widgets = {
            "check_in": forms.DateInput(attrs={"type": "date"}),
            "check_out": forms.DateInput(attrs={"type": "date"}),
            "special_request": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, user, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        hotels_qs = get_user_hotels(user)
        self.fields["hotel"].queryset = hotels_qs
        if not self.instance.pk and hotels_qs.count() == 1:
            self.fields["hotel"].initial = hotels_qs.first()

        hotel = self._determine_hotel_initial(hotels_qs)
        if hotel:
            self.fields["room_category"].queryset = RoomCategory.objects.filter(
                hotel=hotel
            )
        else:
            self.fields["room_category"].queryset = RoomCategory.objects.filter(
                hotel__in=hotels_qs
            )

    def _determine_hotel_initial(self, hotels_qs):
        if self.instance and self.instance.pk:
            return self.instance.hotel
        if "hotel" in self.data:
            try:
                hotel_id = int(self.data.get("hotel"))
            except (TypeError, ValueError):
                return None
            return hotels_qs.filter(id=hotel_id).first()
        return (
            self.initial.get("hotel")
            or (hotels_qs.first() if hotels_qs.count() == 1 else None)
        )

    def clean(self) -> Dict[str, Any]:
        cleaned = super().clean()
        hotel = cleaned.get("hotel")
        category = cleaned.get("room_category")
        check_in = cleaned.get("check_in")
        check_out = cleaned.get("check_out")
        rooms_count = cleaned.get("rooms_count") or 0

        if check_in and check_out and check_in >= check_out:
            self.add_error("check_out", "Check-out must be after check-in.")
        if check_in and check_in < date.today():
            # allow retro bookings but warn in UI, not here
            pass

        if hotel and category and category.hotel_id != hotel.id:
            self.add_error(
                "room_category", "Selected room category does not belong to this hotel."
            )

        if hotel and category and check_in and check_out and rooms_count:
            from bookings.models import get_available_rooms

            available = get_available_rooms(hotel, category, check_in, check_out).count()
            if available < rooms_count:
                self.add_error(
                    "rooms_count",
                    f"Only {available} rooms available for the selected dates.",
                )
        return cleaned
