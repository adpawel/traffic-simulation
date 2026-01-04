import yaml
import subprocess
import csv
import itertools
import re
from pathlib import Path

RESULTS_DIR = Path("src/experiments/results/raw")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

METRIC_RE = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)=([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)")

def run(cmd):
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )
    combined = (result.stdout or "") + "\n" + (result.stderr or "")
    return result.returncode, combined

def parse_metrics_anywhere(text):
    metrics = {}
    for m in METRIC_RE.finditer(text):
        k = m.group(1)
        v = float(m.group(2))
        metrics[k] = v
    return metrics

with open("src/experiments/scenarios.yaml", encoding="utf-8") as f:
    config = yaml.safe_load(f)

global_params = config["global"]
scenarios = config["scenarios"]

for sc in scenarios:
    name = sc["name"]
    base_params = sc.get("params", {})
    sweep = sc.get("sweep", {})

    keys, values = zip(*sweep.items()) if sweep else ([], [])
    combinations = itertools.product(*values) if values else [()]

    csv_file = RESULTS_DIR / f"{name}.csv"
    if csv_file.exists():
        csv_file.unlink()

    wrote_header = False

    for combo in combinations:
        sweep_params = dict(zip(keys, combo))
        params = {**base_params, **sweep_params}

        for seed in global_params["seeds"]:
            cmd = ["python", "main.py"]

            for k, v in params.items():
                cmd += [f"--{k.replace('_','-')}", str(v)]

            cmd += [
                "--steps", str(global_params["steps"]),
                "--seed", str(seed),
                "--no-gui"
            ]

            rc, output = run(cmd)

            if rc != 0:
                tail = "\n".join(output.splitlines()[-40:])
                raise RuntimeError(
                    f"main.py zakończył się kodem {rc} dla {name} {params} seed={seed}\n"
                    f"--- ostatnie linie outputu ---\n{tail}\n"
                )

            metrics = parse_metrics_anywhere(output)

            if not metrics:
                tail = "\n".join(output.splitlines()[-40:])
                print("\n[DEBUG] Nie znaleziono żadnych metryk key=value w outputcie!")
                print("[DEBUG] Ostatnie linie outputu, które widzi runner:")
                print(tail)
                print("[DEBUG] Koniec.\n")

            if "flow" not in metrics:
                pass

            with open(csv_file, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                if not wrote_header:
                    writer.writerow(
                        ["scenario", "seed"] +
                        list(params.keys()) +
                        sorted(metrics.keys())
                    )
                    wrote_header = True

                writer.writerow(
                    [name, seed] +
                    list(params.values()) +
                    [metrics[k] for k in sorted(metrics.keys())]
                )

            print(f"✔ {name} {params} seed={seed} metrics={metrics}")
