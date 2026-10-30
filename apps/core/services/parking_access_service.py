from django.utils import timezone

from apps.core.models import (
    EmployeeParkingRight,
    GuestParkingRight,
)


class ParkingAccessService:

    def get_valid_parking_right(self, vehicle, at=None):
        at = at or timezone.now()
        today = timezone.localdate(at)

        employee_rights = EmployeeParkingRight.objects.filter(
            vehicle=vehicle,
            employee=vehicle.owner,
            employee__is_active=True,
            manually_disabled=False,
            start_date__lte=today,
            end_date__gt=today
        ).order_by("pk")

        for right in employee_rights:
            if right.is_currently_valid(on_date=today):
                return right

        guest_rights = GuestParkingRight.objects.filter(
            vehicle=vehicle,
            manually_disabled=False,
            start_at__lte=at,
            end_at__gt=at
        ).order_by("pk")

        for right in guest_rights:
            if right.is_currently_valid(at=at):
                return right

        raise ValueError(
            "This vehicle does not have a valid parking right."
        )