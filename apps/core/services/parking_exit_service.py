
from django.db import transaction
from django.utils import timezone

from apps.core.models import ParkingRecord


class ParkingExitError(Exception):
    """Raised when a vehicle cannot exit the parking lot."""


class ParkingExitService:
    """Handle vehicle exit from the parking lot."""

    @transaction.atomic
    def record_exit(self, registration_number: str) -> ParkingRecord:
        registration_number = registration_number.strip().upper()

        if not registration_number:
            raise ParkingExitError("Registration number is required.")

        record = (
            ParkingRecord.objects.select_for_update()
            .select_related("vehicle", "vehicle__owner")
            .filter(
                vehicle__registration_number=registration_number,
                exit_time__isnull=True,
            )
            .first()
        )

        if record is None:
            raise ParkingExitError(
                "No active parking record found for this vehicle."
            )

        record.exit_time = timezone.now()
        record.save(update_fields=["exit_time"])

        return record
