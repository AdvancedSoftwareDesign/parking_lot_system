
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class ParkingExtensionRequest(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"

    parking_right = models.ForeignKey(
        "EmployeeParkingRight",
        on_delete=models.PROTECT,
        related_name="extension_requests"
    )

    additional_months = models.PositiveSmallIntegerField(
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
    
    def __str__(self):
        return (
            f"Extension request {self.pk} "
            f"for parking right {self.parking_right_id}"
        )
