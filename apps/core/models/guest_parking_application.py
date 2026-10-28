from django.core.exceptions import ValidationError
from django.db import models


class GuestParkingApplication(models.Model):
    """A guest's request for a single parking visit."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    vehicle = models.ForeignKey(
        "Vehicle",
        on_delete=models.PROTECT,
        related_name="guest_parking_applications",
    )

    guest_name = models.CharField(max_length=120)
    mobile_number = models.CharField(max_length=30)
    email = models.EmailField()
    parking_reason = models.CharField(max_length=500)

    requested_start = models.DateTimeField()
    requested_end = models.DateTimeField()

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def clean(self):
        super().clean()

        if self.requested_end <= self.requested_start:
            raise ValidationError(
                {"requested_end": "The parking end must be after the start."}
            )

    def __str__(self):
        return (
            f"Guest application {self.pk} - "
            f"{self.vehicle.registration_number} ({self.status})"
        )