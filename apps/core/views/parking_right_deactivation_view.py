from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsSecurityGuard
from apps.core.services.parking_right_deactivation_service import (
    ParkingRightDeactivationService,
)


class ParkingRightDeactivationView(APIView):
    """UC08: Security Guard deactivates a selected parking right."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsSecurityGuard]

    def post(self, request, right_type, right_id):
        try:
            parking_right, already_inactive = (
                ParkingRightDeactivationService().deactivate(
                    right_type=right_type,
                    right_id=right_id,
                )
            )
        except ObjectDoesNotExist:
            return Response(
                {"error": "Parking right not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Parking right is inactive.",
                "id": parking_right.id,
                "type": right_type,
                "state": parking_right.state,
                "manually_disabled": parking_right.manually_disabled,
                "already_inactive": already_inactive,
            },
            status=status.HTTP_200_OK,
        )
