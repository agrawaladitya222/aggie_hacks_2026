from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier


FEATURE_COLS = [
    "GrantDependencyPct",
    "ProgramRevenuePct",
    "InvestmentRevenuePct",
    "GovGrantPct",
    "ProgramExpenseRatio",
    "FundraisingRatio",
    "SalaryRatio",
    "SurplusMargin",
    "OperatingReserveMonths",
    "DebtRatio",
    "AssetLiabilityRatio",
    "RevenueGrowthPct",
    "ExpenseGrowthPct",
    "ContributionGrowthPct",
    "NetAssetGrowthPct",
    "OrgAge",
    "Employees",
    "LogRevenue",
    "LogAssets",
]


def add_risk_and_resilience_scores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["AtRisk"] = (
        (df["SurplusMargin"] < -0.10)
        | (df["OperatingReserveMonths"] < 1)
        | (df["NetAssetGrowthPct"] < -0.20)
        | (df["RevenueGrowthPct"] < -0.25)
    ).astype(int)
    df["ResilienceScore"] = (
        np.clip(df["OperatingReserveMonths"] / 12, 0, 1) * 30
        + np.clip(1 - df["GrantDependencyPct"], 0, 1) * 20
        + np.clip(df["ProgramExpenseRatio"], 0, 1) * 20
        + np.clip(df["SurplusMargin"] * 100, 0, 15)
        + np.clip((1 - df["DebtRatio"]) * 15, 0, 15)
    ).round(1)
    return df


def _make_eda_plots(df: pd.DataFrame, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(14, 10))
    corr = df[FEATURE_COLS].corr(numeric_only=True)
    sns.heatmap(corr, cmap="RdBu_r", center=0)
    plt.title("Feature Correlation Matrix")
    plt.tight_layout()
    plt.savefig(output_dir / "eda_correlation_heatmap.png", dpi=140)
    plt.close()

    sample_cols = FEATURE_COLS[:16]
    fig, axes = plt.subplots(4, 4, figsize=(18, 14))
    for ax, col in zip(axes.flat, sample_cols):
        sns.boxplot(data=df, x="AtRisk", y=col, ax=ax)
        ax.set_title(col)
    plt.tight_layout()
    plt.savefig(output_dir / "eda_feature_vs_target.png", dpi=140)
    plt.close()


def train_resilience_model(
    df: pd.DataFrame, artifacts_dir: str = "artifacts", outputs_dir: str = "outputs"
) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = add_risk_and_resilience_scores(df)
    ntee_dummies = pd.get_dummies(df["NTEEMajorGroup"], prefix="NTEE", dummy_na=False)
    model_df = pd.concat([df, ntee_dummies], axis=1)
    feature_cols = FEATURE_COLS + list(ntee_dummies.columns)

    X = model_df[feature_cols]
    y = model_df["AtRisk"]

    imputer = SimpleImputer(strategy="median")
    X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=feature_cols, index=X.index)
    scaler = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X_imputed), columns=feature_cols, index=X.index)

    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.2, random_state=42, stratify=y
    )

    models = {
        "Logistic Regression": LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42),
        "Random Forest": RandomForestClassifier(n_estimators=120, class_weight="balanced", random_state=42, n_jobs=-1),
        "Gradient Boosting": GradientBoostingClassifier(n_estimators=120, learning_rate=0.08, max_depth=3, random_state=42),
        "XGBoost": XGBClassifier(
            n_estimators=120,
            learning_rate=0.08,
            max_depth=4,
            random_state=42,
            eval_metric="logloss",
            subsample=0.8,
            colsample_bytree=0.8,
        ),
    }

    rows: list[dict[str, float | str]] = []
    best_name = ""
    best_model = None
    best_auc = -1.0

    for name, model in models.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, y_prob)
        report = classification_report(y_test, y_pred, output_dict=True)
        rows.append(
            {
                "Model": name,
                "AUC-ROC": auc,
                "Precision (At Risk)": report["1"]["precision"],
                "Recall (At Risk)": report["1"]["recall"],
                "F1 (At Risk)": report["1"]["f1-score"],
                "Accuracy": report["accuracy"],
            }
        )
        if auc > best_auc:
            best_auc = auc
            best_name = name
            best_model = model

    assert best_model is not None
    results_df = pd.DataFrame(rows).sort_values("AUC-ROC", ascending=False)

    importances = pd.Series(best_model.feature_importances_, index=feature_cols).sort_values(ascending=False)
    Path(outputs_dir).mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(9, 7))
    importances.head(20).sort_values().plot(kind="barh")
    plt.title("Top 20 Feature Importances")
    plt.tight_layout()
    plt.savefig(Path(outputs_dir) / "feature_importance.png", dpi=140)
    plt.close()

    _make_eda_plots(model_df, Path(outputs_dir))

    cv_scores = cross_val_score(best_model, X_scaled, y, cv=5, scoring="roc_auc")
    model_df["AtRiskProbability"] = best_model.predict_proba(X_scaled)[:, 1]

    artifacts = Path(artifacts_dir)
    artifacts.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {"model": best_model, "imputer": imputer, "scaler": scaler, "feature_cols": feature_cols},
        artifacts / "resilience_classifier.joblib",
    )
    metrics = {
        "best_model": best_name,
        "cv_auc_mean": float(cv_scores.mean()),
        "cv_auc_std": float(cv_scores.std()),
        "all_models": results_df.to_dict(orient="records"),
        "feature_importances": importances.head(20).to_dict(),
    }
    with (artifacts / "train_metrics.json").open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    return model_df.drop(columns=ntee_dummies.columns), results_df
