
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from apps.core.services.parking_extension_service import (
    ParkingExtensionService,
)


class ParkingExtensionView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        parking_right_id = request.data.get("parking_right_id")
        additional_months = request.data.get("additional_months")

        if parking_right_id is None or additional_months is None:
            return Response(
                {"error": "Parking right ID and additional months are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            parking_right_id = int(parking_right_id)
        except (ValueError, TypeError):
            return Response(
                {"error": "Parking right ID must be an integer."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # JSON numbers normally arrive as integers, but form data may be strings.
        if isinstance(additional_months, str):
            try:
                additional_months = int(additional_months)
            except ValueError:
                return Response(
                    {"error": "Additional months must be a whole number."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        service = ParkingExtensionService()

        try:
            extension = service.request_extension(
                employee=request.user,
                parking_right_id=parking_right_id,
                additional_months=additional_months,
            )
        except ValueError as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "message": "Parking extension request submitted successfully.",
                "extension": {
                    "id": extension.id,
                    "parking_right_id": extension.parking_right_id,
                    "additional_months": extension.additional_months,
                    "status": extension.status,
                },
            },
            status=status.HTTP_201_CREATED,
        )
