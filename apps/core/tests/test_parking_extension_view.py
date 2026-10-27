
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from apps.core.models import EmployeeParkingRight, Vehicle, ParkingExtensionRequest


User = get_user_model()


class ParkingExtensionViewTests(APITestCase):

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

        token = Token.objects.create(user=self.employee)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )
        self.url = "/api/parking-extensions/"

    def test_submit_valid_extension(self):
        response = self.client.post(
            self.url,
            {
                "parking_right_id": self.parking_right.id,
                "additional_months": 3,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            response.data["extension"]["status"],
            "pending",
        )
        self.assertEqual(ParkingExtensionRequest.objects.count(), 1)

    def test_unauthenticated_user_cannot_submit_extension(self):
        self.client.credentials()

        response = self.client.post(
            self.url,
            {
                "parking_right_id": self.parking_right.id,
                "additional_months": 3,
            },
            format="json",
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(ParkingExtensionRequest.objects.count(), 0)

    def test_missing_fields_are_rejected(self):
        response = self.client.post(
            self.url,
            {"parking_right_id": self.parking_right.id},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(ParkingExtensionRequest.objects.count(), 0)
