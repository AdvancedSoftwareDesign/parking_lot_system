from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.core.models import (
    EmployeeParkingRight,
    GuestParkingApplication,
    GuestParkingRight,
    ParkingApplication,
    ParkingExtensionRequest,
    Vehicle,
)


class GuestReviewAndDeactivationTests(APITestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.guard = self.user_model.objects.create_user(
            username="guard",
            password="GuardPass123!",
            is_staff=True,
        )
        self.guard_token = Token.objects.create(user=self.guard)

    def authenticate_guard(self):
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.guard_token.key}"
        )

    def submit_guest_application(self, registration_number):
        start_at = timezone.now() + timedelta(days=1)
        end_at = start_at + timedelta(hours=8)
        return self.client.post(
            "/api/guest-parking-applications/",
            {
                "registration_number": registration_number,
                "guest_name": "Aoife Murphy",
                "mobile_number": "0871234567",
                "email": f"{registration_number.lower()}@example.com",
                "parking_reason": "Client meeting",
                "requested_start": start_at.isoformat(),
                "requested_end": end_at.isoformat(),
            },
            format="json",
        )

    def test_uc04_public_guest_application_is_pending(self):
        response = self.submit_guest_application("26D11111")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        application = GuestParkingApplication.objects.get(
            pk=response.data["application"]["id"]
        )
        self.assertEqual(
            application.status,
            GuestParkingApplication.Status.PENDING,
        )
        self.assertIsNone(application.vehicle.owner)

    def test_uc05_approves_guest_then_uc08_deactivates_right(self):
        submitted = self.submit_guest_application("26D22222")
        application_id = submitted.data["application"]["id"]

        self.authenticate_guard()
        reviewed = self.client.post(
            f"/api/application-reviews/guest/{application_id}/",
            {"approved": True},
            format="json",
        )

        self.assertEqual(reviewed.status_code, status.HTTP_200_OK)
        application = GuestParkingApplication.objects.get(pk=application_id)
        parking_right = GuestParkingRight.objects.get(application=application)
        self.assertEqual(
            application.status,
            GuestParkingApplication.Status.APPROVED,
        )
        self.assertEqual(
            parking_right.state,
            GuestParkingRight.State.SCHEDULED,
        )

        deactivated = self.client.post(
            f"/api/parking-rights/guest/{parking_right.id}/deactivate/",
            {},
            format="json",
        )
        self.assertEqual(deactivated.status_code, status.HTTP_200_OK)
        parking_right.refresh_from_db()
        self.assertEqual(
            parking_right.state,
            GuestParkingRight.State.INACTIVE,
        )
        self.assertTrue(parking_right.manually_disabled)

        repeated = self.client.post(
            f"/api/parking-rights/guest/{parking_right.id}/deactivate/",
            {},
            format="json",
        )
        self.assertTrue(repeated.data["already_inactive"])

    def test_uc05_rejects_guest_without_creating_right(self):
        submitted = self.submit_guest_application("26D33333")
        application_id = submitted.data["application"]["id"]

        self.authenticate_guard()
        response = self.client.post(
            f"/api/application-reviews/guest/{application_id}/",
            {"approved": False},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["status"],
            GuestParkingApplication.Status.REJECTED,
        )
        self.assertFalse(
            GuestParkingRight.objects.filter(
                application_id=application_id
            ).exists()
        )

    def test_uc05_approves_employee_application_and_extension(self):
        employee = self.user_model.objects.create_user(
            username="employee",
            password="EmployeePass123!",
        )
        vehicle = Vehicle.objects.create(
            registration_number="26D44444",
            owner=employee,
        )
        application = ParkingApplication.objects.create(
            employee=employee,
            vehicle=vehicle,
            start_date=date.today(),
            duration_months=1,
        )

        self.authenticate_guard()
        approval = self.client.post(
            f"/api/application-reviews/employee/{application.id}/",
            {"approved": True},
            format="json",
        )
        self.assertEqual(approval.status_code, status.HTTP_200_OK)

        parking_right = EmployeeParkingRight.objects.get(
            application=application
        )
        extension = ParkingExtensionRequest.objects.create(
            parking_right=parking_right,
            additional_months=1,
        )
        extension_approval = self.client.post(
            f"/api/application-reviews/extension/{extension.id}/",
            {"approved": True},
            format="json",
        )

        self.assertEqual(
            extension_approval.status_code,
            status.HTTP_200_OK,
        )
        extension.refresh_from_db()
        self.assertEqual(
            extension.status,
            ParkingExtensionRequest.Status.APPROVED,
        )
