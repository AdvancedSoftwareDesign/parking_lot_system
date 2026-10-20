from unittest.mock import patch
from django.contrib.auth.models import Group, User
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from apps.core.services.capacity_service import (
    CapacityService,
    InvalidCapacityError,
    OccupancyUnavailableError,
)

class FakeCapacityRepository:
    def __init__(self, capacity=100):
        self.capacity = capacity

    def get_current_capacity(self):
        return self.capacity

    def save_capacity(self, total_capacity):
        self.capacity = total_capacity


class FakeOccupancy:
    def __init__(self, occupied=20):
        self.occupied = occupied

    def get_occupied_spaces(self):
        return self.occupied

class HealthCheckTests(TestCase):
    def test_initial_check_returns_ok(self):
        client = APIClient()
        response = client.get("/api/check/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")

class CapacityServiceTests(TestCase):
    def setUp(self):
        self.repository = FakeCapacityRepository(capacity=100)
        self.occupancy = FakeOccupancy(occupied=20)
        self.service = CapacityService(
            capacity_repository=self.repository,
            occupancy_port=self.occupancy,
        )

    def test_get_capacity_status(self):
        result = self.service.get_capacity_status()

        self.assertEqual(result["total_capacity"], 100)
        self.assertEqual(result["occupied_spaces"], 20)
        self.assertEqual(result["available_spaces"], 80)

    def test_set_capacity_successfully(self):
        result = self.service.set_capacity(120)

        self.assertEqual(self.repository.capacity, 120)
        self.assertEqual(result["total_capacity"], 120)
        self.assertEqual(result["occupied_spaces"], 20)
        self.assertEqual(result["available_spaces"], 100)

    def test_reject_zero_capacity(self):
        with self.assertRaises(InvalidCapacityError):
            self.service.set_capacity(0)

        self.assertEqual(self.repository.capacity, 100)

    def test_reject_negative_capacity(self):
        with self.assertRaises(InvalidCapacityError):
            self.service.set_capacity(-1)

        self.assertEqual(self.repository.capacity, 100)

    def test_reject_capacity_below_occupancy(self):
        with self.assertRaises(InvalidCapacityError):
            self.service.set_capacity(19)

        self.assertEqual(self.repository.capacity, 100)

    def test_reject_non_integer_capacity(self):
        for value in (10.5, True, "50"):
            with self.subTest(value=value):
                with self.assertRaises(InvalidCapacityError):
                    self.service.set_capacity(value)

        self.assertEqual(self.repository.capacity, 100)

    def test_occupancy_unavailable_does_not_change_capacity(self):
        class UnavailableOccupancy:
            def get_occupied_spaces(self):
                raise OccupancyUnavailableError(
                    "Vehicle occupancy data is not available yet."
                )

        service = CapacityService(
            capacity_repository=self.repository,
            occupancy_port=UnavailableOccupancy(),
        )

        with self.assertRaises(OccupancyUnavailableError):
            service.set_capacity(120)

        self.assertEqual(self.repository.capacity, 100)

class CapacityAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        admin_group, _ = Group.objects.get_or_create(
            name="Parking Administrator"
        )
        employee_group, _ = Group.objects.get_or_create(
            name="Employee"
        )

        self.admin_user = User.objects.create_user(
            username="capacity_admin",
            password="test-password-123",
        )
        self.admin_user.groups.add(admin_group)

        self.employee_user = User.objects.create_user(
            username="capacity_employee",
            password="test-password-123",
        )
        self.employee_user.groups.add(employee_group)

    def authenticate_as(self, user):
        token = Token.objects.create(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

    def test_anonymous_user_cannot_access_capacity(self):
        response = self.client.get("/api/capacity/")

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_employee_cannot_change_capacity(self):
        self.authenticate_as(self.employee_user)

        response = self.client.put(
            "/api/capacity/set/",
            {"total_capacity": 120},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    @patch("apps.core.views.get_capacity_service")
    def test_admin_request_returns_503_when_occupancy_is_unavailable(
        self, mock_get_service
    ):
        mock_get_service.return_value.set_capacity.side_effect = (
            OccupancyUnavailableError(
                "Vehicle occupancy data is not available yet."
            )
        )
        self.authenticate_as(self.admin_user)

        response = self.client.put(
            "/api/capacity/set/",
            {"total_capacity": 120},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    @patch("apps.core.views.get_capacity_service")
    def test_admin_can_update_capacity_successfully(
        self, mock_get_service
    ):
        mock_get_service.return_value.set_capacity.return_value = {
            "total_capacity": 120,
            "occupied_spaces": 20,
            "available_spaces": 100,
        }
        self.authenticate_as(self.admin_user)

        response = self.client.put(
            "/api/capacity/set/",
            {"total_capacity": 120},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(response.data["total_capacity"], 120)
        self.assertEqual(response.data["occupied_spaces"], 20)
        self.assertEqual(response.data["available_spaces"], 100)
        mock_get_service.return_value.set_capacity.assert_called_once_with(
            120
        )
