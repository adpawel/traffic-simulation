import pandas as pd
import numpy as np


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


def extract_nasch_parameters(tracks_df, recording_meta):
    tracks_df['v_NaSch'] = (tracks_df['speed_m_s'] * TIME_STEP_S) / CELL_LENGTH_M
    
    v_max_95 = tracks_df['v_NaSch'].quantile(0.95)
    V_MAX_EMPIRICAL = int(np.ceil(v_max_95))
    
    P_EMPIRICAL = 0.15

    return V_MAX_EMPIRICAL, P_EMPIRICAL     
    

def calibrate_from_exid(data_dir, rec_ids):
    df, _ = load_and_aggregate_exid(data_dir, rec_ids)
    v_max, p = extract_nasch_parameters(df, None)
    return v_max, p
