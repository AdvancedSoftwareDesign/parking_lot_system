
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from apps.accounts.api_views import get_user_role
from apps.core.services.capacity_repository import DjangoCapacityRepository
from apps.core.services.capacity_service import CapacityService
from apps.core.services.occupancy_service import ParkingRecordOccupancy
from apps.core.services.parking_entry_service import (
    ParkingEntryError,
    ParkingEntryService,
)


class ParkingEntryView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if get_user_role(request.user) != "Security Guard":
            return Response(
                {"error": "Only security guards can record vehicle entry."},
                status=status.HTTP_403_FORBIDDEN,
            )

        registration_number = request.data.get("registration_number")

        service = ParkingEntryService(
            capacity_service=CapacityService(
                capacity_repository=DjangoCapacityRepository(),
                occupancy_port=ParkingRecordOccupancy(),
            )
        )

        try:
            record = service.record_entry(registration_number or "")
        except ParkingEntryError as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Vehicle entry recorded successfully.",
                "record": {
                    "id": record.id,
                    "registration_number": record.vehicle.registration_number,
                    "employee_id": record.vehicle.owner_id,
                    "entry_time": record.entry_time,
                },
            },
            status=status.HTTP_201_CREATED,
        )
