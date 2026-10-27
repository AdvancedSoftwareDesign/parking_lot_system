from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core.models import ParkingLot, ParkingSubscription
from apps.core.services.parking_notification_service import (
    ParkingNotificationService,
)


class ParkingNotificationServiceTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.alice = User.objects.create_user(username="alice")
        self.bob = User.objects.create_user(username="bob")
        self.charlie = User.objects.create_user(username="charlie")

        self.parking_lot = ParkingLot.objects.create(capacity=10)

        ParkingSubscription.objects.create(
            parking_lot=self.parking_lot,
            user=self.alice
        )
        ParkingSubscription.objects.create(
            parking_lot=self.parking_lot,
            user=self.bob
        )

        self.service = ParkingNotificationService()

    @patch("builtins.print")
    def test_only_subscribed_users_are_notified(self, mock_print):
        self.service.notify_subscribers(
            self.parking_lot,
            "parking_lot_full"
        )

        self.assertEqual(mock_print.call_count, 2)

        mock_print.assert_any_call(
            f"Notification for alice: Parking lot "
            f"{self.parking_lot.pk} is full."
        )

        mock_print.assert_any_call(
            f"Notification for bob: Parking lot "
            f"{self.parking_lot.pk} is full."
        )