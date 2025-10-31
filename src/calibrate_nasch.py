from src.data_loader import load_and_aggregate_exid
from src.data_loader import extract_nasch_parameters

def calibrate_from_exid(data_dir, rec_ids):
    print("Kalibracja NaSch z danych ExiD...")
    tracks_df, _ = load_and_aggregate_exid(data_dir, rec_ids)
    v_max, p = extract_nasch_parameters(tracks_df, None)
    print(f"KALIBRACJA: V_MAX={v_max}, P={p:.3f}")
    return v_max, p

