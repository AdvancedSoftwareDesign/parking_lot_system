from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.services.guest_parking_application_service import (
    GuestParkingApplicationService,
)


class GuestParkingApplicationView(APIView):
    """Public endpoint for UC04; guests do not authenticate."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        requested_start = parse_datetime(
            request.data.get("requested_start", "")
        )
        requested_end = parse_datetime(
            request.data.get("requested_end", "")
        )

        if requested_start is None or requested_end is None:
            return Response(
                {
                    "error": (
                        "requested_start and requested_end must use "
                        "ISO 8601 date-time format."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            application = (
                GuestParkingApplicationService().submit_application(
                    registration_number=request.data.get(
                        "registration_number", ""
                    ),
                    guest_name=request.data.get("guest_name", ""),
                    mobile_number=request.data.get("mobile_number", ""),
                    email=request.data.get("email", ""),
                    parking_reason=request.data.get("parking_reason", ""),
                    requested_start=requested_start,
                    requested_end=requested_end,
                )
            )
        except (ValueError, ValidationError) as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Guest parking application submitted for review.",
                "application": {
                    "id": application.id,
                    "vehicle_id": application.vehicle_id,
                    "status": application.status,
                    "requested_start": application.requested_start.isoformat(),
                    "requested_end": application.requested_end.isoformat(),
                },
            },
            status=status.HTTP_201_CREATED,
        )