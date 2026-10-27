from datetime import date

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from apps.core.services.parking_application_service import (
    ParkingApplicationService,
)


class ParkingApplicationView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        vehicle_id = request.data.get("vehicle_id")
        start_date_value = request.data.get("start_date")
        duration_months = request.data.get("duration_months")

        if vehicle_id is None or start_date_value is None:
            return Response(
                {"error": "Vehicle ID and start date are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            start_date = date.fromisoformat(start_date_value)
        except (ValueError, TypeError):
            return Response(
                {"error": "Start date must use YYYY-MM-DD format."},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = ParkingApplicationService()

        try:
            application = service.apply_for_parking(
                employee=request.user,
                vehicle_id=vehicle_id,
                start_date=start_date,
                duration_months=duration_months
            )
        except ValueError as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "message": "Parking application submitted successfully.",
                "application": {
                    "id": application.id,
                    "vehicle_id": application.vehicle_id,
                    "start_date": application.start_date.isoformat(),
                    "duration_months": application.duration_months,
                    "duration_days": application.duration_days,
                    "status": application.status
                }
            },
            status=status.HTTP_201_CREATED
        )
