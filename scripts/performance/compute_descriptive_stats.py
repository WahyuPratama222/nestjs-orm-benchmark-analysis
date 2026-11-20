import pandas as pd

from config import PERF_DATA, DESCRIPTIVE_DIR

# Load dataset
df = pd.read_csv(PERF_DATA)

# Keep valid samples only
df = df[df["valid"] == 1].copy()

# Metrics to summarize and their output file names
metrics = {
    "p95_ms": "p95_descriptive.csv",
    "throughput_rps": "throughput_descriptive.csv"
}

group_columns = ["operation", "vus", "orm"]

DESCRIPTIVE_DIR.mkdir(parents=True, exist_ok=True)

for metric, filename in metrics.items():

    summary = (
        df.groupby(group_columns)[metric]
        .agg(
            n="count",
            mean="mean",
            median="median",
            std="std"
        )
        .reset_index()
    )

    # Sort so the table is easy to read
    operation_order = ["read", "create", "join", "groupby"]
    orm_order = ["prisma", "typeorm", "drizzle", "raw"]

    summary["operation"] = pd.Categorical(
        summary["operation"],
        categories=operation_order,
        ordered=True
    )

    summary["orm"] = pd.Categorical(
        summary["orm"],
        categories=orm_order,
        ordered=True
    )

    summary = summary.sort_values(
        ["operation", "vus", "orm"]
    )

    # Round numeric columns
    numeric_columns = ["mean", "median", "std"]
    summary[numeric_columns] = summary[numeric_columns].round(2)

    # Save CSV
    summary.to_csv(
        DESCRIPTIVE_DIR / filename,
        index=False
    )

    print(f"\n=== {metric} ===")
    print(summary.to_string(index=False))

print(f"\nDescriptive statistics saved to: {DESCRIPTIVE_DIR}")