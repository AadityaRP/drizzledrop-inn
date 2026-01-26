from __future__ import annotations

from typing import Any, Dict

from django import forms

from core.models import get_user_hotels
from hotels.models import Hotel, Room, RoomCategory


class HotelForm(forms.ModelForm):
    """
    Basic form for creating and updating hotels.
    """

    class Meta:
        model = Hotel
        fields = [
            "chain",
            "name",
            "code",
            "address",
            "gstin",
            "contact_numbers",
            "email",
        ]


class RoomCategoryForm(forms.ModelForm):
    """
    Form for room categories with hotel-aware dropdowns.
    """

    class Meta:
        model = RoomCategory
        fields = [
            "hotel",
            "name",
            "with_food",
            "base_rate",
            "extra_bed_rate",
            "tax_rate",
            "max_adults",
            "max_children",
        ]

    def __init__(self, user, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        hotels_qs = get_user_hotels(user)
        self.fields["hotel"].queryset = hotels_qs
        if not self.instance.pk and hotels_qs.count() == 1:
            self.fields["hotel"].initial = hotels_qs.first()


class RoomForm(forms.ModelForm):
    """
    Form for rooms with hotel/category consistency checks.
    """

    class Meta:
        model = Room
        fields = ["hotel", "category", "room_number", "floor", "is_active"]

    def __init__(self, user, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        hotels_qs = get_user_hotels(user)
        self.fields["hotel"].queryset = hotels_qs
        self.fields["category"].queryset = RoomCategory.objects.none()

        initial_hotel = self._determine_hotel_initial(hotels_qs)
        if initial_hotel:
            self.fields["hotel"].initial = initial_hotel
            self.fields["category"].queryset = RoomCategory.objects.filter(
                hotel=initial_hotel
            )
        else:
            self.fields["category"].queryset = RoomCategory.objects.filter(
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
        return self.initial.get("hotel") or (hotels_qs.first() if hotels_qs.count() == 1 else None)

    def clean(self) -> Dict[str, Any]:
        cleaned = super().clean()
        hotel = cleaned.get("hotel")
        category = cleaned.get("category")
        if hotel and category and category.hotel_id != hotel.id:
            self.add_error(
                "category",
                "Selected category does not belong to the chosen hotel.",
            )
        return cleaned
