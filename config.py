from pathlib import Path

# Project root, resolved relative to this file
ROOT = Path(__file__).resolve().parent

# Inputs
PERF_DATA = ROOT / "data" / "performance" / "performance_results.csv"
RESOURCE_DATA = ROOT / "data" / "resource" / "resource_results.csv"

# Outputs
PERF_OUT = ROOT / "outputs" / "performance"
DESCRIPTIVE_DIR = PERF_OUT / "descriptive"
INFERENTIAL_DIR = PERF_OUT / "inferential"
FIGURES_DIR = PERF_OUT / "figures"
RESOURCE_OUT = ROOT / "outputs" / "resource"