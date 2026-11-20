import pandas as pd
from scipy.stats import rankdata

from config import PERF_DATA

df = pd.read_csv(PERF_DATA)

data = df[
    (df["operation"] == "read") &
    (df["vus"] == 10) &
    (df["valid"] == 1)
]

orms = ["prisma", "typeorm", "drizzle", "raw"]

samples = {}

for orm in orms:
    samples[orm] = (
        data[data["orm"] == orm]
        .sort_values("repetition")["p95_ms"]
        .to_numpy()
    )

pairs = [
    ("prisma", "typeorm"),
    ("prisma", "drizzle"),
    ("prisma", "raw"),
    ("typeorm", "drizzle"),
    ("typeorm", "raw"),
    ("drizzle", "raw"),
]

print("Rank-Biserial Correlation - P95 Read 10 VU")
print("-" * 65)

for orm_a, orm_b in pairs:
    diff = samples[orm_a] - samples[orm_b]

    # Ignore zero differences
    diff = diff[diff != 0]

    ranks = rankdata(abs(diff))

    w_positive = ranks[diff > 0].sum()
    w_negative = ranks[diff < 0].sum()

    rbc = (w_positive - w_negative) / (
        w_positive + w_negative
    )

    print(f"{orm_a.upper():10} vs {orm_b.upper():10}")
    print(f"  W+       : {w_positive:.4f}")
    print(f"  W-       : {w_negative:.4f}")
    print(f"  RBC      : {rbc:.4f}")
    print()