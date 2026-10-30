from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.core.models import ParkingLot
from apps.core.services.parking_lot_service import ParkingLotService
from apps.core.models import ParkingSession, Vehicle


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

    def test_capacity_cannot_be_lower_than_occupied_spaces(self):
        parking_lot = ParkingLot.objects.create(capacity=3)

        for plate in ["231-D-111", "231-D-222"]:
            vehicle = Vehicle.objects.create(
                registration_number=plate
            )
            ParkingSession.objects.create(
                vehicle=vehicle,
                parking_lot=parking_lot
            )

        with self.assertRaises(ValidationError):
            self.service.set_capacity(
                parking_lot_id=parking_lot.pk,
                new_capacity=1
            )

        parking_lot.refresh_from_db()
        self.assertEqual(parking_lot.capacity, 3)

    def test_capacity_can_equal_occupied_spaces(self):
        parking_lot = ParkingLot.objects.create(capacity=3)

        vehicle = Vehicle.objects.create(
            registration_number="231-D-111"
        )
        ParkingSession.objects.create(
            vehicle=vehicle,
            parking_lot=parking_lot
        )

        self.service.set_capacity(
            parking_lot_id=parking_lot.pk,
            new_capacity=1
        )

        parking_lot.refresh_from_db()
        self.assertEqual(parking_lot.capacity, 1)
        self.assertEqual(parking_lot.get_available_spaces(), 0)

    def test_finished_sessions_do_not_prevent_capacity_reduction(self):
        parking_lot = ParkingLot.objects.create(capacity=3)

        for plate in ["231-D-111", "231-D-222"]:
            vehicle = Vehicle.objects.create(
                registration_number=plate
            )
            session = ParkingSession.objects.create(
                vehicle=vehicle,
                parking_lot=parking_lot
            )
            session.close()
            session.save(update_fields=["exit_time"])

        self.service.set_capacity(
            parking_lot_id=parking_lot.pk,
            new_capacity=1
        )

        parking_lot.refresh_from_db()
        self.assertEqual(parking_lot.capacity, 1)