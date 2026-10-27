from django.urls import path

from apps.core.views.homepage_view import HomepageView
from apps.core.views.initial_check_view import initial_check
from apps.core.views.login_view import LoginView
from apps.core.views.vehicle_registration_view import VehicleRegistrationView
from apps.core.views.parking_lot_view import (
    ParkingLotCapacityView,
    ParkingLotCreateView,
)

urlpatterns = [
    path("check/", initial_check, name="initial-check"),
    path("login/", LoginView.as_view()),
    path("home/", HomepageView.as_view()),
    path("register/", VehicleRegistrationView.as_view()),
    path(
        "parking-lots/",
        ParkingLotCreateView.as_view(),
    ),
    path(
        "parking-lots/<int:parking_lot_id>/capacity/",
        ParkingLotCapacityView.as_view()
    ),
]