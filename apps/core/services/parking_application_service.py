
from apps.core.models import ParkingApplication, Vehicle


class ParkingApplicationService:

    def apply_for_parking(
        self, employee, vehicle_id, start_date, duration_months
    ):
        if not isinstance(duration_months, int) or isinstance(
            duration_months, bool
        ):
            raise ValueError("Duration must be a whole number of months.")

        if not 1 <= duration_months <= 12:
            raise ValueError("Duration must be between 1 and 12 months.")

        try:
            vehicle = Vehicle.objects.get(
                pk=vehicle_id,
                owner=employee
            )
        except Vehicle.DoesNotExist:
            raise ValueError(
                "Vehicle not found or does not belong to you."
            )

        application = ParkingApplication.objects.create(
            employee=employee,
            vehicle=vehicle,
            start_date=start_date,
            duration_months=duration_months,
            status=ParkingApplication.Status.PENDING
        )

        return application
