from django.db import transaction

from apps.core.models import EmployeeParkingRight, GuestParkingRight


class ParkingRightDeactivationService:
    """UC08: Security Guard manually deactivates a parking right."""

    right_models = {
        "employee": EmployeeParkingRight,
        "guest": GuestParkingRight,
    }

    @transaction.atomic
    def deactivate(self, right_type, right_id):
        model = self.right_models.get(right_type)
        if model is None:
            raise ValueError("right_type must be employee or guest.")

        parking_right = model.objects.select_for_update().get(pk=right_id)
        already_inactive = (
            parking_right.state == parking_right.State.INACTIVE
            and parking_right.manually_disabled
        )
        if not already_inactive:
            parking_right.deactivate()

        return parking_right, already_inactive
