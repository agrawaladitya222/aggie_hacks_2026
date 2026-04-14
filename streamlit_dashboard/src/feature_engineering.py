"""Compute all engineered features for the dashboard."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _safe_div(num: pd.Series, denom: pd.Series) -> pd.Series:
    return np.where(denom.abs() > 0, num / denom, np.nan)


def _coerce(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_numeric(df[col], errors="coerce")


def add_exclusion_flags(df: pd.DataFrame) -> pd.DataFrame:
    """Mark rows that must be excluded from all views or only the brand map."""
    out = df.copy()
    rev = _coerce(out, "TotalRevenueCY")
    exp = _coerce(out, "TotalExpensesCY")
    prog = _coerce(out, "ProgramSvcExpenses")

    # Exclude entirely — can't compute any ratios
    out["_exclude"] = rev.isna() | (rev == 0) | exp.isna() | (exp == 0)
    # Exclude from brand map only — X axis undefined
    out["_exclude_brand_map"] = prog.isna()
    return out


def _efficiency(out: pd.DataFrame) -> pd.DataFrame:
    """Group 1: Efficiency Metrics."""
    exp = _coerce(out, "TotalExpensesCY")
    out["ProgramExpenseRatio"] = _safe_div(_coerce(out, "ProgramSvcExpenses"), exp)
    out["FundraisingOverhead"] = _safe_div(_coerce(out, "FundraisingExpCY"), exp)
    out["SalaryRatio"] = _safe_div(_coerce(out, "SalariesCY"), exp)
    out["AdminOverhead"] = (1 - out["ProgramExpenseRatio"].fillna(0) - out["FundraisingOverhead"].fillna(0)).where(
        out["ProgramExpenseRatio"].notna() & out["FundraisingOverhead"].notna()
    )
    return out


def _stability(out: pd.DataFrame) -> pd.DataFrame:
    """Group 2: Financial Stability Metrics."""
    rev = _coerce(out, "TotalRevenueCY")
    exp = _coerce(out, "TotalExpensesCY")
    assets_eoy = _coerce(out, "TotalAssetsEOY")
    assets_boy = _coerce(out, "TotalAssetsBOY")
    liab_eoy = _coerce(out, "TotalLiabilitiesEOY")
    net_assets = _coerce(out, "NetAssetsEOY")
    net_rev = _coerce(out, "NetRevenueCY")

    out["OperatingReserveMonths"] = np.where(exp > 0, net_assets / (exp / 12), np.nan)
    out["SurplusMargin"] = _safe_div(net_rev, rev)
    out["DebtRatio"] = np.where(assets_eoy > 0, liab_eoy / assets_eoy, np.nan)
    out["AssetGrowth"] = _safe_div(assets_eoy - assets_boy, assets_boy.abs())
    return out


def _revenue_diversification(out: pd.DataFrame) -> pd.DataFrame:
    """Group 3: Revenue Diversification Metrics."""
    rev = _coerce(out, "TotalRevenueCY")
    grants = _coerce(out, "ContributionsGrantsCY")
    earned = _coerce(out, "ProgramServiceRevCY")
    invest = _coerce(out, "InvestmentIncomeCY")

    out["GrantDependency"] = _safe_div(grants, rev)
    out["EarnedRevenuePct"] = _safe_div(earned, rev)
    out["InvestmentIncomePct"] = _safe_div(invest, rev)

    max_stream = np.maximum(np.maximum(grants.fillna(0), earned.fillna(0)), invest.fillna(0))
    out["RevenueConcentration"] = _safe_div(pd.Series(max_stream, index=out.index), rev)
    return out


def _growth(out: pd.DataFrame) -> pd.DataFrame:
    """Group 4: Growth Metrics (YoY using CY/PY fields)."""
    out["RevenueGrowthYoY"] = _safe_div(
        _coerce(out, "TotalRevenueCY") - _coerce(out, "TotalRevenuePY"),
        _coerce(out, "TotalRevenuePY").abs(),
    )
    out["ExpenseGrowthYoY"] = _safe_div(
        _coerce(out, "TotalExpensesCY") - _coerce(out, "TotalExpensesPY"),
        _coerce(out, "TotalExpensesPY").abs(),
    )
    out["NetAssetGrowth"] = _safe_div(
        _coerce(out, "NetAssetsEOY") - _coerce(out, "NetAssetsBOY"),
        _coerce(out, "NetAssetsBOY").abs(),
    )
    out["ContributionGrowth"] = _safe_div(
        _coerce(out, "ContributionsGrantsCY") - _coerce(out, "ContributionsGrantsPY"),
        _coerce(out, "ContributionsGrantsPY").abs(),
    )
    return out


def _categorical(out: pd.DataFrame) -> pd.DataFrame:
    """Group 5: Classification / Categorical Features."""
    rev = _coerce(out, "TotalRevenueCY")
    tax_year = pd.to_numeric(out["TaxYear"], errors="coerce")
    formation_yr = pd.to_numeric(out["FormationYr"], errors="coerce")

    out["SizeBucket"] = pd.cut(
        rev,
        bins=[0, 5_000_000, 20_000_000, float("inf")],
        labels=["Small", "Mid", "Large"],
    )

    ntee = out["NTEE_CD"].astype(str).str.strip().str.upper()
    out["NTEEMajorSector"] = ntee.str[0].where(ntee.str[0].str.isalpha(), other=np.nan)

    out["OrgAge"] = (tax_year - formation_yr).clip(lower=0)

    # DotSize for brand map scatter
    out["DotSize"] = np.log10(rev.clip(lower=1))

    # ResilienceTier
    rm = out["OperatingReserveMonths"]
    sm = out["SurplusMargin"]
    dr = out["DebtRatio"]

    conditions = [
        (rm < 1) | (sm < -0.10) | (dr > 0.8),
        ((rm >= 1) & (rm <= 6)) | ((sm >= -0.10) & (sm <= 0)),
        (rm > 6) & (sm > 0),
    ]
    choices = ["At Risk", "Watch", "Stable"]
    out["ResilienceTier"] = np.select(conditions, choices, default="Watch")

    return out


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run the full feature engineering pipeline on a raw loaded DataFrame.
    Rows with null/zero TotalRevenueCY or TotalExpensesCY are dropped.
    Returns enriched DataFrame.
    """
    out = add_exclusion_flags(df)
    out = out[~out["_exclude"]].copy().reset_index(drop=True)

    out = _efficiency(out)
    out = _stability(out)
    out = _revenue_diversification(out)
    out = _growth(out)
    out = _categorical(out)

    return out
