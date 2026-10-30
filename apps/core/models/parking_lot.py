from django.core.exceptions import ValidationError
from django.db import models


class ParkingLot(models.Model):
    capacity = models.PositiveIntegerField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._observers = []

    def add_observer(self, observer):
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer):
        if observer in self._observers:
            self._observers.remove(observer)

    def notify_observers(self, event):
        for observer in self._observers:
            observer.update(self, event)

    def set_capacity(self, new_capacity):
        original_capacity = self.capacity
        self.capacity = new_capacity

        try:
            self.full_clean()

            occupied_spaces = self.get_occupied_spaces()

            if self.capacity < occupied_spaces:
                raise ValidationError({
                    "capacity": (
                        "Capacity can't be lower than the current "
                        f"number of parked vehicles ({occupied_spaces})."
                    )
                })

            self.save(update_fields=["capacity"])

        except ValidationError:
            self.capacity = original_capacity
            raise

    def get_occupied_spaces(self):
        return self.parking_sessions.filter(
            exit_time__isnull=True
        ).count()

    def get_available_spaces(self):
        return self.capacity - self.get_occupied_spaces()

    def clean(self):
        super().clean()

        if self.capacity is not None and self.capacity < 1:
            raise ValidationError({
                "capacity": "Capacity must be at least 1."
            })

    def __str__(self):
        return f"Parking lot {self.pk} (capacity: {self.capacity})"