from rest_framework.permissions import BasePermission

from apps.core.models import UserProfile


class IsSecurityGuard(BasePermission):
    """Allows the administrator/security-guard role only."""

    message = "Only a Security Guard can perform this action."

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # Supports Django superusers/staff accounts used in the existing project.
        if user.is_staff or user.is_superuser:
            return True

        profile = getattr(user, "profile", None)

        return (
            profile is not None
            and profile.role == UserProfile.Role.ADMIN
        )