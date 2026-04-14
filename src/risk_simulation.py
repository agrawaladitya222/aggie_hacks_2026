from __future__ import annotations

import numpy as np
import pandas as pd


SCENARIOS = {
    "Grant Shock (-30%)": {"ContributionsGrantsCY": 0.70},
    "Gov Grant Shock (-50%)": {"GovernmentGrantsAmt": 0.50},
    "Program Rev Shock (-25%)": {"ProgramServiceRevCY": 0.75},
    "Investment Shock (-40%)": {"InvestmentIncomeCY": 0.60},
    "Combined Recession (-20%)": {
        "ContributionsGrantsCY": 0.80,
        "ProgramServiceRevCY": 0.80,
        "InvestmentIncomeCY": 0.80,
        "GovernmentGrantsAmt": 0.80,
    },
}


def simulate_shock(df: pd.DataFrame, scenario_name: str, adjustments: dict[str, float]) -> pd.DataFrame:
    sim = df.copy()
    total_loss = np.zeros(len(sim))
    for col, multiplier in adjustments.items():
        original = sim[col].fillna(0)
        shocked = original * multiplier
        total_loss += (original - shocked).to_numpy()
        sim[f"PostShock_{col}"] = shocked

    sim["PostShock_TotalRevenue"] = sim["TotalRevenueCY"] - total_loss
    sim["PostShock_NetRevenue"] = sim["PostShock_TotalRevenue"] - sim["TotalExpensesCY"]
    sim["PostShock_SurplusMargin"] = np.where(
        sim["PostShock_TotalRevenue"] > 0,
        sim["PostShock_NetRevenue"] / sim["PostShock_TotalRevenue"],
        np.nan,
    )
    sim["MonthsToInsolvency"] = np.where(
        sim["PostShock_NetRevenue"] < 0,
        sim["NetAssetsEOY"] / (sim["PostShock_NetRevenue"].abs() / 12),
        np.inf,
    )
    sim["MonthsToInsolvency"] = sim["MonthsToInsolvency"].clip(lower=0, upper=120)
    sim["PostShock_Status"] = np.where(
        sim["PostShock_NetRevenue"] >= 0,
        "Survives (Surplus)",
        np.where(
            sim["MonthsToInsolvency"] > 12,
            "Stressed (>12mo reserves)",
            np.where(
                sim["MonthsToInsolvency"] > 3,
                "At Risk (3-12mo reserves)",
                "Critical (<3mo reserves)",
            ),
        ),
    )
    sim["Scenario"] = scenario_name
    return sim


def estimate_recovery(row: pd.Series, annual_recovery_rate: float = 0.05) -> float:
    if row["PostShock_NetRevenue"] >= 0:
        return 0
    deficit = abs(row["PostShock_NetRevenue"])
    revenue = row["PostShock_TotalRevenue"]
    expenses = row["TotalExpensesCY"]
    years = 0
    cumulative_surplus = 0.0
    while cumulative_surplus < deficit and years < 20:
        years += 1
        revenue *= 1 + annual_recovery_rate
        annual_surplus = revenue - expenses
        if annual_surplus > 0:
            cumulative_surplus += annual_surplus
    return float(years) if years < 20 else np.nan


def run_risk_simulations(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    sims = [simulate_shock(df, name, adjustments) for name, adjustments in SCENARIOS.items()]
    sim_df = pd.concat(sims, ignore_index=True)
    sim_df["RecoveryYears"] = sim_df.apply(estimate_recovery, axis=1)

    grant_shock = sim_df[sim_df["Scenario"] == "Grant Shock (-30%)"].copy()
    grant_shock["IsCritical"] = (grant_shock["PostShock_Status"] == "Critical (<3mo reserves)").astype(int)
    grant_shock["DepBucket"] = pd.cut(grant_shock["GrantDependencyPct"], bins=10)
    grant_shock["ReserveBucket"] = pd.cut(
        grant_shock["OperatingReserveMonths"], bins=[0, 1, 3, 6, 12, 120], labels=["<1mo", "1-3mo", "3-6mo", "6-12mo", "12mo+"]
    )
    threshold = grant_shock.pivot_table(
        values="IsCritical",
        index="DepBucket",
        columns="ReserveBucket",
        aggfunc="mean",
        observed=False,
    )
    return sim_df, threshold
