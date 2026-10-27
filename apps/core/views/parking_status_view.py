from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.api_views import get_user_role
from apps.core.models import ParkingRecord


class ParkingStatusVehiclesView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if get_user_role(request.user) != "Security Guard":
            return Response(
                {"error": "Only Security Guards can view vehicles currently inside."},
                status=status.HTTP_403_FORBIDDEN,
            )

        records = (
            ParkingRecord.objects
            .filter(exit_time__isnull=True)
            .select_related("vehicle")
            .order_by("entry_time")
        )

        vehicles = [
            {
                "registration_number": record.vehicle.registration_number,
                "entry_time": record.entry_time,
            }
            for record in records
        ]

        return Response({"vehicles": vehicles}, status=status.HTTP_200_OK)
