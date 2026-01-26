from django.urls import path

from hotels import views

app_name = "hotels"

urlpatterns = [
    # Hotels
    path("hotels/", views.HotelListView.as_view(), name="hotel_list"),
    path("hotels/add/", views.HotelCreateView.as_view(), name="hotel_create"),
    path("hotels/<int:pk>/edit/", views.HotelUpdateView.as_view(), name="hotel_update"),
    path(
        "hotels/<int:pk>/delete/",
        views.HotelDeleteView.as_view(),
        name="hotel_delete",
    ),
    # Room categories
    path(
        "room-categories/",
        views.RoomCategoryListView.as_view(),
        name="room_category_list",
    ),
    path(
        "room-categories/add/",
        views.RoomCategoryCreateView.as_view(),
        name="room_category_create",
    ),
    path(
        "room-categories/<int:pk>/edit/",
        views.RoomCategoryUpdateView.as_view(),
        name="room_category_update",
    ),
    path(
        "room-categories/<int:pk>/delete/",
        views.RoomCategoryDeleteView.as_view(),
        name="room_category_delete",
    ),
    # Rooms
    path("rooms/", views.RoomListView.as_view(), name="room_list"),
    path("rooms/add/", views.RoomCreateView.as_view(), name="room_create"),
    path("rooms/<int:pk>/edit/", views.RoomUpdateView.as_view(), name="room_update"),
    path(
        "rooms/<int:pk>/delete/",
        views.RoomDeleteView.as_view(),
        name="room_delete",
    ),
]
