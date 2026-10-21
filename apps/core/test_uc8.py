from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.test import TestCase
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from apps.core.models import ParkingCapacity, ParkingRecord, Vehicle
from apps.core.services.vehicle_deactivation_service import VehicleDeactivationService


class UC8Tests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_user(username="uc8_admin", password="test-only-password")
        cls.employee = User.objects.create_user(username="uc8_employee")
        cls.guard = User.objects.create_user(username="uc8_guard")
        for user, role in [(cls.admin, "Parking Administrator"), (cls.employee, "Employee"), (cls.guard, "Security Guard")]:
            group, _ = Group.objects.get_or_create(name=role)
            user.groups.add(group)
        cls.vehicle = Vehicle.objects.create(owner=cls.employee, registration_number="12D12345")
        cls.history = ParkingRecord.objects.create(vehicle=cls.vehicle, exit_time=timezone.now())
        ParkingCapacity.objects.create(total_capacity=10)

    def setUp(self):
        self.client = APIClient()
        self.authenticate(self.admin)
        self.url = f"/api/vehicles/{self.vehicle.id}/deactivate/"

    def authenticate(self, user):
        token, _ = Token.objects.get_or_create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def deactivate(self, confirmed=True):
        return self.client.post(self.url, {"confirmed": confirmed}, format="json")

    def assert_active(self):
        self.vehicle.refresh_from_db()
        self.assertTrue(self.vehicle.registration_active)

    def test_search_number_case_and_whitespace(self):
        result = self.client.get('/api/vehicles/search/', {'registration_number': ' 12d '})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['count'], 1)
        self.assertEqual(result.data['results'][0]['employee_id'], self.employee.id)
        self.assertFalse(result.data['results'][0]['currently_parked'])

    def test_employee_list(self):
        Vehicle.objects.create(owner=self.employee, registration_number='22D12345')
        result = self.client.get('/api/vehicles/search/', {'employee_id': self.employee.id})
        self.assertEqual(result.data['count'], 2)

    def test_both_filters_intersect(self):
        result = self.client.get('/api/vehicles/search/', {'employee_id': self.guard.id, 'registration_number': '12D'})
        self.assertEqual(result.data['count'], 0)

    def test_no_results(self):
        result = self.client.get('/api/vehicles/search/', {'registration_number': 'UNKNOWN'})
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data['results'], [])

    def test_invalid_search(self):
        for query in [{}, {'employee_id':'abc'}, {'employee_id':'0'}, {'employee_id':'-1'}, {'employee_id':'9'*30}]:
            with self.subTest(query=query):
                self.assertEqual(self.client.get('/api/vehicles/search/', query).status_code, 400)

    def test_anonymous(self):
        self.client.credentials()
        self.assertEqual(self.deactivate().status_code, 401)
        self.assertEqual(self.client.get('/api/vehicles/search/', {'registration_number':'12D'}).status_code, 401)
        self.assert_active()

    def test_other_roles(self):
        for user in [self.employee, self.guard]:
            self.authenticate(user)
            self.assertEqual(self.deactivate().status_code, 403)
            self.assertEqual(self.client.get('/api/vehicles/search/', {'registration_number':'12D'}).status_code, 403)
        self.assert_active()

    def test_staff_flag_alone_is_not_parking_role(self):
        self.employee.is_staff = True
        self.employee.save()
        self.authenticate(self.employee)
        self.assertEqual(self.deactivate().status_code, 403)

    def test_inactive_account(self):
        self.admin.is_active = False
        self.admin.save()
        self.assertEqual(self.deactivate().status_code, 401)
        self.assert_active()

    def test_service_checks_role(self):
        with self.assertRaises(PermissionDenied):
            VehicleDeactivationService().deactivate_vehicle(self.employee, self.vehicle.id, True)

    def test_deactivate_preserves_vehicle_and_history(self):
        before = list(ParkingRecord.objects.values())
        result = self.deactivate()
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.data['changed'])
        self.vehicle.refresh_from_db()
        self.assertFalse(self.vehicle.registration_active)
        self.assertEqual(Vehicle.objects.count(), 1)
        self.assertEqual(list(ParkingRecord.objects.values()), before)

    def test_cancel_leaves_everything_unchanged(self):
        before = list(ParkingRecord.objects.values())
        result = self.deactivate(False)
        self.assertEqual(result.status_code, 200)
        self.assertFalse(result.data['changed'])
        self.assert_active()
        self.assertEqual(list(ParkingRecord.objects.values()), before)

    def test_explicit_boolean_required(self):
        for value in [None, 'true', 'false', 1, 0, [], {}]:
            with self.subTest(value=value):
                self.assertEqual(self.deactivate(value).status_code, 400)
                self.assert_active()
        self.assertEqual(self.client.post(self.url, {}, format='json').status_code, 400)

    def test_json_array_rejected(self):
        self.assertEqual(self.client.post(self.url, [], format='json').status_code, 400)

    def test_currently_parked_rejected(self):
        record = ParkingRecord.objects.create(vehicle=self.vehicle)
        before = list(ParkingRecord.objects.values())
        self.assertEqual(self.deactivate().status_code, 409)
        self.assert_active()
        record.refresh_from_db()
        self.assertIsNone(record.exit_time)
        self.assertEqual(list(ParkingRecord.objects.values()), before)

    def test_search_then_entry_then_confirm_is_rechecked(self):
        self.client.get('/api/vehicles/search/', {'registration_number':'12D'})
        self.authenticate(self.guard)
        response = self.client.post('/api/entry/', {'registration_number':'12D12345'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.authenticate(self.admin)
        self.assertEqual(self.deactivate().status_code, 409)
        self.assert_active()

    def test_missing_vehicle(self):
        result = self.client.post('/api/vehicles/999999/deactivate/', {'confirmed':True}, format='json')
        self.assertEqual(result.status_code, 404)

    def test_repeat_confirmation(self):
        self.assertEqual(self.deactivate().status_code, 200)
        self.assertEqual(self.deactivate().status_code, 409)

    def test_get_cannot_deactivate(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
        self.assert_active()

    def test_inactive_vehicle_visible_in_search(self):
        self.deactivate()
        result = self.client.get('/api/vehicles/search/', {'registration_number':'12D'})
        self.assertFalse(result.data['results'][0]['registration_active'])

    def test_future_entry_refused(self):
        self.deactivate()
        self.authenticate(self.guard)
        before = ParkingRecord.objects.count()
        result = self.client.post('/api/entry/', {'registration_number':'12D12345'}, format='json')
        self.assertEqual(result.status_code, 400)
        self.assertEqual(result.data['error'], 'The vehicle registration is inactive.')
        self.assertEqual(ParkingRecord.objects.count(), before)

    def test_exit_then_deactivate(self):
        ParkingRecord.objects.create(vehicle=self.vehicle)
        self.authenticate(self.guard)
        self.assertEqual(self.client.post('/api/exit/', {'registration_number':'12D12345'}, format='json').status_code, 200)
        self.authenticate(self.admin)
        self.assertEqual(self.deactivate().status_code, 200)
        self.assertEqual(ParkingRecord.objects.count(), 2)

    def test_pagination(self):
        Vehicle.objects.bulk_create([Vehicle(owner=self.employee, registration_number=f'CAR{i}') for i in range(25)])
        result = self.client.get('/api/vehicles/search/', {'employee_id': self.employee.id})
        self.assertEqual(len(result.data['results']), 20)
        self.assertIsNotNone(result.data['next'])

    def test_real_login_token(self):
        self.client.credentials()
        response = self.client.post('/api/accounts/login/', {'username':'uc8_admin', 'password':'test-only-password'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.client.credentials(HTTP_AUTHORIZATION='Token '+response.data['token'])
        self.assertEqual(self.deactivate().status_code, 200)
