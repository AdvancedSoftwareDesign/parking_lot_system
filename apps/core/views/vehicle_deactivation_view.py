from rest_framework.authentication import TokenAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.services.vehicle_deactivation_service import (
    DeactivationError, RegistrationConflict, RegistrationNotFound,
    VehicleDeactivationService,
)


def vehicle_data(vehicle):
    return {
        "id": vehicle.id,
        "registration_number": vehicle.registration_number,
        # The current team model has no separate company employee ID.
        "employee_id": vehicle.owner_id,
        "employee_username": vehicle.owner.username,
        "registration_active": vehicle.registration_active,
    }


class RegistrationSearchView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            vehicles = VehicleDeactivationService().search_registrations(
                request.user, request.query_params.get("registration_number"),
                request.query_params.get("employee_id"),
            )
        except DeactivationError as exc:
            return Response({"error": str(exc)}, status=400)
        paginator = PageNumberPagination()
        paginator.page_size = 20
        page = paginator.paginate_queryset(vehicles, request)
        results = [{**vehicle_data(v), "currently_parked": v.currently_parked} for v in page]
        return paginator.get_paginated_response(results)


class VehicleDeactivationView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, vehicle_id):
        if not isinstance(request.data, dict):
            return Response({"error": "Send a JSON object with confirmed."}, status=400)
        try:
            vehicle, changed = VehicleDeactivationService().deactivate_vehicle(
                request.user, vehicle_id, request.data.get("confirmed"),
            )
        except RegistrationNotFound as exc:
            return Response({"error": str(exc)}, status=404)
        except RegistrationConflict as exc:
            return Response({"error": str(exc)}, status=409)
        except DeactivationError as exc:
            return Response({"error": str(exc)}, status=400)
        return Response({
            "message": "Registration deactivated. Parking history retained." if changed
                       else "Deactivation cancelled. Registration unchanged.",
            "changed": changed,
            "vehicle": vehicle_data(vehicle),
        })