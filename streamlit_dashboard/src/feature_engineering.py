"""Add display-only derived columns on top of the already-engineered master_990.csv data."""

from __future__ import annotations

import numpy as np
import pandas as pd


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    master_990.csv already contains all engineered financial ratios, peer Z-scores,
    AtRiskProba, AtRiskPredicted, ResilienceScore, etc.

    This function only adds lightweight display helpers needed by chart modules.
    """
    out = df.copy()

    rev = pd.to_numeric(out["TotalRevenueCY"], errors="coerce")

    # Log-scale dot size for scatter plots
    out["DotSize"] = np.log10(rev.clip(lower=1))

    # Exclude flag for brand map (needs ProgramSvcExpenses)
    prog = pd.to_numeric(out.get("ProgramSvcExpenses", pd.Series(dtype=float)), errors="coerce")
    out["_exclude_brand_map"] = prog.isna()

    # Resilience tier derived from rule-based columns (for color coding in charts)
    # master_990 has AtRisk (rule-based) and AtRiskPredicted (model); we keep both.
    # Tier label: use ResilienceScore for a 3-bucket display label
    score = pd.to_numeric(out.get("ResilienceScore", pd.Series(dtype=float)), errors="coerce")
    rm = pd.to_numeric(out.get("OperatingReserveMonths", pd.Series(dtype=float)), errors="coerce")
    sm = pd.to_numeric(out.get("SurplusMargin", pd.Series(dtype=float)), errors="coerce")
    dr = pd.to_numeric(out.get("DebtRatio", pd.Series(dtype=float)), errors="coerce")

    at_risk_rule = (rm < 1) | (sm < -0.10) | (dr > 0.8)
    watch = ((rm >= 1) & (rm <= 6)) | ((sm >= -0.10) & (sm <= 0))
    stable = (rm > 6) & (sm > 0)

    conditions = [at_risk_rule, watch, stable]
    choices = ["At Risk", "Watch", "Stable"]
    out["ResilienceTier"] = np.select(conditions, choices, default="Watch")

    # Revenue display label
    out["_TotalRevenueFmt"] = rev.apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
    out["_SurplusMarginFmt"] = pd.to_numeric(
        out.get("SurplusMargin", pd.Series(dtype=float)), errors="coerce"
    ).apply(lambda x: f"{x * 100:.1f}%" if pd.notna(x) else "N/A")
    out["_GrantDependencyFmt"] = pd.to_numeric(
        out.get("GrantDependencyPct", pd.Series(dtype=float)), errors="coerce"
    ).apply(lambda x: f"{x * 100:.1f}%" if pd.notna(x) else "N/A")

    return out
