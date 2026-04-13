"""Module 1: load Form 990 CSVs, dedupe, clean, engineer features (PRD §5)."""

from __future__ import annotations

import glob
import os
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


def classify_sector(mission: object) -> str:
    """Keyword-based mission sector (PRD §6.2 alternative)."""
    m = str(mission).lower()
    if any(w in m for w in ["school", "education", "student", "university", "college"]):
        return "Education"
    if any(w in m for w in ["health", "hospital", "medical", "clinic", "patient"]):
        return "Healthcare"
    if any(w in m for w in ["housing", "shelter", "homeless"]):
        return "Housing & Shelter"
    if any(w in m for w in ["food", "hunger", "meal", "nutrition"]):
        return "Food & Nutrition"
    if any(w in m for w in ["art", "museum", "cultural", "theater", "music"]):
        return "Arts & Culture"
    if any(w in m for w in ["environment", "conservation", "wildlife", "nature"]):
        return "Environment"
    if any(w in m for w in ["youth", "child", "children", "kid"]):
        return "Youth Services"
    if any(w in m for w in ["church", "faith", "ministry", "religious", "worship"]):
        return "Religious"
    if any(w in m for w in ["community", "civic", "neighborhood"]):
        return "Community Development"
    if any(w in m for w in ["research", "science", "technology"]):
        return "Research & Science"
    return "Other/General"


def load_raw_csvs(data_csv_dir: str | Path) -> pd.DataFrame:
    """Load every ``*_990.csv`` in the directory and concatenate."""
    data_csv_dir = Path(data_csv_dir)
    paths = sorted(data_csv_dir.glob("*_990.csv"))
    if not paths:
        raise FileNotFoundError(f"No *_990.csv files under {data_csv_dir}")
    frames = [pd.read_csv(p) for p in paths]
    return pd.concat(frames, ignore_index=True)


def dedupe_ein_tax_year(df: pd.DataFrame) -> pd.DataFrame:
    """Keep most recent filing per (EIN, TaxYear) by TaxPeriodEnd."""
    out = df.copy()
    out["TaxPeriodEnd"] = pd.to_datetime(out["TaxPeriodEnd"], errors="coerce")
    out = out.sort_values("TaxPeriodEnd", ascending=False, na_position="last")
    return out.drop_duplicates(subset=["EIN", "TaxYear"], keep="first").reset_index(drop=True)


def clean_base(df: pd.DataFrame) -> pd.DataFrame:
    """Type coercion, fills, row filters (PRD §5.2 Step 3)."""
    out = df.copy()
    out["TaxYear"] = pd.to_numeric(out["TaxYear"], errors="coerce").astype("Int64")
    out["FormationYr"] = pd.to_numeric(out["FormationYr"], errors="coerce").astype("Int64")
    out["GovernmentGrantsAmt"] = pd.to_numeric(out["GovernmentGrantsAmt"], errors="coerce").fillna(0)
    out["Volunteers"] = pd.to_numeric(out["Volunteers"], errors="coerce").fillna(0)
    out["Employees"] = pd.to_numeric(out["Employees"], errors="coerce").fillna(0).clip(lower=0)
    out["Volunteers"] = out["Volunteers"].clip(lower=0)

    rev = pd.to_numeric(out["TotalRevenueCY"], errors="coerce")
    out = out[rev.notna() & (rev != 0)].copy()
    return out.reset_index(drop=True)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derived ratios and labels (PRD §5.2 Step 4)."""
    out = df.copy()
    tr = pd.to_numeric(out["TotalRevenueCY"], errors="coerce")
    te = pd.to_numeric(out["TotalExpensesCY"], errors="coerce")
    te = te.replace(0, np.nan)

    out["GrantDependencyPct"] = pd.to_numeric(out["ContributionsGrantsCY"], errors="coerce") / tr
    out["ProgramRevenuePct"] = pd.to_numeric(out["ProgramServiceRevCY"], errors="coerce") / tr
    out["InvestmentRevenuePct"] = pd.to_numeric(out["InvestmentIncomeCY"], errors="coerce") / tr
    out["GovGrantPct"] = pd.to_numeric(out["GovernmentGrantsAmt"], errors="coerce") / tr

    out["ProgramExpenseRatio"] = pd.to_numeric(out["ProgramSvcExpenses"], errors="coerce") / te
    out["FundraisingRatio"] = pd.to_numeric(out["FundraisingExpCY"], errors="coerce") / te
    out["SalaryRatio"] = pd.to_numeric(out["SalariesCY"], errors="coerce") / te

    out["SurplusMargin"] = pd.to_numeric(out["NetRevenueCY"], errors="coerce") / tr
    exp_mo = te / 12
    out["OperatingReserveMonths"] = np.where(
        exp_mo > 0,
        pd.to_numeric(out["NetAssetsEOY"], errors="coerce") / exp_mo,
        np.nan,
    )
    ta = pd.to_numeric(out["TotalAssetsEOY"], errors="coerce")
    tl = pd.to_numeric(out["TotalLiabilitiesEOY"], errors="coerce")
    out["DebtRatio"] = np.where(ta > 0, tl / ta, np.nan)
    out["AssetLiabilityRatio"] = np.where(tl > 0, ta / tl, np.nan)

    tr_py = pd.to_numeric(out["TotalRevenuePY"], errors="coerce")
    te_py = pd.to_numeric(out["TotalExpensesPY"], errors="coerce")
    cg_py = pd.to_numeric(out["ContributionsGrantsPY"], errors="coerce")
    nab = pd.to_numeric(out["NetAssetsBOY"], errors="coerce")

    out["RevenueGrowthPct"] = np.where(
        tr_py.abs() > 0, (tr - tr_py) / tr_py.abs(), np.nan
    )
    out["ExpenseGrowthPct"] = np.where(
        te_py.abs() > 0,
        (te - te_py) / te_py.abs(),
        np.nan,
    )
    out["ContributionGrowthPct"] = np.where(
        cg_py.abs() > 0,
        (pd.to_numeric(out["ContributionsGrantsCY"], errors="coerce") - cg_py) / cg_py.abs(),
        np.nan,
    )
    out["NetAssetGrowthPct"] = np.where(
        nab.abs() > 0,
        (pd.to_numeric(out["NetAssetsEOY"], errors="coerce") - nab) / nab.abs(),
        np.nan,
    )

    nr_py = pd.to_numeric(out["NetRevenuePY"], errors="coerce")
    out["SurplusMargin_PY"] = np.where(tr_py.abs() > 0, nr_py / tr_py.abs(), np.nan)
    exp_py_mo = te_py / 12
    out["ReserveMonths_BOY"] = np.where(exp_py_mo > 0, nab / exp_py_mo, np.nan)

    ty = out["TaxYear"].astype("float")
    fy = out["FormationYr"].astype("float")
    out["OrgAge"] = (ty - fy).clip(lower=0)

    revenue = pd.to_numeric(out["TotalRevenueCY"], errors="coerce")
    out["SizeCategory"] = pd.cut(
        revenue,
        bins=[0, 500_000, 1_000_000, 5_000_000, 10_000_000, 50_000_000, float("inf")],
        labels=["<500K", "500K-1M", "1M-5M", "5M-10M", "10M-50M", "50M+"],
    )
    emp = pd.to_numeric(out["Employees"], errors="coerce")
    out["RevenuePerEmployee"] = np.where(emp > 0, revenue / emp, np.nan)

    out["LogRevenue"] = np.log1p(revenue.clip(lower=0))
    out["LogAssets"] = np.log1p(pd.to_numeric(out["TotalAssetsEOY"], errors="coerce").clip(lower=0))

    ratio_cols = [
        "GrantDependencyPct",
        "ProgramRevenuePct",
        "InvestmentRevenuePct",
        "GovGrantPct",
        "ProgramExpenseRatio",
        "FundraisingRatio",
        "SalaryRatio",
        "SurplusMargin",
        "DebtRatio",
    ]
    for col in ratio_cols:
        if col in out.columns:
            out[col] = out[col].clip(-2, 2)
    out["OperatingReserveMonths"] = out["OperatingReserveMonths"].clip(-120, 120)
    for gcol in [
        "RevenueGrowthPct",
        "ExpenseGrowthPct",
        "ContributionGrowthPct",
        "NetAssetGrowthPct",
        "SurplusMargin_PY",
    ]:
        if gcol in out.columns:
            out[gcol] = out[gcol].clip(-5, 5)
    out["ReserveMonths_BOY"] = out["ReserveMonths_BOY"].clip(-120, 120)

    out["Sector"] = out["Mission"].apply(classify_sector)
    out["PeerGroupID"] = (
        out["Sector"].astype(str)
        + "_"
        + out["SizeCategory"].astype(str)
        + "_"
        + out["State"].astype(str)
    )

    return out


def add_targets(out: pd.DataFrame) -> pd.DataFrame:
    """AtRisk binary and ResilienceScore (PRD §7.2)."""
    df = out.copy()
    debt = df["DebtRatio"].replace([np.inf, -np.inf], np.nan)
    df["AtRisk"] = (
        (df["SurplusMargin"] < -0.10)
        | (df["OperatingReserveMonths"] < 1)
        | (df["NetAssetGrowthPct"] < -0.20)
        | (df["RevenueGrowthPct"] < -0.25)
    ).astype(int)

    df["ResilienceScore"] = (
        np.clip(df["OperatingReserveMonths"] / 12, 0, 1) * 30
        + np.clip(1 - df["GrantDependencyPct"], 0, 1) * 20
        + np.clip(df["ProgramExpenseRatio"], 0, 1) * 20
        + np.clip(df["SurplusMargin"] * 100, 0, 15)
        + np.clip((1 - debt) * 15, 0, 15)
    ).round(1)
    return df


def build_master_table(
    data_csv_dir: Optional[str | Path] = None,
    repo_root: Optional[str | Path] = None,
) -> pd.DataFrame:
    """End-to-end Module 1 table."""
    root = Path(repo_root or Path(__file__).resolve().parents[1])
    csv_dir = Path(data_csv_dir or root / "data" / "data_csv")
    raw = load_raw_csvs(csv_dir)
    raw = dedupe_ein_tax_year(raw)
    raw = clean_base(raw)
    feat = engineer_features(raw)
    return add_targets(feat)


def save_master(df: pd.DataFrame, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
