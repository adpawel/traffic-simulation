"""Testy dla świateł i przeszkód."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation import Position, SpeedLimit, SpeedLimits, Simulation


class TestTrafficLights:
    """Testy dla sygnalizacji świetlnej."""

    def test_traffic_light_creation(self):
        """Sprawdź czy światło jest tworzone poprawnie."""
        light = SpeedLimit(
            pos_start=Position(x=10, lane=0),
            pos_end=Position(x=12, lane=1),
            v_max=0,
            ticks=10,
            active=True
        )
        
        assert light.speedLimit == 0
        assert light.ticks == 10
        assert light.active is True
        assert light.inRange(Position(x=11, lane=0))
        assert light.inRange(Position(x=10, lane=1))
        assert not light.inRange(Position(x=13, lane=0))

    def test_traffic_light_update_toggle(self):
        """Sprawdź czy światło zmienia stan co 'ticks' kroków."""
        light = SpeedLimit(
            pos_start=Position(x=10, lane=0),
            pos_end=Position(x=10, lane=0),
            v_max=0,
            ticks=3,
            active=True
        )
        
        assert light.active is True
        
        # Kroki 1-2: nadal aktywne
        light.update()
        assert light.active is True
        light.update()
        assert light.active is True
        
        # Krok 3: przełączenie na nieaktywne
        light.update()
        assert light.active is False
        
        # Kolejne 3 kroki: przełączenie z powrotem
        light.update()
        light.update()
        light.update()
        assert light.active is True

    def test_obstacle_does_not_toggle(self):
        """Przeszkoda (ticks=0) nie powinna zmieniać stanu."""
        obstacle = SpeedLimit(
            pos_start=Position(x=10, lane=0),
            pos_end=Position(x=12, lane=0),
            v_max=0,
            ticks=0,
            active=True
        )
        
        assert obstacle.active is True
        
        # Wiele aktualizacji - nadal aktywna
        for _ in range(10):
            obstacle.update()
            assert obstacle.active is True

    def test_simulation_with_traffic_light(self):
        """Sprawdź czy symulacja akceptuje światła."""
        light = SpeedLimit(
            pos_start=Position(x=50, lane=0),
            pos_end=Position(x=52, lane=1),
            v_max=0,
            ticks=10,
            active=True
        )
        
        sim = Simulation(
            length=100,
            lanes=2,
            density=0.1,
            speed_limits=[light]
        )
        
        assert len(sim.road.speedLimits.speedLimits) == 1
        
        # Sprawdź czy światło jest uwzględniane
        limit_at_light = sim.road.getLimit(Position(x=51, lane=0))
        assert limit_at_light == 0  # światło czerwone
        
        limit_outside = sim.road.getLimit(Position(x=10, lane=0))
        assert limit_outside == 5  # normalny limit

    def test_simulation_updates_traffic_lights(self):
        """Sprawdź czy step() aktualizuje światła."""
        light = SpeedLimit(
            pos_start=Position(x=50, lane=0),
            pos_end=Position(x=50, lane=0),
            v_max=0,
            ticks=2,
            active=True
        )
        
        sim = Simulation(
            length=100,
            lanes=1,
            density=0.0,
            speed_limits=[light]
        )
        
        assert light.active is True
        
        # Po 2 krokach powinno się przełączyć
        sim.step()
        assert light.active is True
        sim.step()
        assert light.active is False

    def test_multiple_lights_and_obstacles(self):
        """Sprawdź czy można dodać wiele świateł i przeszkód."""
        light1 = SpeedLimit(
            pos_start=Position(x=20, lane=0),
            pos_end=Position(x=22, lane=0),
            v_max=0,
            ticks=5,
            active=True
        )
        
        light2 = SpeedLimit(
            pos_start=Position(x=60, lane=1),
            pos_end=Position(x=62, lane=1),
            v_max=0,
            ticks=8,
            active=False
        )
        
        obstacle = SpeedLimit(
            pos_start=Position(x=40, lane=0),
            pos_end=Position(x=42, lane=1),
            v_max=0,
            ticks=0,
            active=True
        )
        
        sim = Simulation(
            length=100,
            lanes=2,
            density=0.1,
            speed_limits=[light1, light2, obstacle]
        )
        
        assert len(sim.road.speedLimits.speedLimits) == 3
        
        # Sprawdź limity w różnych miejscach
        assert sim.road.getLimit(Position(x=21, lane=0)) == 0  # light1
        assert sim.road.getLimit(Position(x=61, lane=1)) == 5  # light2 nieaktywne
        assert sim.road.getLimit(Position(x=41, lane=0)) == 0  # obstacle
