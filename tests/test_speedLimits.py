"""Testy dla modułu speedLimits: Position, SpeedLimit, SpeedLimits."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation import Position, SpeedLimit, SpeedLimits


class TestPosition:
    """Testy dla dataclass Position."""

    def test_position_creation(self):
        pos = Position(x=10, lane=2)
        assert pos.x == 10
        assert pos.lane == 2

    def test_position_equality(self):
        pos1 = Position(x=5, lane=1)
        pos2 = Position(x=5, lane=1)
        pos3 = Position(x=5, lane=2)
        assert pos1 == pos2
        assert pos1 != pos3


class TestSpeedLimit:
    """Testy dla klasy SpeedLimit."""

    def test_static_speed_limit_creation(self):
        limit = SpeedLimit(
            pos_start=Position(10, 0),
            pos_end=Position(20, 0),
            v_max=30,
            ticks=0
        )
        assert limit.speedLimit == 30
        assert limit.ticks == 0
        assert limit.active is True
        assert limit.xRange == (10, 20)
        assert limit.lanesRange == (0, 0)

    def test_obstacle_creation(self):
        obstacle = SpeedLimit(
            pos_start=Position(15, 1),
            pos_end=Position(15, 1),
            v_max=0,
            ticks=0
        )
        assert obstacle.speedLimit == 0
        assert obstacle.active is True

    def test_traffic_light_creation(self):
        light = SpeedLimit(
            pos_start=Position(50, 0),
            pos_end=Position(50, 2),
            v_max=0,
            ticks=10,
            active=True
        )
        assert light.speedLimit == 0
        assert light.ticks == 10
        assert light.active is True
        assert light.lanesRange == (0, 2)

    def test_in_range_single_cell(self):
        limit = SpeedLimit(
            pos_start=Position(10, 1),
            pos_end=Position(10, 1),
            v_max=20,
            ticks=0
        )
        assert limit.inRange(Position(10, 1)) is True
        assert limit.inRange(Position(10, 0)) is False
        assert limit.inRange(Position(9, 1)) is False
        assert limit.inRange(Position(11, 1)) is False

    def test_in_range_multiple_lanes(self):
        limit = SpeedLimit(
            pos_start=Position(10, 0),
            pos_end=Position(20, 2),
            v_max=30,
            ticks=0
        )
        assert limit.inRange(Position(15, 0)) is True
        assert limit.inRange(Position(15, 1)) is True
        assert limit.inRange(Position(15, 2)) is True
        assert limit.inRange(Position(15, 3)) is False
        assert limit.inRange(Position(5, 1)) is False
        assert limit.inRange(Position(25, 1)) is False

    def test_in_range_reversed_positions(self):
        # SpeedLimit powinien poprawnie obsłużyć odwróconą kolejność start/end
        limit = SpeedLimit(
            pos_start=Position(20, 2),
            pos_end=Position(10, 0),
            v_max=25,
            ticks=0
        )
        assert limit.xRange == (10, 20)
        assert limit.lanesRange == (0, 2)
        assert limit.inRange(Position(15, 1)) is True


class TestSpeedLimits:
    """Testy dla klasy SpeedLimits zarządzającej listą ograniczeń."""

    def test_no_limits_returns_max_speed(self):
        limits = SpeedLimits(speedLimits=[], maxSpeed=50)
        pos = Position(10, 1)
        assert limits.getLimit(pos) == 50

    def test_single_active_limit(self):
        limit = SpeedLimit(
            pos_start=Position(10, 0),
            pos_end=Position(20, 0),
            v_max=30,
            ticks=0
        )
        limits = SpeedLimits(speedLimits=[limit], maxSpeed=50)
        
        assert limits.getLimit(Position(15, 0)) == 30
        assert limits.getLimit(Position(5, 0)) == 50
        assert limits.getLimit(Position(25, 0)) == 50

    def test_inactive_limit_returns_max_speed(self):
        limit = SpeedLimit(
            pos_start=Position(10, 0),
            pos_end=Position(20, 0),
            v_max=30,
            ticks=0,
            active=False
        )
        limits = SpeedLimits(speedLimits=[limit], maxSpeed=50)
        
        assert limits.getLimit(Position(15, 0)) == 50

    def test_multiple_limits_first_match_wins(self):
        limit1 = SpeedLimit(
            pos_start=Position(10, 0),
            pos_end=Position(30, 0),
            v_max=40,
            ticks=0
        )
        limit2 = SpeedLimit(
            pos_start=Position(15, 0),
            pos_end=Position(25, 0),
            v_max=20,
            ticks=0
        )
        limits = SpeedLimits(speedLimits=[limit1, limit2], maxSpeed=50)
        
        # Pierwsza reguła pasująca wygrywa
        assert limits.getLimit(Position(20, 0)) == 40

    def test_should_stop_with_zero_limit(self):
        obstacle = SpeedLimit(
            pos_start=Position(15, 1),
            pos_end=Position(15, 1),
            v_max=0,
            ticks=0
        )
        limits = SpeedLimits(speedLimits=[obstacle], maxSpeed=50)
        
        assert limits.shouldStop(Position(15, 1)) is True
        assert limits.shouldStop(Position(16, 1)) is False

    def test_should_stop_with_nonzero_limit(self):
        limit = SpeedLimit(
            pos_start=Position(10, 0),
            pos_end=Position(20, 0),
            v_max=30,
            ticks=0
        )
        limits = SpeedLimits(speedLimits=[limit], maxSpeed=50)
        
        assert limits.shouldStop(Position(15, 0)) is False
