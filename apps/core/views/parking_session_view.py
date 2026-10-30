from django.core.exceptions import ValidationError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import ParkingLot, Vehicle
from apps.core.services.parking_session_service import ParkingSessionService


class ParkingEntryView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, parking_lot_id):
        registration_number = request.data.get("registration_number")

        if (
            not isinstance(registration_number, str)
            or not registration_number.strip()
        ):
            return Response(
                {"error": "Please provide the vehicle registration number."},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = ParkingSessionService()

        try:
            session = service.enter(
                parking_lot_id=parking_lot_id,
                registration_number=registration_number
            )
        except ParkingLot.DoesNotExist as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_404_NOT_FOUND
            )
        except Vehicle.DoesNotExist:
            return Response(
                {"error": "Vehicle not registered."},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as error:
            return Response(
                {"errors": error.messages},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "message": "Vehicle entered successfully.",
                "session_id": session.pk,
                "user_id": session.user_id,
                "vehicle_id": session.vehicle_id,
                "registration_number": session.vehicle.registration_number,
                "parking_lot_id": session.parking_lot_id,
                "entry_time": session.entry_time.isoformat(),
                "exit_time": None
            },
            status=status.HTTP_201_CREATED
        )


class ParkingExitView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, parking_lot_id):
        registration_number = request.data.get("registration_number")

        if (
            not isinstance(registration_number, str)
            or not registration_number.strip()
        ):
            return Response(
                {"error": "Please provide the vehicle registration number."},
                status=status.HTTP_400_BAD_REQUEST
            )

        service = ParkingSessionService()

        try:
            session = service.exit(
                parking_lot_id=parking_lot_id,
                registration_number=registration_number
            )
        except ParkingLot.DoesNotExist:
            return Response(
                {"error": "Parking lot not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        except Vehicle.DoesNotExist:
            return Response(
                {"error": "Vehicle not registered."},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValidationError as error:
            return Response(
                {"errors": error.messages},
                status=status.HTTP_400_BAD_REQUEST
            )
        except ValueError as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "message": "Vehicle exited successfully.",
                "session_id": session.pk,
                "user_id": session.user_id,
                "vehicle_id": session.vehicle_id,
                "registration_number": session.vehicle.registration_number,
                "parking_lot_id": session.parking_lot_id,
                "entry_time": session.entry_time.isoformat(),
                "exit_time": session.exit_time.isoformat()
            },
            status=status.HTTP_200_OK
        )