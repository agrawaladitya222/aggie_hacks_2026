"""Load master_990.csv and train_metrics.json for the dashboard."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

_REPO_ROOT = Path(__file__).resolve().parents[2]
MASTER_CSV = _REPO_ROOT / "data" / "master_990.csv"
TRAIN_METRICS_JSON = _REPO_ROOT / "artifacts" / "train_metrics.json"


def load_data(master_csv: Path = MASTER_CSV) -> pd.DataFrame:
    """Load the pre-built master_990.csv with all features, peer scores, and model predictions."""
    if not master_csv.exists():
        raise FileNotFoundError(
            f"master_990.csv not found at {master_csv}. "
            "Run `python3 scripts/build_artifacts.py` to generate it."
        )
    df = pd.read_csv(
        master_csv,
        dtype={"EIN": str, "NTEE_CD": str},
        low_memory=False,
    )
    df["TaxYear"] = pd.to_numeric(df["TaxYear"], errors="coerce")
    df["TaxPeriodEnd"] = pd.to_datetime(df["TaxPeriodEnd"], errors="coerce")
    return df


def load_train_metrics(metrics_json: Path = TRAIN_METRICS_JSON) -> dict:
    """Load model evaluation metrics from artifacts/train_metrics.json."""
    if not metrics_json.exists():
        return {}
    with open(metrics_json, "r", encoding="utf-8") as f:
        return json.load(f)
