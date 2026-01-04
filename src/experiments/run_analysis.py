import yaml
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RESULTS_DIR = BASE_DIR / "src" / "experiments" / "results"
PLOTS_DIR = RESULTS_DIR / "plots"
HEATMAPS_DIR = RESULTS_DIR / "heatmaps"

PLOTS_DIR.mkdir(parents=True, exist_ok=True)
HEATMAPS_DIR.mkdir(parents=True, exist_ok=True)

def run(cmd):
    print("▶", " ".join(cmd))
    subprocess.run(cmd, check=True)

with open(BASE_DIR / "src" / "experiments" / "scenarios.yaml") as f:
    config = yaml.safe_load(f)

for sc in config["scenarios"]:
    name = sc["name"]
    analysis = sc.get("analysis", {})

    print(f"\n=== ANALYSIS: {name} ===")

    # Fundamental Diagram
    if analysis.get("fundamental_diagram"):
        out_png = PLOTS_DIR / f"{name}_fundamental.png"

        cmd = [
            "python", str(BASE_DIR / "fundamental_diagram.py"),
            "--png", str(out_png),
            "--no-plot"
        ]

        # Przenieś istotne parametry
        params = sc.get("params", {})
        if "lanes" in params:
            cmd += ["--lanes", str(params["lanes"])]

        run(cmd)

    # Heatmapa
    heatmap_cfg = analysis.get("heatmap", {})
    if heatmap_cfg.get("enabled"):
        out_png = HEATMAPS_DIR / f"{name}_heatmap.png"

        cmd = [
            "python", str(BASE_DIR / "trajectory_heatmap.py"),
            "--heatmap-png", str(out_png),
            "--no-plot"
        ]

        if "density" in heatmap_cfg:
            cmd += ["--density", str(heatmap_cfg["density"])]

        if "steps" in heatmap_cfg:
            cmd += ["--steps", str(heatmap_cfg["steps"])]

        run(cmd)
