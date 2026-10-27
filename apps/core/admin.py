from django.contrib import admin

from apps.core.models import (
    ParkingApplication,
    EmployeeParkingRight,
    ParkingExtensionRequest,
)
from django.db import transaction
from datetime import timedelta
from django.core.exceptions import ValidationError

@admin.register(ParkingApplication)
class ParkingApplicationAdmin(admin.ModelAdmin):
    list_display = ("id", "employee", "vehicle", "start_date", "status")
    list_filter = ("status",)
    search_fields = ("employee__username", "vehicle__registration_number")


    @transaction.atomic
    def save_model(self, request, obj, form, change):
        previous_status = None

        if change:
            previous_status = (
                ParkingApplication.objects
                .select_for_update()
                .get(pk=obj.pk)
                .status
            )

        approving = (
            obj.status == ParkingApplication.Status.APPROVED
            and previous_status != ParkingApplication.Status.APPROVED
        )

        if approving:
            if obj.start_date < obj.created_at.date():
                raise ValidationError(
                    "The parking start date cannot be before the application date."
                )

            if not 1 <= obj.duration_months <= 12:
                raise ValidationError(
                    "Duration must be between 1 and 12 months."
                )

        super().save_model(request, obj, form, change)

        if approving:
            EmployeeParkingRight.objects.get_or_create(
                application=obj,
                defaults={
                    "employee": obj.employee,
                    "vehicle": obj.vehicle,
                    "start_date": obj.start_date,
                    "end_date": obj.start_date + timedelta(
                        days=obj.duration_months * 30
                    ),
                },
            )


@admin.register(EmployeeParkingRight)
class EmployeeParkingRightAdmin(admin.ModelAdmin):
    list_display = ("id", "employee", "vehicle", "start_date", "end_date")
    search_fields = ("employee__username", "vehicle__registration_number")


@admin.register(ParkingExtensionRequest)
class ParkingExtensionRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "parking_right",
        "additional_months",
        "status",
        "created_at",
    )
    list_filter = ("status",)
