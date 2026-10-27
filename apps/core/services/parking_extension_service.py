
from datetime import date

from apps.core.models import (
    EmployeeParkingRight,
    ParkingExtensionRequest,
)


class ParkingExtensionService:

    def request_extension(self, employee, parking_right_id, additional_months):
        # Validate the requested duration.
        if (
            not isinstance(additional_months, int)
            or isinstance(additional_months, bool)
        ):
            raise ValueError("Duration must be a whole number of months.")

        if not 1 <= additional_months <= 12:
            raise ValueError("Duration must be between 1 and 12 months.")

        # Find a parking right belonging to this employee.
        try:
            parking_right = EmployeeParkingRight.objects.get(
                pk=parking_right_id,
                employee=employee,
            )
        except EmployeeParkingRight.DoesNotExist:
            raise ValueError(
                "Parking right not found or does not belong to you."
            )

        # An expired right must be handled through UC02.
        if parking_right.end_date < date.today():
            raise ValueError(
                "Your parking right has expired. Please apply again using UC02."
            )

        # Save a pending request without modifying the existing right.
        return ParkingExtensionRequest.objects.create(
            parking_right=parking_right,
            additional_months=additional_months,
            status=ParkingExtensionRequest.Status.PENDING,
        )
