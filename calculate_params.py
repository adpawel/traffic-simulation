import pandas as pd
import numpy as np
from src.data_loader import CELL_LENGTH_M, TIME_STEP_S, load_and_aggregate_exid

def calculate_nasch_params(df_recording, cell_length_m, time_step_s):
    """
    Oblicza parametry v_max i p dla wszystkich danych z jednego nagrania
    (niezależnie od liczby pasów).
    """
    if df_recording.empty:
        return {'v_max': None, 'p_final': None, 'count': 0}

    # Krok 1: Konwersja prędkości na jednostki NaSch
    df_recording['v_nasch'] = (df_recording['lonVelocity'] * time_step_s) / cell_length_m
    
    # --- Wyznaczenie v_max ---
    # 95. percentyl prędkości w m/s
    v_max_ms = df_recording['lonVelocity'].quantile(0.95)
    v_max_kmh = v_max_ms * 3.6
    
    # Przeliczenie 95. percentyla na jednostki NaSch i zaokrąglenie w górę
    v_max_nasch = int(np.ceil((v_max_ms * time_step_s) / cell_length_m))

    # --- Wyznaczenie p ---
    # 1. Estymacja na podstawie zmienności
    mean_speed = df_recording['lonVelocity'].mean()
    std_speed = df_recording['lonVelocity'].std()
    cv = std_speed / mean_speed if mean_speed > 0 else 0
    p_estimated = np.clip(cv * 0.5, 0.05, 0.5)

    # 2. Estymacja na podstawie hamowania (praktyczne p)
    ACCEL_THRESHOLD = -0.2
    deceleration_events = (df_recording['lonAcceleration'] < ACCEL_THRESHOLD).sum()
    total_events = len(df_recording) 
    p_from_decel = deceleration_events / total_events if total_events > 0 else 0.15

    # 3. Finalne p (uśrednione)
    p_final = (p_estimated + p_from_decel) / 2
    p_final = np.clip(p_final, 0.05, 0.5)
    
    return {
        'v_max': v_max_nasch,
        'p_final': p_final,
        'v_max_kmh': v_max_kmh,
        'p_estimated': p_estimated,
        'p_from_decel': p_from_decel,
        'count': len(df_recording)
    }

# --- Główna pętla i agregacja ---

# Wczytywanie i agregacja danych
# Zakładamy, że `load_and_aggregate_exid` działa poprawnie
tracks_df, _ = load_and_aggregate_exid(data_dir="data/data/", rec_ids=[f"{i:02}" for i in range(38)])
results = []
# Używamy tylko nagrań, które mają dane
unique_recording_ids = tracks_df['recordingId'].unique()

print(f"Rozpoczynanie kalibracji dla {len(unique_recording_ids)} nagrań...")
print(f"Użyte stałe: CELL_LENGTH_M = {CELL_LENGTH_M} m, TIME_STEP_S = {TIME_STEP_S} s")

for rec_id in sorted(unique_recording_ids):
    # Filtrowanie danych tylko dla bieżącego nagrania
    df_rec = tracks_df[tracks_df['recordingId'] == rec_id].copy()
    
    # Wywołanie funkcji kalibracyjnej
    params = calculate_nasch_params(df_rec, CELL_LENGTH_M, TIME_STEP_S)
    params['recordingId'] = rec_id
    results.append(params)
    
    # Pomiń wyświetlanie, jeśli nie ma danych (choć `unique_recording_ids` to wyklucza)
    if params['v_max'] is not None:
        print(f"Nagranie {rec_id} ({params['count']} pom.): v_max={params['v_max']} ({params['v_max_kmh']:.0f} km/h), p={params['p_final']:.3f}")

# Zbieranie wyników do końcowego DataFrame
calibration_df = pd.DataFrame(results)

# Usuwanie wierszy z brakującymi danymi (jeśli jakieś się pojawiłyby)
calibration_df.dropna(subset=['v_max', 'p_final'], inplace=True)

print("\n--- Podsumowanie Kalibracji ---")
print(calibration_df[['recordingId', 'v_max', 'p_final', 'v_max_kmh', 'count']])

# --- Obliczanie i wyświetlanie średnich wartości końcowych ---

if not calibration_df.empty:
    # Obliczanie średnich (ważonych, jeśli 'count' miałby duże różnice)
    # Dla uproszczenia (NaSch jest modelem dyskretnym, ale średnia daje sens estymacji)
    
    # Średnie są używane jako finalne parametry modelu
    mean_v_max_nasch = calibration_df['v_max'].mean()
    mean_v_max_kmh = calibration_df['v_max_kmh'].mean()
    mean_p = calibration_df['p_final'].mean()
    
    # Zapis finalnych wartości do zmiennych
    P_FINAL = mean_p
    V_MAX_NASCH_FINAL = int(np.ceil(mean_v_max_nasch))
    V_MAX_KMH_FINAL = mean_v_max_kmh
    
    print("\n==============================================")
    print("FINALNE WYZNACZONE PARAMETRY KALIBRACYJNE")
    print("==============================================")
    print(f"Średnia v_max (NaSch, zaokrąglona):  V_MAX = {V_MAX_NASCH_FINAL} komórek/krok")
    print(f"Średnia v_max (wartość ciągła):      v_max_avg = {mean_v_max_nasch:.2f}")
    print(f"Średnia v_max (km/h):                v_max_kmh = {V_MAX_KMH_FINAL:.1f} km/h")
    print(f"Średnie p (prawdopodobieństwo):      P = {P_FINAL:.3f}")
    print("==============================================")
    
    # --- ZAPIS DO PLIKU CSV ---
    final_params_summary = pd.DataFrame({
        'Parameter': ['V_MAX_NASCH_FINAL', 'P_FINAL'],
        'Value': [V_MAX_NASCH_FINAL, P_FINAL]
    })
    
    # Zapis do pliku
    final_params_summary.to_csv('./data/nasch_calibration_summary.csv', index=False)
else:
    print("\nBrak danych do obliczenia średnich parametrów.")