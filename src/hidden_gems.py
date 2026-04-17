from __future__ import annotations

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Minimum meaningful stabilization donation.
# Orgs whose DonationToStabilize falls below this floor are considered
# effectively already stable — their "need" is operating float, not a
# strategic grant. They're excluded from Cost-Efficiency ranking so we
# don't produce inflated ROI ratios driven by tiny denominators
# (e.g. an org that needs $2,540 to stabilize and spends $1M/yr on
# programs shows a nominal ROI of $400+ per $1 donated, which isn't a
# meaningful funding opportunity).
# Tune here to change the floor across the whole pipeline.
# ---------------------------------------------------------------------------
MIN_MEANINGFUL_DONATION: float = 25_000.0


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

    # --- Candidate pool ---------------------------------------------------
    # High impact, modest budget, growing, not already at high risk.
    hidden = out[
        (out["ImpactEfficiencyScore"] > out["ImpactEfficiencyScore"].quantile(0.80))
        & (out["TotalRevenueCY"] < out["TotalRevenueCY"].quantile(0.50))
        & (out["RevenueGrowthPct"] > 0)
        & (out["ResilienceScore"] > 40)
    ].copy()

    # Deduplicate: one row per organization, keeping the most recent filing.
    # Prevents the same org from being counted 7x across 2018–2024.
    if "TaxYear" in hidden.columns:
        hidden = (
            hidden.sort_values("TaxYear", ascending=False)
            .drop_duplicates(subset="EIN", keep="first")
        )

    hidden["DonationToStabilize"] = hidden.apply(donation_tipping_point, axis=1)

    # --- Per-organization ROI metrics ------------------------------------
    # AnnualProgramImpact: dollars of mission work the org delivers each year.
    # ProgramImpactPerDollar: for every $1 of stabilization funding, how many
    # dollars of annual program activity are preserved. This is the core ROI.
    hidden["AnnualProgramImpact"] = hidden["ProgramSvcExpenses"]
    hidden["ProgramImpactPerDollar"] = np.where(
        hidden["DonationToStabilize"] > 0,
        hidden["AnnualProgramImpact"] / hidden["DonationToStabilize"],
        np.nan,
    )
    # People (staff + volunteers) engaged per $10K of stabilization donation.
    hidden["PeopleEngagedPer10K"] = np.where(
        hidden["DonationToStabilize"] > 0,
        (hidden["Employees"].fillna(0) + hidden["Volunteers"].fillna(0))
        * 10_000 / hidden["DonationToStabilize"],
        np.nan,
    )

    # --- Cost-Efficiency Score (0–100) -----------------------------------
    # Computed only on orgs whose stabilization need meets the minimum
    # meaningful threshold (MIN_MEANINGFUL_DONATION). This excludes
    # "token-donation" cases whose tiny denominators would otherwise
    # produce extreme ROI ratios and distort the ranking.
    # Weights:
    #   40%  ROI (program impact per donation dollar)
    #   30%  ImpactEfficiencyScore (overall quality)
    #   15%  Revenue growth (momentum)
    #   15%  Urgency (lower reserves = higher score — funding matters more)
    hidden["CostEfficiencyScore"] = np.nan
    hidden["ROI_Percentile"] = np.nan
    mask_needs = hidden["DonationToStabilize"] >= MIN_MEANINGFUL_DONATION
    if mask_needs.any():
        sub = hidden.loc[mask_needs]
        rank_roi = percentile_rank(sub["ProgramImpactPerDollar"])
        rank_impact = percentile_rank(sub["ImpactEfficiencyScore"])
        rank_growth = percentile_rank(sub["RevenueGrowthPct"])
        rank_urgency = 1 - percentile_rank(sub["OperatingReserveMonths"])
        cost_eff = (
            0.40 * rank_roi
            + 0.30 * rank_impact
            + 0.15 * rank_growth
            + 0.15 * rank_urgency
        ) * 100
        hidden.loc[mask_needs, "CostEfficiencyScore"] = cost_eff.values
        hidden.loc[mask_needs, "ROI_Percentile"] = rank_roi.values

    # --- Priority tier assignment ---------------------------------------
    ranked = hidden["CostEfficiencyScore"].rank(ascending=False, method="min")
    hidden["PriorityRank"] = ranked.astype("Int64")
    hidden["PriorityTier"] = "Broader Universe"
    hidden.loc[ranked <= 500, "PriorityTier"] = "Extended Shortlist"
    hidden.loc[ranked <= 100, "PriorityTier"] = "Priority Shortlist"
    hidden.loc[ranked <= 25, "PriorityTier"] = "Top 25 Priority"
    hidden.loc[~mask_needs, "PriorityTier"] = "Already Stable"

    hidden = hidden.sort_values(
        ["CostEfficiencyScore", "ImpactEfficiencyScore"],
        ascending=[False, False],
        na_position="last",
    )
    return out, hidden
