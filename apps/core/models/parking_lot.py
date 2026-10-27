from django.core.exceptions import ValidationError
from django.db import models


class ParkingLot(models.Model):
    capacity = models.PositiveIntegerField()

    def clean(self):
        super().clean()

        if self.capacity is not None and self.capacity < 1:
            raise ValidationError({
                "capacity": "Capacity must be at least 1."
            })

    def __str__(self):
        return f"Parking lot {self.pk} (capacity: {self.capacity})"