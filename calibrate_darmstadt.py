#!/usr/bin/env python3
"""Kalibracja modelu NaSch na danych z detektorów pętlowych (Darmstadt)."""

import pandas as pd
import numpy as np
from scipy.optimize import minimize
from pathlib import Path
import sys
import random
from itertools import product
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
import matplotlib.pyplot as plt
import json
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from simulation.simulation import Simulation
from src.config import CELL_LENGTH_M, TIME_STEP_S, MAX_SPEED


@dataclass
class CalibrationConfig:
    csv_path: str = "data/A001/A001_20250101_000000_-_20250201_000000_1min.csv"
    detector_group: str = "D4"
    road_length: int = 133
    
    p_slow_range: Tuple[float, float] = (0.05, 0.45)
    p_change_range: Tuple[float, float] = (0.1, 0.9)
    gap_rear_values: List[int] = None
    reaction_delay_values: List[int] = None
    
    warmup_steps: int = 100
    measurement_steps: int = 300
    seed: int = 42
    densities: List[float] = None
    max_iter: int = 10
    
    def __post_init__(self):
        if self.gap_rear_values is None:
            self.gap_rear_values = [2]
        if self.reaction_delay_values is None:
            self.reaction_delay_values = [0, 1]
        if self.densities is None:
            self.densities = [0.01, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.15,
                              0.20, 0.25, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80]


def load_darmstadt_data(csv_path: str, detector_group: str = "D4") -> pd.DataFrame:
    print(f"Wczytywanie: {csv_path}")
    df = pd.read_csv(csv_path, sep=';', low_memory=False)
    
    flow_cols = [c for c in df.columns if c.startswith(detector_group) and 'Belegungen' in c]
    occ_cols = [c for c in df.columns if c.startswith(detector_group) and 'Verweilzeit' in c]
    
    if not flow_cols:
        available = [c for c in df.columns if 'Belegungen' in c]
        raise ValueError(f"Brak detektorów '{detector_group}'. Dostępne: {available}")
    
    n_lanes = len(flow_cols)
    print(f"  {n_lanes} pasów: {[c.split()[0] for c in flow_cols]}")
    
    result = pd.DataFrame()
    result['timestamp'] = pd.to_datetime(df['Intervallbeginn (Lokalzeit)'], dayfirst=True)
    
    for col in flow_cols + occ_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    result['total_flow'] = df[flow_cols].sum(axis=1)
    result['total_occupancy_ms'] = df[occ_cols].sum(axis=1)
    result['n_lanes'] = n_lanes
    result['occupancy'] = (result['total_occupancy_ms'] / (60000 * n_lanes)).clip(0, 1)
    result['flow_per_lane'] = result['total_flow'] / n_lanes
    
    result = result[(result['total_flow'] > 0) | (result['occupancy'] > 0.001)].copy()
    print(f"  {len(result)} rekordów z danymi")
    
    return result


def compute_real_fundamental_diagram(df: pd.DataFrame, n_bins: int = 15) -> pd.DataFrame:
    df = df[df['total_flow'] > 0].copy()
    
    if len(df) == 0:
        raise ValueError("Brak danych z niezerowym przepływem")
    
    df['occ_bin'] = pd.cut(df['occupancy'], bins=n_bins, labels=False)
    
    fd = df.groupby('occ_bin').agg({
        'occupancy': 'mean',
        'total_flow': ['mean', 'std', 'count'],
        'n_lanes': 'first'
    })
    
    fd.columns = ['occupancy', 'total_flow', 'flow_std', 'count', 'n_lanes']
    fd = fd.dropna(subset=['occupancy', 'total_flow'])
    fd = fd[fd['count'] >= 5]
    fd = fd.reset_index(drop=True)
    
    print(f"  Diagram fundamentalny: {len(fd)} punktów")
    return fd


def occupancy_to_density(occupancy: float, scale: float = 2.0) -> float:
    return min(occupancy * scale, 0.95)


def flow_nasch_to_real(flow_nasch: float, time_step_s: float = TIME_STEP_S,
                       scale: float = 0.5) -> float:
    steps_per_min = 60.0 / time_step_s
    return flow_nasch * steps_per_min * scale


def simulate_fundamental_diagram(
    densities: List[float],
    n_lanes: int,
    road_length: int,
    p_slow: float,
    p_change: float,
    gap_rear: int,
    reaction_delay: int,
    warmup_steps: int = 100,
    measurement_steps: int = 300,
    seed: int = 42
) -> Dict[str, List[float]]:
    flows = []
    
    for i, density in enumerate(densities):
        random.seed(seed + i)
        np.random.seed(seed + i)
        
        try:
            sim = Simulation(
                length=road_length,
                lanes=n_lanes,
                density=density,
                p_slow=p_slow,
                p_change=p_change,
                gap_rear=gap_rear,
                reaction_delay=reaction_delay,
            )
            
            for _ in range(warmup_steps):
                sim.step()
            
            sim.stats.cumulative_flow = 0
            sim.stats.step_count = 0
            
            for _ in range(measurement_steps):
                sim.step()
            
            flows.append(sim.stats.avg_flow)
            
        except Exception as e:
            print(f"  Błąd dla density={density}: {e}")
            flows.append(0.0)
    
    return {'densities': densities, 'flows': flows}


def compute_rmse(real_fd: pd.DataFrame, sim_fd: Dict[str, List[float]],
                 occ_scale: float = 2.0) -> float:
    errors = []
    weights = []
    sim_densities = np.array(sim_fd['densities'])
    sim_flows = np.array(sim_fd['flows'])
    
    for _, row in real_fd.iterrows():
        density = occupancy_to_density(row['occupancy'], occ_scale)
        
        if density <= sim_densities[0]:
            sim_flow_nasch = sim_flows[0]
        elif density >= sim_densities[-1]:
            sim_flow_nasch = sim_flows[-1]
        else:
            sim_flow_nasch = np.interp(density, sim_densities, sim_flows)
        
        sim_flow_real = flow_nasch_to_real(sim_flow_nasch)
        errors.append((row['total_flow'] - sim_flow_real) ** 2)
        weights.append(row['count'])
    
    if not errors:
        return float('inf')
    weights = np.array(weights)
    return np.sqrt(np.average(errors, weights=weights))


def compute_mae(real_fd: pd.DataFrame, sim_fd: Dict[str, List[float]],
                occ_scale: float = 2.0) -> float:
    errors = []
    weights = []
    sim_densities = np.array(sim_fd['densities'])
    sim_flows = np.array(sim_fd['flows'])
    
    for _, row in real_fd.iterrows():
        density = occupancy_to_density(row['occupancy'], occ_scale)
        
        if density <= sim_densities[0]:
            sim_flow_nasch = sim_flows[0]
        elif density >= sim_densities[-1]:
            sim_flow_nasch = sim_flows[-1]
        else:
            sim_flow_nasch = np.interp(density, sim_densities, sim_flows)
        
        sim_flow_real = flow_nasch_to_real(sim_flow_nasch)
        errors.append(abs(row['total_flow'] - sim_flow_real))
        weights.append(row['count'])
    
    if not errors:
        return float('inf')
    return np.average(errors, weights=weights)


class CalibrationObjective:
    def __init__(self, real_fd: pd.DataFrame, n_lanes: int, config: CalibrationConfig,
                 gap_rear: int, reaction_delay: int):
        self.real_fd = real_fd
        self.n_lanes = n_lanes
        self.config = config
        self.gap_rear = gap_rear
        self.reaction_delay = reaction_delay
        self.eval_count = 0
        self.best_rmse = float('inf')
        self.best_params = None
    
    def __call__(self, params: np.ndarray) -> float:
        p_slow, p_change = params
        
        if not (self.config.p_slow_range[0] <= p_slow <= self.config.p_slow_range[1]):
            return float('inf')
        if not (self.config.p_change_range[0] <= p_change <= self.config.p_change_range[1]):
            return float('inf')
        
        self.eval_count += 1
        
        sim_fd = simulate_fundamental_diagram(
            densities=self.config.densities,
            n_lanes=self.n_lanes,
            road_length=self.config.road_length,
            p_slow=p_slow,
            p_change=p_change,
            gap_rear=self.gap_rear,
            reaction_delay=self.reaction_delay,
            warmup_steps=self.config.warmup_steps,
            measurement_steps=self.config.measurement_steps,
            seed=self.config.seed
        )
        
        rmse = compute_rmse(self.real_fd, sim_fd)
        
        if rmse < self.best_rmse:
            self.best_rmse = rmse
            self.best_params = (p_slow, p_change)
        
        return rmse


def optimize_continuous_params(real_fd: pd.DataFrame, n_lanes: int, config: CalibrationConfig,
                               gap_rear: int, reaction_delay: int) -> Tuple[float, float, float]:
    objective = CalibrationObjective(real_fd, n_lanes, config, gap_rear, reaction_delay)
    
    x0 = [
        (config.p_slow_range[0] + config.p_slow_range[1]) / 2,
        (config.p_change_range[0] + config.p_change_range[1]) / 2
    ]
    
    result = minimize(
        objective, x0=x0, method='Nelder-Mead',
        options={'maxiter': config.max_iter, 'xatol': 0.01, 'fatol': 1.0, 'adaptive': True}
    )
    
    print(f"    {objective.eval_count} ewaluacji, "
          f"p_slow={result.x[0]:.3f}, p_change={result.x[1]:.3f}, RMSE={result.fun:.2f}")
    
    return result.x[0], result.x[1], result.fun


def calibrate(config: CalibrationConfig) -> Dict:
    print("=" * 60)
    print("KALIBRACJA MODELU NaSch")
    print("=" * 60)
    
    df = load_darmstadt_data(config.csv_path, config.detector_group)
    n_lanes = int(df['n_lanes'].iloc[0])
    real_fd = compute_real_fundamental_diagram(df)
    
    print(f"\nKonfiguracja: {n_lanes} pasów, {config.road_length} komórek")
    
    best_result = {
        'rmse': float('inf'), 'mae': float('inf'),
        'p_slow': None, 'p_change': None, 'gap_rear': None, 'reaction_delay': None
    }
    
    all_results = []
    combinations = list(product(config.gap_rear_values, config.reaction_delay_values))
    
    print(f"\nTestowanie {len(combinations)} kombinacji...")
    print("-" * 60)
    
    for i, (gap_rear, reaction_delay) in enumerate(combinations, 1):
        print(f"[{i}/{len(combinations)}] gap_rear={gap_rear}, reaction_delay={reaction_delay}")
        
        p_slow, p_change, rmse = optimize_continuous_params(
            real_fd, n_lanes, config, gap_rear, reaction_delay
        )
        
        result = {
            'p_slow': p_slow, 'p_change': p_change,
            'gap_rear': gap_rear, 'reaction_delay': reaction_delay, 'rmse': rmse
        }
        all_results.append(result)
        
        if rmse < best_result['rmse']:
            best_result.update(result)
            print(f"    ★ Najlepszy!")
    
    sim_fd_best = simulate_fundamental_diagram(
        densities=config.densities, n_lanes=n_lanes, road_length=config.road_length,
        p_slow=best_result['p_slow'], p_change=best_result['p_change'],
        gap_rear=best_result['gap_rear'], reaction_delay=best_result['reaction_delay'],
        warmup_steps=config.warmup_steps, measurement_steps=config.measurement_steps * 2,
        seed=config.seed
    )
    
    best_result['mae'] = compute_mae(real_fd, sim_fd_best)
    best_result['sim_fd'] = sim_fd_best
    best_result['real_fd'] = real_fd
    best_result['n_lanes'] = n_lanes
    best_result['all_results'] = all_results
    
    print("\n" + "=" * 60)
    print("WYNIKI:")
    print("=" * 60)
    print(f"  p_slow:         {best_result['p_slow']:.4f}")
    print(f"  p_change:       {best_result['p_change']:.4f}")
    print(f"  gap_rear:       {best_result['gap_rear']}")
    print(f"  reaction_delay: {best_result['reaction_delay']}")
    print(f"\n  RMSE: {best_result['rmse']:.2f} poj/min")
    print(f"  MAE:  {best_result['mae']:.2f} poj/min")
    print("=" * 60)
    
    return best_result


def plot_results(result: Dict, save_path: Optional[str] = None, show: bool = True) -> None:
    real_fd = result['real_fd']
    sim_fd = result['sim_fd']
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    ax1 = axes[0]
    ax1.errorbar(
        real_fd['occupancy'] * 100, real_fd['total_flow'],
        yerr=real_fd['flow_std'].fillna(0),
        fmt='o', color='blue', alpha=0.7, label='Dane rzeczywiste (Darmstadt)', capsize=3
    )
    
    sim_densities = np.array(sim_fd['densities'])
    sim_flows_real = [flow_nasch_to_real(f) for f in sim_fd['flows']]
    sim_occupancies = sim_densities / 2.0 * 100
    
    ax1.plot(sim_occupancies, sim_flows_real, 's-', color='red', alpha=0.8,
             markersize=6, label='Model NaSch (skalibrowany)')
    
    ax1.set_xlabel('Zajętość detektora [%]', fontsize=11)
    ax1.set_ylabel('Przepływ [pojazdy/min]', fontsize=11)
    ax1.set_title('Diagram fundamentalny', fontsize=12, fontweight='bold')
    ax1.legend(fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(0, None)
    ax1.set_ylim(0, None)
    
    ax2 = axes[1]
    ax2.axis('off')
    
    text = (
        f"SKALIBROWANE PARAMETRY\n"
        f"{'─' * 30}\n\n"
        f"p_slow:           {result['p_slow']:.4f}\n"
        f"p_change:         {result['p_change']:.4f}\n"
        f"gap_rear:         {result['gap_rear']}\n"
        f"reaction_delay:   {result['reaction_delay']}\n\n"
        f"{'─' * 30}\n"
        f"METRYKI\n"
        f"{'─' * 30}\n\n"
        f"RMSE:  {result['rmse']:.2f} poj/min\n"
        f"MAE:   {result['mae']:.2f} poj/min\n\n"
        f"{'─' * 30}\n"
        f"DANE\n"
        f"{'─' * 30}\n\n"
        f"Pasy:     {result['n_lanes']}\n"
        f"Detektor: {result.get('detector_group', 'D4')}\n"
    )
    
    ax2.text(0.1, 0.9, text, transform=ax2.transAxes, fontsize=11,
             verticalalignment='top', fontfamily='monospace',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        print(f"\nWykres: {save_path}")
    
    if show:
        plt.show()


def save_json(result: Dict, path: str) -> None:
    output = {
        'timestamp': datetime.now().isoformat(),
        'params': {
            'p_slow': result['p_slow'],
            'p_change': result['p_change'],
            'gap_rear': result['gap_rear'],
            'reaction_delay': result['reaction_delay'],
        },
        'metrics': {'rmse': result['rmse'], 'mae': result['mae']},
        'config': {'n_lanes': result['n_lanes'], 'detector': result.get('detector_group', 'D4')},
        'all_results': result.get('all_results', [])
    }
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"JSON: {path}")


def print_config_suggestion(result: Dict) -> None:
    print("\nSugerowana aktualizacja config.py:")
    print(f"""
P_SLOW = {result['p_slow']:.4f}
P_CHANGE = {result['p_change']:.4f}
GAP_REAR = {result['gap_rear']}
REACTION_DELAY = {result['reaction_delay']}
""")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Kalibracja modelu NaSch")
    parser.add_argument("--csv", type=str,
                        default="data/A001/A001_20250101_000000_-_20250201_000000_1min.csv")
    parser.add_argument("--detector", type=str, default="D4")
    parser.add_argument("--output-plot", type=str, default="calibration_result.png")
    parser.add_argument("--output-json", type=str, default="calibration_result.json")
    parser.add_argument("--no-plot", action="store_true")
    
    args = parser.parse_args()
    
    config = CalibrationConfig(csv_path=args.csv, detector_group=args.detector)
    
    result = calibrate(config)
    result['detector_group'] = args.detector
    
    save_json(result, args.output_json)
    plot_results(result, save_path=args.output_plot, show=not args.no_plot)
    print_config_suggestion(result)
    
    return result


if __name__ == "__main__":
    main()
