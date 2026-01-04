import pandas as pd
from pathlib import Path

df = pd.read_csv("src/experiments/results/raw/baseline.csv")

summary = df.groupby(["density"]).agg(
    flow_mean=("flow", "mean"),
)

summary.to_csv("src/experiments/results/summary/baseline_summary.csv")

import pandas as pd
from pathlib import Path

RAW_DIR = Path("src/experiments/results/raw")
OUT_DIR = Path("src/experiments/results/summary")
OUT_DIR.mkdir(parents=True, exist_ok=True)

csv_path = RAW_DIR / "density_sweep.csv"
df = pd.read_csv(csv_path)

summary = (
    df
    .groupby("density")
    .agg(
        flow_mean=("flow", "mean"),
        flow_std=("flow", "std"),
    )
    .reset_index()
)

out_path = OUT_DIR / "density_sweep_summary.csv"
summary.to_csv(out_path, index=False)

print("Zapisano:", out_path)
print(summary)
