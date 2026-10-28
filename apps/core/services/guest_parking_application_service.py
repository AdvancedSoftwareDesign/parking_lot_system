from django.db import transaction

from apps.core.models import GuestParkingApplication, Vehicle


class GuestParkingApplicationService:
    """UC04 business rules; this class does not handle HTTP details."""

    REQUIRED_TEXT_FIELDS = (
        "guest_name",
        "mobile_number",
        "email",
        "parking_reason",
    )

    @transaction.atomic
    def submit_application(
        self,
        *,
        registration_number,
        guest_name,
        mobile_number,
        email,
        parking_reason,
        requested_start,
        requested_end,
    ):
        values = {
            "registration_number": registration_number,
            "guest_name": guest_name,
            "mobile_number": mobile_number,
            "email": email,
            "parking_reason": parking_reason,
        }

        for field_name, value in values.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} is required.")

        if requested_start is None or requested_end is None:
            raise ValueError("Parking start and end times are required.")

        if requested_end <= requested_start:
            raise ValueError(
                "The parking end time must be after the start time."
            )

        normalised_registration = registration_number.strip().upper()

        # UC04 permits repeat and overlapping guest applications.
        # The unique vehicle record is reused when the plate already exists.
        vehicle, _ = Vehicle.objects.get_or_create(
            registration_number=normalised_registration,
            defaults={"owner": None},
        )

        application = GuestParkingApplication(
            vehicle=vehicle,
            guest_name=guest_name.strip(),
            mobile_number=mobile_number.strip(),
            email=email.strip(),
            parking_reason=parking_reason.strip(),
            requested_start=requested_start,
            requested_end=requested_end,
            status=GuestParkingApplication.Status.PENDING,
        )
        application.full_clean()
        application.save()

        return application