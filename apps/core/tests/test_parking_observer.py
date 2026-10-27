from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core.models import ParkingLot
from apps.core.observers.user_observer import UserObserver

from django.core.exceptions import ValidationError


class ParkingLotObserverTests(TestCase):

    def setUp(self):
        self.parking_lot = ParkingLot.objects.create(capacity=10)

        User = get_user_model()
        self.user1 = User.objects.create_user(username="alice")
        self.user2 = User.objects.create_user(username="bob")

        self.observer1 = UserObserver(self.user1)
        self.observer2 = UserObserver(self.user2)

    def test_all_registered_observers_receive_notification(self):
        self.parking_lot.add_observer(self.observer1)
        self.parking_lot.add_observer(self.observer2)

        with patch.object(self.observer1, "update") as update1:
            with patch.object(self.observer2, "update") as update2:
                self.parking_lot.notify_observers("parking_lot_full")

        update1.assert_called_once_with(
            self.parking_lot,
            "parking_lot_full"
        )
        update2.assert_called_once_with(
            self.parking_lot,
            "parking_lot_full"
        )

    def test_removed_observer_does_not_receive_notification(self):
        self.parking_lot.add_observer(self.observer1)
        self.parking_lot.add_observer(self.observer2)
        self.parking_lot.remove_observer(self.observer1)

        with patch.object(self.observer1, "update") as update1:
            with patch.object(self.observer2, "update") as update2:
                self.parking_lot.notify_observers("parking_lot_full")

        update1.assert_not_called()
        update2.assert_called_once_with(
            self.parking_lot,
            "parking_lot_full"
        )

    @patch("builtins.print")
    def test_user_observer_prints_parking_lot_full_message(self, mock_print):
        self.observer1.update(self.parking_lot, "parking_lot_full")

        mock_print.assert_called_once_with(
            "Notification for alice: Parking lot "
            f"{self.parking_lot.pk} is full."
        )

    @patch("builtins.print")
    def test_user_observer_prints_space_available_message(self, mock_print):
        self.observer1.update(self.parking_lot, "space_available")

        mock_print.assert_called_once_with(
            "Notification for alice: Parking lot "
            f"{self.parking_lot.pk} has available spaces."
        )

class ParkingLotCapacityTests(TestCase):

    def setUp(self):
        self.parking_lot = ParkingLot.objects.create(capacity=10)

    def test_set_capacity_saves_valid_capacity(self):
        self.parking_lot.set_capacity(20)

        self.parking_lot.refresh_from_db()

        self.assertEqual(self.parking_lot.capacity, 20)

    def test_set_capacity_rejects_zero(self):
        with self.assertRaises(ValidationError):
            self.parking_lot.set_capacity(0)

        self.parking_lot.refresh_from_db()

        self.assertEqual(self.parking_lot.capacity, 10)

    def test_set_capacity_rejects_negative_value(self):
        with self.assertRaises(ValidationError):
            self.parking_lot.set_capacity(-1)

        self.parking_lot.refresh_from_db()

        self.assertEqual(self.parking_lot.capacity, 10)