from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone


class ParkingSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="parking_sessions"
    )

    vehicle = models.ForeignKey(
        "Vehicle",
        on_delete=models.PROTECT,
        related_name="parking_sessions"
    )

    parking_lot = models.ForeignKey(
        "ParkingLot",
        on_delete=models.PROTECT,
        related_name="parking_sessions"
    )

    entry_time = models.DateTimeField(default=timezone.now)

    exit_time = models.DateTimeField(
        null=True,
        blank=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["vehicle"],
                condition=Q(exit_time__isnull=True),
                name="unique_open_session_per_vehicle"
            ),
            models.CheckConstraint(
                condition=(
                    Q(exit_time__isnull=True)
                    | Q(exit_time__gte=F("entry_time"))
                ),
                name="session_exit_not_before_entry"
            )
        ]

    def __str__(self):
        return (
            f"Parking session {self.pk}: "
            f"vehicle {self.vehicle_id}, "
            f"parking lot {self.parking_lot_id}"
        )