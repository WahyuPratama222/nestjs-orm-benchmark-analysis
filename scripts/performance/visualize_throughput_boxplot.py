import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from config import PERF_DATA, FIGURES_DIR

# Load dataset
df = pd.read_csv(PERF_DATA)
df = df[df["valid"] == 1]

# Configuration
metric = "throughput_rps"
metric_label = "Throughput (req/s)"
prefix = "throughput_boxplot"

operations = [
    ["read", "create"],
    ["join", "groupby"]
]

orms = ["prisma", "typeorm", "drizzle", "raw"]
vus_levels = [10, 50, 100]

titles = {
    "read": "Read",
    "create": "Create",
    "join": "Join",
    "groupby": "Group By"
}

colors = plt.rcParams["axes.prop_cycle"].by_key()["color"][:4]

FIGURES_DIR.mkdir(parents=True, exist_ok=True)

for operation_group in operations:

    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    for ax, operation in zip(axes, operation_group):

        operation_data = df[df["operation"] == operation]

        positions = []
        data = []
        box_colors = []

        for i, vus in enumerate(vus_levels):
            for j, orm in enumerate(orms):

                values = operation_data[
                    (operation_data["vus"] == vus) &
                    (operation_data["orm"] == orm)
                ][metric].dropna().values

                positions.append(i * 5 + j)
                data.append(values)
                box_colors.append(colors[j])

        bp = ax.boxplot(
            data,
            positions=positions,
            widths=0.8,
            patch_artist=True,
            showfliers=True,
            medianprops=dict(color="black", linewidth=1.5),
            whiskerprops=dict(linewidth=1.2),
            capprops=dict(linewidth=1.2)
        )

        for box, color in zip(bp["boxes"], box_colors):
            box.set_facecolor(color)
            box.set_alpha(0.65)

        ax.set_title(titles[operation], fontsize=13, fontweight="bold")
        ax.set_xlabel("Concurrent Users (VU)")
        ax.set_ylabel(metric_label)

        ax.set_xticks([1.5, 6.5, 11.5])
        ax.set_xticklabels(vus_levels)
        ax.grid(axis="y", linestyle="--", alpha=0.4)

    # Shared legend
    legend_items = [
        Patch(facecolor=colors[i], alpha=0.65, label=orm.upper())
        for i, orm in enumerate(orms)
    ]

    fig.legend(
        handles=legend_items,
        loc="upper center",
        ncol=4,
        frameon=False,
        bbox_to_anchor=(0.5, 1.0)
    )

    fig.suptitle(
        f"{metric_label} Distribution Comparison",
        fontsize=14,
        fontweight="bold",
        y=1.06
    )

    plt.tight_layout()

    # e.g. throughput_boxplot_read_create.png
    filename = f"{prefix}_{'_'.join(operation_group)}.png"

    plt.savefig(
        FIGURES_DIR / filename,
        dpi=300,
        bbox_inches="tight"
    )

    print(f"Figure saved: {FIGURES_DIR / filename}")

    plt.show()
    plt.close()