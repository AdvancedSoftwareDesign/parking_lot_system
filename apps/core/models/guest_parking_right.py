from django.db import models
from django.utils import timezone


class GuestParkingRight(models.Model):
    """A right created only after a guest application is approved."""

    class State(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        ACTIVE = "active", "Active"
        INACTIVE = "inactive", "Inactive"

    application = models.OneToOneField(
        "GuestParkingApplication",
        on_delete=models.PROTECT,
        related_name="parking_right",
    )

    vehicle = models.ForeignKey(
        "Vehicle",
        on_delete=models.PROTECT,
        related_name="guest_parking_rights",
    )

    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    state = models.CharField(
        max_length=10,
        choices=State.choices,
        default=State.SCHEDULED,
    )

    # A manually disabled right must never be reactivated automatically.
    manually_disabled = models.BooleanField(default=False)

    def is_currently_valid(self, at=None):
        at = at or timezone.now()
        return (
            not self.manually_disabled
            and self.start_at <= at < self.end_at
        )

    def refresh_state(self, at=None):
        at = at or timezone.now()

        if self.manually_disabled or at >= self.end_at:
            self.state = self.State.INACTIVE
        elif at < self.start_at:
            self.state = self.State.SCHEDULED
        else:
            self.state = self.State.ACTIVE

        return self.state

    def deactivate(self):
        """UC08: disable this right without deleting any history."""
        if self.manually_disabled:
            return False

        self.manually_disabled = True
        self.state = self.State.INACTIVE
        self.save(update_fields=["manually_disabled", "state"])
        return True

    def __str__(self):
        return f"Guest parking right {self.pk} ({self.state})"