from apps.core.views.parking_right_deactivation_view import ParkingRightDeactivationView
from apps.core.views.application_review_view import ApplicationReviewView
from django.urls import path

from apps.core.views.homepage_view import HomepageView
from apps.core.views.initial_check_view import initial_check
from apps.core.views.login_view import LoginView
from apps.core.views.vehicle_registration_view import VehicleRegistrationView
from apps.core.views.parking_lot_view import (
    ParkingLotCapacityView,
    ParkingLotCreateView,
)
from apps.core.views.parking_subscription_view import ParkingSubscriptionView
from apps.core.views.parking_application_view import ParkingApplicationView
from apps.core.views.parking_extension_view import ParkingExtensionView
from apps.core.views.guest_parking_application_view import (
    GuestParkingApplicationView,
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
    path(
        "parking-lots/<int:parking_lot_id>/subscription/",
        ParkingSubscriptionView.as_view()
    ),
    path(
    "parking-applications/",
    ParkingApplicationView.as_view(),
    name="parking-application",
    ),
    path(
    "guest-parking-applications/",
    GuestParkingApplicationView.as_view(),
    name="guest-parking-application",
    ),
    path(
    "parking-extensions/",
    ParkingExtensionView.as_view(),
    name="parking-extension",
    ),
    path(
        "application-reviews/<str:review_type>/<int:item_id>/",
        ApplicationReviewView.as_view(),
        name="application-review",
    ),
    path(
        "parking-rights/<str:right_type>/<int:right_id>/deactivate/",
        ParkingRightDeactivationView.as_view(),
        name="parking-right-deactivate",
    ),
]