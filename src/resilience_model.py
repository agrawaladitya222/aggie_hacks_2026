"""Module 3: AtRisk classification, model training, evaluation (PRD §7, §11)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    fbeta_score,
    roc_auc_score,
)
from sklearn.model_selection import GroupKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.utils.class_weight import compute_sample_weight

# Exclude CY terms that appear directly in the AtRisk rule (PRD §7.2) to avoid
# same-period definitional leakage; use PY proxies + composition/structure instead.
FEATURE_COLS = [
    "GrantDependencyPct",
    "ProgramRevenuePct",
    "InvestmentRevenuePct",
    "GovGrantPct",
    "ProgramExpenseRatio",
    "FundraisingRatio",
    "SalaryRatio",
    "DebtRatio",
    "AssetLiabilityRatio",
    "ExpenseGrowthPct",
    "ContributionGrowthPct",
    "SurplusMargin_PY",
    "ReserveMonths_BOY",
    "OrgAge",
    "Employees",
    "LogRevenue",
    "LogAssets",
]


def _make_xgb_class():
    try:
        import xgboost as xgb

        return xgb.XGBClassifier
    except ImportError:
        return None


def _xgb_pos_weight(y: np.ndarray) -> float:
    y = np.asarray(y)
    n_pos = (y == 1).sum()
    n_neg = (y == 0).sum()
    return float(n_neg / max(n_pos, 1))


def build_estimator(name: str, pos_weight: float) -> Any:
    if name == "LogisticRegression":
        return LogisticRegression(
            class_weight="balanced",
            max_iter=2000,
            random_state=42,
            solver="lbfgs",
        )
    if name == "RandomForest":
        return RandomForestClassifier(
            n_estimators=200,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=-1,
            max_depth=12,
            min_samples_leaf=5,
        )
    if name == "GradientBoosting":
        return GradientBoostingClassifier(
            n_estimators=180,
            learning_rate=0.06,
            max_depth=4,
            min_samples_leaf=20,
            subsample=0.9,
            random_state=42,
        )
    if name == "XGBoost":
        xgb_cls = _make_xgb_class()
        if xgb_cls is None:
            raise ValueError("XGBoost not installed")
        return xgb_cls(
            n_estimators=200,
            learning_rate=0.06,
            max_depth=5,
            min_child_weight=5,
            subsample=0.9,
            colsample_bytree=0.85,
            reg_lambda=1.0,
            scale_pos_weight=pos_weight,
            random_state=42,
            eval_metric="logloss",
        )
    raise KeyError(name)


def make_full_pipeline(estimator: Any) -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
            ("clf", estimator),
        ]
    )


def fit_pipeline(name: str, pipe: Pipeline, X: pd.DataFrame, y: np.ndarray) -> None:
    if name == "GradientBoosting":
        sw = compute_sample_weight("balanced", y)
        pipe.fit(X, y, clf__sample_weight=sw)
    else:
        pipe.fit(X, y)


def evaluate_binary(y_true, y_prob, y_pred) -> dict[str, float]:
    out: dict[str, float] = {
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "pr_auc": float(average_precision_score(y_true, y_prob)),
    }
    rep = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
    out["precision_at_risk"] = float(rep["1"]["precision"])
    out["recall_at_risk"] = float(rep["1"]["recall"])
    out["f1_at_risk"] = float(rep["1"]["f1-score"])
    out["accuracy"] = float(rep["accuracy"])
    return out


def temporal_split_mask(ty: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    t = pd.to_numeric(ty, errors="coerce")
    return np.where(t <= 2018)[0], np.where(t >= 2019)[0]


def group_kfold_auc(
    name: str,
    base_estimator: Any,
    X: pd.DataFrame,
    y: np.ndarray,
    groups: np.ndarray,
    n_splits: int = 5,
) -> tuple[float, float]:
    n_groups = len(np.unique(groups))
    n_splits = int(min(n_splits, max(2, n_groups - 1)))
    gkf = GroupKFold(n_splits=n_splits)
    scores: list[float] = []
    for train_i, val_i in gkf.split(X, y, groups):
        y_tr, y_va = y[train_i], y[val_i]
        if len(np.unique(y_va)) < 2:
            continue
        est = clone(base_estimator)
        if name == "XGBoost":
            est.set_params(scale_pos_weight=_xgb_pos_weight(y_tr))
        pipe = make_full_pipeline(est)
        fit_pipeline(name, pipe, X.iloc[train_i], y_tr)
        prob = pipe.predict_proba(X.iloc[val_i])[:, 1]
        pred = (prob >= 0.5).astype(int)
        scores.append(roc_auc_score(y_va, prob))
    if not scores:
        return float("nan"), float("nan")
    return float(np.mean(scores)), float(np.std(scores))


@dataclass
class TrainResult:
    best_model_name: str
    metrics_random_holdout: dict[str, float]
    metrics_temporal: dict[str, float]
    metrics_group_cv: dict[str, float]
    feature_importances: Optional[dict[str, float]]
    threshold_resilience_score: Optional[float]
    decision_threshold: float
    metrics_temporal_tuned: dict[str, float]


def _feature_importances(pipe: Pipeline) -> Optional[dict[str, float]]:
    clf = pipe.named_steps["clf"]
    if hasattr(clf, "feature_importances_"):
        imp = clf.feature_importances_
        return {n: float(v) for n, v in zip(FEATURE_COLS, imp)}
    if hasattr(clf, "coef_"):
        coef = np.ravel(np.abs(clf.coef_))
        return {n: float(v) for n, v in zip(FEATURE_COLS, coef)}
    return None


def tune_decision_threshold(y_true: np.ndarray, y_prob: np.ndarray) -> tuple[float, dict[str, float]]:
    """Pick cutoff maximizing F_beta (beta=1.4) to favor recall while keeping precision reasonable."""
    best_t, best_score = 0.5, -1.0
    for t in np.linspace(0.12, 0.88, 39):
        pred = (y_prob >= t).astype(int)
        fb = fbeta_score(y_true, pred, beta=1.4, zero_division=0)
        if fb > best_score:
            best_score, best_t = fb, float(t)
    pred = (y_prob >= best_t).astype(int)
    metrics = evaluate_binary(y_true, y_prob, pred)
    return best_t, metrics


def resilience_probability_threshold(
    df: pd.DataFrame,
    pipe: Pipeline,
    prob_target: float = 0.5,
) -> Optional[float]:
    """Rough score where P(AtRisk) crosses ``prob_target`` (linear interp between neighbors)."""
    sub = df[FEATURE_COLS + ["ResilienceScore"]].dropna(subset=["ResilienceScore"])
    if sub.empty:
        return None
    p = pipe.predict_proba(sub[FEATURE_COLS])[:, 1]
    tmp = sub[["ResilienceScore"]].copy()
    tmp["p"] = p
    tmp = tmp.sort_values("ResilienceScore")
    s = tmp["ResilienceScore"].to_numpy()
    pr = tmp["p"].to_numpy()
    for i in range(len(pr) - 1):
        a, b = pr[i], pr[i + 1]
        if (a - prob_target) * (b - prob_target) <= 0 and b != a:
            t = (prob_target - a) / (b - a)
            return float(s[i] + t * (s[i + 1] - s[i]))
    return float(np.median(s))


def train_and_select(
    df: pd.DataFrame,
    random_state: int = 42,
    *,
    max_rows: Optional[int] = None,
    cv_splits: int = 4,
) -> tuple[Pipeline, TrainResult]:
    full_df = df[df["AtRisk"].notna()].copy()
    select_df = full_df
    if max_rows is not None and len(full_df) > max_rows:
        select_df = full_df.sample(max_rows, random_state=random_state).reset_index(drop=True)
    X = select_df[FEATURE_COLS]
    y = select_df["AtRisk"].astype(int).values
    groups = pd.to_numeric(select_df["TaxYear"], errors="coerce").fillna(-1).astype(int).values

    X_train_r, X_test_r, y_train_r, y_test_r = train_test_split(
        X, y, test_size=0.2, random_state=random_state, stratify=y
    )

    tr_idx, te_idx = temporal_split_mask(select_df["TaxYear"])
    use_temporal = len(tr_idx) > 500 and len(te_idx) > 500

    model_names = ["LogisticRegression", "RandomForest", "GradientBoosting"]
    if _make_xgb_class() is not None:
        model_names.append("XGBoost")

    leaderboard: list[tuple[float, float, str, Any]] = []

    for name in model_names:
        pos_w = _xgb_pos_weight(y_train_r) if name == "XGBoost" else 1.0
        est = build_estimator(name, pos_w)
        pipe = make_full_pipeline(est)
        fit_pipeline(name, pipe, X_train_r, y_train_r)
        prob_r = pipe.predict_proba(X_test_r)[:, 1]
        pred_r = (prob_r >= 0.5).astype(int)
        m_random = evaluate_binary(y_test_r, prob_r, pred_r)

        if use_temporal:
            Xt, yt = X.iloc[tr_idx], y[tr_idx]
            Xv, yv = X.iloc[te_idx], y[te_idx]
            pos_te = _xgb_pos_weight(yt) if name == "XGBoost" else 1.0
            est_te = build_estimator(name, pos_te)
            pipe_te = make_full_pipeline(est_te)
            fit_pipeline(name, pipe_te, Xt, yt)
            if len(np.unique(yv)) >= 2:
                prob_t = pipe_te.predict_proba(Xv)[:, 1]
                pred_t = (prob_t >= 0.5).astype(int)
                m_temp = evaluate_binary(yv, prob_t, pred_t)
                temporal_auc = m_temp["roc_auc"]
            else:
                m_temp = m_random
                temporal_auc = m_random["roc_auc"]
        else:
            m_temp = m_random
            temporal_auc = m_random["roc_auc"]

        base_for_cv = build_estimator(name, _xgb_pos_weight(y))
        cv_mean, cv_std = group_kfold_auc(name, base_for_cv, X, y, groups, n_splits=cv_splits)

        leaderboard.append((temporal_auc, m_random["roc_auc"], name, m_temp, m_random, cv_mean, cv_std))

    leaderboard.sort(key=lambda row: (row[0], row[1]), reverse=True)
    (
        _,
        _,
        best_name,
        best_m_temp,
        best_m_random,
        cv_mean,
        cv_std,
    ) = leaderboard[0]

    dec_threshold = 0.5
    tuned_temporal = best_m_temp
    if use_temporal:
        Xt, yt = X.iloc[tr_idx], y[tr_idx]
        Xv, yv = X.iloc[te_idx], y[te_idx]
        pos_te = _xgb_pos_weight(yt) if best_name == "XGBoost" else 1.0
        est_tune = build_estimator(best_name, pos_te)
        pipe_tune = make_full_pipeline(est_tune)
        fit_pipeline(best_name, pipe_tune, Xt, yt)
        prob_v = pipe_tune.predict_proba(Xv)[:, 1]
        if len(np.unique(yv)) >= 2:
            dec_threshold, tuned_temporal = tune_decision_threshold(yv, prob_v)
    elif len(y_test_r) and len(np.unique(y_test_r)) >= 2:
        pos_w = _xgb_pos_weight(y_train_r) if best_name == "XGBoost" else 1.0
        est_tune = build_estimator(best_name, pos_w)
        pipe_tune = make_full_pipeline(est_tune)
        fit_pipeline(best_name, pipe_tune, X_train_r, y_train_r)
        prob_v = pipe_tune.predict_proba(X_test_r)[:, 1]
        dec_threshold, tuned_temporal = tune_decision_threshold(y_test_r, prob_v)

    X_full = full_df[FEATURE_COLS]
    y_full = full_df["AtRisk"].astype(int).values
    pos_final = _xgb_pos_weight(y_full) if best_name == "XGBoost" else 1.0
    final_est = build_estimator(best_name, pos_final)
    final_pipe = make_full_pipeline(final_est)
    fit_pipeline(best_name, final_pipe, X_full, y_full)

    thresh = resilience_probability_threshold(full_df, final_pipe)

    result = TrainResult(
        best_model_name=best_name,
        metrics_random_holdout=best_m_random,
        metrics_temporal=best_m_temp,
        metrics_group_cv={"mean_roc_auc": cv_mean, "std_roc_auc": cv_std},
        feature_importances=_feature_importances(final_pipe),
        threshold_resilience_score=thresh,
        decision_threshold=dec_threshold,
        metrics_temporal_tuned=tuned_temporal,
    )
    return final_pipe, result


def add_model_scores(
    df: pd.DataFrame,
    pipe: Pipeline,
    decision_threshold: float = 0.5,
) -> pd.DataFrame:
    out = df.copy()
    out["AtRiskProba"] = pipe.predict_proba(out[FEATURE_COLS])[:, 1]
    out["AtRiskPredicted"] = (out["AtRiskProba"] >= decision_threshold).astype(int)
    return out


def save_artifacts(pipe: Pipeline, result: TrainResult, out_dir: str | Path) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, out_dir / "resilience_classifier.joblib")
    with open(out_dir / "train_metrics.json", "w", encoding="utf-8") as f:
        json.dump(asdict(result), f, indent=2)
