import numpy as np
import pandas as pd
from config import PERF_DATA, INFERENTIAL_DIR

from itertools import combinations
from scipy.stats import friedmanchisquare, wilcoxon, rankdata


# ==========================================
# CONFIGURATION
# ==========================================

INPUT_FILE = PERF_DATA
ALPHA = 0.05

# Make sure the output folder exists before saving
INFERENTIAL_DIR.mkdir(parents=True, exist_ok=True)

OPERATIONS = ["read", "create", "join", "groupby"]
VUS_LEVELS = [10, 50, 100]

ORMS = ["prisma", "typeorm", "drizzle", "raw"]

METRICS = {
    "p95_ms": "P95",
    "throughput_rps": "Throughput"
}

PAIRS = list(combinations(ORMS, 2))


# ==========================================
# HOLM CORRECTION
# ==========================================

def holm_correction(p_values):
    p_values = np.asarray(p_values, dtype=float)

    m = len(p_values)
    order = np.argsort(p_values)

    sorted_p = p_values[order]

    adjusted_sorted = np.maximum.accumulate(
        (m - np.arange(m)) * sorted_p
    )

    adjusted_sorted = np.minimum(adjusted_sorted, 1.0)

    adjusted = np.empty(m)
    adjusted[order] = adjusted_sorted

    return adjusted


# ==========================================
# RANK-BISERIAL CORRELATION
# ==========================================

def calculate_rbc(a, b):
    differences = a - b

    # Wilcoxon zero_method="wilcox"
    # so zero differences are not counted
    nonzero = differences[differences != 0]

    if len(nonzero) == 0:
        return 0.0, 0.0, 0.0

    ranks = rankdata(np.abs(nonzero))

    w_positive = ranks[nonzero > 0].sum()
    w_negative = ranks[nonzero < 0].sum()

    total = w_positive + w_negative

    rbc = (w_positive - w_negative) / total

    return w_positive, w_negative, rbc


# ==========================================
# LOAD DATA
# ==========================================

print("Loading benchmark data...")

df = pd.read_csv(INPUT_FILE)

required_columns = [
    "repetition",
    "orm",
    "operation",
    "vus",
    "valid",
    "p95_ms",
    "throughput_rps"
]

missing = set(required_columns) - set(df.columns)

if missing:
    raise ValueError(f"Missing columns: {missing}")

df = df[df["valid"] == 1].copy()

print(f"Valid samples: {len(df)}")


# ==========================================
# FRIEDMAN TEST - 24 SCENARIOS
# ==========================================

friedman_results = []

print("\nRunning Friedman tests...")

for metric, metric_label in METRICS.items():

    for operation in OPERATIONS:

        for vus in VUS_LEVELS:

            subset = df[
                (df["operation"] == operation) &
                (df["vus"] == vus)
            ]

            pivot = subset.pivot(
                index="repetition",
                columns="orm",
                values=metric
            ).sort_index()

            if list(pivot.columns) != ORMS:
                pivot = pivot.reindex(columns=ORMS)

            if pivot.shape != (10, 4) or pivot.isna().any().any():
                raise ValueError(
                    f"Incomplete data: {metric_label}, "
                    f"{operation}, {vus} VU"
                )

            samples = [
                pivot[orm].to_numpy()
                for orm in ORMS
            ]

            statistic, p_value = friedmanchisquare(*samples)

            n = len(pivot)
            k = len(ORMS)

            kendall_w = statistic / (n * (k - 1))

            friedman_results.append({
                "metric": metric_label,
                "operation": operation,
                "vus": vus,
                "n": n,
                "statistic": statistic,
                "df": k - 1,
                "p_value": p_value,
                "kendall_w": kendall_w
            })


friedman_df = pd.DataFrame(friedman_results)

# Holm correction across all 24 omnibus tests
friedman_df["p_adjusted_holm"] = holm_correction(
    friedman_df["p_value"]
)

friedman_df["significant"] = (
    friedman_df["p_adjusted_holm"] < ALPHA
)

friedman_df.to_csv(
    INFERENTIAL_DIR / "friedman_results.csv",
    index=False
)


# ==========================================
# WILCOXON POST-HOC
# Only significant Friedman scenarios
# ==========================================

wilcoxon_results = []

significant_scenarios = friedman_df[
    friedman_df["significant"]
]

print("\nRunning Wilcoxon post-hoc tests...")

for _, scenario in significant_scenarios.iterrows():

    metric_label = scenario["metric"]

    metric = next(
        key for key, value in METRICS.items()
        if value == metric_label
    )

    operation = scenario["operation"]
    vus = scenario["vus"]

    subset = df[
        (df["operation"] == operation) &
        (df["vus"] == vus)
    ]

    pivot = subset.pivot(
        index="repetition",
        columns="orm",
        values=metric
    ).sort_index()

    pivot = pivot.reindex(columns=ORMS)

    scenario_results = []

    for orm_a, orm_b in PAIRS:

        a = pivot[orm_a].to_numpy()
        b = pivot[orm_b].to_numpy()

        differences = a - b

        result = wilcoxon(
            differences,
            alternative="two-sided",
            zero_method="wilcox",
            method="auto"
        )

        w_positive, w_negative, rbc = calculate_rbc(
            differences,
            np.zeros_like(differences)
        )

        scenario_results.append({
            "metric": metric_label,
            "operation": operation,
            "vus": vus,
            "orm_a": orm_a,
            "orm_b": orm_b,
            "statistic": result.statistic,
            "p_value": result.pvalue,
            "mean_difference": np.mean(a - b),
            "median_difference": np.median(a - b),
            "w_positive": w_positive,
            "w_negative": w_negative,
            "rank_biserial": rbc
        })

    # Holm correction within each scenario
    scenario_df = pd.DataFrame(scenario_results)

    scenario_df["p_adjusted_holm"] = holm_correction(
        scenario_df["p_value"]
    )

    scenario_df["significant"] = (
        scenario_df["p_adjusted_holm"] < ALPHA
    )

    wilcoxon_results.extend(
        scenario_df.to_dict("records")
    )


# ==========================================
# SAVE RESULTS
# ==========================================

wilcoxon_columns = [
    "metric",
    "operation",
    "vus",
    "orm_a",
    "orm_b",
    "statistic",
    "p_value",
    "mean_difference",
    "median_difference",
    "w_positive",
    "w_negative",
    "rank_biserial",
    "p_adjusted_holm",
    "significant"
]

wilcoxon_df = pd.DataFrame(
    wilcoxon_results,
    columns=wilcoxon_columns
)

wilcoxon_df.to_csv(
    INFERENTIAL_DIR / "wilcoxon_posthoc_results.csv",
    index=False
)


# ==========================================
# SUMMARY
# ==========================================

print("\n" + "=" * 60)
print("STATISTICAL ANALYSIS SUMMARY")
print("=" * 60)

print(f"Total Friedman scenarios : {len(friedman_df)}")

print(
    "Significant Friedman     : "
    f"{friedman_df['significant'].sum()}"
)

print(
    "Non-significant Friedman : "
    f"{(~friedman_df['significant']).sum()}"
)

print(
    "Total Wilcoxon tests     : "
    f"{len(wilcoxon_df)}"
)

if len(wilcoxon_df) > 0:
    print(
        "Significant Wilcoxon     : "
        f"{wilcoxon_df['significant'].sum()}"
    )

print("\nGenerated files:")
print(f"- {INFERENTIAL_DIR / 'friedman_results.csv'}")
print(f"- {INFERENTIAL_DIR / 'wilcoxon_posthoc_results.csv'}")

print("\nAnalysis completed.")