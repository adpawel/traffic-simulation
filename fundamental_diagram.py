#!/usr/bin/env python3
"""
Skrypt generujący Fundamental Diagram (gęstość vs przepływ).
Uruchamia symulację dla różnych gęstości i zbiera statystyki przepływu.
"""

import sys
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from simulation.simulation import Simulation
import numpy as np
import matplotlib.pyplot as plt

def run_simulation_for_density(density, length=133, lanes=1, steps=2000, 
                               p_slow=0.2, p_change=0.6, gap_rear=2, 
                               reaction_delay=0, seed=None):
    """
    Uruchamia symulację dla danej gęstości i zwraca średni przepływ.
    
    Args:
        density: gęstość pojazdów (0.0-1.0)
        length: długość drogi
        lanes: liczba pasów
        steps: liczba kroków symulacji
        p_slow: prawdopodobieństwo losowego zwolnienia
        p_change: prawdopodobieństwo zmiany pasa
        gap_rear: minimalny odstęp z tyłu
        reaction_delay: opóźnienie reakcji kierowcy
        seed: seed dla powtarzalności (opcjonalny)
    
    Returns:
        average_flow: średni przepływ (pojazdy/krok)
        vehicle_count: liczba inicjalnie rozmieszczonych pojazdów
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
    
    vehicle_count = len(sim.vehicles)
    
    for _ in range(steps):
        sim.step()
    
    avg_flow = sim.stats.avg_flow
    return avg_flow, vehicle_count


def generate_fundamental_diagram(densities=None, steps_per_density=2000, 
                                 reaction_delay=0, seed=42, **sim_kwargs):
    """
    Generuje dane do fundamental diagram.
    
    Args:
        densities: lista gęstości (domyślnie: 0.05, 0.1, ..., 0.95, 1.0)
        steps_per_density: liczba kroków na każdą gęstość
        reaction_delay: opóźnienie reakcji
        seed: seed dla powtarzalności
        **sim_kwargs: dodatkowe parametry symulacji
    
    Returns:
        densities: lista gęstości
        flows: lista średnich przepływów
        vehicle_counts: lista liczby pojazdów na każdą gęstość
    """
    if densities is None:
        densities = [0.0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20, 
                     0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
    
    flows = []
    vehicle_counts = []
    
    total = len(densities)
    for i, density in enumerate(densities, 1):
        print(f"[{i:2d}/{total}] Gęstość: {density:.2f}... ", end="", flush=True)
        
        try:
            avg_flow, vc = run_simulation_for_density(
                density=density,
                steps=steps_per_density,
                reaction_delay=reaction_delay,
                seed=seed,
                **sim_kwargs
            )
            flows.append(avg_flow)
            vehicle_counts.append(vc)
            print(f"Przepływ: {avg_flow:.4f}, Pojazdy: {vc}")
        except Exception as e:
            print(f"BŁĄD: {e}")
            flows.append(None)
            vehicle_counts.append(None)
    
    return densities, flows, vehicle_counts


def plot_fundamental_diagram(densities, flows, title="", save_path=None):
    """
    Rysuje fundamental diagram (gęstość vs przepływ).
    """
    # Filtruj None wartości
    valid_data = [(d, f) for d, f in zip(densities, flows) if f is not None]
    if not valid_data:
        print("Brak ważnych danych do wykreślenia!")
        return
    
    densities_clean, flows_clean = zip(*valid_data)
    
    plt.figure(figsize=(10, 6))
    plt.plot(densities_clean, flows_clean, 'o-', linewidth=2, markersize=8, label='Przepływ')
    
    plt.xlabel('Gęstość pojazdów (% drogi zajęte)', fontsize=12)
    plt.ylabel('Przepływ (pojazdy/krok)', fontsize=12)
    plt.title(title or 'Fundamental Diagram - Model NaSch', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=11)
    
    # Skalowanie osi z gęstszą siatką na osi X
    max_flow = max(flows_clean) if flows_clean else 1
    plt.ylim(0, max_flow * 1.1)
    plt.xlim(0, 1.05)
    
    # Więcej ticków na osi X (co 0.05 zamiast domyślnie)
    import matplotlib.ticker as ticker
    ax = plt.gca()
    ax.xaxis.set_major_locator(ticker.MultipleLocator(0.1))
    ax.xaxis.set_minor_locator(ticker.MultipleLocator(0.05))
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"\nWykres zapisany: {save_path}")
    
    plt.show()


def save_data_to_csv(densities, flows, vehicle_counts, csv_path):
    """Zapisuje dane do pliku CSV."""
    import csv
    
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Density', 'Average_Flow', 'Vehicle_Count'])
        for d, flow, vc in zip(densities, flows, vehicle_counts):
            if flow is not None:
                writer.writerow([f'{d:.4f}', f'{flow:.6f}', vc])
    
    print(f"Dane zapisane: {csv_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Fundamental Diagram Generator")
    parser.add_argument("--steps", type=int, default=2000, 
                       help="Kroki na każdą gęstość (domyślnie: 2000)")
    parser.add_argument("--delay", type=int, default=0,
                       help="Opóźnienie reakcji (domyślnie: 0)")
    parser.add_argument("--lanes", type=int, default=1,
                       help="Liczba pasów (domyślnie: 1)")
    parser.add_argument("--length", type=int, default=133,
                       help="Długość drogi (domyślnie: 133)")
    parser.add_argument("--seed", type=int, default=42,
                       help="Seed losowości (domyślnie: 42)")
    parser.add_argument("--csv", type=str, default="fundamental_diagram.csv",
                       help="Ścieżka do zapisania CSV (domyślnie: fundamental_diagram.csv)")
    parser.add_argument("--png", type=str, default="fundamental_diagram.png",
                       help="Ścieżka do zapisania PNG (domyślnie: fundamental_diagram.png)")
    parser.add_argument("--no-plot", action="store_true",
                       help="Nie wyświetlaj wykresu (tylko zapisz do pliku)")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("GENEROWANIE FUNDAMENTAL DIAGRAM")
    print("=" * 60)
    print(f"Parametry:")
    print(f"  - Kroki na gęstość: {args.steps}")
    print(f"  - Opóźnienie reakcji: {args.delay}")
    print(f"  - Liczba pasów: {args.lanes}")
    print(f"  - Długość drogi: {args.length}")
    print(f"  - Seed: {args.seed}")
    print("=" * 60)
    print()
    
    # Gęstości do testowania: lista dostosowana do rejestru
    densities = [0.0, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20, 
                 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00]
    
    # Generuj dane
    densities, flows, vehicle_counts = generate_fundamental_diagram(
        densities=densities,
        steps_per_density=args.steps,
        reaction_delay=args.delay,
        seed=args.seed,
        length=args.length,
        lanes=args.lanes,
    )
    
    print()
    
    # Zapisz do CSV
    # save_data_to_csv(densities, flows, vehicle_counts, args.csv)
    
    # Wykreśl (jeśli nie --no-plot)
    if not args.no_plot:
        title = f"Fundamental Diagram (delay={args.delay}, lanes={args.lanes})"
        plot_fundamental_diagram(densities, flows, title=title, save_path=args.png)
    else:
        print(f"Wykres zapisany bez wyświetlania: {args.png}")
        # Zapisz plik bez wyświetlania
        valid_data = [(d, f) for d, f in zip(densities, flows) if f is not None]
        if valid_data:
            densities_clean, flows_clean = zip(*valid_data)
            plt.figure(figsize=(10, 6))
            plt.plot(densities_clean, flows_clean, 'o-', linewidth=2, markersize=8)
            plt.xlabel('Gęstość pojazdów (% drogi zajęte)', fontsize=12)
            plt.ylabel('Przepływ (pojazdy/krok)', fontsize=12)
            plt.title(f"Fundamental Diagram (delay={args.delay}, lanes={args.lanes})", 
                     fontsize=14, fontweight='bold')
            plt.grid(True, alpha=0.3)
            plt.xlim(0, 1.05)
            max_flow = max(flows_clean) if flows_clean else 1
            plt.ylim(0, max_flow * 1.1)
            plt.savefig(args.png, dpi=150, bbox_inches='tight')
            print(f"Wykres zapisany: {args.png}")
