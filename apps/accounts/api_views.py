from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
)
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


def get_user_role(user):
    """Return the user's role based on their Django group."""
    role_groups = [
        "Employee",
        "Security Guard",
        "Parking Administrator",
    ]

    for role in role_groups:
        if user.groups.filter(name=role).exists():
            return role

    return None


@api_view(["POST"])
@authentication_classes([])
@permission_classes([])
def api_login(request):
    username = request.data.get("username", "").strip()
    password = request.data.get("password", "")

    if not username or not password:
        return Response(
            {"error": "Username and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(
        request=request,
        username=username,
        password=password,
    )

    if user is None:
        return Response(
            {"error": "Invalid username or password."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    role = get_user_role(user)

    if role is None:
        return Response(
            {"error": "Your account has no assigned role."},
            status=status.HTTP_403_FORBIDDEN,
        )

    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        "message": "Login successful.",
        "token": token.key,
        "username": user.username,
        "role": role,
    })


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_me(request):
    return Response({
        "username": request.user.username,
        "role": get_user_role(request.user),
    })


@api_view(["POST"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_logout(request):
    Token.objects.filter(user=request.user).delete()

    return Response(
        {"message": "Logout successful."},
        status=status.HTTP_200_OK,
    )


def role_endpoint(request, required_role):
    actual_role = get_user_role(request.user)

    if actual_role != required_role:
        return Response(
            {"error": "You do not have permission to access this resource."},
            status=status.HTTP_403_FORBIDDEN,
        )

    return Response({
        "message": "Access granted.",
        "username": request.user.username,
        "role": actual_role,
    })


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_employee(request):
    return role_endpoint(request, "Employee")


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_guard(request):
    return role_endpoint(request, "Security Guard")


@api_view(["GET"])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def api_admin(request):
    return role_endpoint(request, "Parking Administrator")
