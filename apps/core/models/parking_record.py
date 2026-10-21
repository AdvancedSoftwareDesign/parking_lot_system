from django.db import models

from .vehicle import Vehicle


class ParkingRecord(models.Model):
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name="parking_records",
    )
    entry_time = models.DateTimeField(auto_now_add=True)
    exit_time = models.DateTimeField(null=True, blank=True)

    @property
    def is_active(self):
        return self.exit_time is None

    def __str__(self):
        return f"{self.vehicle.registration_number} - {self.entry_time}"