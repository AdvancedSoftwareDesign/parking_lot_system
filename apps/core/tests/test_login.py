
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.core.models import UserProfile


class LoginTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username="employee1",
            password="TestPass123!"
        )
        UserProfile.objects.create(
            user=self.user,
            role=UserProfile.Role.EMPLOYEE
        )

    def test_login_returns_token_and_employee_role(self):
        response = self.client.post(
            "/api/login/",
            {
                "username": "employee1",
                "password": "TestPass123!"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["username"], "employee1")
        self.assertEqual(response.data["role"], "employee")

    def test_login_rejects_invalid_password(self):
        response = self.client.post(
            "/api/login/",
            {
                "username": "employee1",
                "password": "WrongPassword123!"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 401)

    def test_login_rejects_inactive_user(self):
        self.user.is_active = False
        self.user.save()

        response = self.client.post(
            "/api/login/",
            {
                "username": "employee1",
                "password": "TestPass123!"
            },
            format="json"
        )

        self.assertEqual(response.status_code, 401)
