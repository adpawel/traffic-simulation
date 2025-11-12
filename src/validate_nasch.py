import matplotlib.pyplot as plt
import numpy as np
import pandas as pd # <-- DODANO
from src.nasch_core import run_simulation
from src.data_loader import TIME_STEP_S, CELL_LENGTH_M
from src.nasch_core import L

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
    
    # Krok 1: Definicja parametrów eksperymentu
    densities_sim = np.linspace(0.01, 1.0, 30) # 30 punktów od 1% do 100%
    
    # Stałe czasowe i pomiarowe
    STEPS_WARMUP = 1000
    STEPS_MEASURE = 5000
    SECONDS_PER_HOUR = 3600
    
    Q_values = []
    K_values = []
    
    # Krok 2: Uruchomienie symulacji dla każdej gęstości (K)
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

        print(f"Gęstość (K={initial_density:.2f}) -> Przepływ Q: {flow_per_hour:.0f} poj/h")


    # Krok 3: Zapis wyników i zwrócenie danych
    
    # Utworzenie DataFrame z wynikami
    results_df = pd.DataFrame({
        'Density_K_poj_km': K_values,
        'Flow_Q_poj_h': Q_values,
        'V_max_sim': v_max,
        'P_sim': p
    })
    
    # Zapis do pliku CSV
    try:
        results_df.to_csv(output_filename, index=False)
        print(f"\n✅ Zapisano wyniki symulacji do pliku: **{output_filename}**")
    except Exception as e:
        print(f"\n⚠️ Błąd podczas zapisu do CSV: {e}")

    
    # Krok 4: Rysowanie Diagramu (Przywrócony kod)
    print("\n📈 Generowanie wykresu Q vs K...")
    plt.figure(figsize=(10, 6))
    plt.scatter(K_values, Q_values, label=f'Symulacja NaSch (Vmax={v_max}, P={p:.3f})', c='blue', alpha=0.7)
    
    # Dodanie teoretycznej linii zatora (Q=0 przy K_max)
    K_max = 1.0 / cell_length * 1000 # Maksymalna gęstość w poj/km
    
    # Poprawiony teoretyczny wzór Q_max (nie jest potrzebny, ale poprawnie pokazuje linię zatora)
    plt.plot([0, K_max], [0, 0], 'r--', label='Teoretyczny zator') 
    
    plt.xlabel('Gęstość K [pojazdy/km]')
    plt.ylabel('Przepływ Q [pojazdy/h]')
    plt.title('Diagram Fundamentalny (Q vs K) - Model NaSch')
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.show() # Wyświetlenie wykresu
    
    return K_values, Q_values


# --- Zaktualizowana Walidacja/Użycie ---

def validate_nasch_model(v_max, p):
    print("Walidacja modelu NaSch...")
    
    # Używamy stałej CELL_LENGTH_M i L zaimportowanych z modułów
    generate_fundamental_diagram(
        v_max=v_max, 
        p=p, 
        length=L, 
        cell_length=CELL_LENGTH_M,
        output_filename=f'./data/nasch_sim_K_Q.csv'
    )

