from django.test import TestCase

# Create your tests here.
from django.test import TestCase
from rest_framework.test import APIClient


class HealthCheckTests(TestCase):
    def test_initial_check_returns_ok(self):
        client = APIClient()
        response = client.get("/api/check/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "ok")