#!/usr/bin/env python3
"""Scenariusze demonstracyjne modelu NaSch."""

import sys
import random
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent))

from simulation.simulation import Simulation
from simulation.speedLimits import SpeedLimit, SpeedLimits, Position
from simulation.pygame_view import PygameView


CALIBRATED = {
    'p_slow': 0.25,
    'p_change': 0.525,
    'gap_rear': 1,
    'reaction_delay': 1
}


def create_simulation(length: int = 200, lanes: int = 3, density: float = 0.15,
                      speed_limits: list = None, **kwargs) -> Simulation:
    params = {**CALIBRATED, **kwargs}
    return Simulation(
        length=length,
        lanes=lanes,
        density=density,
        p_slow=params['p_slow'],
        p_change=params['p_change'],
        gap_rear=params['gap_rear'],
        reaction_delay=params['reaction_delay'],
        speed_limits=speed_limits
    )


def collect_spacetime_data(sim: Simulation, steps: int) -> np.ndarray:
    data = []
    for _ in range(steps):
        step_data = []
        for lane in range(sim.lanes):
            lane_state = []
            for x in range(sim.length):
                v = sim.grid[lane][x]
                lane_state.append(v.velocity if v is not None else -1)
            step_data.append(lane_state)
        data.append(step_data)
        sim.step()
    return np.array(data)


def collect_flow_data(sim: Simulation, steps: int) -> List[int]:
    flows = []
    for _ in range(steps):
        sim.step()
        flows.append(sim.stats.last_flow)
    return flows


def scenario_shockwave(save_path: str = "scenario_shockwave.png"):
    """Fala uderzeniowa - propagacja korka wstecz po usunięciu przeszkody."""
    print("=" * 60)
    print("SCENARIUSZ: Fala uderzeniowa (Shockwave)")
    print("=" * 60)
    
    length = 300
    lanes = 1
    density = 0.20
    
    print("Faza 1: Ustabilizowanie ruchu...")
    sim = create_simulation(length=length, lanes=lanes, density=density)
    
    for _ in range(200):
        sim.step()
    
    print("Faza 2: Zbieranie danych przed zaburzeniem...")
    data_before = collect_spacetime_data(sim, steps=100)
    
    print("Faza 3: Wprowadzenie przeszkody...")
    obstacle_pos = length // 2
    obstacle = SpeedLimit(
        pos_start=Position(x=obstacle_pos, lane=0),
        pos_end=Position(x=obstacle_pos + 5, lane=0),
        v_max=0,
        ticks=0
    )
    sim.road.speedLimits.speedLimits.append(obstacle)
    
    data_obstacle = collect_spacetime_data(sim, steps=50)
    
    print("Faza 4: Usunięcie przeszkody, obserwacja fali...")
    sim.road.speedLimits.speedLimits.remove(obstacle)
    
    data_after = collect_spacetime_data(sim, steps=150)
    all_data = np.concatenate([data_before, data_obstacle, data_after], axis=0)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    ax1 = axes[0]
    spacetime = all_data[:, 0, :]
    spacetime_plot = np.where(spacetime >= 0, spacetime, np.nan)
    
    im = ax1.imshow(spacetime_plot.T, aspect='auto', cmap='RdYlGn',
                    origin='lower', vmin=0, vmax=5)
    ax1.axhline(y=obstacle_pos, color='red', linestyle='--', linewidth=2, label='Pozycja przeszkody')
    ax1.axvline(x=100, color='orange', linestyle='-', linewidth=1, label='Początek przeszkody')
    ax1.axvline(x=150, color='blue', linestyle='-', linewidth=1, label='Koniec przeszkody')
    
    ax1.set_xlabel('Czas [kroki]', fontsize=11)
    ax1.set_ylabel('Pozycja [komórki]', fontsize=11)
    ax1.set_title('Diagram czasoprzestrzenny - propagacja fali', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=9)
    
    cbar = plt.colorbar(im, ax=ax1)
    cbar.set_label('Prędkość [komórki/krok]')
    
    ax2 = axes[1]
    ax2.axis('off')
    
    explanation = """
    FALA UDERZENIOWA (SHOCKWAVE)

    Co widzimy:

    1. Przed przeszkodą (t < 100):
       Płynny ruch, zielone kolory
       
    2. Podczas przeszkody (100 < t < 150):
       Tworzenie się korka za przeszkodą
       Czerwone/żółte = wolny ruch
       
    3. Po usunięciu przeszkody (t > 150):
       Przeszkody już nie ma, ale korek
       propaguje się WSTECZ!

    Wniosek: Jedno hamowanie powoduje
    korek, który cofa się w czasie
    nawet po usunięciu przyczyny.
    """
    
    ax2.text(0.1, 0.9, explanation, transform=ax2.transAxes, fontsize=11,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    plt.suptitle('Scenariusz 1: Fala uderzeniowa (Shockwave)', fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\nZapisano: {save_path}")
    plt.show()


def scenario_light_timing(save_path: str = "scenario_lights.png"):
    """Wpływ czasu cyklu świateł na powstawanie korków przy różnych gęstościach."""
    print("=" * 60)
    print("SCENARIUSZ: Światła - krótki vs długi cykl")
    print("=" * 60)
    
    length = 150
    lanes = 1
    warmup = 100
    spacetime_steps = 200
    
    configs = [
        ('Niski ruch\nkrótki cykl', 0.12, 15),
        ('Niski ruch\ndługi cykl', 0.12, 50),
        ('Wysoki ruch\nkrótki cykl', 0.30, 15),
        ('Wysoki ruch\ndługi cykl', 0.30, 50),
    ]
    
    results = {}
    spacetime_data = {}
    
    for name, density, cycle in configs:
        print(f"Symulacja: gęstość {density*100:.0f}%, cykl {cycle}...")
        
        random.seed(123)
        np.random.seed(123)
        
        light_pos = length // 2
        light = SpeedLimit(
            pos_start=Position(x=light_pos, lane=0),
            pos_end=Position(x=light_pos + 2, lane=0),
            v_max=0,
            ticks=cycle // 2,
            active=True
        )
        
        sim = create_simulation(length=length, lanes=lanes, density=density,
                               speed_limits=[light])
        
        for _ in range(warmup):
            sim.step()
        
        st_data = collect_spacetime_data(sim, spacetime_steps)
        spacetime_data[name] = st_data
        
        sim.stats.cumulative_flow = 0
        sim.stats.step_count = 0
        flows = collect_flow_data(sim, 300)
        
        results[name] = {
            'density': density,
            'cycle': cycle,
            'avg_flow': np.mean(flows),
            'std_flow': np.std(flows)
        }
        print(f"  Przepływ: {results[name]['avg_flow']:.3f}")
    
    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    
    # Diagramy czasoprzestrzenne (2x2)
    for idx, (name, data) in enumerate(spacetime_data.items()):
        row, col = idx // 2, idx % 2
        ax = axes[row, col]
        
        st = data[:, 0, :]
        st_plot = np.where(st >= 0, st, np.nan)
        
        im = ax.imshow(st_plot.T, aspect='auto', cmap='RdYlGn',
                      origin='lower', vmin=0, vmax=5)
        
        # Zaznaczenie pozycji światła
        ax.axhline(y=length//2, color='white', linestyle='--', linewidth=1, alpha=0.7)
        
        ax.set_xlabel('Czas [kroki]', fontsize=10)
        ax.set_ylabel('Pozycja', fontsize=10)
        ax.set_title(name, fontsize=11, fontweight='bold')
    
    # Colorbar
    cbar = plt.colorbar(im, ax=axes[0, 1], shrink=0.8, pad=0.02)
    cbar.set_label('Prędkość', fontsize=10)
    
    # Porównanie przepływu
    ax_bar = axes[0, 2]
    names_short = ['Niski/krótki', 'Niski/długi', 'Wysoki/krótki', 'Wysoki/długi']
    avgs = [results[n]['avg_flow'] for n in spacetime_data.keys()]
    colors = ['lightblue', 'blue', 'lightcoral', 'darkred']
    
    bars = ax_bar.bar(range(4), avgs, color=colors)
    ax_bar.set_xticks(range(4))
    ax_bar.set_xticklabels(names_short, fontsize=9, rotation=15, ha='right')
    ax_bar.set_ylabel('Przepływ [poj/krok]', fontsize=11)
    ax_bar.set_title('Porównanie przepływu', fontsize=12, fontweight='bold')
    
    for bar, val in zip(bars, avgs):
        ax_bar.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                   f'{val:.3f}', ha='center', fontsize=9, fontweight='bold')
    ax_bar.grid(True, alpha=0.3, axis='y')
    
    # Wnioski
    ax_text = axes[1, 2]
    ax_text.axis('off')
    
    low_short = results['Niski ruch\nkrótki cykl']['avg_flow']
    low_long = results['Niski ruch\ndługi cykl']['avg_flow']
    high_short = results['Wysoki ruch\nkrótki cykl']['avg_flow']
    high_long = results['Wysoki ruch\ndługi cykl']['avg_flow']
    
    diff_low = (low_long / low_short - 1) * 100
    diff_high = (high_long / high_short - 1) * 100
    
    conclusions = f"""
    ANALIZA WYNIKÓW

    Przy NISKIM ruchu (12%):
    Krótki cykl: {low_short:.3f}
    Długi cykl:  {low_long:.3f}
    Różnica: {diff_low:+.1f}%

    Przy WYSOKIM ruchu (30%):
    Krótki cykl: {high_short:.3f}
    Długi cykl:  {high_long:.3f}
    Różnica: {diff_high:+.1f}%

    WNIOSEK:
    
    Przy wysokim natężeniu krótki cykl
    tworzy KOLEJKĘ przed światłem -
    widać czerwone pasy propagujące
    się wstecz (efekt fali).

    Długi cykl pozwala rozładować
    kolejkę zanim zmieni się na
    czerwone.
    """
    
    ax_text.text(0.05, 0.95, conclusions, transform=ax_text.transAxes, fontsize=10,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    plt.suptitle('Scenariusz 2: Wpływ czasu cyklu świateł na ruch przy różnych gęstościach', 
                 fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\nZapisano: {save_path}")
    plt.show()
    
    print("\nPODSUMOWANIE:")
    print(f"  Niski ruch: zmiana cyklu daje {diff_low:+.1f}% przepływu")
    print(f"  Wysoki ruch: zmiana cyklu daje {diff_high:+.1f}% przepływu")


def scenario_accident(save_path: str = "scenario_accident.png"):
    """Symulacja wypadku - blokada środkowego pasa."""
    print("=" * 60)
    print("SCENARIUSZ: Wypadek na autostradzie")
    print("=" * 60)
    
    length = 250
    lanes = 3
    density = 0.18
    
    print("Faza 1: Normalne warunki...")
    sim = create_simulation(length=length, lanes=lanes, density=density)
    
    for _ in range(300):
        sim.step()
    
    sim.stats.cumulative_flow = 0
    sim.stats.step_count = 0
    
    flows_before = collect_flow_data(sim, steps=200)
    
    print("Faza 2: Wypadek - blokada środkowego pasa...")
    accident_pos = length // 2
    accident_length = 15
    
    accident = SpeedLimit(
        pos_start=Position(x=accident_pos, lane=1),
        pos_end=Position(x=accident_pos + accident_length, lane=1),
        v_max=0,
        ticks=0
    )
    sim.road.speedLimits.speedLimits.append(accident)
    
    flows_during = collect_flow_data(sim, steps=300)
    
    print("Faza 3: Usunięcie wypadku...")
    sim.road.speedLimits.speedLimits.remove(accident)
    
    flows_after = collect_flow_data(sim, steps=300)
    
    all_flows = flows_before + flows_during + flows_after
    
    window = 15
    smoothed = np.convolve(all_flows, np.ones(window)/window, mode='valid')
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    ax1 = axes[0, 0]
    ax1.plot(smoothed, color='blue', linewidth=2)
    ax1.axvspan(0, 200, alpha=0.2, color='green', label='Przed wypadkiem')
    ax1.axvspan(200, 500, alpha=0.2, color='red', label='Podczas wypadku')
    ax1.axvspan(500, 800, alpha=0.2, color='yellow', label='Po wypadku')
    ax1.set_xlabel('Czas [kroki]', fontsize=11)
    ax1.set_ylabel('Przepływ [pojazdy/krok]', fontsize=11)
    ax1.set_title('Przepływ w czasie - wpływ wypadku', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    
    ax2 = axes[0, 1]
    phases = ['Przed', 'Podczas', 'Po']
    avgs = [np.mean(flows_before), np.mean(flows_during), np.mean(flows_after)]
    colors = ['green', 'red', 'orange']
    
    bars = ax2.bar(phases, avgs, color=colors)
    ax2.set_ylabel('Średni przepływ [poj/krok]', fontsize=11)
    ax2.set_title('Średni przepływ w każdej fazie', fontsize=12, fontweight='bold')
    
    for bar, val in zip(bars, avgs):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f'{val:.2f}', ha='center', fontsize=11, fontweight='bold')
    
    ax3 = axes[1, 0]
    ax3.hist(flows_before, bins=20, alpha=0.5, color='green', label='Przed', density=True)
    ax3.hist(flows_during, bins=20, alpha=0.5, color='red', label='Podczas', density=True)
    ax3.hist(flows_after, bins=20, alpha=0.5, color='orange', label='Po', density=True)
    ax3.set_xlabel('Przepływ [poj/krok]', fontsize=11)
    ax3.set_ylabel('Gęstość prawdopodobieństwa', fontsize=11)
    ax3.set_title('Rozkład przepływu w fazach', fontsize=12, fontweight='bold')
    ax3.legend()
    
    ax4 = axes[1, 1]
    ax4.axis('off')
    
    drop_during = (1 - np.mean(flows_during) / np.mean(flows_before)) * 100
    recovery = np.mean(flows_after) / np.mean(flows_before) * 100
    
    stats_text = f"""
    STATYSTYKI WYPADKU

    Lokalizacja:     Pas środkowy
    Długość blokady: {accident_length} komórek

    PRZEPŁYW:

    Przed wypadkiem:  {np.mean(flows_before):.2f} poj/krok
    Podczas wypadku:  {np.mean(flows_during):.2f} poj/krok
    Po wypadku:       {np.mean(flows_after):.2f} poj/krok

    WPŁYW:

    Spadek przepływu: {drop_during:.1f}%
    Odzyskanie:       {recovery:.1f}% normy

    Wniosek: Blokada 1 z 3 pasów
    powoduje spadek przepływu o ~{drop_during:.0f}%,
    a nie o 33% jak by się wydawało!
    """
    
    ax4.text(0.1, 0.95, stats_text, transform=ax4.transAxes, fontsize=11,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    plt.suptitle('Scenariusz 3: Wypadek na autostradzie (blokada środkowego pasa)', 
                 fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\nZapisano: {save_path}")
    plt.show()


def scenario_driver_behavior(save_path: str = "scenario_drivers.png"):
    """Porównanie agresywnych vs spokojnych kierowców (różne p_slow)."""
    print("=" * 60)
    print("SCENARIUSZ: Agresywny vs spokojny kierowca")
    print("=" * 60)
    
    length = 200
    lanes = 2
    density = 0.25
    steps = 600
    
    configs = {
        'Agresywni (p=0.10)': {'p_slow': 0.10},
        'Normalni (p=0.25)': {'p_slow': 0.25},
        'Spokojni (p=0.40)': {'p_slow': 0.40}
    }
    
    results = {}
    spacetime_data = {}
    
    for name, params in configs.items():
        print(f"Symulacja: {name}...")
        
        random.seed(42)
        np.random.seed(42)
        
        sim = create_simulation(length=length, lanes=lanes, density=density, **params)
        
        for _ in range(200):
            sim.step()
        
        sim.stats.cumulative_flow = 0
        sim.stats.step_count = 0
        
        st_data = collect_spacetime_data(sim, steps=300)
        spacetime_data[name] = st_data
        
        flows = collect_flow_data(sim, steps=steps-300)
        
        results[name] = {
            'flows': flows,
            'avg_flow': np.mean(flows),
            'std_flow': np.std(flows)
        }
        
        print(f"  Średni przepływ: {results[name]['avg_flow']:.2f} ± {results[name]['std_flow']:.2f}")
    
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    colors = ['red', 'blue', 'green']
    
    im = None
    for i, (name, data) in enumerate(spacetime_data.items()):
        ax = axes[0, i]
        st = data[:, 0, :]
        st_plot = np.where(st >= 0, st, np.nan)
        
        im = ax.imshow(st_plot.T, aspect='auto', cmap='RdYlGn',
                       origin='lower', vmin=0, vmax=5)
        ax.set_xlabel('Czas [kroki]', fontsize=10)
        ax.set_ylabel('Pozycja', fontsize=10)
        ax.set_title(name, fontsize=11, fontweight='bold')
    
    if im is not None:
        cbar = plt.colorbar(im, ax=axes[0, 2], shrink=0.8, pad=0.02)
        cbar.set_label('Prędkość', fontsize=10)
    
    ax_flow = axes[1, 0]
    for i, (name, data) in enumerate(results.items()):
        window = 20
        smoothed = np.convolve(data['flows'], np.ones(window)/window, mode='valid')
        ax_flow.plot(smoothed, color=colors[i], label=name, linewidth=2, alpha=0.8)
    
    ax_flow.set_xlabel('Czas [kroki]', fontsize=11)
    ax_flow.set_ylabel('Przepływ [poj/krok]', fontsize=11)
    ax_flow.set_title('Przepływ w czasie', fontsize=12, fontweight='bold')
    ax_flow.legend(fontsize=9)
    ax_flow.grid(True, alpha=0.3)
    
    ax_bar = axes[1, 1]
    names = list(results.keys())
    avgs = [results[n]['avg_flow'] for n in names]
    stds = [results[n]['std_flow'] for n in names]
    
    x = range(len(names))
    ax_bar.bar(x, avgs, yerr=stds, color=colors, capsize=5)
    ax_bar.set_xticks(x)
    ax_bar.set_xticklabels(['Agresywni', 'Normalni', 'Spokojni'], fontsize=10)
    ax_bar.set_ylabel('Średni przepływ [poj/krok]', fontsize=11)
    ax_bar.set_title('Porównanie przepływu', fontsize=12, fontweight='bold')
    
    ax_text = axes[1, 2]
    ax_text.axis('off')
    
    conclusions = """
    WNIOSKI

    Parametr p_slow określa jak często
    kierowca losowo hamuje (model NaSch).

    p_slow = 0.10 (agresywni):
    → Mniej hamowań = wyższy przepływ
    → ALE: więcej "fantomowych" korków

    p_slow = 0.25 (normalni):
    → Zbalansowane zachowanie
    → Odpowiada danym z Darmstadt

    p_slow = 0.40 (spokojni):
    → Częste hamowanie = niższy przepływ
    → Bardziej stabilny ruch

    Paradoks: Agresywna jazda może
    ZMNIEJSZYĆ przepływ przez korki!
    """
    
    ax_text.text(0.05, 0.95, conclusions, transform=ax_text.transAxes, fontsize=10,
                 verticalalignment='top', fontfamily='monospace',
                 bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    plt.suptitle('Scenariusz 4: Wpływ stylu jazdy na przepływ (p_slow)', 
                 fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout(rect=[0, 0, 0.98, 1])
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\nZapisano: {save_path}")
    plt.show()


def scenario_speed_limit(save_path: str = "scenario_speedlimit.png"):
    """Wpływ strefy ograniczenia prędkości na przepływ."""
    print("=" * 60)
    print("SCENARIUSZ: Strefa ograniczenia prędkości")
    print("=" * 60)
    
    length = 300
    lanes = 2
    steps = 500
    
    densities = [0.15, 0.25, 0.35]
    results = {'bez_limitu': {}, 'z_limitem': {}}
    
    for density in densities:
        print(f"\nGęstość {density*100:.0f}%:")
        
        print("  Bez ograniczenia...")
        random.seed(42)
        sim1 = create_simulation(length=length, lanes=lanes, density=density)
        
        for _ in range(300):
            sim1.step()
        sim1.stats.cumulative_flow = 0
        sim1.stats.step_count = 0
        
        flows1 = collect_flow_data(sim1, steps)
        results['bez_limitu'][density] = np.mean(flows1)
        
        print("  Z ograniczeniem (strefa wolna)...")
        random.seed(42)
        
        limit_start = length // 3
        limit_length = length // 3
        
        speed_limit = SpeedLimit(
            pos_start=Position(x=limit_start, lane=0),
            pos_end=Position(x=limit_start + limit_length, lane=1),
            v_max=2,
            ticks=0
        )
        
        sim2 = create_simulation(length=length, lanes=lanes, density=density,
                                 speed_limits=[speed_limit])
        
        for _ in range(300):
            sim2.step()
        sim2.stats.cumulative_flow = 0
        sim2.stats.step_count = 0
        
        flows2 = collect_flow_data(sim2, steps)
        results['z_limitem'][density] = np.mean(flows2)
        
        print(f"  Bez limitu: {results['bez_limitu'][density]:.3f}")
        print(f"  Z limitem:  {results['z_limitem'][density]:.3f}")
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    ax1 = axes[0]
    x = np.arange(len(densities))
    width = 0.35
    
    ax1.bar(x - width/2, [results['bez_limitu'][d] for d in densities],
            width, label='Bez ograniczenia', color='red', alpha=0.8)
    ax1.bar(x + width/2, [results['z_limitem'][d] for d in densities],
            width, label='Z ograniczeniem (v≤2)', color='blue', alpha=0.8)
    
    ax1.set_xlabel('Gęstość ruchu', fontsize=11)
    ax1.set_ylabel('Średni przepływ [poj/krok]', fontsize=11)
    ax1.set_title('Wpływ ograniczenia prędkości', fontsize=12, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f'{d*100:.0f}%' for d in densities])
    ax1.legend()
    ax1.grid(True, alpha=0.3, axis='y')
    
    ax2 = axes[1]
    changes = [(results['z_limitem'][d] / results['bez_limitu'][d] - 1) * 100 for d in densities]
    
    colors = ['green' if c > 0 else 'red' for c in changes]
    bars = ax2.bar(x, changes, color=colors, alpha=0.8)
    
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax2.set_xlabel('Gęstość ruchu', fontsize=11)
    ax2.set_ylabel('Zmiana przepływu [%]', fontsize=11)
    ax2.set_title('Efekt ograniczenia prędkości', fontsize=12, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels([f'{d*100:.0f}%' for d in densities])
    
    for bar, val in zip(bars, changes):
        y_pos = bar.get_height() + (1 if val >= 0 else -3)
        ax2.text(bar.get_x() + bar.get_width()/2, y_pos,
                f'{val:+.1f}%', ha='center', fontsize=11, fontweight='bold')
    
    ax2.grid(True, alpha=0.3, axis='y')
    
    plt.suptitle('Scenariusz 5: Wpływ ograniczenia prędkości na przepływ', 
                 fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"\nZapisano: {save_path}")
    plt.show()
    
    print("\nWNIOSKI:")
    for d in densities:
        change = (results['z_limitem'][d] / results['bez_limitu'][d] - 1) * 100
        effect = "POPRAWA" if change > 0 else "SPADEK"
        print(f"  Gęstość {d*100:.0f}%: {effect} o {abs(change):.1f}%")


# Pygame

def pygame_shockwave():
    print("SHOCKWAVE - Naciśnij SPACE aby zatrzymać, S aby dodać przeszkodę")
    sim = create_simulation(length=150, lanes=1, density=0.18)
    for _ in range(100):
        sim.step()
    view = PygameView(simulation=sim, cell_size=25, fps=8, window_width=1400)
    view.run()


def pygame_accident():
    print("ACCIDENT - Wypadek na środkowym pasie")
    length = 150
    accident_pos = length // 2
    accident = SpeedLimit(
        pos_start=Position(x=accident_pos, lane=1),
        pos_end=Position(x=accident_pos + 10, lane=1),
        v_max=0,
        ticks=0
    )
    sim = create_simulation(length=length, lanes=3, density=0.20, speed_limits=[accident])
    for _ in range(100):
        sim.step()
    view = PygameView(simulation=sim, cell_size=25, fps=10, window_width=1400)
    view.run()


def pygame_speedlimit():
    print("SPEEDLIMIT - Strefa ograniczenia (żółta)")
    length = 150
    limit_start = length // 3
    limit_length = length // 3
    speed_limit = SpeedLimit(
        pos_start=Position(x=limit_start, lane=0),
        pos_end=Position(x=limit_start + limit_length, lane=2),
        v_max=2,
        ticks=0
    )
    sim = create_simulation(length=length, lanes=3, density=0.25, speed_limits=[speed_limit])
    for _ in range(100):
        sim.step()
    view = PygameView(simulation=sim, cell_size=25, fps=10, window_width=1400)
    view.run()


def pygame_traffic_lights():
    print("TRAFFIC LIGHTS - Światła co 50 komórek")
    length = 200
    lights = []
    for x in [50, 100, 150]:
        light = SpeedLimit(
            pos_start=Position(x=x, lane=0),
            pos_end=Position(x=x + 2, lane=2),
            v_max=0,
            ticks=30,
            active=True
        )
        lights.append(light)
    sim = create_simulation(length=length, lanes=3, density=0.15, speed_limits=lights)
    view = PygameView(simulation=sim, cell_size=20, fps=10, window_width=1400)
    view.run()


def run_all_scenarios():
    print("\nURUCHAMIANIE WSZYSTKICH SCENARIUSZY\n")
    
    scenario_shockwave()
    print("\n")
    scenario_light_timing()
    print("\n")
    scenario_accident()
    print("\n")
    scenario_driver_behavior()
    print("\n")
    scenario_speed_limit()
    
    print("\nWszystkie scenariusze zakończone!")
    print("Wygenerowane pliki:")
    print("  - scenario_shockwave.png")
    print("  - scenario_lights.png")
    print("  - scenario_accident.png")
    print("  - scenario_drivers.png")
    print("  - scenario_speedlimit.png")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Scenariusze demonstracyjne NaSch")
    parser.add_argument("scenario", nargs='?', default="all",
                        choices=['all', 'shockwave', 'lighttiming', 'accident', 'drivers', 'speedlimit', 'lights'])
    parser.add_argument("--no-show", action="store_true")
    parser.add_argument("--pygame", "-p", action="store_true")
    
    args = parser.parse_args()
    
    if args.pygame:
        pygame_scenarios = {
            'shockwave': pygame_shockwave,
            'accident': pygame_accident,
            'speedlimit': pygame_speedlimit,
            'lights': pygame_traffic_lights,
        }
        
        if args.scenario == 'all':
            print("Tryb pygame: uruchom konkretny scenariusz, np.:")
            print("  python scenarios.py shockwave --pygame")
            return
        
        if args.scenario in ['drivers', 'lighttiming']:
            print(f"Scenariusz '{args.scenario}' nie ma wersji pygame (wymaga porównania)")
            return
            
        pygame_scenarios[args.scenario]()
        return
    
    if args.no_show:
        import matplotlib
        matplotlib.use('Agg')
    
    chart_scenarios = {
        'shockwave': scenario_shockwave,
        'lighttiming': scenario_light_timing,
        'accident': scenario_accident,
        'drivers': scenario_driver_behavior,
        'speedlimit': scenario_speed_limit,
        'all': run_all_scenarios
    }
    
    if args.scenario == 'lights':
        print("Scenariusz 'lights' dostępny tylko w trybie pygame:")
        print("  python scenarios.py lights --pygame")
        return
    
    chart_scenarios[args.scenario]()


if __name__ == "__main__":
    main()
