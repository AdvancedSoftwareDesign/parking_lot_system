from django.db import IntegrityError
from apps.core.models import Vehicle

import re


class VehicleRegistrationService:

    def register_vehicle(self, user, registration_number):
        registration_number = registration_number.strip().upper()

        self._validate_registration_number(registration_number)

        try:
            vehicle = Vehicle.objects.create(
                registration_number=registration_number,
                owner=user
            )
        except IntegrityError:
            raise ValueError("This vehicle is already registered.")

        return vehicle

    def _validate_registration_number(self, registration_number):
        if not registration_number:
            raise ValueError("Please enter the registration number.")

        if len(registration_number) > 10:
            raise ValueError("Registration number must not exceed 10 characters.")

        if not re.fullmatch(r"[A-Z0-9-]+", registration_number):
            raise ValueError("Registration number can only contain letters, numbers, and hyphens.")