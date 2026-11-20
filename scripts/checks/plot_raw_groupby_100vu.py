import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

from config import PERF_DATA, FIGURES_DIR

# Load dataset
df = pd.read_csv(PERF_DATA)

# Filter: Raw SQL - Group By - 100 VU
data = df[
    (df["orm"] == "raw") &
    (df["operation"] == "groupby") &
    (df["vus"] == 100) &
    (df["valid"] == 1)
].copy()

data = data.sort_values("repetition")

if len(data) != 10:
    raise ValueError(f"Found {len(data)} samples, expected 10.")

# Bar positions
x = np.arange(len(data))
width = 0.65

# Two side-by-side charts
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

# P95 Latency
axes[0].bar(x, data["p95_ms"], width)
axes[0].set_title("P95 Latency")
axes[0].set_ylabel("Latency (ms)")
axes[0].set_xlabel("Repetition")
axes[0].set_xticks(x)
axes[0].set_xticklabels(data["repetition"])
axes[0].grid(axis="y", linestyle="--", alpha=0.5)
axes[0].set_axisbelow(True)

# Throughput
axes[1].bar(x, data["throughput_rps"], width)
axes[1].set_title("Throughput")
axes[1].set_ylabel("Throughput (req/s)")
axes[1].set_xlabel("Repetition")
axes[1].set_xticks(x)
axes[1].set_xticklabels(data["repetition"])
axes[1].grid(axis="y", linestyle="--", alpha=0.5)
axes[1].set_axisbelow(True)

fig.suptitle("Raw SQL Group By (100 VU)", fontsize=13)
plt.tight_layout()

FIGURES_DIR.mkdir(parents=True, exist_ok=True)

output_file = FIGURES_DIR / "raw_groupby_100vu.png"

plt.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight"
)

print(f"Figure saved: {output_file}")

plt.show()