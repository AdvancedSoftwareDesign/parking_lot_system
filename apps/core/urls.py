
from django.urls import path

from apps.core.views.homepage_view import HomepageView
from apps.core.views.initial_check_view import initial_check
from apps.core.views.login_view import LoginView
from apps.core.views.vehicle_registration_view import VehicleRegistrationView

from .views import capacity_status, set_capacity

from apps.core.views.parking_entry_view import ParkingEntryView
from apps.core.views.parking_exit_view import ParkingExitView

from apps.core.views.vehicle_deactivation_view import (
    RegistrationSearchView, VehicleDeactivationView,
)

urlpatterns = [
    path("vehicles/search/", RegistrationSearchView.as_view(), name="registration-search"),
    path("vehicles/<int:vehicle_id>/deactivate/", VehicleDeactivationView.as_view(), name="vehicle-deactivate"),
    path("check/", initial_check, name="initial-check"),
    path("login/", LoginView.as_view()),
    path("home/", HomepageView.as_view()),
    path("register/", VehicleRegistrationView.as_view()),
    path("capacity/", capacity_status, name="capacity-status"),
    path("capacity/set/", set_capacity, name="set-capacity"),
    path("entry/", ParkingEntryView.as_view(), name="parking-entry"),
    path("exit/", ParkingExitView.as_view(), name="parking-exit"),
]
