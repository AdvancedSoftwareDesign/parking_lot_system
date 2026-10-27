from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import ParkingLot
from apps.core.services.parking_lot_service import ParkingLotService


class ParkingLotCreateView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def post(self, request):
        capacity = request.data.get("capacity")

        if not isinstance(capacity, int) or isinstance(capacity, bool):
            return Response(
                {"error": "Capacity must be an integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = ParkingLotService()

        try:
            parking_lot = service.create_parking_lot(capacity)
        except ValidationError as error:
            return Response(
                {"errors": error.message_dict},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "id": parking_lot.pk,
                "capacity": parking_lot.capacity
            },
            status=status.HTTP_201_CREATED
        )


class ParkingLotCapacityView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAdminUser]

    def patch(self, request, parking_lot_id):
        capacity = request.data.get("capacity")

        if not isinstance(capacity, int) or isinstance(capacity, bool):
            return Response(
                {"error": "Capacity must be an integer."},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = ParkingLotService()

        try:
            parking_lot = service.set_capacity(
                parking_lot_id=parking_lot_id,
                new_capacity=capacity
            )
        except ParkingLot.DoesNotExist:
            return Response(
                {"error": "Parking lot not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as error:
            return Response(
                {"errors": error.message_dict},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "id": parking_lot.pk,
                "capacity": parking_lot.capacity
            },
            status=status.HTTP_200_OK
        )