from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.core.models import ParkingLot
from apps.core.services.parking_lot_service import ParkingLotService


class ParkingLotServiceTests(TestCase):

    def setUp(self):
        self.service = ParkingLotService()

    def test_create_parking_lot_with_valid_capacity(self):
        parking_lot = self.service.create_parking_lot(capacity=10)

        self.assertIsNotNone(parking_lot.pk)
        self.assertEqual(parking_lot.capacity, 10)
        self.assertTrue(
            ParkingLot.objects.filter(pk=parking_lot.pk).exists()
        )

    def test_create_parking_lot_with_invalid_capacity(self):
        with self.assertRaises(ValidationError):
            self.service.create_parking_lot(capacity=0)

        self.assertEqual(ParkingLot.objects.count(), 0)

    def test_set_capacity_for_existing_parking_lot(self):
        parking_lot = ParkingLot.objects.create(capacity=10)

        result = self.service.set_capacity(
            parking_lot_id=parking_lot.pk,
            new_capacity=20
        )

        parking_lot.refresh_from_db()

        self.assertEqual(result.capacity, 20)
        self.assertEqual(parking_lot.capacity, 20)

    def test_set_capacity_for_nonexistent_parking_lot(self):
        with self.assertRaises(ParkingLot.DoesNotExist):
            self.service.set_capacity(
                parking_lot_id=999,
                new_capacity=20
            )