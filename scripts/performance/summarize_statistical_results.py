import pandas as pd

from config import INFERENTIAL_DIR

# Input files (produced by run_statistical_analysis.py)
FRIEDMAN_FILE = INFERENTIAL_DIR / "friedman_results.csv"
WILCOXON_FILE = INFERENTIAL_DIR / "wilcoxon_posthoc_results.csv"

# Output files
SUMMARY_FILE = INFERENTIAL_DIR / "inferential_summary.csv"
DETAIL_FILE = INFERENTIAL_DIR / "inferential_summary_detailed.csv"


def main():
    # Make sure the previous step has been run
    for path in (FRIEDMAN_FILE, WILCOXON_FILE):
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found. Run run_statistical_analysis first."
            )

    # Load test results
    friedman = pd.read_csv(FRIEDMAN_FILE)
    wilcoxon = pd.read_csv(WILCOXON_FILE)

    # Make sure the significance column is boolean
    for df in [friedman, wilcoxon]:
        df["significant"] = (
            df["significant"]
            .astype(str)
            .str.lower()
            .map({"true": True, "false": False})
        )

    # Key columns used to join the two results
    keys = ["metric", "operation", "vus"]

    friedman_columns = [
        "metric",
        "operation",
        "vus",
        "n",
        "statistic",
        "df",
        "p_value",
        "kendall_w",
        "p_adjusted_holm",
        "significant",
    ]

    # Attach the Friedman result to every Wilcoxon row
    detailed = wilcoxon.merge(
        friedman[friedman_columns],
        on=keys,
        how="left",
        suffixes=("_wilcoxon", "_friedman"),
        validate="many_to_one",
    )

    # Count post-hoc comparisons per scenario
    posthoc_summary = (
        wilcoxon.groupby(keys)
        .agg(
            posthoc_count=("significant", "size"),
            pair_significant_count=("significant", "sum"),
        )
        .reset_index()
    )

    posthoc_summary["pair_nonsignificant_count"] = (
        posthoc_summary["posthoc_count"]
        - posthoc_summary["pair_significant_count"]
    )

    # Merge the post-hoc summary into all Friedman results
    summary = friedman.merge(
        posthoc_summary,
        on=keys,
        how="left",
        validate="one_to_one",
    )

    # Scenarios that failed Friedman have no post-hoc results
    count_columns = [
        "posthoc_count",
        "pair_significant_count",
        "pair_nonsignificant_count",
    ]

    summary[count_columns] = (
        summary[count_columns].fillna(0).astype(int)
    )

    # Describe the post-hoc status of each scenario
    def get_posthoc_status(row):
        if not row["significant"]:
            return "Tidak dilakukan: Friedman tidak signifikan"

        return (
            f"{row['pair_significant_count']} dari "
            f"{row['posthoc_count']} perbandingan signifikan"
        )

    summary["posthoc_status"] = summary.apply(
        get_posthoc_status,
        axis=1,
    )

    # Sort the results.
    # The metric column holds the labels written by
    # run_statistical_analysis.py ("P95" and "Throughput").
    sort_order = {
        "P95": 0,
        "Throughput": 1,
    }

    summary["_metric_order"] = summary["metric"].map(sort_order)
    detailed["_metric_order"] = detailed["metric"].map(sort_order)

    summary = (
        summary.sort_values(
            ["_metric_order", "operation", "vus"]
        )
        .drop(columns="_metric_order")
    )

    detailed = (
        detailed.sort_values(
            ["_metric_order", "operation", "vus", "orm_a", "orm_b"]
        )
        .drop(columns="_metric_order")
    )

    # Save results
    summary.to_csv(SUMMARY_FILE, index=False)
    detailed.to_csv(DETAIL_FILE, index=False)

    # Console summary
    print("=== STATISTICAL SUMMARY ===")
    print(f"Total skenario Friedman : {len(summary)}")
    print(
        "Friedman signifikan     : "
        f"{summary['significant'].sum()}"
    )
    print(
        "Friedman tidak signifikan: "
        f"{(~summary['significant']).sum()}"
    )
    print(f"Total pengujian Wilcoxon: {len(wilcoxon)}")
    print(
        "Wilcoxon signifikan     : "
        f"{wilcoxon['significant'].sum()}"
    )
    print(
        "Wilcoxon tidak signifikan: "
        f"{(~wilcoxon['significant']).sum()}"
    )

    print("\nFile berhasil dibuat:")
    print(SUMMARY_FILE)
    print(DETAIL_FILE)


if __name__ == "__main__":
    main()