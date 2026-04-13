#!/usr/bin/env python3
"""Build master table, train resilience model, optional EDA plots (PRD §5–7)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

from src.data_pipeline import build_master_table, save_master
from src.peers import add_peer_benchmarks
from src.resilience_model import (
    FEATURE_COLS,
    add_model_scores,
    save_artifacts,
    train_and_select,
)


def run_eda(df: pd.DataFrame, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    feat = [c for c in FEATURE_COLS if c in df.columns]
    plt.figure(figsize=(14, 10))
    corr = df[feat].corr()
    sns.heatmap(corr, annot=False, fmt=".2f", cmap="RdBu_r", center=0)
    plt.title("Feature correlation (resilience model inputs)")
    plt.tight_layout()
    plt.savefig(out_dir / "eda_correlation_heatmap.png", dpi=150)
    plt.close()

    n = min(16, len(feat))
    fig, axes = plt.subplots(4, 4, figsize=(16, 14))
    axes = axes.ravel()
    for i, col in enumerate(feat[:n]):
        df.boxplot(column=col, by="AtRisk", ax=axes[i])
        axes[i].set_title(col)
        axes[i].set_xlabel("AtRisk")
    for j in range(n, len(axes)):
        axes[j].set_visible(False)
    plt.suptitle("")
    plt.tight_layout()
    plt.savefig(out_dir / "eda_feature_vs_target.png", dpi=150)
    plt.close()


def plot_feature_importance(result, out_dir: Path) -> None:
    imp = result.feature_importances
    if not imp:
        return
    s = pd.Series(imp).sort_values(ascending=True)
    plt.figure(figsize=(10, 8))
    s.plot(kind="barh")
    plt.title("Feature importance — resilience model")
    plt.xlabel("Importance")
    plt.tight_layout()
    plt.savefig(out_dir / "feature_importance.png", dpi=150)
    plt.close()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--eda", action="store_true", help="Write EDA plots to outputs/")
    p.add_argument("--root", type=Path, default=ROOT, help="Repository root")
    p.add_argument(
        "--max-train-rows",
        type=int,
        default=None,
        help="Subsample rows for faster training (debug)",
    )
    p.add_argument("--cv-splits", type=int, default=4, help="GroupKFold splits by TaxYear")
    args = p.parse_args()

    data_csv = args.root / "data" / "data_csv"
    master_path = args.root / "data" / "master_990.csv"
    artifact_dir = args.root / "artifacts"
    output_dir = args.root / "outputs"

    print("Building master table...")
    df = build_master_table(data_csv_dir=data_csv, repo_root=args.root)
    df = add_peer_benchmarks(df)
    save_master(df, master_path)
    print(f"Saved {master_path} ({len(df)} rows)")

    if args.eda:
        print("Writing EDA plots...")
        run_eda(df, output_dir)

    print("Training models (random holdout, temporal, group CV)...")
    pipe, result = train_and_select(df, max_rows=args.max_train_rows, cv_splits=args.cv_splits)
    save_artifacts(pipe, result, artifact_dir)
    plot_feature_importance(result, output_dir)

    df = add_model_scores(df, pipe, decision_threshold=result.decision_threshold)
    save_master(df, master_path)
    print(f"Updated {master_path} with AtRiskProba / AtRiskPredicted")

    print("\n=== Selected model:", result.best_model_name)
    print("Random holdout:", result.metrics_random_holdout)
    print("Temporal (train<=2018, test>=2019):", result.metrics_temporal)
    print("Temporal with tuned P cutoff:", result.metrics_temporal_tuned)
    print("Decision threshold (prob):", result.decision_threshold)
    print("Group CV (by TaxYear):", result.metrics_group_cv)
    print("Resilience score ~ P(AtRisk)>=0.5 threshold:", result.threshold_resilience_score)


if __name__ == "__main__":
    main()
