from django.conf import settings
from django.db import models


class Vehicle(models.Model):
    """A vehicle is shared by all parking workflows and is identified by its plate."""

    registration_number = models.CharField(
        max_length=10,
        unique=True,
    )

    # Guests have no application account, so a vehicle may not have an owner.
    # SET_NULL preserves historical applications if an employee account is removed.
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vehicles",
    )

    def __str__(self):
        return self.registration_number