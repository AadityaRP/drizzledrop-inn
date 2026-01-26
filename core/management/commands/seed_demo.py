from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from hotels.models import Chain, Hotel, RoomCategory, Room
from users.models import HotelUser


class Command(BaseCommand):
    help = "Seed chain, hotels, room categories, rooms, and a chain owner."

    def handle(self, *args, **options):
        User = get_user_model()

        chain, _ = Chain.objects.get_or_create(name="Drizzle Drop Inn")
        hotel_city, _ = Hotel.objects.get_or_create(
            chain=chain,
            code="CITY",
            defaults={"name": "Drizzle Drop Inn City", "address": "City Center"},
        )
        hotel_resort, _ = Hotel.objects.get_or_create(
            chain=chain,
            code="RESORT",
            defaults={"name": "Drizzle Drop Inn Resort", "address": "Hilltop"},
        )

        def ensure_category(hotel, name, rate, with_food=False):
            cat, _ = RoomCategory.objects.get_or_create(
                hotel=hotel,
                name=name,
                with_food=with_food,
                defaults={"base_rate": rate, "tax_rate": 12},
            )
            return cat

        city_cat = ensure_category(hotel_city, "Deluxe", 3100, with_food=True)
        resort_cat = ensure_category(hotel_resort, "Family", 5000, with_food=False)

        for num in range(101, 106):
            Room.objects.get_or_create(
                hotel=hotel_city,
                category=city_cat,
                room_number=str(num),
                defaults={"floor": "1"},
            )
        for num in range(201, 204):
            Room.objects.get_or_create(
                hotel=hotel_resort,
                category=resort_cat,
                room_number=str(num),
                defaults={"floor": "2"},
            )

        owner_username = "chainowner"
        owner_password = "Chain@123"
        owner, created = User.objects.get_or_create(
            username=owner_username,
            defaults={
                "role": User.Roles.CHAIN_OWNER,
                "is_staff": True,
                "is_superuser": True,
                "email": "owner@example.com",
            },
        )
        if created:
            owner.set_password(owner_password)
            owner.save()

        HotelUser.objects.get_or_create(user=owner, hotel=hotel_city, is_primary_admin=True)
        HotelUser.objects.get_or_create(user=owner, hotel=hotel_resort)

        self.stdout.write(self.style.SUCCESS("Seed data ready."))
        self.stdout.write(f"Chain owner credentials -> {owner_username} / {owner_password}")
