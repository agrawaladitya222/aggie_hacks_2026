"""Module 2: peer-group Z-scores and deviation flags (PRD §6)."""

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


def add_peer_benchmarks(df: pd.DataFrame) -> pd.DataFrame:
    """Append Z-scores and Above/Below peer norm flags per PRD §6.2."""
    out = df.copy()
    for metric in BENCHMARK_METRICS:
        if metric not in out.columns:
            continue
        gm = out.groupby("PeerGroupID", observed=True)[metric].transform("mean")
        gs = out.groupby("PeerGroupID", observed=True)[metric].transform("std").replace(0, np.nan)
        z = (out[metric] - gm) / gs
        z_col = f"{metric}_ZScore"
        out[z_col] = z
        out[f"{metric}_Flag"] = np.where(
            z.abs() > 1.5,
            np.where(z > 0, "Above Peer Norm", "Below Peer Norm"),
            "Within Norm",
        )
    return out
