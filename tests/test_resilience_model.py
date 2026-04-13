"""Smoke tests for resilience training."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data_pipeline import build_master_table
from src.peers import add_peer_benchmarks
from src.resilience_model import add_model_scores, train_and_select


def test_train_on_real_csv_smoke():
    csv_dir = ROOT / "data" / "data_csv"
    if not any(csv_dir.glob("*_990.csv")):
        return
    df = build_master_table(data_csv_dir=csv_dir, repo_root=ROOT)
    df = add_peer_benchmarks(df)
    pipe, result = train_and_select(df, max_rows=6000, cv_splits=3)
    assert result.best_model_name
    assert result.metrics_random_holdout["roc_auc"] >= 0.5
    scored = add_model_scores(df.head(200), pipe, decision_threshold=result.decision_threshold)
    assert "AtRiskProba" in scored.columns
