import pandas as pd

from config import DESCRIPTIVE_DIR


def generate_table(input_file, output_file):
    if not input_file.exists():
        raise FileNotFoundError(
            f"{input_file} not found. Run compute_descriptive_stats first."
        )

    df = pd.read_csv(input_file)

    # Format the statistics into a single cell
    df["statistics"] = df.apply(
        lambda row: (
            f"{row['mean']:.2f} "
            f"({row['median']:.2f}; {row['std']:.2f})"
        ),
        axis=1
    )

    # Pivot so each ORM becomes a column
    table = df.pivot(
        index=["operation", "vus"],
        columns="orm",
        values="statistics"
    ).reset_index()

    # Set column order
    table = table[
        ["operation", "vus", "prisma", "typeorm", "drizzle", "raw"]
    ]

    # Rename columns
    table.columns = [
        "Operasi",
        "VUs",
        "Prisma",
        "TypeORM",
        "Drizzle ORM",
        "Raw SQL"
    ]

    table["Operasi"] = table["Operasi"].str.capitalize()

    # Use a decimal comma
    for column in table.columns[2:]:
        table[column] = table[column].str.replace(".", ",", regex=False)

    # Save to CSV
    table.to_csv(output_file, index=False)

    print(f"Table created: {output_file}")
    print(table.to_string(index=False))


# Table III: P95 Latency
generate_table(
    DESCRIPTIVE_DIR / "p95_descriptive.csv",
    DESCRIPTIVE_DIR / "p95_table.csv"
)

# Table IV: Throughput
generate_table(
    DESCRIPTIVE_DIR / "throughput_descriptive.csv",
    DESCRIPTIVE_DIR / "throughput_table.csv"
)