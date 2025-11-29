#!/usr/bin/env python3
"""
Skrypt generujący heatmapę trajektorii pojazdów (czas vs pozycja, kolory = prędkość).
"""

import sys
import random
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent / "src"))

from simulation.simulation import Simulation
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


def record_trajectories(density=0.3, length=133, lanes=1, steps=1000,
                        p_slow=0.2, p_change=0.6, gap_rear=2,
                        reaction_delay=0, seed=None):
    """
    Uruchamia symulację i zapisuje trajektorie pojazdów (czas, pozycja, prędkość).
    
    Returns:
        trajectories: dict {vehicle_id: [(time, x, v), ...]}
        vehicle_ids: lista ID pojazdów
    """
    if seed is not None:
        random.seed(seed)
    
    sim = Simulation(
        length=length,
        lanes=lanes,
        density=density,
        p_slow=p_slow,
        p_change=p_change,
        gap_rear=gap_rear,
        reaction_delay=reaction_delay,
    )
    
    trajectories = defaultdict(list)
    vehicle_ids = {id(v): v for v in sim.vehicles}
    
    for step in range(steps):
        # Zapisz pozycje przed krokiem
        for v in sim.vehicles:
            v_id = id(v)
            trajectories[v_id].append((step, v.pos.x, v.velocity))
        
        # Wykonaj krok
        sim.step()
    
    return trajectories, vehicle_ids, sim.length


def plot_trajectory_heatmap(trajectories, vehicle_ids, road_length, 
                            title="", save_path=None, max_velocity=5):
    """
    Rysuje heatmapę: oś X = pozycja, oś Y = czas, kolor = prędkość.
    """
    if not trajectories:
        print("Brak danych trajektorii!")
        return
    
    # Zbierz dane do macierzy
    # Wymiary: (czas, pozycja)
    max_time = max(max(t for t, _, _ in traj) for traj in trajectories.values())
    
    # Macierz: average velocity na każdej pozycji w każdym időkroku
    # Inicjalizacja: NaN (żeby później były białe pola bez danych)
    velocity_grid = np.full((max_time + 1, road_length), np.nan)
    count_grid = np.zeros((max_time + 1, road_length))
    
    # Wypełnij macierz
    for v_id, trajectory in trajectories.items():
        for time, x, v in trajectory:
            if 0 <= x < road_length and 0 <= time <= max_time:
                if np.isnan(velocity_grid[time, x]):
                    velocity_grid[time, x] = v
                    count_grid[time, x] = 1
                else:
                    # Średnia jeśli kilka pojazdów na tej pozycji
                    old_val = velocity_grid[time, x]
                    old_count = count_grid[time, x]
                    velocity_grid[time, x] = (old_val * old_count + v) / (old_count + 1)
                    count_grid[time, x] += 1
    
    # Rysuj heatmapę
    fig, ax = plt.subplots(figsize=(14, 8))
    
    # Normalizacja kolorów (0 = niebieski, max_velocity = czerwony)
    norm = mcolors.Normalize(vmin=0, vmax=max_velocity)
    im = ax.imshow(velocity_grid, aspect='auto', origin='lower', cmap='RdYlBu_r', norm=norm,
                   extent=[0, road_length, 0, max_time])
    
    ax.set_xlabel('Pozycja (komórka)', fontsize=12)
    ax.set_ylabel('Czas (krok)', fontsize=12)
    ax.set_title(title or 'Trajektorie pojazdów - Heatmapa prędkości', 
                fontsize=14, fontweight='bold')
    
    # Colorbar
    cbar = plt.colorbar(im, ax=ax, label='Prędkość (komórki/krok)')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Heatmapa zapisana: {save_path}")
    
    plt.show()


def plot_single_vehicle_trajectory(trajectories, vehicle_id, road_length,
                                   title="", save_path=None, max_velocity=5):
    """
    Rysuje trajektorię pojedynczego pojazdu (czas vs pozycja, kolor = prędkość).
    """
    if vehicle_id not in trajectories:
        print(f"Pojazd {vehicle_id} nie znaleziony!")
        return
    
    trajectory = trajectories[vehicle_id]
    times, positions, velocities = zip(*trajectory)
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Scatter plot z kolorami
    scatter = ax.scatter(times, positions, c=velocities, s=20, cmap='RdYlBu_r',
                        vmin=0, vmax=max_velocity, alpha=0.7)
    
    # Połącz liniami
    ax.plot(times, positions, 'k-', alpha=0.2, linewidth=0.5)
    
    ax.set_xlabel('Czas (krok)', fontsize=12)
    ax.set_ylabel('Pozycja (komórka)', fontsize=12)
    ax.set_title(title or f'Trajektoria pojazdu (ID: {vehicle_id})', 
                fontsize=14, fontweight='bold')
    
    cbar = plt.colorbar(scatter, ax=ax, label='Prędkość (komórki/krok)')
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"Trajektoria zapisana: {save_path}")
    
    plt.show()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Trajectory Heatmap Generator")
    parser.add_argument("--density", type=float, default=0.3,
                       help="Gęstość pojazdów (domyślnie: 0.3)")
    parser.add_argument("--steps", type=int, default=1000,
                       help="Liczba kroków symulacji (domyślnie: 1000)")
    parser.add_argument("--delay", type=int, default=0,
                       help="Opóźnienie reakcji (domyślnie: 0)")
    parser.add_argument("--lanes", type=int, default=1,
                       help="Liczba pasów (domyślnie: 1)")
    parser.add_argument("--length", type=int, default=133,
                       help="Długość drogi (domyślnie: 133)")
    parser.add_argument("--seed", type=int, default=42,
                       help="Seed losowości (domyślnie: 42)")
    parser.add_argument("--heatmap-png", type=str, default="trajectory_heatmap.png",
                       help="Ścieżka do heatmapy (domyślnie: trajectory_heatmap.png)")
    parser.add_argument("--single-vehicle", action="store_true",
                       help="Rysuj trajektorię pierwszego pojazdu zamiast heatmapy całej drogi")
    parser.add_argument("--no-plot", action="store_true",
                       help="Nie wyświetlaj wykresu (tylko zapisz do pliku)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("GENEROWANIE HEATMAPY TRAJEKTORII")
    print("=" * 60)
    print(f"Parametry:")
    print(f"  - Gęstość: {args.density:.2f}")
    print(f"  - Kroki: {args.steps}")
    print(f"  - Opóźnienie: {args.delay}")
    print(f"  - Pasy: {args.lanes}")
    print(f"  - Długość: {args.length}")
    print(f"  - Seed: {args.seed}")
    print("=" * 60)
    print()
    
    print("Nagrywanie trajektorii...", flush=True)
    trajectories, vehicle_ids, road_length = record_trajectories(
        density=args.density,
        length=args.length,
        lanes=args.lanes,
        steps=args.steps,
        reaction_delay=args.delay,
        seed=args.seed,
    )
    
    print(f"Zarejestrowano {len(trajectories)} pojazdy\n")
    
    # Rysuj
    if args.single_vehicle:
        # Pierwsza pojazd z trajektorii
        first_vid = list(trajectories.keys())[0]
        title = f"Trajektoria pojazdu (delay={args.delay})"
        if not args.no_plot:
            plot_single_vehicle_trajectory(trajectories, first_vid, road_length,
                                          title=title, save_path=args.heatmap_png)
        else:
            plot_single_vehicle_trajectory(trajectories, first_vid, road_length,
                                          title=title, save_path=args.heatmap_png)
            print(f"Trajektoria zapisana: {args.heatmap_png}")
    else:
        # Całe droga - heatmapa
        title = f"Heatmapa trajektorii (density={args.density:.2f}, delay={args.delay})"
        if not args.no_plot:
            plot_trajectory_heatmap(trajectories, vehicle_ids, road_length,
                                   title=title, save_path=args.heatmap_png)
        else:
            plot_trajectory_heatmap(trajectories, vehicle_ids, road_length,
                                   title=title, save_path=args.heatmap_png)
            print(f"Heatmapa zapisana: {args.heatmap_png}")
