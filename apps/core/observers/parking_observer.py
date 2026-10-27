from abc import ABC, abstractmethod


class ParkingObserver(ABC):

    @abstractmethod
    def update(self, parking_lot, event):
        pass