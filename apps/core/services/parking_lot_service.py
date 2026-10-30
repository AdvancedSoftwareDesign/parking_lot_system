from apps.core.models import ParkingLot
from django.db import transaction
from django.db.models import F

class ParkingLotService:

    def create_parking_lot(self, capacity):
        parking_lot = ParkingLot(capacity=capacity)

        parking_lot.full_clean()
        parking_lot.save()

        return parking_lot

    @transaction.atomic
    def set_capacity(self, parking_lot_id, new_capacity):
        updated = ParkingLot.objects.filter(
            pk=parking_lot_id
        ).update(capacity=F("capacity"))

        if updated == 0:
            raise ParkingLot.DoesNotExist(
                "Parking lot not found."
            )

        parking_lot = ParkingLot.objects.get(pk=parking_lot_id)
        parking_lot.set_capacity(new_capacity)

        return parking_lot