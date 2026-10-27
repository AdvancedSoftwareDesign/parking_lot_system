
from datetime import date, timedelta
from unittest.mock import patch

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory

from apps.core.admin import ParkingApplicationAdmin
from apps.core.models import (
    EmployeeParkingRight,
    ParkingApplication,
    Vehicle,
)


User = get_user_model()


class ParkingApplicationApprovalTests(TestCase):

    def setUp(self):
        self.employee = User.objects.create_user(
            username="employee1",
            password="testpass123",
        )
        self.admin_user = User.objects.create_superuser(
            username="admin1",
            email="admin@example.com",
            password="testpass123",
        )
        self.vehicle = Vehicle.objects.create(
            registration_number="12L12345",
            owner=self.employee,
        )
        self.application = ParkingApplication.objects.create(
            employee=self.employee,
            vehicle=self.vehicle,
            start_date=date.today(),
            duration_months=3,
            status=ParkingApplication.Status.PENDING,
        )

        self.model_admin = ParkingApplicationAdmin(
            ParkingApplication, AdminSite()
        )
        self.request = RequestFactory().post("/admin/")
        self.request.user = self.admin_user

    def test_approval_creates_linked_parking_right(self):
        self.application.status = ParkingApplication.Status.APPROVED

        self.model_admin.save_model(
            self.request, self.application, None, True
        )

        right = EmployeeParkingRight.objects.get(
            application=self.application
        )
        self.assertEqual(right.employee, self.employee)
        self.assertEqual(right.vehicle, self.vehicle)
        self.assertEqual(right.start_date, self.application.start_date)
        self.assertEqual(
            right.end_date,
            self.application.start_date + timedelta(days=90),
        )

    def test_repeated_approval_does_not_create_duplicate_right(self):
        self.application.status = ParkingApplication.Status.APPROVED
        self.model_admin.save_model(
            self.request, self.application, None, True
        )

        self.application.refresh_from_db()
        self.model_admin.save_model(
            self.request, self.application, None, True
        )

        self.assertEqual(
            EmployeeParkingRight.objects.filter(
                application=self.application
            ).count(),
            1,
        )

    def test_right_creation_failure_rolls_back_approval(self):
        self.application.status = ParkingApplication.Status.APPROVED

        with patch.object(
            EmployeeParkingRight.objects,
            "get_or_create",
            side_effect=RuntimeError("Simulated creation failure"),
        ):
            with self.assertRaises(RuntimeError):
                self.model_admin.save_model(
                    self.request, self.application, None, True
                )

        self.application.refresh_from_db()
        self.assertEqual(
            self.application.status,
            ParkingApplication.Status.PENDING,
        )
        self.assertEqual(EmployeeParkingRight.objects.count(), 0)
