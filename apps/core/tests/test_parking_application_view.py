

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token

from apps.core.models import Vehicle, ParkingApplication

class ParkingApplicationViewTests(APITestCase):

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

        self.token = Token.objects.create(user=self.employee)

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {self.token.key}"
        )

        self.url = "/api/parking-applications/"

    def test_submit_valid_application(self):
            response = self.client.post(
                self.url,
                {
                    "vehicle_id": self.vehicle.id,
                    "start_date": "2026-11-01",
                    "duration_months": 6
                },
                format="json"
            )

            self.assertEqual(response.status_code, 201)
            self.assertEqual(
                response.data["application"]["status"],
                "pending"
            )
            self.assertEqual(
                response.data["application"]["duration_days"],
                180
            )
            self.assertNotIn("fee", response.data["application"])
            self.assertEqual(ParkingApplication.objects.count(), 1)

    def test_cannot_apply_with_another_users_vehicle(self):
                User = get_user_model()
                another_employee = User.objects.create_user(
                    username="employee2",
                    password="TestPass123!"
                )

                another_vehicle = Vehicle.objects.create(
                    registration_number="13L54321",
                    owner=another_employee
                )

                response = self.client.post(
                    self.url,
                    {
                        "vehicle_id": another_vehicle.id,
                        "start_date": "2026-11-01",
                        "duration_months": 3
                    },
                    format="json"
                )

                self.assertEqual(response.status_code, 400)
                self.assertEqual(ParkingApplication.objects.count(), 0)

    def test_unauthenticated_user_cannot_apply(self):
                    self.client.credentials()

                    response = self.client.post(
                        self.url,
                        {
                            "vehicle_id": self.vehicle.id,
                            "start_date": "2026-11-01",
                            "duration_months": 3
                        },
                        format="json"
                    )

                    self.assertEqual(response.status_code, 401)
                    self.assertEqual(ParkingApplication.objects.count(), 0)