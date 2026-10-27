from .parking_observer import ParkingObserver


class UserObserver(ParkingObserver):

    def __init__(self, user):
        self.user = user

    def update(self, parking_lot, event):
        if event == "parking_lot_full":
            print(
                f"Notification for {self.user.username}: "
                f"Parking lot {parking_lot.pk} is full."
            )

        elif event == "space_available":
            print(
                f"Notification for {self.user.username}: "
                f"Parking lot {parking_lot.pk} has available spaces."
            )