from apps.core.ports import CapacityRepositoryPort, OccupancyPort

class CapacityNotConfiguredError(Exception):
    pass

class OccupancyUnavailableError(Exception):
    pass

class InvalidCapacityError(ValueError):
    pass

class CapacityService:
    def __init__(
        self,
        capacity_repository: CapacityRepositoryPort,
        occupancy_port: OccupancyPort,
    ):
        self.capacity_repository = capacity_repository
        self.occupancy_port = occupancy_port

    def get_capacity_status(self) -> dict:
        total_capacity = self.capacity_repository.get_current_capacity()

        if total_capacity is None:
            raise CapacityNotConfiguredError(
                "Parking capacity has not been configured."
            )

        occupied_spaces = self.occupancy_port.get_occupied_spaces()

        return {
            "total_capacity": total_capacity,
            "occupied_spaces": occupied_spaces,
            "available_spaces": total_capacity - occupied_spaces,
        }

    def set_capacity(self, new_capacity: int) -> dict:
        if isinstance(new_capacity, bool) or not isinstance(new_capacity, int):
            raise InvalidCapacityError(
                "Capacity must be a positive whole number."
            )

        if new_capacity <= 0:
            raise InvalidCapacityError(
                "Capacity must be a positive whole number."
            )

        occupied_spaces = self.occupancy_port.get_occupied_spaces()

        if new_capacity < occupied_spaces:
            raise InvalidCapacityError(
                "Capacity cannot be lower than occupied spaces."
            )

        self.capacity_repository.save_capacity(new_capacity)

        return {
            "total_capacity": new_capacity,
            "occupied_spaces": occupied_spaces,
            "available_spaces": new_capacity - occupied_spaces,
        }
