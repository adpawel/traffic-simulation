from dataclasses import dataclass
from enum import Enum, auto

from .speedLimits import Position
from .localview import LocalView


class LaneDecision(Enum):
    """Możliwa decyzja pojazdu dotycząca pasa ruchu."""
    STAY = auto()   # zostań na swoim pasie
    UP = auto()     # lane - 1
    DOWN = auto()   # lane + 1


@dataclass
class Vehicle:
    """
    Reprezentuje pojedynczy pojazd w modelu NaSch.

    Pojazd:
      - NIE zna drogi ani innych pojazdów,
      - dostaje tylko LocalView i na tej podstawie:
          * decyduje o zmianie pasa,
          * decyduje o nowej prędkości.
    """
    pos: Position
    velocity: int = 0
    v_max: int = 5
    lane_change_motivation: int = 1  # minimalny zysk (w komórkach), żeby opłacało się zmienić pas

    def decideLaneChange(self, view: LocalView) -> LaneDecision:
        """
        Zwraca intencję zmiany pasa:
          - STAY: zostań na pasie,
          - UP:   spróbuj przejść na lane-1,
          - DOWN: spróbuj przejść na lane+1.

        Tu sprawdzamy tylko, czy zmiana PASA SIĘ OPŁACA (motywacja),
        a nie czy jest BEZPIECZNA – bezpieczeństwo i konflikty ogarnia Simulation.
        """

        best_decision = LaneDecision.STAY
        best_gain = 0  # ile więcej wolnych komórek z przodu daje inny pas

        # kandydat: pas wyżej
        if view.can_change_up and view.dist_front_up is not None:
            gain_up = view.dist_front_up - view.dist_front_same
            if gain_up >= self.lane_change_motivation and gain_up > best_gain:
                best_gain = gain_up
                best_decision = LaneDecision.UP

        # kandydat: pas niżej
        if view.can_change_down and view.dist_front_down is not None:
            gain_down = view.dist_front_down - view.dist_front_same
            if gain_down >= self.lane_change_motivation and gain_down > best_gain:
                best_gain = gain_down
                best_decision = LaneDecision.DOWN

        return best_decision

    def decideSpeed(self, view: LocalView) -> int:
        """
        Reguły NaSch (bez losowego hamowania – to zrobi Simulation):
          1. Przyspiesz o 1 do v_max.
          2. Przytnij prędkość limitem prędkości z drogi.
          3. Przytnij prędkość dystansem do auta z przodu (nie skaczemy w niego).
        """

        # 1. przyspieszanie
        new_v = min(self.velocity + 1, self.v_max)

        # 2. ograniczenie limitem prędkości z drogi
        new_v = min(new_v, view.speed_limit)

        # 3. ograniczenie dystansem do auta przed sobą
        new_v = min(new_v, view.dist_front_same)

        return new_v
