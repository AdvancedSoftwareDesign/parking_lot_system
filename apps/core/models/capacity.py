from django.db import models


class ParkingCapacity(models.Model):
    """Store the current usable parking capacity."""

    total_capacity = models.PositiveIntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Parking capacity: {self.total_capacity}"