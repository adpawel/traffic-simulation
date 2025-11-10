import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from src.validate_nasch import validate_nasch_model
from src.visualize_nasch import run_full_visualization
from src.data_loader import read_nasch_params

CALIBRATION_FILE = './data/nasch_calibration_summary.csv'

def main():
    print("=== ETAP 1: KALIBRACJA ===")
    v_max, p = read_nasch_params(CALIBRATION_FILE) 

    print("\n=== ETAP 2: WALIDACJA ===")
    validate_nasch_model(v_max, p)

    print("\n=== ETAP 3: WIZUALIZACJA ===")
    run_full_visualization(v_max, p, density=0.2)

if __name__ == "__main__":
    main()