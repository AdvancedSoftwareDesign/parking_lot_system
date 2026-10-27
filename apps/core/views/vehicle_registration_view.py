from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from apps.core.services.vehicle_registration_service import VehicleRegistrationService


class VehicleRegistrationView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        registration_number = request.data.get("registration_number")

        service = VehicleRegistrationService()

        try:
            vehicle = service.register_vehicle(
                user=request.user,
                registration_number=registration_number
            )
        except ValueError as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "message": "Vehicle registered successfully.",
                "vehicle": {
                    "id": vehicle.id,
                    "registration_number": vehicle.registration_number,
                    "owner_id": vehicle.owner_id
                }
            },
            status=status.HTTP_201_CREATED
        )
