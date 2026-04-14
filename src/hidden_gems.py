from __future__ import annotations

import numpy as np
import pandas as pd


def percentile_rank(series: pd.Series) -> pd.Series:
    return series.rank(pct=True)


def donation_tipping_point(row: pd.Series) -> float:
    current_reserves_months = row["OperatingReserveMonths"]
    monthly_expenses = row["TotalExpensesCY"] / 12
    if current_reserves_months >= 6:
        return 0.0
    months_needed = 6 - max(current_reserves_months, 0)
    return float(round(months_needed * monthly_expenses, 0))


def find_hidden_gems(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = df.copy()
    out["Impact_ProgramEff"] = percentile_rank(out["ProgramExpenseRatio"])
    out["Impact_Growth"] = percentile_rank(out["RevenueGrowthPct"])
    out["ProgramLeverage"] = np.where(
        out["ContributionsGrantsCY"] > 0, out["ProgramSvcExpenses"] / out["ContributionsGrantsCY"], np.nan
    )
    out["Impact_Leverage"] = percentile_rank(out["ProgramLeverage"])
    out["CommunityReach"] = (out["Employees"].fillna(0) + out["Volunteers"].fillna(0)) / (out["TotalRevenueCY"] / 1_000_000)
    out["Impact_Reach"] = percentile_rank(out["CommunityReach"])
    out["Impact_Sustainability"] = percentile_rank(out["ResilienceScore"])
    out["ImpactEfficiencyScore"] = (
        0.25 * out["Impact_ProgramEff"]
        + 0.20 * out["Impact_Growth"]
        + 0.20 * out["Impact_Leverage"]
        + 0.15 * out["Impact_Reach"]
        + 0.20 * out["Impact_Sustainability"]
    ) * 100

    hidden = out[
        (out["ImpactEfficiencyScore"] > out["ImpactEfficiencyScore"].quantile(0.80))
        & (out["TotalRevenueCY"] < out["TotalRevenueCY"].quantile(0.50))
        & (out["RevenueGrowthPct"] > 0)
        & (out["ResilienceScore"] > 40)
    ].copy()
    hidden["DonationToStabilize"] = hidden.apply(donation_tipping_point, axis=1)
    hidden = hidden.sort_values("ImpactEfficiencyScore", ascending=False)
    return out, hidden
