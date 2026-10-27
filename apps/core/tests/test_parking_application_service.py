from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core.models import Vehicle, ParkingApplication
from apps.core.services.parking_application_service import (
    ParkingApplicationService,
)

class ParkingApplicationServiceTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.employee = User.objects.create_user(
            username="employee1",
            password="TestPass123!"
        )

        self.vehicle = Vehicle.objects.create(
            registration_number="12L12345",
            owner=self.employee
        )

        self.service = ParkingApplicationService()

    def test_create_valid_application(self):
        application = self.service.apply_for_parking(
            employee=self.employee,
            vehicle_id=self.vehicle.id,
            start_date=date(2026, 11, 1),
            duration_months=6
        )

        self.assertEqual(application.employee, self.employee)
        self.assertEqual(application.vehicle, self.vehicle)
        self.assertEqual(application.duration_months, 6)
        self.assertEqual(
            application.status,
            ParkingApplication.Status.PENDING
        )
        self.assertEqual(application.duration_days, 180)


    def test_reject_duration_below_one_month(self):
        with self.assertRaises(ValueError):
            self.service.apply_for_parking(
                employee=self.employee,
                vehicle_id=self.vehicle.id,
                start_date=date(2026, 11, 1),
                duration_months=0
            )

    def test_reject_duration_above_twelve_months(self):
        with self.assertRaises(ValueError):
            self.service.apply_for_parking(
                employee=self.employee,
                vehicle_id=self.vehicle.id,
                start_date=date(2026, 11, 1),
                duration_months=13
            )

    def test_reject_another_users_vehicle(self):
        User = get_user_model()
        another_employee = User.objects.create_user(
            username="employee2",
            password="TestPass123!"
        )

        with self.assertRaises(ValueError):
            self.service.apply_for_parking(
                employee=another_employee,
                vehicle_id=self.vehicle.id,
                start_date=date(2026, 11, 1),
                duration_months=3
            )

        self.assertEqual(ParkingApplication.objects.count(), 0)