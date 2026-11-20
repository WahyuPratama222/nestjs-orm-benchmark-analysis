import csv
import re
import statistics
from collections import defaultdict

from config import RESOURCE_DATA, RESOURCE_OUT

# ==================================================
# CONFIGURATION
# ==================================================

INPUT_FILE = RESOURCE_DATA
OUTPUT_DIR = RESOURCE_OUT

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONTAINERS = {
    "orm-benchmark-api": "api",
    "orm-benchmark-db": "postgres",
}

ORM_NAMES = {"prisma", "typeorm", "drizzle", "raw"}


# ==================================================
# HELPER FUNCTIONS
# ==================================================

def parse_cpu(value):
    return float(value.strip().replace("%", ""))


def parse_memory(value):
    """
    Convert Docker memory usage into MiB.
    Example: 79.16MiB / 2GiB -> 79.16
    """
    usage = value.split("/")[0].strip()
    match = re.match(r"([\d.]+)\s*([A-Za-z]+)", usage)

    if not match:
        raise ValueError(f"Invalid memory value: {value}")

    number = float(match.group(1))
    unit = match.group(2).lower()

    factors = {
        "b": 1 / (1024 ** 2),
        "kib": 1 / 1024,
        "mib": 1,
        "gib": 1024,
        "kb": 1000 / (1024 ** 2),
        "mb": 1000 ** 2 / (1024 ** 2),
        "gb": 1000 ** 3 / (1024 ** 2),
    }

    if unit not in factors:
        raise ValueError(f"Unsupported memory unit: {unit}")

    return number * factors[unit]


def parse_sample(sample):
    """
    Expected format:
    1_drizzle_groupby_100
    """
    parts = sample.lower().split("_")

    if len(parts) != 4:
        raise ValueError(f"Invalid sample name: {sample}")

    repetition, orm, operation, vu = parts

    if orm not in ORM_NAMES:
        raise ValueError(f"Unknown ORM: {orm}")

    if operation != "groupby":
        raise ValueError(f"Unexpected operation: {operation}")

    return {
        "repetition": int(repetition),
        "orm": orm,
        "operation": operation,
        "vu": int(vu),
    }


# ==================================================
# READ RAW DATA
# ==================================================

if not INPUT_FILE.exists():
    raise FileNotFoundError(f"File not found: {INPUT_FILE}")

raw_data = defaultdict(lambda: defaultdict(list))

with INPUT_FILE.open(newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    required_columns = {
        "sample",
        "timestamp",
        "container",
        "cpu_percent",
        "memory_usage",
        "memory_percent",
    }

    if not required_columns.issubset(reader.fieldnames or []):
        raise ValueError("CSV header does not match expected structure.")

    for row in reader:
        sample = row["sample"].strip()
        container = row["container"].strip()

        if container not in CONTAINERS:
            continue

        raw_data[sample][container].append({
            "cpu": parse_cpu(row["cpu_percent"]),
            "memory": parse_memory(row["memory_usage"]),
        })


# ==================================================
# CALCULATE PER-SAMPLE METRICS
# ==================================================

per_sample = []

for sample, containers in sorted(raw_data.items()):

    # Skip warm-up data
    if sample.lower() == "discard":
        continue

    metadata = parse_sample(sample)

    result = {
        "sample": sample,
        **metadata,
    }

    for container, short_name in CONTAINERS.items():
        readings = containers.get(container, [])

        if len(readings) < 2:
            raise ValueError(
                f"Insufficient readings for {sample} / {container}"
            )

        # First reading is treated as pre-load baseline.
        active_readings = readings[1:]

        cpu_values = [item["cpu"] for item in active_readings]
        memory_values = [item["memory"] for item in active_readings]

        result[f"cpu_{short_name}_mean"] = statistics.mean(cpu_values)
        result[f"ram_{short_name}_max"] = max(memory_values)

        result[f"readings_{short_name}"] = len(readings)

    per_sample.append(result)


# ==================================================
# SAVE PER-SAMPLE CSV
# ==================================================

per_sample_file = OUTPUT_DIR / "resource_per_sample.csv"

per_sample_fields = [
    "sample",
    "repetition",
    "orm",
    "operation",
    "vu",
    "cpu_api_mean",
    "cpu_postgres_mean",
    "ram_api_max",
    "ram_postgres_max",
    "readings_api",
    "readings_postgres",
]

with per_sample_file.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=per_sample_fields)
    writer.writeheader()

    for row in per_sample:
        writer.writerow({
            key: (
                round(row[key], 2)
                if key in {
                    "cpu_api_mean",
                    "cpu_postgres_mean",
                    "ram_api_max",
                    "ram_postgres_max",
                }
                else row[key]
            )
            for key in per_sample_fields
        })


# ==================================================
# AGGREGATE BY ORM AND VU
# ==================================================

groups = defaultdict(list)

for row in per_sample:
    groups[(row["orm"], row["vu"])].append(row)

summary = []

for (orm, vu), samples in sorted(groups.items()):
    summary.append({
        "orm": orm,
        "vu": vu,
        "n": len(samples),

        "cpu_api_mean": statistics.mean(
            row["cpu_api_mean"] for row in samples
        ),

        "cpu_postgres_mean": statistics.mean(
            row["cpu_postgres_mean"] for row in samples
        ),

        "ram_api_mean_max": statistics.mean(
            row["ram_api_max"] for row in samples
        ),

        "ram_postgres_mean_max": statistics.mean(
            row["ram_postgres_max"] for row in samples
        ),
    })


# ==================================================
# SAVE SUMMARY CSV
# ==================================================

summary_file = OUTPUT_DIR / "resource_summary.csv"

summary_fields = [
    "orm",
    "vu",
    "n",
    "cpu_api_mean",
    "cpu_postgres_mean",
    "ram_api_mean_max",
    "ram_postgres_mean_max",
]

with summary_file.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=summary_fields)
    writer.writeheader()

    for row in summary:
        writer.writerow({
            key: (
                round(row[key], 2)
                if key in summary_fields[3:]
                else row[key]
            )
            for key in summary_fields
        })


# ==================================================
# VALIDATION & OUTPUT
# ==================================================

print("\n========== ANALYSIS COMPLETE ==========")
print(f"Total samples : {len(per_sample)}")
print(f"Summary groups: {len(summary)}")

for row in summary:
    print(
        f"{row['orm']:8} | "
        f"VU {row['vu']:3} | "
        f"N={row['n']} | "
        f"API CPU={row['cpu_api_mean']:.2f}% | "
        f"DB CPU={row['cpu_postgres_mean']:.2f}%"
    )

print(f"\nPer-sample: {per_sample_file}")
print(f"Summary   : {summary_file}")