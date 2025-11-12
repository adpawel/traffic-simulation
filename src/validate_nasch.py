import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from src.nasch_core import run_simulation
from src.config import TIME_STEP_S, CELL_LENGTH_M, L

# Stałe czasowe i pomiarowe
STEPS_WARMUP = 1000
STEPS_MEASURE = 5000
SECONDS_PER_HOUR = 3600
    

def generate_fundamental_diagram(v_max, p, length, cell_length, output_filename='nasch_simulation_results.csv'):
    """
    Generuje punkty (K, Q) do narysowania Diagramu Fundamentalnego
    poprzez uruchomienie symulacji NaSch dla różnych gęstości, zapisuje wyniki do CSV i rysuje wykres.
    
    Args:
        v_max (int): Maksymalna prędkość NaSch.
        p (float): Prawdopodobieństwo losowego spowolnienia.
        length (int): Długość drogi w komórkach (L).
        cell_length (float): Długość jednej komórki w metrach.
        output_filename (str): Nazwa pliku CSV do zapisu.
        
    Returns:
        tuple: (Lista gęstości [poj/km], Lista przepływów [poj/h])
    """
    print("--- Generowanie Punktów Symulacji (Q vs K) ---")
    
    densities_sim = np.linspace(0.01, 1.0, 30) # 30 punktów od 1% do 100%
    
    Q_values = []
    K_values = []
    
    # Uruchomienie symulacji dla każdej gęstości (K)
    for initial_density in densities_sim:
        
        total_steps = STEPS_WARMUP + STEPS_MEASURE
        _, flows_raw = run_simulation(
            steps=total_steps, 
            length=length, 
            density=initial_density, 
            v_max=v_max, 
            p=p
        )
        
        # 1. Pomiń okres przejściowy (rozgrzewki)
        measured_flows = flows_raw[STEPS_WARMUP:]
        
        # 2. Oblicz Przepływ (Q) [pojazdy/godzinę]
        total_flow_count = sum(measured_flows)
        total_time_s = STEPS_MEASURE * TIME_STEP_S
        
        flow_per_s = total_flow_count / total_time_s
        flow_per_hour = flow_per_s * SECONDS_PER_HOUR
        
        # 3. Oblicz Gęstość (K) [pojazdy/km]
        density_per_m = initial_density / cell_length
        density_per_km = density_per_m * 1000
        
        Q_values.append(flow_per_hour)
        K_values.append(density_per_km)

    results_df = pd.DataFrame({
        'Density_K_poj_km': K_values,
        'Flow_Q_poj_h': Q_values,
        'V_max_sim': v_max,
        'P_sim': p
    })
    
    try:
        results_df.to_csv(output_filename, index=False)
        print(f"\nZapisano wyniki symulacji do pliku: **{output_filename}**")
    except Exception as e:
        print(f"\nBłąd podczas zapisu do CSV: {e}")

    
    print("\nGenerowanie wykresu Q vs K...")
    plt.figure(figsize=(10, 6))
    plt.scatter(K_values, Q_values, label=f'Symulacja NaSch (Vmax={v_max}, P={p:.3f})', c='blue', alpha=0.7)
    
    
    plt.xlabel('Gęstość K [pojazdy/km]')
    plt.ylabel('Przepływ Q [pojazdy/h]')
    plt.title('Diagram Fundamentalny (Q vs K) - Model NaSch')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.show() 
    
    return K_values, Q_values


def validate_nasch_model(v_max, p):
    print("Walidacja modelu NaSch...")
    
    generate_fundamental_diagram(
        v_max=v_max, 
        p=p, 
        length=L, 
        cell_length=CELL_LENGTH_M,
        output_filename=f'./data/nasch_sim_K_Q.csv'
    )