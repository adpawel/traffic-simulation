"""Testy dla modułu localview: LocalView."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation import LocalView, Position


class TestLocalView:
    """Testy dla dataclass LocalView."""

    def test_localview_creation_basic(self):
        view = LocalView(
            pos=Position(x=10, lane=1),
            speed_limit=50,
            dist_front_same=15,
            dist_front_up=10,
            dist_front_down=20,
            dist_back_up=5,
            dist_back_down=7,
            can_change_up=True,
            can_change_down=True
        )
        assert view.pos == Position(x=10, lane=1)
        assert view.speed_limit == 50
        assert view.dist_front_same == 15
        assert view.dist_front_up == 10
        assert view.dist_front_down == 20
        assert view.dist_back_up == 5
        assert view.dist_back_down == 7
        assert view.can_change_up is True
        assert view.can_change_down is True

    def test_localview_edge_lane_no_up(self):
        """Widok dla pojazdu na najwyższym pasie (brak pasa wyżej)."""
        view = LocalView(
            pos=Position(x=5, lane=0),
            speed_limit=60,
            dist_front_same=12,
            dist_front_up=None,
            dist_front_down=15,
            dist_back_up=None,
            dist_back_down=6,
            can_change_up=False,
            can_change_down=True
        )
        assert view.dist_front_up is None
        assert view.dist_back_up is None
        assert view.can_change_up is False

    def test_localview_edge_lane_no_down(self):
        """Widok dla pojazdu na najniższym pasie (brak pasa niżej)."""
        view = LocalView(
            pos=Position(x=20, lane=2),
            speed_limit=70,
            dist_front_same=8,
            dist_front_up=10,
            dist_front_down=None,
            dist_back_up=4,
            dist_back_down=None,
            can_change_up=True,
            can_change_down=False
        )
        assert view.dist_front_down is None
        assert view.dist_back_down is None
        assert view.can_change_down is False

    def test_localview_single_lane_road(self):
        """Widok dla pojazdu na drodze jednopasowej."""
        view = LocalView(
            pos=Position(x=30, lane=0),
            speed_limit=50,
            dist_front_same=25,
            dist_front_up=None,
            dist_front_down=None,
            dist_back_up=None,
            dist_back_down=None,
            can_change_up=False,
            can_change_down=False
        )
        assert view.dist_front_up is None
        assert view.dist_front_down is None
        assert view.can_change_up is False
        assert view.can_change_down is False

    def test_localview_blocked_lane_changes(self):
        """Sąsiednie pasy istnieją, ale zmiana zablokowana przez ruch."""
        view = LocalView(
            pos=Position(x=15, lane=1),
            speed_limit=55,
            dist_front_same=10,
            dist_front_up=12,
            dist_front_down=8,
            dist_back_up=1,  # za mało z tyłu
            dist_back_down=2,  # za mało z tyłu
            can_change_up=False,  # zablokowane
            can_change_down=False  # zablokowane
        )
        assert view.can_change_up is False
        assert view.can_change_down is False
