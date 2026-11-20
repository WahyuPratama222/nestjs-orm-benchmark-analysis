import pandas as pd
from scipy.stats import friedmanchisquare

from config import PERF_DATA

df = pd.read_csv(PERF_DATA)

# Pick one scenario
data = df[
    (df["operation"] == "read") &
    (df["vus"] == 10) &
    (df["valid"] == 1)
]

# Arrange data by repetition
orms = ["prisma", "typeorm", "drizzle", "raw"]

samples = []

for orm in orms:
    values = (
        data[data["orm"] == orm]
        .sort_values("repetition")["p95_ms"]
        .to_numpy()
    )
    samples.append(values)

# Friedman test
statistic, p_value = friedmanchisquare(*samples)

print("Friedman Test - P95 Read 10 VU")
print(f"Statistic : {statistic:.6f}")
print(f"P-value   : {p_value:.10f}")
print(f"DF        : {len(orms) - 1}")