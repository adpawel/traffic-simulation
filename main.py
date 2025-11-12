import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
from src.validate_nasch import validate_nasch_model
from src.visualize_nasch import run_full_visualization
from src.data_loader import read_nasch_params
from src.config import DENSITY, LANES

CALIBRATION_FILE = './data/nasch_calibration_summary.csv'

def main():
    print("=== POZYSKANIE PARAMETRŌw ===")
    v_max, p = read_nasch_params(CALIBRATION_FILE) 

    if LANES == 1:
        validate_nasch_model(v_max, p)

    print("\n=== SYMULACJA ===")
    run_full_visualization(v_max, p, density=DENSITY)

if __name__ == "__main__":
    main()