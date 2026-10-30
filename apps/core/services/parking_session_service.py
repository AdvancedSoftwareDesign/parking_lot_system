from functools import partial

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from apps.core.models import (
    EmployeeParkingRight,
    ParkingLot,
    ParkingSession,
    Vehicle,
)
from apps.core.services.parking_access_service import ParkingAccessService
from apps.core.services.parking_notification_service import (
    ParkingNotificationService,
)


class ParkingSessionService:

    def __init__(self):
        self.access_service = ParkingAccessService()
        self.notification_service = ParkingNotificationService()

    @transaction.atomic
    def enter(self, parking_lot_id, registration_number):
        # Obtain write lock in SQLite
        updated = ParkingLot.objects.filter(
            pk=parking_lot_id
        ).update(capacity=F("capacity"))

        if updated == 0:
            raise ParkingLot.DoesNotExist(
                "Parking lot not found."
            )

        parking_lot = ParkingLot.objects.get(pk=parking_lot_id)
        vehicle = Vehicle.objects.get(registration_number=registration_number.strip().upper()
)

        now = timezone.now()

        parking_right = self.access_service.get_valid_parking_right(
            vehicle,
            at=now
        )

        already_parked = ParkingSession.objects.filter(
            vehicle=vehicle,
            exit_time__isnull=True
        ).exists()

        if already_parked:
            raise ValueError(
                "This vehicle is already inside a parking lot."
            )

        if parking_lot.get_available_spaces() <= 0:
            raise ValueError(
                "This parking lot is full."
            )

        user = (
            parking_right.employee
            if isinstance(parking_right, EmployeeParkingRight)
            else None
        )

        session = ParkingSession(
            user=user,
            vehicle=vehicle,
            parking_lot=parking_lot,
            entry_time=now
        )

        session.full_clean()
        session.save()

        if parking_lot.get_available_spaces() == 0:
            transaction.on_commit(
                partial(
                    self.notification_service.notify_subscribers,
                    parking_lot,
                    "parking_lot_full"
                )
            )

        return session

    @transaction.atomic
    def exit(self, parking_lot_id, registration_number):
        # Obtain write lock in SQLite
        updated = ParkingLot.objects.filter(
            pk=parking_lot_id
        ).update(capacity=F("capacity"))

        if updated == 0:
            raise ParkingLot.DoesNotExist(
                "Parking lot not found."
            )

        parking_lot = ParkingLot.objects.get(pk=parking_lot_id)
        vehicle = Vehicle.objects.get(registration_number=registration_number.strip().upper()
)

        session = ParkingSession.objects.filter(
            parking_lot=parking_lot,
            vehicle=vehicle,
            exit_time__isnull=True
        ).first()

        if session is None:
            raise ValueError(
                "This vehicle is not currently inside this parking lot."
            )

        available_before = parking_lot.get_available_spaces()

        session.close()
        session.save(update_fields=["exit_time"])

        if available_before == 0:
            transaction.on_commit(
                partial(
                    self.notification_service.notify_subscribers,
                    parking_lot,
                    "space_available"
                )
            )

        return session