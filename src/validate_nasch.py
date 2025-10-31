from src.nasch_core import run_simulation

def validate_nasch_model(v_max, p):
    print("Walidacja modelu NaSch...")
    history, flows = run_simulation(steps=300, length=133, density=0.25, v_max=v_max, p=p)
    print(f"Średni przepływ: {sum(flows)/len(flows):.2f} veh/s")
