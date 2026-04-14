from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


NTEE_SECTOR_MAP = {
    "A": "Arts, Culture & Humanities",
    "B": "Education",
    "C": "Environment & Animals",
    "D": "Environment & Animals",
    "E": "Healthcare",
    "F": "Mental Health & Crisis",
    "G": "Diseases & Medical Research",
    "H": "Diseases & Medical Research",
    "I": "Crime & Legal",
    "J": "Employment & Jobs",
    "K": "Food, Agriculture & Nutrition",
    "L": "Housing & Shelter",
    "M": "Public Safety & Disaster Relief",
    "N": "Recreation & Sports",
    "O": "Youth Development",
    "P": "Human Services",
    "Q": "International Affairs",
    "R": "Civil Rights & Advocacy",
    "S": "Community Improvement",
    "T": "Philanthropy & Grantmaking",
    "U": "Science & Technology",
    "V": "Social Science Research",
    "W": "Public Policy",
    "X": "Religion",
    "Y": "Mutual Benefit",
    "Z": "Unknown / Unclassified",
}


@dataclass
class DataPipelineConfig:
    input_glob: str = "data/data_csv/*990*.csv"
    output_path: str = "data/master_990.csv"
    panel_start_year: int = 2018
    panel_end_year: int = 2024


def _coerce_numeric(df: pd.DataFrame, columns: Iterable[str]) -> pd.DataFrame:
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def sector_from_ntee(ntee_code: object) -> str | None:
    if pd.isna(ntee_code):
        return None
    ntee = str(ntee_code).strip()
    if not ntee:
        return None
    return NTEE_SECTOR_MAP.get(ntee[0].upper())


def classify_sector_from_mission(mission: object) -> str:
    m = str(mission).lower()
    if any(w in m for w in ["school", "education", "student", "university", "college"]):
        return "Education"
    if any(w in m for w in ["health", "hospital", "medical", "clinic", "patient"]):
        return "Healthcare"
    if any(w in m for w in ["housing", "shelter", "homeless"]):
        return "Housing & Shelter"
    if any(w in m for w in ["food", "hunger", "meal", "nutrition"]):
        return "Food, Agriculture & Nutrition"
    if any(w in m for w in ["art", "museum", "cultural", "theater", "music"]):
        return "Arts, Culture & Humanities"
    if any(w in m for w in ["environment", "conservation", "wildlife", "nature"]):
        return "Environment & Animals"
    if any(w in m for w in ["youth", "child", "children", "kid"]):
        return "Youth Development"
    if any(w in m for w in ["church", "faith", "ministry", "religious", "worship"]):
        return "Religion"
    if any(w in m for w in ["community", "civic", "neighborhood"]):
        return "Community Improvement"
    if any(w in m for w in ["research", "science", "technology"]):
        return "Science & Technology"
    return "Human Services"


def run_data_pipeline(config: DataPipelineConfig = DataPipelineConfig()) -> pd.DataFrame:
    files = sorted(Path(".").glob(config.input_glob))
    if not files:
        raise FileNotFoundError(f"No files matched: {config.input_glob}")

    df = pd.concat((pd.read_csv(path, low_memory=False) for path in files), ignore_index=True)
    df = _coerce_numeric(
        df,
        [
            "TaxYear",
            "FormationYr",
            "GovernmentGrantsAmt",
            "TotalRevenueCY",
            "TotalRevenuePY",
            "ContributionsGrantsCY",
            "ContributionsGrantsPY",
            "ProgramServiceRevCY",
            "InvestmentIncomeCY",
            "OtherRevenueCY",
            "TotalExpensesCY",
            "TotalExpensesPY",
            "SalariesCY",
            "FundraisingExpCY",
            "ProgramSvcExpenses",
            "NetRevenueCY",
            "NetAssetsEOY",
            "NetAssetsBOY",
            "TotalAssetsEOY",
            "TotalLiabilitiesEOY",
            "Employees",
            "Volunteers",
        ],
    )

    df["TaxPeriodEnd"] = pd.to_datetime(df["TaxPeriodEnd"], errors="coerce")
    df = df.sort_values("TaxPeriodEnd", ascending=False)
    df = df.drop_duplicates(subset=["EIN", "TaxYear"], keep="first")
    df["TaxYear"] = df["TaxYear"].astype("Int64")
    df = df[df["TaxYear"].between(config.panel_start_year, config.panel_end_year)]

    df["FormationYr"] = df["FormationYr"].astype("Int64")
    df["GovernmentGrantsAmt"] = df["GovernmentGrantsAmt"].fillna(0)
    df = df[df["TotalRevenueCY"].notna() & (df["TotalRevenueCY"] > 0)]

    df.loc[df["Employees"] > 50000, "Employees"] = np.nan
    df["Employees"] = df["Employees"].clip(lower=0)
    df["Volunteers"] = df["Volunteers"].clip(lower=0)

    df.loc[df["TotalExpensesCY"] < 0, "TotalExpensesCY"] = np.nan
    df = df[df["TotalExpensesCY"].notna() & (df["TotalExpensesCY"] > 0)]

    df["GrantDependencyPct"] = df["ContributionsGrantsCY"] / df["TotalRevenueCY"]
    df["ProgramRevenuePct"] = df["ProgramServiceRevCY"] / df["TotalRevenueCY"]
    df["InvestmentRevenuePct"] = df["InvestmentIncomeCY"] / df["TotalRevenueCY"]
    df["GovGrantPct"] = df["GovernmentGrantsAmt"] / df["TotalRevenueCY"]

    df["ProgramExpenseRatio"] = df["ProgramSvcExpenses"] / df["TotalExpensesCY"]
    df["FundraisingRatio"] = df["FundraisingExpCY"] / df["TotalExpensesCY"]
    df["SalaryRatio"] = df["SalariesCY"] / df["TotalExpensesCY"]

    df["SurplusMargin"] = df["NetRevenueCY"] / df["TotalRevenueCY"]
    df["OperatingReserveMonths"] = np.where(
        df["TotalExpensesCY"] > 0,
        df["NetAssetsEOY"] / (df["TotalExpensesCY"] / 12),
        np.nan,
    )
    df["DebtRatio"] = np.where(
        df["TotalAssetsEOY"] > 0,
        df["TotalLiabilitiesEOY"] / df["TotalAssetsEOY"],
        np.nan,
    )
    df["AssetLiabilityRatio"] = np.where(
        df["TotalLiabilitiesEOY"] > 0,
        df["TotalAssetsEOY"] / df["TotalLiabilitiesEOY"],
        np.nan,
    )

    df["RevenueGrowthPct"] = np.where(
        df["TotalRevenuePY"].abs() > 0,
        (df["TotalRevenueCY"] - df["TotalRevenuePY"]) / df["TotalRevenuePY"].abs(),
        np.nan,
    )
    df["ExpenseGrowthPct"] = np.where(
        df["TotalExpensesPY"].abs() > 0,
        (df["TotalExpensesCY"] - df["TotalExpensesPY"]) / df["TotalExpensesPY"].abs(),
        np.nan,
    )
    df["ContributionGrowthPct"] = np.where(
        df["ContributionsGrantsPY"].abs() > 0,
        (df["ContributionsGrantsCY"] - df["ContributionsGrantsPY"]) / df["ContributionsGrantsPY"].abs(),
        np.nan,
    )
    df["NetAssetGrowthPct"] = np.where(
        df["NetAssetsBOY"].abs() > 0,
        (df["NetAssetsEOY"] - df["NetAssetsBOY"]) / df["NetAssetsBOY"].abs(),
        np.nan,
    )

    df["OrgAge"] = (df["TaxYear"] - df["FormationYr"]).clip(lower=0)
    df["SizeCategory"] = pd.cut(
        df["TotalRevenueCY"],
        bins=[0, 500_000, 1_000_000, 5_000_000, 10_000_000, 50_000_000, float("inf")],
        labels=["<500K", "500K-1M", "1M-5M", "5M-10M", "10M-50M", "50M+"],
    )
    df["RevenuePerEmployee"] = np.where(df["Employees"] > 0, df["TotalRevenueCY"] / df["Employees"], np.nan)
    df["LogRevenue"] = np.log1p(df["TotalRevenueCY"].clip(lower=0))
    df["LogAssets"] = np.log1p(df["TotalAssetsEOY"].clip(lower=0))

    df["Sector"] = df["NTEE_CD"].apply(sector_from_ntee)
    no_sector = df["Sector"].isna()
    df.loc[no_sector, "Sector"] = df.loc[no_sector, "Mission"].apply(classify_sector_from_mission)
    df["NTEEMajorGroup"] = (
        df["NTEE_CD"].astype(str).str.strip().str[0].str.upper().where(df["NTEE_CD"].notna())
    )

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
        df[col] = df[col].clip(-2, 2)
    df["OperatingReserveMonths"] = df["OperatingReserveMonths"].clip(-120, 120)
    df["RevenueGrowthPct"] = df["RevenueGrowthPct"].clip(-5, 5)
    df["ExpenseGrowthPct"] = df["ExpenseGrowthPct"].clip(-5, 5)

    assert df.duplicated(subset=["EIN", "TaxYear"]).sum() == 0
    assert df["TaxYear"].between(config.panel_start_year, config.panel_end_year).all()
    assert df["Sector"].notna().all()
    assert (df["TotalRevenueCY"] > 0).all()
    assert (df["TotalExpensesCY"] > 0).all()
    assert (df["Employees"].fillna(0) <= 50000).all()

    output = Path(config.output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output, index=False)
    return df
