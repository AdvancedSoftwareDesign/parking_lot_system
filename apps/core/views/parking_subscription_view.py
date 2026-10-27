from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import ParkingLot
from apps.core.services.parking_subscription_service import (
    ParkingSubscriptionService,
)


class ParkingSubscriptionView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, parking_lot_id):
        service = ParkingSubscriptionService()

        try:
            subscription, created = service.subscribe(
                parking_lot_id=parking_lot_id,
                user=request.user
            )
        except ParkingLot.DoesNotExist:
            return Response(
                {"error": "Parking lot not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not created:
            return Response(
                {"message": "You are already subscribed."},
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "message": "Subscribed successfully.",
                "parking_lot_id": subscription.parking_lot_id
            },
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, parking_lot_id):
        service = ParkingSubscriptionService()

        try:
            deleted = service.unsubscribe(
                parking_lot_id=parking_lot_id,
                user=request.user
            )
        except ParkingLot.DoesNotExist:
            return Response(
                {"error": "Parking lot not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not deleted:
            return Response(
                {"message": "You are not subscribed."},
                status=status.HTTP_200_OK
            )

        return Response(
            {"message": "Unsubscribed successfully."},
            status=status.HTTP_200_OK
        )