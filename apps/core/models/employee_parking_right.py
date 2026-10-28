from datetime import date

from django.conf import settings
from django.db import models


class EmployeeParkingRight(models.Model):
    """An approved employee parking entitlement."""

    class State(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    application = models.OneToOneField(
        "ParkingApplication",
        on_delete=models.PROTECT,
        related_name="parking_right",
        null=True,
        blank=True,
    )

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="parking_rights",
    )

    vehicle = models.ForeignKey(
        "Vehicle",
        on_delete=models.PROTECT,
        related_name="parking_rights",
    )

    start_date = models.DateField()
    end_date = models.DateField()

    state = models.CharField(
        max_length=10,
        choices=State.choices,
        default=State.SCHEDULED,
    )

    manually_disabled = models.BooleanField(default=False)

    def is_currently_valid(self, on_date=None):
        on_date = on_date or date.today()
        return (
            not self.manually_disabled
            and self.start_date <= on_date < self.end_date
        )

    def refresh_state(self, on_date=None):
        on_date = on_date or date.today()

        if self.manually_disabled or on_date >= self.end_date:
            self.state = self.State.INACTIVE
        elif on_date < self.start_date:
            self.state = self.State.SCHEDULED
        else:
            self.state = self.State.ACTIVE

        return self.state

    def deactivate(self):
        """UC08: disable the entitlement but preserve all records."""
        if self.manually_disabled:
            return False

        self.manually_disabled = True
        self.state = self.State.INACTIVE
        self.save(update_fields=["manually_disabled", "state"])
        return True

    def __str__(self):
        return f"Parking right {self.pk} for {self.employee.username}"