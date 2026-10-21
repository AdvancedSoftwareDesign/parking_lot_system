
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from apps.accounts.api_views import get_user_role
from apps.core.services.parking_exit_service import (
    ParkingExitError,
    ParkingExitService,
)


class ParkingExitView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if get_user_role(request.user) != "Security Guard":
            return Response(
                {"error": "Only security guards can record vehicle exit."},
                status=status.HTTP_403_FORBIDDEN,
            )

        registration_number = request.data.get("registration_number")

        try:
            record = ParkingExitService().record_exit(
                registration_number or ""
            )
        except ParkingExitError as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Vehicle exit recorded successfully.",
                "record": {
                    "id": record.id,
                    "registration_number": record.vehicle.registration_number,
                    "employee_id": record.vehicle.owner_id,
                    "entry_time": record.entry_time,
                    "exit_time": record.exit_time,
                },
            },
            status=status.HTTP_200_OK,
        )
