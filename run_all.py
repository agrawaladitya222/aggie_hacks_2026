from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_pipeline import run_data_pipeline
from src.hidden_gems import find_hidden_gems
from src.peers import add_peer_benchmarks
from src.resilience_model import train_resilience_model
from src.risk_simulation import run_risk_simulations


def main() -> None:
    Path("data").mkdir(exist_ok=True)
    Path("artifacts").mkdir(exist_ok=True)
    Path("outputs").mkdir(exist_ok=True)

    print("Module 1: Data ingestion + feature engineering...")
    df = run_data_pipeline()
    print(f"  Master rows: {len(df):,}")

    print("Module 2: Peer benchmarking...")
    df, peer_summary = add_peer_benchmarks(df)
    peer_summary.to_csv("data/peer_group_stats.csv")
    print(f"  Peer groups: {peer_summary.shape[0]:,}")

    print("Module 3: Resilience model + artifacts...")
    df, model_results = train_resilience_model(df, artifacts_dir="artifacts", outputs_dir="outputs")
    model_results.to_csv("outputs/model_comparison.csv", index=False)
    print(f"  Best AUC: {model_results['AUC-ROC'].max():.4f}")

    print("Module 4: Financial risk simulation...")
    sim_df, threshold = run_risk_simulations(df)
    summary_cols = [
        "EIN",
        "OrgName",
        "Sector",
        "State",
        "SizeCategory",
        "Scenario",
        "PostShock_TotalRevenue",
        "PostShock_NetRevenue",
        "PostShock_SurplusMargin",
        "MonthsToInsolvency",
        "PostShock_Status",
        "RecoveryYears",
    ]
    sim_df[summary_cols].to_csv("data/simulation_results.csv", index=False)
    threshold.to_csv("outputs/threshold_heatmap_data.csv")

    print("Module 5: Hidden gems discovery...")
    df, hidden = find_hidden_gems(df)
    gem_cols = [
        "EIN",
        "OrgName",
        "State",
        "City",
        "Sector",
        "SizeCategory",
        "TotalRevenueCY",
        "ImpactEfficiencyScore",
        "ResilienceScore",
        "ProgramExpenseRatio",
        "RevenueGrowthPct",
        "OperatingReserveMonths",
        "DonationToStabilize",
        "Mission",
    ]
    hidden[gem_cols].to_csv("data/hidden_gems.csv", index=False)

    df.to_csv("data/master_990.csv", index=False)
    print("Done.")
    print(f"  Final master rows: {len(df):,}")
    print(f"  Hidden gems: {len(hidden):,}")
    print(f"  At-risk rate: {df['AtRisk'].mean():.1%}")


if __name__ == "__main__":
    main()
