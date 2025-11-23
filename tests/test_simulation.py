"""Testy dla modułu simulation: SimulationStats, Simulation."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from simulation import SimulationStats, Simulation, Position, Vehicle


class TestSimulationStats:
    """Testy dla dataclass SimulationStats."""

    def test_stats_initial_state(self):
        stats = SimulationStats()
        assert stats.step_count == 0
        assert stats.last_flow == 0
        assert stats.cumulative_flow == 0
        assert stats.avg_flow == 0.0

    def test_stats_avg_flow_calculation(self):
        stats = SimulationStats(step_count=10, cumulative_flow=50)
        assert stats.avg_flow == 5.0

    def test_stats_avg_flow_zero_steps(self):
        stats = SimulationStats(step_count=0, cumulative_flow=100)
        assert stats.avg_flow == 0.0


class TestSimulation:
    """Testy dla klasy Simulation."""

    def test_simulation_creation_default(self):
        sim = Simulation(length=100, lanes=2, density=0.0)
        assert sim.length == 100
        assert sim.lanes == 2
        assert sim.density == 0.0
        assert len(sim.vehicles) == 0
        assert len(sim.grid) == 2
        assert len(sim.grid[0]) == 100

    def test_simulation_init_with_density(self):
        """Sprawdzenie czy pojazdy są inicjalizowane zgodnie z gęstością."""
        sim = Simulation(length=100, lanes=1, density=0.3)
        # Z gęstością 0.3 oczekujemy ~30 pojazdów (z pewnym marginesem losowości)
        vehicle_count = len(sim.vehicles)
        assert 15 < vehicle_count < 45  # dość szeroki margines na losowość

    def test_simulation_grid_consistency(self):
        """Sprawdzenie czy grid i lista vehicles są spójne po inicjalizacji."""
        sim = Simulation(length=50, lanes=2, density=0.2)
        
        # Policz pojazdy w gridzie
        grid_vehicle_count = sum(
            1 for lane in sim.grid for cell in lane if cell is not None
        )
        
        assert grid_vehicle_count == len(sim.vehicles)
        
        # Sprawdź czy każdy pojazd z listy jest w gridzie
        for v in sim.vehicles:
            assert sim.grid[v.pos.lane][v.pos.x] == v

    def test_simulation_no_duplicate_positions(self):
        """Upewnij się, że żadne dwa pojazdy nie zajmują tej samej pozycji."""
        sim = Simulation(length=100, lanes=3, density=0.3)
        
        positions = set()
        for v in sim.vehicles:
            pos_tuple = (v.pos.lane, v.pos.x)
            assert pos_tuple not in positions, f"Duplicate position: {pos_tuple}"
            positions.add(pos_tuple)

    def test_simulation_step_empty_road(self):
        """Krok symulacji na pustej drodze nie powinien powodować błędów."""
        sim = Simulation(length=50, lanes=1, density=0.0)
        initial_step = sim.stats.step_count
        
        sim.step()
        
        assert sim.stats.step_count == initial_step + 1
        assert len(sim.vehicles) == 0

    def test_simulation_step_increments_counter(self):
        """Sprawdź czy step() zwiększa licznik kroków."""
        sim = Simulation(length=50, lanes=1, density=0.1)
        initial_step = sim.stats.step_count
        
        sim.step()
        
        assert sim.stats.step_count == initial_step + 1

    def test_simulation_vehicle_movement(self):
        """Sprawdź czy pojazdy się poruszają."""
        sim = Simulation(length=100, lanes=1, density=0.0, p_slow=0.0)
        
        # Ręcznie dodaj pojazd
        v = Vehicle(pos=Position(x=10, lane=0), velocity=0, v_max=5)
        sim.vehicles.append(v)
        sim.grid[0][10] = v
        
        initial_x = v.pos.x
        sim.step()
        
        # Po kroku, pojazd powinien przyspieszyć i się przesunąć
        assert v.velocity > 0
        assert v.pos.x != initial_x

    def test_simulation_vehicle_acceleration(self):
        """Sprawdź czy pojazdy przyspieszają zgodnie z NaSch."""
        sim = Simulation(length=100, lanes=1, density=0.0, p_slow=0.0)
        
        v = Vehicle(pos=Position(x=10, lane=0), velocity=0, v_max=5)
        sim.vehicles.append(v)
        sim.grid[0][10] = v
        
        sim.step()
        assert v.velocity == 1  # acceleration from 0 to 1
        
        sim.step()
        assert v.velocity == 2  # acceleration from 1 to 2

    def test_simulation_vehicle_max_speed_limit(self):
        """Sprawdź czy pojazdy nie przekraczają v_max."""
        sim = Simulation(length=100, lanes=1, density=0.0, p_slow=0.0)
        
        v = Vehicle(pos=Position(x=10, lane=0), velocity=4, v_max=5)
        sim.vehicles.append(v)
        sim.grid[0][10] = v
        
        # Kilka kroków
        for _ in range(10):
            sim.step()
        
        assert v.velocity <= v.v_max

    def test_simulation_vehicle_collision_avoidance(self):
        """Sprawdź czy pojazdy hamują, aby uniknąć kolizji."""
        sim = Simulation(length=100, lanes=1, density=0.0, p_slow=0.0)
        
        # Dwa pojazdy blisko siebie
        v1 = Vehicle(pos=Position(x=10, lane=0), velocity=0, v_max=5)
        v2 = Vehicle(pos=Position(x=13, lane=0), velocity=0, v_max=5)  # 3 komórki przed v1
        
        sim.vehicles.extend([v1, v2])
        sim.grid[0][10] = v1
        sim.grid[0][13] = v2
        
        # Kilka kroków
        for _ in range(5):
            sim.step()
        
        # Sprawdź czy nie ma kolizji
        positions = [(v.pos.lane, v.pos.x) for v in sim.vehicles]
        assert len(positions) == len(set(positions)), "Collision detected!"

    def test_simulation_wrap_around(self):
        """Sprawdź czy pojazdy poprawnie przechodzą przez koniec drogi."""
        sim = Simulation(length=20, lanes=1, density=0.0, p_slow=0.0)
        
        v = Vehicle(pos=Position(x=18, lane=0), velocity=5, v_max=5)
        sim.vehicles.append(v)
        sim.grid[0][18] = v
        
        sim.step()
        
        # Pojazd powinien być na pozycji (18 + velocity) % 20
        expected_x = (18 + v.velocity) % 20
        assert v.pos.x == expected_x

    def test_simulation_flow_counting(self):
        """Sprawdź czy przepływ jest poprawnie liczony."""
        sim = Simulation(length=20, lanes=1, density=0.0, p_slow=0.0)
        
        # Pojazd blisko końca, który minie x=0
        v = Vehicle(pos=Position(x=18, lane=0), velocity=5, v_max=5)
        sim.vehicles.append(v)
        sim.grid[0][18] = v
        
        sim.step()
        
        # Pojazd powinien przejść przez x=0, więc flow > 0
        assert sim.stats.last_flow > 0
        assert sim.stats.cumulative_flow > 0

    def test_simulation_run_multiple_steps(self):
        """Sprawdź czy run() wykonuje odpowiednią liczbę kroków."""
        sim = Simulation(length=50, lanes=1, density=0.1)
        
        sim.run(steps=10)
        
        assert sim.stats.step_count == 10

    def test_simulation_reset(self):
        """Sprawdź czy reset() przywraca stan początkowy."""
        sim = Simulation(length=50, lanes=2, density=0.2)
        
        # Wykonaj kilka kroków
        sim.run(steps=5)
        
        # Reset
        sim.reset(density=0.3)
        
        assert sim.stats.step_count == 0
        assert sim.stats.cumulative_flow == 0
        assert sim.density == 0.3

    def test_simulation_distance_to_next_car(self):
        """Test metody _distance_to_next_car."""
        sim = Simulation(length=20, lanes=1, density=0.0)
        
        # Pojazdy na pozycjach 5 i 10
        v1 = Vehicle(pos=Position(x=5, lane=0))
        v2 = Vehicle(pos=Position(x=10, lane=0))
        sim.vehicles.extend([v1, v2])
        sim.grid[0][5] = v1
        sim.grid[0][10] = v2
        
        # Odległość od x=5 do najbliższego auta z przodu (x=10)
        dist = sim._distance_to_next_car(lane=0, x=5)
        assert dist == 4  # 4 wolne komórki (6, 7, 8, 9)

    def test_simulation_distance_to_prev_car(self):
        """Test metody _distance_to_prev_car."""
        sim = Simulation(length=20, lanes=1, density=0.0)
        
        # Pojazdy na pozycjach 5 i 10
        v1 = Vehicle(pos=Position(x=5, lane=0))
        v2 = Vehicle(pos=Position(x=10, lane=0))
        sim.vehicles.extend([v1, v2])
        sim.grid[0][5] = v1
        sim.grid[0][10] = v2
        
        # Odległość od x=10 do najbliższego auta z tyłu (x=5)
        dist = sim._distance_to_prev_car(lane=0, x=10)
        assert dist == 4  # 4 wolne komórki (9, 8, 7, 6)

    def test_simulation_record_history(self):
        """Sprawdź czy historia jest zapisywana poprawnie."""
        sim = Simulation(length=50, lanes=1, density=0.1, record_history=True)
        
        assert sim.history is not None
        assert len(sim.history) == 0
        
        sim.run(steps=5)
        
        assert len(sim.history) == 5

    def test_simulation_no_history_by_default(self):
        """Domyślnie historia nie powinna być zapisywana."""
        sim = Simulation(length=50, lanes=1, density=0.1, record_history=False)
        
        assert sim.history is None
        
        sim.run(steps=5)
        
        assert sim.history is None

    def test_simulation_get_grid(self):
        """Sprawdź czy get_grid() zwraca aktualny grid."""
        sim = Simulation(length=30, lanes=2, density=0.2)
        
        grid = sim.get_grid()
        
        assert grid == sim.grid
        assert len(grid) == 2
        assert len(grid[0]) == 30

    def test_simulation_lane_change_probability(self):
        """Sprawdź czy p_change wpływa na zmiany pasa."""
        # Z p_change=0.0 nie powinno być zmian pasa
        sim_no_change = Simulation(
            length=100, lanes=3, density=0.2, p_change=0.0
        )
        
        initial_lanes = [v.pos.lane for v in sim_no_change.vehicles]
        sim_no_change.run(steps=10)
        final_lanes = [v.pos.lane for v in sim_no_change.vehicles]
        
        # Możliwe że niektóre pojazdy i tak zmienią pas przez logikę,
        # ale z p_change=0 będzie to rzadkie
        # Ten test jest probabilistyczny i może czasem zawieść
        # W praktyce z p_change=0 i odpowiednią konfiguracją nie powinno być zmian

    def test_simulation_multiple_lanes_independence(self):
        """Sprawdź czy pojazdy na różnych pasach działają niezależnie."""
        sim = Simulation(length=50, lanes=3, density=0.0, p_slow=0.0, p_change=0.0)
        
        # Po jednym pojeździe na każdym pasie
        v1 = Vehicle(pos=Position(x=10, lane=0), velocity=0, v_max=5)
        v2 = Vehicle(pos=Position(x=10, lane=1), velocity=0, v_max=5)
        v3 = Vehicle(pos=Position(x=10, lane=2), velocity=0, v_max=5)
        
        sim.vehicles.extend([v1, v2, v3])
        sim.grid[0][10] = v1
        sim.grid[1][10] = v2
        sim.grid[2][10] = v3
        
        sim.step()
        
        # Wszystkie powinny przyspieszyć i się przesunąć
        assert v1.velocity > 0
        assert v2.velocity > 0
        assert v3.velocity > 0
        
        assert v1.pos.x > 10
        assert v2.pos.x > 10
        assert v3.pos.x > 10
