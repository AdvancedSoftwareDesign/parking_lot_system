
from django.db import transaction

from apps.core.models import ParkingRecord, Vehicle
from apps.core.services.capacity_service import (
    CapacityNotConfiguredError,
    CapacityService,
    OccupancyUnavailableError,
)


class ParkingEntryError(Exception):
    """Raised when a vehicle cannot enter the parking lot."""


class ParkingEntryService:
    """Handle vehicle entry into the parking lot."""

    def __init__(self, capacity_service: CapacityService):
        self.capacity_service = capacity_service

    @transaction.atomic
    def record_entry(self, registration_number: str) -> ParkingRecord:
        registration_number = registration_number.strip().upper()

        if not registration_number:
            raise ParkingEntryError("Registration number is required.")

        vehicle = (
            Vehicle.objects.select_for_update().select_related("owner")
            .filter(registration_number=registration_number)
            .first()
        )

        if vehicle is None:
            raise ParkingEntryError("Vehicle is not registered.")

        if not vehicle.registration_active:
            raise ParkingEntryError("The vehicle registration is inactive.")

        if not vehicle.owner.is_active:
            raise ParkingEntryError("The employee account is inactive.")

        if ParkingRecord.objects.filter(
            vehicle=vehicle,
            exit_time__isnull=True,
        ).exists():
            raise ParkingEntryError("This vehicle is already inside.")

        try:
            status = self.capacity_service.get_capacity_status()
        except CapacityNotConfiguredError as exc:
            raise ParkingEntryError(
                "Parking capacity has not been configured."
            ) from exc
        except OccupancyUnavailableError as exc:
            raise ParkingEntryError(
                "Parking occupancy is currently unavailable."
            ) from exc

        if status["available_spaces"] <= 0:
            raise ParkingEntryError("The parking lot is full.")

        return ParkingRecord.objects.create(vehicle=vehicle)
