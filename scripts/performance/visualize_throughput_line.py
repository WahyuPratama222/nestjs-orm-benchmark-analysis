import pandas as pd
import matplotlib.pyplot as plt

from config import PERF_DATA, FIGURES_DIR

# Load dataset
df = pd.read_csv(PERF_DATA)

# Keep valid samples only
df = df[df["valid"] == 1]

# Mean and standard deviation per scenario
summary = (
    df.groupby(["operation", "vus", "orm"])["throughput_rps"]
    .agg(["mean", "std"])
    .reset_index()
)

operations = ["read", "create", "join", "groupby"]
orms = ["prisma", "typeorm", "drizzle", "raw"]

titles = {
    "read": "Read",
    "create": "Create",
    "join": "Join",
    "groupby": "Group By"
}

# 2x2 figure
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
axes = axes.flatten()

for ax, operation in zip(axes, operations):
    operation_data = summary[
        summary["operation"] == operation
    ]

    for orm in orms:
        orm_data = operation_data[
            operation_data["orm"] == orm
        ].sort_values("vus")

        ax.errorbar(
            orm_data["vus"],
            orm_data["mean"],
            yerr=orm_data["std"],
            marker="o",
            markersize=5,
            linewidth=1.8,
            capsize=4,
            label=orm.upper()
        )

    ax.set_title(titles[operation])
    ax.set_xlabel("Concurrent Users (VU)")
    ax.set_ylabel("Throughput (req/s)")
    ax.set_xticks([10, 50, 100])
    ax.grid(True, linestyle="--", alpha=0.4)

# Shared legend
handles, labels = axes[0].get_legend_handles_labels()

fig.legend(
    handles,
    labels,
    loc="upper center",
    ncol=4,
    frameon=False,
    bbox_to_anchor=(0.5, 1.0)
)

fig.suptitle(
    "Throughput Comparison Across Data Access Approaches",
    fontsize=14,
    fontweight="bold",
    y=1.05
)

plt.tight_layout()

# Save figure
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

output_file = FIGURES_DIR / "throughput_line.png"

plt.savefig(
    output_file,
    dpi=300,
    bbox_inches="tight"
)

print(f"Figure saved: {output_file}")

plt.show()