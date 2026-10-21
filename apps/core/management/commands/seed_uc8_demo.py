from getpass import getpass

from django.contrib.auth.models import Group, User
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.core.models import ParkingCapacity, ParkingRecord, Vehicle


class Command(BaseCommand):
    help = 'Create local UC8 demo accounts and vehicles without replacing existing data.'

    @transaction.atomic
    def handle(self, *args, **options):
        names = ['uc8_admin', 'uc8_employee', 'uc8_guard']
        numbers = ['12D12345', '22D23456', '23D34567']
        if User.objects.filter(username__in=names).exists() or Vehicle.objects.filter(registration_number__in=numbers).exists():
            raise CommandError('Demo accounts or vehicles already exist. No changes made; use existing accounts or a fresh local database.')
        password = getpass('Local demo password (at least 8 characters): ')
        if len(password) < 8:
            raise CommandError('Use at least 8 characters.')
        users = []
        for name, role in zip(names, ['Parking Administrator', 'Employee', 'Security Guard']):
            user = User.objects.create_user(username=name, password=password)
            group, _ = Group.objects.get_or_create(name=role)
            user.groups.add(group)
            users.append(user)
        vehicles = [Vehicle.objects.create(owner=users[1], registration_number=n) for n in numbers]
        ParkingRecord.objects.create(vehicle=vehicles[0], exit_time=timezone.now())
        ParkingRecord.objects.create(vehicle=vehicles[1])
        if not ParkingCapacity.objects.exists():
            ParkingCapacity.objects.create(total_capacity=10)
        self.stdout.write(self.style.SUCCESS('Local UC8 demo data created.'))
        self.stdout.write(f'Accounts: {", ".join(names)}; employee ID: {users[1].id}')
        for vehicle in vehicles:
            self.stdout.write(f'Vehicle {vehicle.id}: {vehicle.registration_number}')
        self.stdout.write('12D12345: exited history; 22D23456: currently parked; 23D34567: cancellation example.')
