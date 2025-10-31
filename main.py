import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from src.calibrate_nasch import calibrate_from_exid
from src.validate_nasch import validate_nasch_model
from src.visualize_nasch import run_full_visualization

def main():
    print("=== ETAP 1: KALIBRACJA ===")
    v_max, p = calibrate_from_exid(data_dir="data/data/", rec_ids=[f"{i:02}" for i in range(8)])

    print("\n=== ETAP 2: WALIDACJA ===")
    validate_nasch_model(v_max, p)

    print("\n=== ETAP 3: WIZUALIZACJA ===")
    run_full_visualization(v_max, p, density=0.2)

if __name__ == "__main__":
    main()