from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from apps.core.services.occupancy_service import ParkingRecordOccupancy
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.accounts.api_views import get_user_role
from apps.core.services.capacity_repository import DjangoCapacityRepository
from apps.core.services.capacity_service import (
    CapacityNotConfiguredError,
    CapacityService,
    InvalidCapacityError,
    OccupancyUnavailableError,
)
from django.utils import timezone
from django.db import DatabaseError
from django.utils import timezone


class UnavailableOccupancy:
    def get_occupied_spaces(self) -> int:
        raise OccupancyUnavailableError(
            "Vehicle occupancy data is not available yet."
        )


def get_capacity_service():
    return CapacityService(
        capacity_repository=DjangoCapacityRepository(),
        occupancy_port=ParkingRecordOccupancy(),
    )


def administrator_required(request):
    return get_user_role(request.user) == "Parking Administrator"


@api_view(["GET"])
def initial_check(request):
    return Response({
        "status": "ok",
        "message": "API is running",
    })


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def capacity_status(request):
    role = get_user_role(request.user)

    if role not in ("Employee", "Security Guard"):
        return Response(
            {"error": "Only Employees and Security Guards can view parking status."},
            status=status.HTTP_403_FORBIDDEN,
        )

    try:
        result = get_capacity_service().get_capacity_status()
    except CapacityNotConfiguredError as error:
        return Response(
            {"error": str(error)},
            status=status.HTTP_404_NOT_FOUND,
        )
    except (OccupancyUnavailableError, DatabaseError):
        return Response(
            {"error": "Status unavailable. Please retry."},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    result["checked_at"] = timezone.now().isoformat()
    result["status"] = (
        "Full" if result["available_spaces"] == 0 else "Available"
    )

    return Response(result)


@api_view(["PUT"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def set_capacity(request):
    if not administrator_required(request):
        return Response(
            {"error": "Only Parking Administrators can change capacity."},
            status=status.HTTP_403_FORBIDDEN,
        )

    new_capacity = request.data.get("total_capacity")

    if isinstance(new_capacity, str):
        try:
            if not new_capacity.strip():
                raise ValueError
            new_capacity = int(new_capacity)
        except ValueError:
            return Response(
                {"error": "Capacity must be a positive whole number."},
                status=status.HTTP_400_BAD_REQUEST,
            )

    try:
        result = get_capacity_service().set_capacity(new_capacity)
    except InvalidCapacityError as error:
        return Response(
            {"error": str(error)},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except OccupancyUnavailableError as error:
        return Response(
            {"error": str(error)},
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    return Response(result, status=status.HTTP_200_OK)
