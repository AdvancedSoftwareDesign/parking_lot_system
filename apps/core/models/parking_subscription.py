from django.conf import settings
from django.db import models


class ParkingSubscription(models.Model):
    parking_lot = models.ForeignKey(
        "ParkingLot",
        on_delete=models.CASCADE,
        related_name="subscriptions"
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="parking_subscriptions"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["parking_lot", "user"],
                name="unique_parking_lot_user_subscription"
            )
        ]

    def __str__(self):
        return f"{self.user.username} subscribes to parking lot {self.parking_lot_id}"