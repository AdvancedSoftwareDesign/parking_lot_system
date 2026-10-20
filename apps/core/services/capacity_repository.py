from apps.core.models import ParkingCapacity
from apps.core.ports import CapacityRepositoryPort

class DjangoCapacityRepository(CapacityRepositoryPort):
    def get_current_capacity(self) -> int | None:
        capacity = ParkingCapacity.objects.order_by("id").first()

        if capacity is None:
            return None

        return capacity.total_capacity

    def save_capacity(self, total_capacity: int) -> None:
        capacity = ParkingCapacity.objects.order_by("id").first()

        if capacity is None:
            ParkingCapacity.objects.create(total_capacity=total_capacity)
            return

        capacity.total_capacity = total_capacity
        capacity.save(update_fields=["total_capacity", "updated_at"])
