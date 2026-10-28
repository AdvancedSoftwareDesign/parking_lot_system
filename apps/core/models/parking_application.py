
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class ParkingApplication(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    employee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="parking_applications"
    )

    vehicle = models.ForeignKey(
        "Vehicle",
        on_delete=models.PROTECT,
        related_name="parking_applications"
    )

    start_date = models.DateField()

    duration_months = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(12)
        ]
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PENDING
    )

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    
    @property
    def duration_days(self):
        return self.duration_months * 30



    def __str__(self):
        return (
            f"Parking application {self.pk} "
            f"for {self.employee.username}"
        )
