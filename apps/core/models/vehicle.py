from django.conf import settings
from django.db import models


class Vehicle(models.Model):
    registration_number = models.CharField(
        max_length=10,
        unique=True
    )

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vehicles"
    )

    registration_active = models.BooleanField(default=True)

    def deactivate(self):
        """Keep the registration and its history; remove entry eligibility."""
        self.registration_active = False
        self.save(update_fields=["registration_active"])

    def __str__(self):
        return self.registration_number