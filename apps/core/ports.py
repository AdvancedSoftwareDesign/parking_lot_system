from typing import Protocol

class CapacityRepositoryPort(Protocol):
    def get_current_capacity(self) -> int | None:
        ...

    def save_capacity(self, total_capacity: int) -> None:
        ...

class OccupancyPort(Protocol):
    def get_occupied_spaces(self) -> int:
        ...
