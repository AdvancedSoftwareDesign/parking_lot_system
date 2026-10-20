from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated


class HomepageView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        return Response({
            "message": "Welcome.",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": "admin" if user.is_staff else "user"
            }
        })
