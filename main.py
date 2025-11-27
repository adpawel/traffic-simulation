"""
Główny punkt wejścia do symulacji ruchu drogowego.

Uruchamia wizualizację pygame z parametrami z config.py lub przekazanymi z CLI.
"""

import argparse
import sys
import random
from pathlib import Path

# Dodaj src do ścieżki
sys.path.insert(0, str(Path(__file__).parent / "src"))

from simulation.simulation import Simulation
from simulation.pygame_view import PygameView
from src.config import L, LANES, DENSITY, P_SLOW, P_CHANGE, GAP_REAR


def parse_args():
    """Parsowanie argumentów linii poleceń."""
    parser = argparse.ArgumentParser(
        description="Symulacja ruchu drogowego - model NaSch z wieloma pasami"
    )
    
    # Parametry symulacji
    parser.add_argument(
        "--length",
        type=int,
        default=L,
        help=f"Długość drogi w komórkach (domyślnie: {L})"
    )
    parser.add_argument(
        "--lanes",
        type=int,
        default=LANES,
        help=f"Liczba pasów ruchu (domyślnie: {LANES})"
    )
    parser.add_argument(
        "--density",
        type=float,
        default=DENSITY,
        help=f"Początkowa gęstość pojazdów 0.0-1.0 (domyślnie: {DENSITY})"
    )
    parser.add_argument(
        "--p-slow",
        type=float,
        default=P_SLOW,
        help=f"Prawdopodobieństwo losowego zwolnienia (domyślnie: {P_SLOW})"
    )
    parser.add_argument(
        "--p-change",
        type=float,
        default=P_CHANGE,
        help=f"Prawdopodobieństwo próby zmiany pasa (domyślnie: {P_CHANGE})"
    )
    parser.add_argument(
        "--gap-rear",
        type=int,
        default=GAP_REAR,
        help=f"Minimalny odstęp z tyłu przy zmianie pasa (domyślnie: {GAP_REAR})"
    )
    parser.add_argument(
        "--reaction-delay",
        type=int,
        default=0,
        help="Opóźnienie reakcji kierowcy w krokach, 0=brak, 1=~1.6s (domyślnie: 0)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Seed losowości dla powtarzalnych testów (domyślnie: brak)"
    )
    
    # Światła i przeszkody
    parser.add_argument(
        "--traffic-lights",
        type=str,
        default="",
        help="Pozycje świateł: 'x1,lane1,x2,lane2,ticks;...' (np. '50,0,52,2,10')"
    )
    parser.add_argument(
        "--obstacles",
        type=str,
        default="",
        help="Pozycje przeszkód: 'x1,lane1,x2,lane2;...' (np. '30,1,32,1')"
    )
    parser.add_argument(
        "--speed-limits",
        type=str,
        default="",
        help="Lokalne ograniczenia prędkości: 'x1,lane1,x2,lane2,vmax;...' (np. '60,0,80,1,3')"
    )
    
    # Parametry wizualizacji
    parser.add_argument(
        "--cell-size",
        type=int,
        default=20,
        help="Wysokość komórki w pikselach (domyślnie: 20)"
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=2,
        help="Liczba klatek na sekundę (domyślnie: 10)"
    )
    parser.add_argument(
        "--window-width",
        type=int,
        default=1400,
        help="Szerokość okna w pikselach (domyślnie: 1400)"
    )
    
    # Tryb bez GUI (tylko symulacja)
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Uruchom symulację bez wizualizacji (tylko konsola)"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=1000,
        help="Liczba kroków w trybie --no-gui (domyślnie: 1000)"
    )
    
    return parser.parse_args()


def run_simulation_no_gui(sim: Simulation, steps: int) -> None:
    """Uruchom symulację bez GUI - tylko statystyki w konsoli."""
    print(f"Uruchamiam symulację na {steps} kroków...")
    print(f"Parametry:")
    print(f"  - Długość: {sim.length} komórek")
    print(f"  - Pasy: {sim.lanes}")
    print(f"  - Początkowa gęstość: {sim.density:.2%}")
    print(f"  - p_slow: {sim.p_slow}")
    print(f"  - p_change: {sim.p_change}")
    print(f"  - gap_rear: {sim.gap_rear}")
    print(f"  - Liczba pojazdów: {len(sim.vehicles)}")
    print()
    
    # Progress bar co 10%
    checkpoint_interval = max(1, steps // 10)
    
    for step in range(steps):
        sim.step()
        
        if (step + 1) % checkpoint_interval == 0 or step == 0:
            progress = (step + 1) / steps * 100
            print(f"[{progress:5.1f}%] Krok {step + 1}/{steps} | "
                  f"Przepływ: {sim.stats.last_flow:3d} | "
                  f"Średni przepływ: {sim.stats.avg_flow:6.2f}")
    
    print()
    print("=== WYNIKI ===")
    print(f"Wykonane kroki: {sim.stats.step_count}")
    print(f"Łączny przepływ: {sim.stats.cumulative_flow}")
    print(f"Średni przepływ: {sim.stats.avg_flow:.4f} pojazdów/krok\n\n\n")


def parse_traffic_lights(lights_str: str, length: int):
    """Parsuje string ze światłami i zwraca listę SpeedLimit."""
    from simulation.speedLimits import SpeedLimit, Position
    
    if not lights_str.strip():
        return []
    
    lights = []
    for light_spec in lights_str.split(';'):
        if not light_spec.strip():
            continue
        parts = light_spec.split(',')
        if len(parts) != 5:
            print(f"Uwaga: Nieprawidłowy format światła '{light_spec}', pomijam")
            continue
        try:
            x1, lane1, x2, lane2, ticks = map(int, parts)
            lights.append(SpeedLimit(
                pos_start=Position(x=x1, lane=lane1),
                pos_end=Position(x=x2, lane=lane2),
                v_max=0,
                ticks=ticks,
                active=True
            ))
        except ValueError:
            print(f"Uwaga: Nieprawidłowe wartości w '{light_spec}', pomijam")
    
    return lights


def parse_obstacles(obstacles_str: str, length: int):
    """Parsuje string z przeszkodami i zwraca listę SpeedLimit."""
    from simulation.speedLimits import SpeedLimit, Position
    
    if not obstacles_str.strip():
        return []
    
    obstacles = []
    for obs_spec in obstacles_str.split(';'):
        if not obs_spec.strip():
            continue
        parts = obs_spec.split(',')
        if len(parts) != 4:
            print(f"Uwaga: Nieprawidłowy format przeszkody '{obs_spec}', pomijam")
            continue
        try:
            x1, lane1, x2, lane2 = map(int, parts)
            obstacles.append(SpeedLimit(
                pos_start=Position(x=x1, lane=lane1),
                pos_end=Position(x=x2, lane=lane2),
                v_max=0,
                ticks=0,
                active=True
            ))
        except ValueError:
            print(f"Uwaga: Nieprawidłowe wartości w '{obs_spec}', pomijam")
    
    return obstacles


def parse_speed_limits(speed_limits_str: str, length: int):
    """Parsuje string z lokalnymi ograniczeniami prędkości i zwraca listę SpeedLimit."""
    from simulation.speedLimits import SpeedLimit, Position
    
    if not speed_limits_str.strip():
        return []
    
    speed_limits = []
    for limit_spec in speed_limits_str.split(';'):
        if not limit_spec.strip():
            continue
        parts = limit_spec.split(',')
        if len(parts) != 5:
            print(f"Uwaga: Nieprawidłowy format ograniczenia prędkości '{limit_spec}', pomijam")
            continue
        try:
            x1, lane1, x2, lane2, v_max = map(int, parts)
            if v_max < 0:
                print(f"Uwaga: v_max musi być >= 0 w '{limit_spec}', pomijam")
                continue
            speed_limits.append(SpeedLimit(
                pos_start=Position(x=x1, lane=lane1),
                pos_end=Position(x=x2, lane=lane2),
                v_max=v_max,
                ticks=0,
                active=True
            ))
        except ValueError:
            print(f"Uwaga: Nieprawidłowe wartości w '{limit_spec}', pomijam")
    
    return speed_limits


def main():
    """Główna funkcja."""
    args = parse_args()
    
    # Walidacja parametrów
    if not (0.0 <= args.density <= 1.0):
        print("Błąd: density musi być w zakresie [0.0, 1.0]")
        sys.exit(1)
    
    if not (0.0 <= args.p_slow <= 1.0):
        print("Błąd: p_slow musi być w zakresie [0.0, 1.0]")
        sys.exit(1)
    
    if not (0.0 <= args.p_change <= 1.0):
        print("Błąd: p_change musi być w zakresie [0.0, 1.0]")
        sys.exit(1)
    
    # Parsuj światła, przeszkody i lokalne ograniczenia prędkości
    speed_limits = []
    speed_limits.extend(parse_traffic_lights(args.traffic_lights, args.length))
    speed_limits.extend(parse_obstacles(args.obstacles, args.length))
    speed_limits.extend(parse_speed_limits(args.speed_limits, args.length))
    
    # Ustaw seed losowości jeśli podano
    if args.seed is not None:
        random.seed(args.seed)
    
    # Tworzenie symulacji
    sim = Simulation(
        length=args.length,
        lanes=args.lanes,
        density=args.density,
        p_slow=args.p_slow,
        p_change=args.p_change,
        gap_rear=args.gap_rear,
        reaction_delay=args.reaction_delay,
        speed_limits=speed_limits,
    )
    
    # Tryb bez GUI
    if args.no_gui:
        run_simulation_no_gui(sim, args.steps)
        return
    
    # Wizualizacja pygame
    try:
        view = PygameView(
            simulation=sim,
            cell_size=args.cell_size,
            fps=args.fps,
            window_width=args.window_width,
        )
        view.run()
    except KeyboardInterrupt:
        print("\nPrzerwano przez użytkownika.")
        sys.exit(0)


if __name__ == "__main__":
    main()