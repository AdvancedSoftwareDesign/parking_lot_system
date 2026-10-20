
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token


class LoginService:

    def login(self, username, password):
        user = authenticate(username=username, password=password)

        if user is None:
            return None

        token, created = Token.objects.get_or_create(user=user)

        return {
            "token": token.key,
            "user_id": user.id,
            "username": user.username
        }
