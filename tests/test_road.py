"""Testy dla modułu road: Road."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation import Position, SpeedLimit, SpeedLimits, Road


class TestRoad:
    """Testy dla klasy Road."""

    def test_road_creation_basic(self):
        """Test podstawowego tworzenia drogi."""
        speed_limits = SpeedLimits(speedLimits=[], maxSpeed=50)
        road = Road(lanesCount=3, length=100, speedLimits=speed_limits)
        
        assert road.lanesCount == 3
        assert road.length == 100
        assert road.speedLimits == speed_limits

    def test_is_inside_valid_positions(self):
        """Sprawdzenie czy poprawne pozycje są rozpoznawane jako wewnątrz."""
        speed_limits = SpeedLimits(speedLimits=[], maxSpeed=50)
        road = Road(lanesCount=2, length=50, speedLimits=speed_limits)
        
        assert road.isInside(Position(x=0, lane=0)) is True
        assert road.isInside(Position(x=0, lane=1)) is True
        assert road.isInside(Position(x=25, lane=0)) is True
        assert road.isInside(Position(x=49, lane=1)) is True

    def test_is_inside_invalid_positions(self):
        """Sprawdzenie czy niepoprawne pozycje są rozpoznawane jako na zewnątrz."""
        speed_limits = SpeedLimits(speedLimits=[], maxSpeed=50)
        road = Road(lanesCount=2, length=50, speedLimits=speed_limits)
        
        # lane poza zakresem
        assert road.isInside(Position(x=25, lane=-1)) is False
        assert road.isInside(Position(x=25, lane=2)) is False
        assert road.isInside(Position(x=25, lane=10)) is False
        
        # x poza zakresem
        assert road.isInside(Position(x=-1, lane=0)) is False
        assert road.isInside(Position(x=50, lane=0)) is False
        assert road.isInside(Position(x=100, lane=1)) is False

    def test_get_limit_no_restrictions(self):
        """Bez lokalnych ograniczeń zwraca maxSpeed."""
        speed_limits = SpeedLimits(speedLimits=[], maxSpeed=60)
        road = Road(lanesCount=1, length=100, speedLimits=speed_limits)
        
        assert road.getLimit(Position(x=10, lane=0)) == 60
        assert road.getLimit(Position(x=90, lane=0)) == 60

    def test_get_limit_with_local_restriction(self):
        """Z lokalnym ograniczeniem zwraca limit w danej strefie."""
        limit = SpeedLimit(
            pos_start=Position(20, 0),
            pos_end=Position(40, 0),
            v_max=30,
            ticks=0
        )
        speed_limits = SpeedLimits(speedLimits=[limit], maxSpeed=60)
        road = Road(lanesCount=1, length=100, speedLimits=speed_limits)
        
        assert road.getLimit(Position(x=10, lane=0)) == 60
        assert road.getLimit(Position(x=30, lane=0)) == 30
        assert road.getLimit(Position(x=50, lane=0)) == 60

    def test_get_limit_multiple_lanes(self):
        """Różne ograniczenia na różnych pasach."""
        limit_lane0 = SpeedLimit(
            pos_start=Position(10, 0),
            pos_end=Position(30, 0),
            v_max=40,
            ticks=0
        )
        limit_lane1 = SpeedLimit(
            pos_start=Position(10, 1),
            pos_end=Position(30, 1),
            v_max=50,
            ticks=0
        )
        speed_limits = SpeedLimits(
            speedLimits=[limit_lane0, limit_lane1],
            maxSpeed=60
        )
        road = Road(lanesCount=2, length=100, speedLimits=speed_limits)
        
        assert road.getLimit(Position(x=20, lane=0)) == 40
        assert road.getLimit(Position(x=20, lane=1)) == 50
        assert road.getLimit(Position(x=40, lane=0)) == 60
        assert road.getLimit(Position(x=40, lane=1)) == 60

    def test_get_limit_with_obstacle(self):
        """Ograniczenie v_max=0 działa jak przeszkoda."""
        obstacle = SpeedLimit(
            pos_start=Position(25, 0),
            pos_end=Position(25, 0),
            v_max=0,
            ticks=0
        )
        speed_limits = SpeedLimits(speedLimits=[obstacle], maxSpeed=50)
        road = Road(lanesCount=1, length=100, speedLimits=speed_limits)
        
        assert road.getLimit(Position(x=25, lane=0)) == 0
        assert road.getLimit(Position(x=24, lane=0)) == 50
        assert road.getLimit(Position(x=26, lane=0)) == 50
