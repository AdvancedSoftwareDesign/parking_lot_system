from apps.core.models import ParkingLot, ParkingSubscription


class ParkingSubscriptionService:

    def subscribe(self, parking_lot_id, user):
        parking_lot = ParkingLot.objects.get(pk=parking_lot_id)

        subscription, created = ParkingSubscription.objects.get_or_create(
            parking_lot=parking_lot,
            user=user
        )

        return subscription, created

    def unsubscribe(self, parking_lot_id, user):
        parking_lot = ParkingLot.objects.get(pk=parking_lot_id)

        deleted_count, _ = ParkingSubscription.objects.filter(
            parking_lot=parking_lot,
            user=user
        ).delete()

        return deleted_count > 0