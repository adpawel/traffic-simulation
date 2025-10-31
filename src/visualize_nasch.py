from src.nasch_core import run_pygame_simulation, run_simulation, history_to_array, plot_heatmap

def run_full_visualization(v_max, p, density):
    print("Uruchamianie wizualizacji...")
    run_pygame_simulation(initial_density=density, v_max=v_max, p=p, steps_per_second=10)
    history, _ = run_simulation(steps=300, length=133, density=density, v_max=v_max, p=p)
    arr = history_to_array(history)
    plot_heatmap(arr, v_max, p)
