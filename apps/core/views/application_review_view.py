from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.permissions import IsSecurityGuard
from apps.core.services.application_review_service import ApplicationReviewService


class ApplicationReviewView(APIView):
    """UC05: a Security Guard approves or rejects a pending request."""

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsSecurityGuard]

    def post(self, request, review_type, item_id):
        approved = request.data.get("approved")
        if not isinstance(approved, bool):
            return Response(
                {"error": "approved must be true or false."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = ApplicationReviewService()
        review_actions = {
            "guest": service.review_guest_application,
            "employee": service.review_employee_application,
            "extension": service.review_extension_request,
        }
        action = review_actions.get(review_type)
        if action is None:
            return Response(
                {"error": "review_type must be guest, employee, or extension."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            reviewed_item, parking_right = action(
                item_id=item_id,
                approved=approved,
            )
        except ObjectDoesNotExist:
            return Response(
                {"error": "Request not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response_data = {
            "id": reviewed_item.id,
            "status": reviewed_item.status,
            "decision": "approved" if approved else "rejected",
        }
        if parking_right is not None:
            response_data["parking_right"] = {
                "id": parking_right.id,
                "type": parking_right.__class__.__name__,
                "state": parking_right.state,
            }
        return Response(response_data, status=status.HTTP_200_OK)
