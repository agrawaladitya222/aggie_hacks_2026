from __future__ import annotations

import numpy as np
import pandas as pd


BENCHMARK_METRICS = [
    "ProgramExpenseRatio",
    "FundraisingRatio",
    "SurplusMargin",
    "OperatingReserveMonths",
    "DebtRatio",
    "GrantDependencyPct",
    "ProgramRevenuePct",
    "RevenueGrowthPct",
    "RevenuePerEmployee",
]


def add_peer_benchmarks(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = df.copy()
    df["PeerGroupID"] = df["Sector"].astype(str) + "_" + df["SizeCategory"].astype(str) + "_" + df["State"].astype(str)

    peer_counts = df["PeerGroupID"].value_counts()
    small_groups = set(peer_counts[peer_counts < 5].index)
    fallback = df["Sector"].astype(str) + "_" + df["SizeCategory"].astype(str)
    df.loc[df["PeerGroupID"].isin(small_groups), "PeerGroupID"] = fallback[df["PeerGroupID"].isin(small_groups)]

    for metric in BENCHMARK_METRICS:
        group_mean = df.groupby("PeerGroupID")[metric].transform("mean")
        group_std = df.groupby("PeerGroupID")[metric].transform("std")
        df[f"{metric}_ZScore"] = (df[metric] - group_mean) / group_std.replace(0, np.nan)
        z_col = f"{metric}_ZScore"
        df[f"{metric}_Flag"] = np.where(
            df[z_col].abs() > 1.5,
            np.where(df[z_col] > 0, "Above Peer Norm", "Below Peer Norm"),
            "Within Norm",
        )
        df[f"{metric}_PeerPctile"] = df.groupby("PeerGroupID")[metric].rank(pct=True)

    peer_summary = df.groupby("PeerGroupID")[BENCHMARK_METRICS].agg(["median", "mean", "std", "count"])
    return df, peer_summary
