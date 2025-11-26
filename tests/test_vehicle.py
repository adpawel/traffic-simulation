"""Testy dla modułu vehicle: LaneDecision, Vehicle."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation import Vehicle, LaneDecision, Position, LocalView


class TestLaneDecision:
    """Testy dla enum LaneDecision."""

    def test_lane_decision_values(self):
        assert LaneDecision.STAY is not None
        assert LaneDecision.UP is not None
        assert LaneDecision.DOWN is not None


class TestVehicle:
    """Testy dla klasy Vehicle."""

    def test_vehicle_creation_default(self):
        pos = Position(x=10, lane=1)
        v = Vehicle(pos=pos)
        assert v.pos == pos
        assert v.velocity == 0
        assert v.v_max == 5
        assert v.lane_change_motivation == 1

    def test_vehicle_creation_custom(self):
        pos = Position(x=5, lane=0)
        v = Vehicle(pos=pos, velocity=3, v_max=7, lane_change_motivation=2)
        assert v.pos == pos
        assert v.velocity == 3
        assert v.v_max == 7
        assert v.lane_change_motivation == 2

    def test_decide_lane_change_stay_when_no_benefit(self):
        """Pojazd pozostaje na pasie, gdy nie ma korzyści z zmiany."""
        v = Vehicle(pos=Position(10, 1), velocity=3)
        view = LocalView(
            pos=Position(10, 1),
            speed_limit=50,
            dist_front_same=10,
            dist_front_up=10,  # tyle samo co na swoim pasie
            dist_front_down=10,
            dist_back_up=5,
            dist_back_down=5,
            can_change_up=True,
            can_change_down=True
        )
        assert v.decideLaneChange(view) == LaneDecision.STAY

    def test_decide_lane_change_up_when_beneficial(self):
        """Pojazd wybiera pas wyżej, gdy tam jest więcej miejsca."""
        v = Vehicle(pos=Position(10, 1), velocity=3, lane_change_motivation=2)
        view = LocalView(
            pos=Position(10, 1),
            speed_limit=50,
            dist_front_same=5,
            dist_front_up=10,  # o 5 więcej -> przekracza motywację (2)
            dist_front_down=6,
            dist_back_up=5,
            dist_back_down=5,
            can_change_up=True,
            can_change_down=True
        )
        assert v.decideLaneChange(view) == LaneDecision.UP

    def test_decide_lane_change_down_when_beneficial(self):
        """Pojazd wybiera pas niżej, gdy tam jest najwięcej miejsca."""
        v = Vehicle(pos=Position(10, 1), velocity=3, lane_change_motivation=1)
        view = LocalView(
            pos=Position(10, 1),
            speed_limit=50,
            dist_front_same=5,
            dist_front_up=7,
            dist_front_down=12,  # najlepiej
            dist_back_up=5,
            dist_back_down=5,
            can_change_up=True,
            can_change_down=True
        )
        assert v.decideLaneChange(view) == LaneDecision.DOWN

    def test_decide_lane_change_insufficient_motivation(self):
        """Pojazd zostaje, gdy zysk nie osiąga progu motywacji."""
        v = Vehicle(pos=Position(10, 1), velocity=3, lane_change_motivation=5)
        view = LocalView(
            pos=Position(10, 1),
            speed_limit=50,
            dist_front_same=10,
            dist_front_up=13,  # tylko +3, potrzeba +5
            dist_front_down=12,
            dist_back_up=5,
            dist_back_down=5,
            can_change_up=True,
            can_change_down=True
        )
        assert v.decideLaneChange(view) == LaneDecision.STAY

    def test_decide_lane_change_cannot_change_up(self):
        """Pojazd nie może jechać w górę, nawet jeśli tam lepiej."""
        v = Vehicle(pos=Position(10, 1), velocity=3)
        view = LocalView(
            pos=Position(10, 1),
            speed_limit=50,
            dist_front_same=5,
            dist_front_up=15,
            dist_front_down=6,
            dist_back_up=1,  # za mało miejsca z tyłu
            dist_back_down=5,
            can_change_up=False,  # blokada
            can_change_down=True
        )
        decision = v.decideLaneChange(view)
        # Jeśli down daje zysk >= motivation, to DOWN, inaczej STAY
        assert decision in [LaneDecision.STAY, LaneDecision.DOWN]

    def test_decide_lane_change_cannot_change_down(self):
        """Pojazd nie może jechać w dół."""
        v = Vehicle(pos=Position(10, 0), velocity=3)  # lane=0, nie ma niżej
        view = LocalView(
            pos=Position(10, 0),
            speed_limit=50,
            dist_front_same=5,
            dist_front_up=None,
            dist_front_down=15,
            dist_back_up=None,
            dist_back_down=3,
            can_change_up=False,
            can_change_down=False  # blokada
        )
        assert v.decideLaneChange(view) == LaneDecision.STAY

    def test_decide_speed_acceleration(self):
        """Pojazd przyspiesza o 1, jeśli ma miejsce."""
        v = Vehicle(pos=Position(10, 1), velocity=2, v_max=5)
        view = LocalView(
            pos=Position(10, 1),
            speed_limit=50,
            dist_front_same=20,  # dużo miejsca
            dist_front_up=None,
            dist_front_down=None,
            dist_back_up=None,
            dist_back_down=None,
            can_change_up=False,
            can_change_down=False
        )
        new_speed = v.decideSpeed(view)
        assert new_speed == 3  # velocity 2 -> 3

    def test_decide_speed_max_velocity(self):
        """Pojazd nie przekracza v_max."""
        v = Vehicle(pos=Position(10, 1), velocity=5, v_max=5)
        view = LocalView(
            pos=Position(10, 1),
            speed_limit=50,
            dist_front_same=20,
            dist_front_up=None,
            dist_front_down=None,
            dist_back_up=None,
            dist_back_down=None,
            can_change_up=False,
            can_change_down=False
        )
        new_speed = v.decideSpeed(view)
        assert new_speed == 5

    def test_decide_speed_limited_by_speed_limit(self):
        """Pojazd respektuje speed_limit z drogi."""
        v = Vehicle(pos=Position(10, 1), velocity=2, v_max=7)
        view = LocalView(
            pos=Position(10, 1),
            speed_limit=4,  # ograniczenie
            dist_front_same=20,
            dist_front_up=None,
            dist_front_down=None,
            dist_back_up=None,
            dist_back_down=None,
            can_change_up=False,
            can_change_down=False
        )
        new_speed = v.decideSpeed(view)
        assert new_speed == 3  # min(2+1, 7, 4, 20) = 3

    def test_decide_speed_limited_by_gap(self):
        """Pojazd hamuje, aby nie wjechać w auto z przodu."""
        v = Vehicle(pos=Position(10, 1), velocity=4, v_max=5)
        view = LocalView(
            pos=Position(10, 1),
            speed_limit=50,
            dist_front_same=2,  # tylko 2 wolne komórki
            dist_front_up=None,
            dist_front_down=None,
            dist_back_up=None,
            dist_back_down=None,
            can_change_up=False,
            can_change_down=False
        )
        new_speed = v.decideSpeed(view)
        assert new_speed == 2  # min(4+1, 5, 50, 2) = 2

    def test_decide_speed_zero_gap_must_stop(self):
        """Pojazd musi się zatrzymać, gdy auto jest tuż przed nim."""
        v = Vehicle(pos=Position(10, 1), velocity=3, v_max=5)
        view = LocalView(
            pos=Position(10, 1),
            speed_limit=50,
            dist_front_same=0,  # auto bezpośrednio przed nami
            dist_front_up=None,
            dist_front_down=None,
            dist_back_up=None,
            dist_back_down=None,
            can_change_up=False,
            can_change_down=False
        )
        new_speed = v.decideSpeed(view)
        assert new_speed == 0
