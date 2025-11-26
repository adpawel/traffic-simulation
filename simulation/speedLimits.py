from dataclasses import dataclass

@dataclass
class Position:
    x: int
    lane: int


class SpeedLimit:
    """Reprezentuje ograniczenie prędkości na drodze, takie jak światła, zamknięty pas lub ograniczenie prędkości."""

    def __init__(self, pos_start: Position, pos_end: Position, v_max: int, ticks: int, active:bool = True):
        """
        Argumenty:
            pos_start (Position):
                Początek obszaru ograniczenia prędkości.
                Określa minimalne wartości x oraz lane.
            pos_end (Position):
                Koniec obszaru ograniczenia prędkości.
                Określa maksymalne wartości x oraz lane.
            v_max (int):
                Wartość ograniczenia prędkości.
                Jeśli v_max = 0, obszar działa jak przeszkoda (trzeba się zatrzymać).
            ticks (int):
                Liczba cykli potrzebna do przełączenia stanu ograniczenia (aktywny/nieaktywny).
                Jeśli ticks = 0, ograniczenie jest statyczne.
            active (bool):
                Czy ograniczenie prędkości jest aktywne na początku.

        Przykłady:
        SpeedLimit(Position(10, 0), Position(20, 0), 30, 0)   # Typowe ograniczenie prędkości
        SpeedLimit(Position(10, 0), Position(20, 0), 0, 0)    # Przeszkoda
        SpeedLimit(Position(10, 0), Position(20, 0), 0, 10)   # Światła (cykliczne włączanie/wyłączanie)
        """
        self.speedLimit = v_max
        self.ticks = ticks
        self.active = active
        self.ticks_left = 0

        lane_min = min(pos_start.lane, pos_end.lane)
        lane_max = max(pos_start.lane, pos_end.lane)
        x_min = min(pos_start.x, pos_end.x)
        x_max = max(pos_start.x, pos_end.x)

        self.lanesRange: tuple[int, int] = (lane_min, lane_max)
        self.xRange: tuple[int, int] = (x_min, x_max)
    
    def inRange(self, pos: Position) -> bool:
        """Zwraca True, jeśli pozycja pos znajduje się w obszarze działania tego ograniczenia."""
        lane_min, lane_max = self.lanesRange
        x_min, x_max = self.xRange
        return lane_min <= pos.lane <= lane_max and x_min <= pos.x <= x_max

    def update(self) -> None:
        """Aktualizuje stan ograniczenia (przełączanie active co 'ticks' kroków)."""
        if self.ticks <= 0:
            return  # statyczne ograniczenie

        self.ticks_left += 1
        if self.ticks_left >= self.ticks:
            self.ticks_left = 0
            self.active = not self.active


class SpeedLimits:
    """
    Zarządza listą ograniczeń prędkości.
    Odpowiada za:
      - aktualizację wszystkich ograniczeń,
      - określenie jaki limit obowiązuje w danym miejscu drogi.
    """
    def __init__(self, speedLimits: list[SpeedLimit], maxSpeed: int):
        self.speedLimits = speedLimits
        self.maxSpeed = maxSpeed  # domyślny limit, jeśli żadne lokalne ograniczenie nie pasuje

    def update(self) -> None:
        for speedLimit in self.speedLimits:
            speedLimit.update()

    def getLimit(self, pos: Position) -> int:
        # aktualizuje każde lokalne ograniczenie (np. światła), jeśli nie ma to zwraca domyślne ograniczenie
        for speedLimit in self.speedLimits:
            if speedLimit.active and speedLimit.inRange(pos):
                return speedLimit.speedLimit
        return self.maxSpeed

    def shouldStop(self, pos: Position) -> bool:
        return self.getLimit(pos) == 0
