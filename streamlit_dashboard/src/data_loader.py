"""Load and deduplicate all *_990.csv files from data/data_csv/."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# Repo root is two levels above this file: streamlit_dashboard/src/data_loader.py
_REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_CSV_DIR = _REPO_ROOT / "data" / "data_csv"


def load_data(data_csv_dir: Path = DATA_CSV_DIR) -> pd.DataFrame:
    """
    Glob all *_990.csv files, concatenate, and deduplicate.
    Returns one row per (EIN, TaxYear), keeping the most recent TaxPeriodEnd.
    """
    paths = sorted(data_csv_dir.glob("*_990.csv"))
    if not paths:
        raise FileNotFoundError(f"No *_990.csv files found in {data_csv_dir}")

    df = pd.concat([pd.read_csv(p, dtype={"EIN": str, "NTEE_CD": str}) for p in paths], ignore_index=True)

    df["TaxPeriodEnd"] = pd.to_datetime(df["TaxPeriodEnd"], errors="coerce")
    df = (
        df.sort_values("TaxPeriodEnd", ascending=False, na_position="last")
        .drop_duplicates(subset=["EIN", "TaxYear"], keep="first")
        .reset_index(drop=True)
    )

    return df
