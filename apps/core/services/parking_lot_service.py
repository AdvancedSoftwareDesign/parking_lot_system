from apps.core.models import ParkingLot


class ParkingLotService:

    def create_parking_lot(self, capacity):
        parking_lot = ParkingLot(capacity=capacity)

        parking_lot.full_clean()
        parking_lot.save()

        return parking_lot

    def set_capacity(self, parking_lot_id, new_capacity):
        parking_lot = ParkingLot.objects.get(pk=parking_lot_id)

        parking_lot.set_capacity(new_capacity)

        return parking_lot