from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.core.models import (
    EmployeeParkingRight,
    GuestParkingApplication,
    GuestParkingRight,
    ParkingLot,
    ParkingSession,
    Vehicle,
)
from apps.core.services.parking_session_service import ParkingSessionService


class ParkingSessionServiceTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.employee = User.objects.create_user(
            username="alice"
        )

        self.vehicle = Vehicle.objects.create(
            registration_number="231-D-123",
            owner=self.employee
        )

        self.parking_lot = ParkingLot.objects.create(capacity=2)

        today = timezone.localdate()

        self.employee_right = EmployeeParkingRight.objects.create(
            employee=self.employee,
            vehicle=self.vehicle,
            start_date=today - timedelta(days=1),
            end_date=today + timedelta(days=30),
            state=EmployeeParkingRight.State.ACTIVE
        )

        self.service = ParkingSessionService()

        self.notification_patch = patch.object(
            self.service.notification_service,
            "notify_subscribers"
        )
        self.notify = self.notification_patch.start()
        self.addCleanup(self.notification_patch.stop)

    def enter_vehicle(self, registration_number=None):
        with self.captureOnCommitCallbacks(execute=True):
            session = self.service.enter(
                parking_lot_id=self.parking_lot.pk,
                registration_number=(
                    registration_number
                    if registration_number is not None
                    else self.vehicle.registration_number
                )
            )

        return session

    def exit_vehicle(self):
        with self.captureOnCommitCallbacks(execute=True):
            session = self.service.exit(
                parking_lot_id=self.parking_lot.pk,
                registration_number=self.vehicle.registration_number
            )

        return session

    def test_employee_entry_creates_session(self):
        session = self.enter_vehicle()

        saved_session = ParkingSession.objects.get(pk=session.pk)

        self.assertEqual(saved_session.user_id, self.employee.pk)
        self.assertEqual(saved_session.vehicle_id, self.vehicle.pk)
        self.assertEqual(
            saved_session.parking_lot_id,
            self.parking_lot.pk
        )
        self.assertIsNotNone(saved_session.entry_time)
        self.assertIsNone(saved_session.exit_time)

        self.assertEqual(
            self.parking_lot.get_available_spaces(),
            1
        )
        self.notify.assert_not_called()

    def test_guest_entry_creates_session_without_user(self):
        guest_vehicle = Vehicle.objects.create(
            registration_number="242-C-456"
        )

        now = timezone.now()
        start = now - timedelta(hours=1)
        end = now + timedelta(hours=2)

        application = GuestParkingApplication.objects.create(
            vehicle=guest_vehicle,
            guest_name="Guest User",
            mobile_number="0851234567",
            email="guest@example.com",
            parking_reason="Meeting",
            requested_start=start,
            requested_end=end,
            status=GuestParkingApplication.Status.APPROVED
        )

        GuestParkingRight.objects.create(
            application=application,
            vehicle=guest_vehicle,
            start_at=start,
            end_at=end,
            state=GuestParkingRight.State.ACTIVE
        )

        session = self.enter_vehicle(
            guest_vehicle.registration_number
        )

        session.refresh_from_db()

        self.assertIsNone(session.user_id)
        self.assertEqual(session.vehicle_id, guest_vehicle.pk)
        self.assertIsNone(session.exit_time)

    def test_entry_normalises_registration_number(self):
        session = self.enter_vehicle("  231-d-123  ")

        self.assertEqual(session.vehicle_id, self.vehicle.pk)

    def test_entry_rejects_vehicle_without_valid_right(self):
        self.employee_right.manually_disabled = True
        self.employee_right.save(
            update_fields=["manually_disabled"]
        )

        with self.assertRaises(ValueError):
            self.enter_vehicle()

        self.assertEqual(ParkingSession.objects.count(), 0)
        self.notify.assert_not_called()

    def test_entry_rejects_unregistered_vehicle(self):
        with self.assertRaises(Vehicle.DoesNotExist):
            self.enter_vehicle("999-X-999")

        self.assertEqual(ParkingSession.objects.count(), 0)
        self.notify.assert_not_called()

    def test_entry_rejects_nonexistent_parking_lot(self):
        deleted_lot = ParkingLot.objects.create(capacity=1)
        deleted_lot_id = deleted_lot.pk
        deleted_lot.delete()

        with self.assertRaises(ParkingLot.DoesNotExist):
            self.service.enter(
                parking_lot_id=deleted_lot_id,
                registration_number=self.vehicle.registration_number
            )

        self.assertEqual(ParkingSession.objects.count(), 0)
        self.notify.assert_not_called()

    def test_entry_rejects_vehicle_already_inside_another_lot(self):
        other_lot = ParkingLot.objects.create(capacity=2)

        existing_session = ParkingSession.objects.create(
            user=self.employee,
            vehicle=self.vehicle,
            parking_lot=other_lot
        )

        with self.assertRaises(ValueError):
            self.enter_vehicle()

        self.assertEqual(ParkingSession.objects.count(), 1)

        existing_session.refresh_from_db()
        self.assertIsNone(existing_session.exit_time)
        self.notify.assert_not_called()

    def test_entry_rejects_full_parking_lot(self):
        self.parking_lot.set_capacity(1)

        other_vehicle = Vehicle.objects.create(
            registration_number="241-D-789"
        )

        ParkingSession.objects.create(
            vehicle=other_vehicle,
            parking_lot=self.parking_lot
        )

        with self.assertRaises(ValueError):
            self.enter_vehicle()

        self.assertFalse(
            ParkingSession.objects.filter(
                vehicle=self.vehicle
            ).exists()
        )
        self.assertEqual(ParkingSession.objects.count(), 1)
        self.notify.assert_not_called()

    def test_entry_notifies_when_last_space_is_taken(self):
        self.parking_lot.set_capacity(1)

        self.enter_vehicle()

        self.assertEqual(
            self.parking_lot.get_available_spaces(),
            0
        )

        self.notify.assert_called_once()
        notified_lot, event = self.notify.call_args.args

        self.assertEqual(notified_lot.pk, self.parking_lot.pk)
        self.assertEqual(event, "parking_lot_full")

    def test_exit_updates_existing_session(self):
        entered_session = self.enter_vehicle()
        entry_time = entered_session.entry_time

        exited_session = self.exit_vehicle()
        exited_session.refresh_from_db()

        self.assertEqual(exited_session.pk, entered_session.pk)
        self.assertEqual(ParkingSession.objects.count(), 1)
        self.assertEqual(exited_session.entry_time, entry_time)
        self.assertIsNotNone(exited_session.exit_time)
        self.assertGreaterEqual(
            exited_session.exit_time,
            exited_session.entry_time
        )

        self.assertEqual(
            self.parking_lot.get_available_spaces(),
            2
        )

        self.notify.assert_not_called()

    def test_exit_rejects_vehicle_without_open_session(self):
        with self.assertRaises(ValueError):
            self.exit_vehicle()

        self.assertEqual(ParkingSession.objects.count(), 0)
        self.notify.assert_not_called()

    def test_exit_rejects_vehicle_in_a_different_lot(self):
        other_lot = ParkingLot.objects.create(capacity=2)

        session = ParkingSession.objects.create(
            user=self.employee,
            vehicle=self.vehicle,
            parking_lot=other_lot
        )

        with self.assertRaises(ValueError):
            self.exit_vehicle()

        session.refresh_from_db()
        self.assertIsNone(session.exit_time)
        self.notify.assert_not_called()

    def test_exit_rejects_repeated_exit(self):
        entered_session = self.enter_vehicle()
        exited_session = self.exit_vehicle()
        original_exit_time = exited_session.exit_time

        with self.assertRaises(ValueError):
            self.exit_vehicle()

        entered_session.refresh_from_db()

        self.assertEqual(ParkingSession.objects.count(), 1)
        self.assertEqual(
            entered_session.exit_time,
            original_exit_time
        )
        self.notify.assert_not_called()

    def test_exit_is_allowed_after_parking_right_expires(self):
        self.enter_vehicle()

        # expired permission when entering
        self.employee_right.end_date = timezone.localdate()
        self.employee_right.save(update_fields=["end_date"])

        self.assertFalse(
            self.employee_right.is_currently_valid(
                on_date=timezone.localdate()
            )
        )

        session = self.exit_vehicle()
        session.refresh_from_db()

        self.assertIsNotNone(session.exit_time)

    def test_exit_notifies_when_full_lot_has_space_again(self):
        self.parking_lot.set_capacity(1)

        self.enter_vehicle()

        self.notify.reset_mock()

        self.exit_vehicle()

        self.assertEqual(
            self.parking_lot.get_available_spaces(),
            1
        )

        self.notify.assert_called_once()
        notified_lot, event = self.notify.call_args.args

        self.assertEqual(notified_lot.pk, self.parking_lot.pk)
        self.assertEqual(event, "space_available")