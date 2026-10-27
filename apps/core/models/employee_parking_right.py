
from django.conf import settings
from django.db import models


class EmployeeParkingRight(models.Model):
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
        related_name="parking_rights"
    )

    vehicle = models.ForeignKey(
        "Vehicle",
        on_delete=models.PROTECT,
        related_name="parking_rights"
    )

    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"Parking right {self.pk} for {self.employee.username}"
