from django.urls import path

from enquiries import views

app_name = "enquiries"

urlpatterns = [
    path("", views.EnquiryListView.as_view(), name="enquiry_list"),
    path("add/", views.EnquiryCreateView.as_view(), name="enquiry_create"),
    path("<int:pk>/edit/", views.EnquiryUpdateView.as_view(), name="enquiry_update"),
    path("<int:pk>/convert/",views.convert_enquiry_to_booking,name="enquiry_convert"),
    path(
        "<int:pk>/delete/",
        views.EnquiryDeleteView.as_view(),
        name="enquiry_delete",
    ),
]
