from datetime import date, timedelta

from django.db import transaction
from django.utils import timezone

from apps.core.models import (
    EmployeeParkingRight,
    GuestParkingApplication,
    GuestParkingRight,
    ParkingApplication,
    ParkingExtensionRequest,
)


class ApplicationReviewService:
    """UC05: Security Guard approves or rejects pending requests."""

    @transaction.atomic
    def review_guest_application(self, item_id, approved):
        application = (
            GuestParkingApplication.objects.select_for_update()
            .select_related("vehicle")
            .get(pk=item_id)
        )
        self._ensure_pending(application)

        if not approved:
            return self._reject(application)

        now = timezone.now()
        if application.requested_end <= now:
            raise ValueError(
                "A guest visit that has already ended cannot be approved."
            )

        parking_right = GuestParkingRight.objects.create(
            application=application,
            vehicle=application.vehicle,
            start_at=max(application.requested_start, now),
            end_at=application.requested_end,
        )
        parking_right.refresh_state(now)
        parking_right.save(update_fields=["state"])

        application.status = GuestParkingApplication.Status.APPROVED
        application.reviewed_at = now
        application.save(update_fields=["status", "reviewed_at"])
        return application, parking_right

    @transaction.atomic
    def review_employee_application(self, item_id, approved):
        application = (
            ParkingApplication.objects.select_for_update()
            .select_related("employee", "vehicle")
            .get(pk=item_id)
        )
        self._ensure_pending(application)

        if not approved:
            return self._reject(application)
        if not application.employee.is_active:
            raise ValueError(
                "An inactive employee cannot receive a parking right."
            )

        right_start = max(application.start_date, date.today())
        parking_right = EmployeeParkingRight.objects.create(
            application=application,
            employee=application.employee,
            vehicle=application.vehicle,
            start_date=right_start,
            end_date=right_start + timedelta(days=application.duration_months * 30),
        )
        parking_right.refresh_state()
        parking_right.save(update_fields=["state"])

        application.status = ParkingApplication.Status.APPROVED
        application.reviewed_at = timezone.now()
        application.save(update_fields=["status", "reviewed_at"])
        return application, parking_right

    @transaction.atomic
    def review_extension_request(self, item_id, approved):
        extension = (
            ParkingExtensionRequest.objects.select_for_update()
            .select_related("parking_right", "parking_right__employee")
            .get(pk=item_id)
        )
        self._ensure_pending(extension)

        if not approved:
            return self._reject(extension)

        parking_right = extension.parking_right
        if not parking_right.employee.is_active:
            raise ValueError(
                "An inactive employee cannot receive a parking extension."
            )
        if parking_right.manually_disabled:
            raise ValueError(
                "A manually disabled parking right cannot be reactivated."
            )

        today = date.today()
        extension_start = max(parking_right.end_date, today)
        if parking_right.end_date < today:
            parking_right.start_date = today
        parking_right.end_date = extension_start + timedelta(
            days=extension.additional_months * 30
        )
        parking_right.refresh_state()
        parking_right.save(update_fields=["start_date", "end_date", "state"])

        extension.status = ParkingExtensionRequest.Status.APPROVED
        extension.reviewed_at = timezone.now()
        extension.save(update_fields=["status", "reviewed_at"])
        return extension, parking_right

    @staticmethod
    def _ensure_pending(item):
        if item.status != item.Status.PENDING:
            raise ValueError("This request has already been processed.")

    @staticmethod
    def _reject(item):
        item.status = item.Status.REJECTED
        item.reviewed_at = timezone.now()
        item.save(update_fields=["status", "reviewed_at"])
        return item, None
