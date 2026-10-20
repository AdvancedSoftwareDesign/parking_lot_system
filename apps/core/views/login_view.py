from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from apps.core.services.login_service import LoginService


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not isinstance(username, str) or not username.strip():
            return Response(
                {"error": "Please provide your username."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(password, str) or not password:
            return Response(
                {"error": "Please provide your password."},
                status=status.HTTP_400_BAD_REQUEST
            )

        login_service = LoginService()
        result = login_service.login(username, password)

        if result is None:
            return Response(
                {"error": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        return Response(
            result,
            status=status.HTTP_200_OK
        )
