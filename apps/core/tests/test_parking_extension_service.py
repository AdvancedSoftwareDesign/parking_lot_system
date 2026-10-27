
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core.models import (
    EmployeeParkingRight,
    ParkingExtensionRequest,
    Vehicle,
)
from apps.core.services.parking_extension_service import (
    ParkingExtensionService,
)


User = get_user_model()


class ParkingExtensionServiceTests(TestCase):

    def setUp(self):
        self.employee = User.objects.create_user(
            username="employee1",
            password="testpass123",
        )
        self.vehicle = Vehicle.objects.create(
            registration_number="12L12345",
            owner=self.employee,
        )
        self.parking_right = EmployeeParkingRight.objects.create(
            employee=self.employee,
            vehicle=self.vehicle,
            start_date=date.today() - timedelta(days=30),
            end_date=date.today() + timedelta(days=30),
        )
        self.service = ParkingExtensionService()

    def test_valid_extension_creates_pending_request(self):
        original_end_date = self.parking_right.end_date

        extension = self.service.request_extension(
            self.employee,
            self.parking_right.id,
            3,
        )

        self.assertEqual(extension.status, ParkingExtensionRequest.Status.PENDING)
        self.assertEqual(extension.additional_months, 3)

        self.parking_right.refresh_from_db()
        self.assertEqual(self.parking_right.end_date, original_end_date)

    def test_rejects_duration_below_one(self):
        with self.assertRaises(ValueError):
            self.service.request_extension(
                self.employee,
                self.parking_right.id,
                0,
            )

        self.assertEqual(ParkingExtensionRequest.objects.count(), 0)

    def test_rejects_duration_above_twelve(self):
        with self.assertRaises(ValueError):
            self.service.request_extension(
                self.employee,
                self.parking_right.id,
                13,
            )

        self.assertEqual(ParkingExtensionRequest.objects.count(), 0)

    def test_rejects_expired_parking_right(self):
        self.parking_right.end_date = date.today() - timedelta(days=1)
        self.parking_right.save()

        with self.assertRaisesMessage(ValueError, "expired"):
            self.service.request_extension(
                self.employee,
                self.parking_right.id,
                2,
            )

        self.assertEqual(ParkingExtensionRequest.objects.count(), 0)

    def test_employee_cannot_extend_another_users_right(self):
        other_employee = User.objects.create_user(
            username="employee2",
            password="testpass123",
        )

        with self.assertRaises(ValueError):
            self.service.request_extension(
                other_employee,
                self.parking_right.id,
                2,
            )

        self.assertEqual(ParkingExtensionRequest.objects.count(), 0)
