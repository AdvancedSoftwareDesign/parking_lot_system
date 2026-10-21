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
from apps.core.models import ParkingRecord, Vehicle
from apps.core.services.parking_entry_service import (
    ParkingEntryError,
    ParkingEntryService,
)
from apps.core.services.parking_exit_service import (
    ParkingExitError,
    ParkingExitService,
)

from apps.core.views.parking_entry_view import ParkingEntryView
from apps.core.views.parking_exit_view import ParkingExitView

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

    @patch("apps.core.views.initial_check_view.get_capacity_service")
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

    @patch("apps.core.views.initial_check_view.get_capacity_service")
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
        
class ParkingEntryServiceTests(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            username="entry_employee",
            password="test-password-123",
            is_active=True,
        )
        self.vehicle = Vehicle.objects.create(
            registration_number="12D12345",
            owner=self.employee,
        )

        self.capacity_repository = FakeCapacityRepository(capacity=100)
        self.occupancy = FakeOccupancy(occupied=20)
        self.capacity_service = CapacityService(
            capacity_repository=self.capacity_repository,
            occupancy_port=self.occupancy,
        )
        self.service = ParkingEntryService(
            capacity_service=self.capacity_service,
        )

    def test_entry_creates_parking_record(self):
        record = self.service.record_entry("12d12345")

        self.assertEqual(record.vehicle, self.vehicle)
        self.assertIsNone(record.exit_time)
        self.assertEqual(
            ParkingRecord.objects.filter(exit_time__isnull=True).count(),
            1,
        )

    def test_entry_rejects_unregistered_vehicle(self):
        with self.assertRaisesMessage(
            ParkingEntryError, "Vehicle is not registered."
        ):
            self.service.record_entry("99D99999")

        self.assertEqual(ParkingRecord.objects.count(), 0)

    def test_entry_rejects_inactive_employee(self):
        self.employee.is_active = False
        self.employee.save()

        with self.assertRaisesMessage(
            ParkingEntryError, "The employee account is inactive."
        ):
            self.service.record_entry("12D12345")

        self.assertEqual(ParkingRecord.objects.count(), 0)

    def test_entry_rejects_vehicle_already_inside(self):
        ParkingRecord.objects.create(vehicle=self.vehicle)

        with self.assertRaisesMessage(
            ParkingEntryError, "This vehicle is already inside."
        ):
            self.service.record_entry("12D12345")

        self.assertEqual(ParkingRecord.objects.count(), 1)

    def test_entry_rejects_full_parking_lot(self):
        self.capacity_repository.capacity = 20
        self.occupancy.occupied = 20

        with self.assertRaisesMessage(
            ParkingEntryError, "The parking lot is full."
        ):
            self.service.record_entry("12D12345")

        self.assertEqual(ParkingRecord.objects.count(), 0)

    def test_entry_rejects_empty_registration_number(self):
        with self.assertRaisesMessage(
            ParkingEntryError, "Registration number is required."
        ):
            self.service.record_entry("   ")

        self.assertEqual(ParkingRecord.objects.count(), 0)
        
class ParkingExitServiceTests(TestCase):
    def setUp(self):
        self.employee = User.objects.create_user(
            username="exit_employee",
            password="test-password-123",
        )
        self.vehicle = Vehicle.objects.create(
            registration_number="15D54321",
            owner=self.employee,
        )
        self.record = ParkingRecord.objects.create(
            vehicle=self.vehicle,
        )
        self.service = ParkingExitService()

    def test_exit_closes_active_record(self):
        record = self.service.record_exit("15d54321")

        record.refresh_from_db()

        self.assertIsNotNone(record.exit_time)
        self.assertEqual(record.id, self.record.id)
        self.assertEqual(
            ParkingRecord.objects.filter(
                vehicle=self.vehicle,
                exit_time__isnull=True,
            ).count(),
            0,
        )

    def test_exit_rejects_unregistered_or_inactive_vehicle(self):
        with self.assertRaisesMessage(
            ParkingExitError,
            "No active parking record found for this vehicle.",
        ):
            self.service.record_exit("99D99999")

        self.assertIsNone(self.record.exit_time)

    def test_exit_rejects_vehicle_already_exited(self):
        self.record.exit_time = __import__(
            "django.utils.timezone",
            fromlist=["now"],
        ).now()
        self.record.save(update_fields=["exit_time"])

        with self.assertRaisesMessage(
            ParkingExitError,
            "No active parking record found for this vehicle.",
        ):
            self.service.record_exit("15D54321")

        self.record.refresh_from_db()
        self.assertIsNotNone(self.record.exit_time)

    def test_exit_rejects_blank_registration(self):
        with self.assertRaisesMessage(
            ParkingExitError,
            "Registration number is required.",
        ):
            self.service.record_exit("   ")

        self.assertIsNone(self.record.exit_time)
        
class ParkingEntryExitAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.employee_group, _ = Group.objects.get_or_create(
            name="Employee"
        )
        self.guard_group, _ = Group.objects.get_or_create(
            name="Security Guard"
        )

        self.employee = User.objects.create_user(
            username="api_employee",
            password="test-password-123",
        )
        self.employee.groups.add(self.employee_group)

        self.guard = User.objects.create_user(
            username="api_guard",
            password="test-password-123",
        )
        self.guard.groups.add(self.guard_group)

    def authenticate_as(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

    def test_anonymous_user_cannot_record_entry(self):
        response = self.client.post(
            "/api/entry/",
            {"registration_number": "12D12345"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_anonymous_user_cannot_record_exit(self):
        response = self.client.post(
            "/api/exit/",
            {"registration_number": "12D12345"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_employee_cannot_record_entry(self):
        self.authenticate_as(self.employee)

        response = self.client.post(
            "/api/entry/",
            {"registration_number": "12D12345"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_cannot_record_exit(self):
        self.authenticate_as(self.employee)

        response = self.client.post(
            "/api/exit/",
            {"registration_number": "12D12345"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
    def test_guard_can_record_vehicle_entry_and_exit(self):
        from apps.core.models import ParkingRecord, Vehicle
        from apps.core.models import ParkingCapacity

        # Configure capacity and create a registered vehicle.
        ParkingCapacity.objects.create(total_capacity=10)
        vehicle = Vehicle.objects.create(
            registration_number="26D12345",
            owner=self.employee,
        )

        self.authenticate_as(self.guard)

        # Record vehicle entry.
        entry_response = self.client.post(
            "/api/entry/",
            {"registration_number": vehicle.registration_number},
            format="json",
        )

        self.assertEqual(entry_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            ParkingRecord.objects.filter(
                vehicle=vehicle,
                exit_time__isnull=True,
            ).count(),
            1,
        )

        # Record vehicle exit.
        exit_response = self.client.post(
            "/api/exit/",
            {"registration_number": vehicle.registration_number},
            format="json",
        )

        self.assertEqual(exit_response.status_code, status.HTTP_200_OK)

        record = ParkingRecord.objects.get(vehicle=vehicle)
        self.assertIsNotNone(record.exit_time)
        self.assertEqual(
            ParkingRecord.objects.filter(exit_time__isnull=True).count(),
            0,
        )




