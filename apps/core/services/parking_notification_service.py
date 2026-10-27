from apps.core.models import ParkingLot
from apps.core.observers.user_observer import UserObserver


class ParkingNotificationService:

    def notify_subscribers(self, parking_lot, event):

        subject = ParkingLot.objects.get(pk=parking_lot.pk)

        subscriptions = subject.subscriptions.select_related("user")

        for subscription in subscriptions:
            observer = UserObserver(subscription.user)
            subject.add_observer(observer)

        subject.notify_observers(event)