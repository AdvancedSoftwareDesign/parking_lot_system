from django.contrib.auth.models import User, Group
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase


class AccountAPITests(APITestCase):
    def setUp(self):
        # Create the roles used by the API.
        self.employee_group, _ = Group.objects.get_or_create(
            name="Employee"
        )
        self.guard_group, _ = Group.objects.get_or_create(
            name="Security Guard"
        )
        self.admin_group, _ = Group.objects.get_or_create(
            name="Parking Administrator"
        )

        # Create an employee test account.
        self.employee = User.objects.create_user(
            username="employee_test",
            password="TestPassword123!",
        )
        self.employee.groups.add(self.employee_group)

        # Create a security guard test account.
        self.guard = User.objects.create_user(
            username="guard_test",
            password="TestPassword123!",
        )
        self.guard.groups.add(self.guard_group)

        # Create an account without a role.
        self.no_role_user = User.objects.create_user(
            username="no_role_test",
            password="TestPassword123!",
        )

        self.login_url = reverse("api_login")
        self.me_url = reverse("api_me")
        self.logout_url = reverse("api_logout")
        self.employee_url = reverse("api_employee")
        self.guard_url = reverse("api_guard")

    def test_login_success(self):
        response = self.client.post(
            self.login_url,
            {
                "username": "employee_test",
                "password": "TestPassword123!",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "employee_test")
        self.assertEqual(response.data["role"], "Employee")
        self.assertIn("token", response.data)

    def test_login_with_wrong_password(self):
        response = self.client.post(
            self.login_url,
            {
                "username": "employee_test",
                "password": "WrongPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_login_without_role_is_rejected(self):
        response = self.client.post(
            self.login_url,
            {
                "username": "no_role_test",
                "password": "TestPassword123!",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_authenticated_user_can_access_me(self):
        token = Token.objects.create(user=self.employee)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

        response = self.client.get(self.me_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "employee_test")
        self.assertEqual(response.data["role"], "Employee")

    def test_unauthenticated_user_cannot_access_me(self):
        response = self.client.get(self.me_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )

    def test_employee_can_access_employee_endpoint(self):
        token = Token.objects.create(user=self.employee)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

        response = self.client.get(self.employee_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_employee_cannot_access_guard_endpoint(self):
        token = Token.objects.create(user=self.employee)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

        response = self.client.get(self.guard_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_logout_invalidates_token(self):
        token = Token.objects.create(user=self.employee)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

        response = self.client.post(self.logout_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            Token.objects.filter(user=self.employee).exists()
        )

        response = self.client.get(self.me_url)

        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
        )
