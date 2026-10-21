
from apps.core.models import ParkingRecord


class ParkingRecordOccupancy:
    """Calculate occupied spaces from active parking records."""

    def get_occupied_spaces(self) -> int:
        return ParkingRecord.objects.filter(exit_time__isnull=True).count()
