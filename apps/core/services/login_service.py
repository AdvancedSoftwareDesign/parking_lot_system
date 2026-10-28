from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token

from apps.core.models import UserProfile


class LoginService:
    """Authenticates users and guarantees that each has a role profile."""

    def login(self, username, password):
        user = authenticate(username=username, password=password)
        if user is None:
            return None

        administrator = user.is_staff or user.is_superuser
        default_role = (
            UserProfile.Role.ADMIN
            if administrator
            else UserProfile.Role.EMPLOYEE
        )
        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={"role": default_role},
        )
        if administrator and profile.role != UserProfile.Role.ADMIN:
            profile.role = UserProfile.Role.ADMIN
            profile.save(update_fields=["role"])

        token, _ = Token.objects.get_or_create(user=user)
        return {
            "token": token.key,
            "user_id": user.id,
            "username": user.username,
            "role": profile.role,
        }
