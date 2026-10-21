from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Exists, OuterRef

from apps.accounts.api_views import get_user_role
from apps.core.models import ParkingRecord, Vehicle


class DeactivationError(ValueError):
    pass


class RegistrationNotFound(DeactivationError):
    pass


class RegistrationConflict(DeactivationError):
    pass


class VehicleDeactivationService:
    """UC8: administrator search and confirmed soft deactivation."""

    def _require_administrator(self, user):
        if not (user.is_authenticated and user.is_active
                and get_user_role(user) == "Parking Administrator"):
            raise PermissionDenied("Only Parking Administrators can deactivate registrations.")

    def search_registrations(self, user, registration_number=None, employee_id=None):
        self._require_administrator(user)
        number = (registration_number or "").strip().upper()
        employee = (employee_id or "").strip()
        if not number and not employee:
            raise DeactivationError("Enter a vehicle number or employee ID.")
        vehicles = Vehicle.objects.select_related("owner").order_by("id")
        if number:
            vehicles = vehicles.filter(registration_number__icontains=number)
        if employee:
            if not employee.isascii() or not employee.isdecimal() or len(employee) > 18 or int(employee) <= 0:
                raise DeactivationError("Employee ID must be a positive integer.")
            vehicles = vehicles.filter(owner_id=int(employee))
        return vehicles.annotate(currently_parked=Exists(
            ParkingRecord.objects.filter(vehicle_id=OuterRef("pk"), exit_time__isnull=True)
        ))

    @transaction.atomic
    def deactivate_vehicle(self, user, vehicle_id, confirmed):
        self._require_administrator(user)
        if type(confirmed) is not bool:
            raise DeactivationError("confirmed must be a JSON boolean (true or false).")
        try:
            vehicle = Vehicle.objects.select_for_update().get(pk=vehicle_id)
        except Vehicle.DoesNotExist as exc:
            raise RegistrationNotFound("No matching registration found.") from exc
        if not confirmed:
            return vehicle, False
        if not vehicle.registration_active:
            raise RegistrationConflict("The vehicle registration is already inactive.")
        # Re-check at confirmation time: a vehicle may have entered after search.
        if ParkingRecord.objects.filter(vehicle=vehicle, exit_time__isnull=True).exists():
            raise RegistrationConflict("The vehicle is currently parked. Record its exit first.")
        vehicle.deactivate()
        return vehicle, True
