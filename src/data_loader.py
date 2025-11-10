import pandas as pd
import numpy as np
import os

CELL_LENGTH_M = 7.5
TIME_STEP_S = 1.0

def load_and_aggregate_exid(data_dir, rec_ids):
    """
    Ładuje i łączy dane trajektorii z wielu nagrań ExiD.
    """
    all_tracks = []
    
    for rec_id in rec_ids:
        tracks_path = f'{data_dir}{rec_id}_tracks.csv'
        meta_path = f'{data_dir}{rec_id}_tracksMeta.csv'

        try:
            tracks = pd.read_csv(tracks_path, low_memory=False)
            tracks_meta = pd.read_csv(meta_path, low_memory=False)

            # tracks = tracks[tracks['xVelocity'] > 0]
            required_meta_cols = ['trackId', 'class', 'width'] 
            available_meta_cols = [col for col in required_meta_cols if col in tracks_meta.columns]
            
            tracks = pd.merge(tracks, tracks_meta[available_meta_cols], on='trackId', how='left')
            
            # Oblicz całkowitą prędkość w m/s
            tracks['speed_m_s'] = np.sqrt(tracks['xVelocity']**2 + tracks['yVelocity']**2)
            
            # Zapisz ID nagrania
            tracks['recordingId'] = rec_id
            
            all_tracks.append(tracks)
            print(f"Załadowano nagranie ID: {rec_id}. Pojazdów: {len(tracks['trackId'].unique())}")
            
        except FileNotFoundError:
            print(f"Ostrzeżenie: Nie znaleziono plików dla nagrania ID: {rec_id}. Pomijam.")
        except KeyError as e:
            print(f"Ostrzeżenie: Błąd kolumny w nagraniu ID: {rec_id}: {e}. Pomijam.")

    if not all_tracks:
        return None, None
        
    return pd.concat(all_tracks, ignore_index=True), None


def read_nasch_params(filename):
    """
    Odczytuje parametry V_MAX_NASCH_FINAL i P_FINAL z pliku CSV.
    """
    if not os.path.exists(filename):
        print(f"Błąd: Plik kalibracyjny '{filename}' nie został znaleziony.")
        # Zwracanie domyślnych wartości w razie błędu
        return 10, 0.2

    try:
        df = pd.read_csv(filename)
        
        # Używamy metody .set_index() i .loc[] do wygodnego odczytu wartości
        df = df.set_index('Parameter')
        
        # Wartość V_MAX musi być liczbą całkowitą
        v_max = int(df.loc['V_MAX_NASCH_FINAL', 'Value'])
        
        # Wartość P jest liczbą zmiennoprzecinkową
        p = df.loc['P_FINAL', 'Value']
        
        print(f"✅ Odczytano parametry: V_MAX = {v_max}, P = {p:.3f}")
        return v_max, p
        
    except KeyError as e:
        print(f"Błąd odczytu: Brak oczekiwanej kolumny lub indeksu w pliku. Brakuje: {e}")
        return 10, 0.2
    except Exception as e:
        print(f"Wystąpił nieoczekiwany błąd podczas wczytywania pliku: {e}")
        return 10, 0.2