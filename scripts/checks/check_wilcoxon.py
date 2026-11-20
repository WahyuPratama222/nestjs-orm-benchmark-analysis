import pandas as pd
from scipy.stats import wilcoxon

from config import PERF_DATA

df = pd.read_csv(PERF_DATA)

data = df[
    (df["operation"] == "read") &
    (df["vus"] == 10) &
    (df["valid"] == 1)
]

orms = ["prisma", "typeorm", "drizzle", "raw"]

# Sort by repetition so the samples stay paired
samples = {}

for orm in orms:
    values = (
        data[data["orm"] == orm]
        .sort_values("repetition")["p95_ms"]
        .to_numpy()
    )

    if len(values) != 10:
        raise ValueError(f"Sample count for {orm} is not 10")

    samples[orm] = values

# Six Wilcoxon pairs
pairs = [
    ("prisma", "typeorm"),
    ("prisma", "drizzle"),
    ("prisma", "raw"),
    ("typeorm", "drizzle"),
    ("typeorm", "raw"),
    ("drizzle", "raw"),
]

print("Wilcoxon Signed-Rank Test - P95 Read 10 VU")
print("-" * 65)

for orm_a, orm_b in pairs:
    a = samples[orm_a]
    b = samples[orm_b]

    result = wilcoxon(
        a,
        b,
        alternative="two-sided",
        zero_method="wilcox",
        method="auto"
    )

    mean_diff = (a - b).mean()

    print(f"{orm_a.upper():10} vs {orm_b.upper():10}")
    print(f"  Statistic            : {result.statistic:.6f}")
    print(f"  P-value              : {result.pvalue:.10f}")
    print(f"  Mean difference (A-B): {mean_diff:.6f} ms")
    print()