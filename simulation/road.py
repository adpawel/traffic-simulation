from dataclasses import dataclass
from .speedLimits import SpeedLimits, Position


@dataclass
class Road:
    """
    Model drogi:
      - posiada określoną długość i liczbę pasów,
      - zawiera limity prędkości jako atrybut
      - zawiera metody pomocnicze isInside() i getLimit().
    """
    lanesCount: int
    length: int
    speedLimits: SpeedLimits

    def isInside(self, pos: Position) -> bool:
        """Sprawdza, czy pozycja (x, lane) znajduje się w obrębie drogi."""
        return (
            0 <= pos.x < self.length and
            0 <= pos.lane < self.lanesCount
        )

    def getLimit(self, pos: Position) -> int:
        """
        Zwraca obowiązujący limit prędkości w danej pozycji.
        Deleguje pytanie do obiektu SpeedLimits.
        """
        return self.speedLimits.getLimit(pos)
