"""Tab 2: Resilience Model Insights — XGBoost predictions and explainability."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

_FEATURE_CATEGORY = {
    "ReserveMonths_BOY": "Balance Sheet",
    "AssetLiabilityRatio": "Balance Sheet",
    "DebtRatio": "Balance Sheet",
    "LogAssets": "Balance Sheet",
    "SurplusMargin_PY": "Prior-Year Financials",
    "ContributionGrowthPct": "Growth / Momentum",
    "ExpenseGrowthPct": "Growth / Momentum",
    "RevenueGrowthPct": "Growth / Momentum",
    "GrantDependencyPct": "Revenue Mix",
    "ProgramRevenuePct": "Revenue Mix",
    "InvestmentRevenuePct": "Revenue Mix",
    "GovGrantPct": "Revenue Mix",
    "ProgramExpenseRatio": "Operations",
    "FundraisingRatio": "Operations",
    "SalaryRatio": "Operations",
    "LogRevenue": "Scale",
    "OrgAge": "Scale",
    "Employees": "Scale",
}

_CATEGORY_COLORS = {
    "Balance Sheet": "#4a90d9",
    "Prior-Year Financials": "#9b59b6",
    "Growth / Momentum": "#27ae60",
    "Revenue Mix": "#e67e22",
    "Operations": "#e74c3c",
    "Scale": "#7f8c8d",
}

_FEATURE_LABELS = {
    "ReserveMonths_BOY": "Reserve Months (prior year)",
    "ContributionGrowthPct": "Contribution Growth %",
    "AssetLiabilityRatio": "Asset / Liability Ratio",
    "DebtRatio": "Debt Ratio",
    "SurplusMargin_PY": "Surplus Margin (prior year)",
    "ExpenseGrowthPct": "Expense Growth %",
    "GrantDependencyPct": "Grant Dependency %",
    "ProgramRevenuePct": "Program Revenue %",
    "InvestmentRevenuePct": "Investment Income %",
    "GovGrantPct": "Gov Grant %",
    "ProgramExpenseRatio": "Program Expense Ratio",
    "FundraisingRatio": "Fundraising Ratio",
    "SalaryRatio": "Salary Ratio",
    "LogRevenue": "Log Revenue",
    "LogAssets": "Log Assets",
    "OrgAge": "Organization Age",
    "Employees": "Employee Count",
}


def render(df: pd.DataFrame, train_metrics: dict) -> None:
    st.header("Resilience Model Insights")
    st.caption(
        "XGBoost classifier trained on 7 years of Form 990 data. "
        "Decision threshold tuned at 0.36 to maximize recall of at-risk organizations."
    )

    if not train_metrics:
        st.warning("Model metrics not available. Run `scripts/build_artifacts.py` to generate artifacts.")
        return

    # ── Model Performance Cards ───────────────────────────────────────────────
    st.subheader("Model Performance Summary")
    _model_performance_cards(train_metrics)
    st.divider()

    # ── Feature Importance ────────────────────────────────────────────────────
    col_imp, col_exp = st.columns([2, 1])
    with col_imp:
        st.subheader("What Drives At-Risk Predictions?")
        _feature_importance_chart(train_metrics)

    with col_exp:
        st.subheader("Feature Interpretation Guide")
        _feature_guide()

    st.divider()

    # ── Risk Probability Distribution ─────────────────────────────────────────
    col_hist, col_scatter = st.columns(2)
    with col_hist:
        st.subheader("Risk Probability Distribution")
        _risk_histogram(df, train_metrics)

    with col_scatter:
        st.subheader("Resilience Score vs. Model Risk Probability")
        _score_vs_proba(df, train_metrics)

    st.divider()

    # ── Confusion Matrix style metrics ────────────────────────────────────────
    st.subheader("Threshold Analysis: Temporal Holdout (2019+)")
    _threshold_analysis(train_metrics)


# ─────────────────────────── helpers ─────────────────────────────────────────

def _model_performance_cards(tm: dict) -> None:
    views = [
        ("Random 80/20 Holdout", tm.get("metrics_random_holdout", {})),
        ("Temporal (train ≤2018, test ≥2019)", tm.get("metrics_temporal", {})),
        ("Temporal + Tuned Threshold (0.36)", tm.get("metrics_temporal_tuned", {})),
        ("Group CV by Tax Year", tm.get("metrics_group_cv", {})),
    ]

    cols = st.columns(len(views))
    for col, (label, m) in zip(cols, views):
        with col:
            st.markdown(f"**{label}**")
            if "roc_auc" in m:
                st.metric("ROC-AUC", f"{m['roc_auc']:.3f}")
            if "pr_auc" in m:
                st.metric("PR-AUC", f"{m['pr_auc']:.3f}")
            if "precision_at_risk" in m:
                st.metric("Precision (At Risk)", f"{m['precision_at_risk']:.3f}")
            if "recall_at_risk" in m:
                st.metric("Recall (At Risk)", f"{m['recall_at_risk']:.3f}")
            if "f1_at_risk" in m:
                st.metric("F1 (At Risk)", f"{m['f1_at_risk']:.3f}")
            if "mean_roc_auc" in m:
                std = m.get("std_roc_auc", 0)
                st.metric("Mean ROC-AUC (CV)", f"{m['mean_roc_auc']:.3f} ± {std:.3f}")


def _feature_importance_chart(tm: dict) -> None:
    importances = tm.get("feature_importances", {})
    if not importances:
        st.info("Feature importances not available.")
        return

    sorted_feats = sorted(importances.items(), key=lambda x: x[1])
    names = [_FEATURE_LABELS.get(k, k) for k, _ in sorted_feats]
    values = [v for _, v in sorted_feats]
    categories = [_FEATURE_CATEGORY.get(k, "Other") for k, _ in sorted_feats]
    colors = [_CATEGORY_COLORS.get(c, "#aaaaaa") for c in categories]

    fig = go.Figure(go.Bar(
        x=values,
        y=names,
        orientation="h",
        marker_color=colors,
        text=[f"{v:.3f}" for v in values],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Importance: %{x:.4f}<extra></extra>",
    ))

    # Legend for categories (manual traces for legend)
    seen = set()
    for cat, col in _CATEGORY_COLORS.items():
        if cat in categories and cat not in seen:
            fig.add_trace(go.Bar(
                x=[None], y=[None],
                orientation="h",
                name=cat,
                marker_color=col,
                showlegend=True,
            ))
            seen.add(cat)

    fig.update_layout(
        xaxis_title="Feature Importance (XGBoost gain)",
        yaxis_title="",
        xaxis=dict(range=[0, max(values) * 1.3]),
        legend=dict(title="Category", x=0.6, y=0.05, font_size=11),
        margin=dict(t=10, b=10, l=10, r=60),
        height=max(340, len(names) * 22),
        plot_bgcolor="#f9f9f9",
        barmode="overlay",
    )
    st.plotly_chart(fig, use_container_width=True)


def _feature_guide() -> None:
    guide = [
        ("Reserve Months (BOY)", "Months of expenses covered by net assets at start of year. <b>Top predictor</b>."),
        ("Contribution Growth %", "YoY change in donations/grants. Declining momentum signals risk."),
        ("Asset/Liability Ratio", "Higher = stronger balance sheet cushion."),
        ("Debt Ratio", "Liabilities as % of assets. >80% is a critical threshold."),
        ("Surplus Margin (PY)", "Prior-year net margin. Persistent deficits predict future distress."),
        ("Expense Growth %", "Rising costs without revenue growth precedes risk."),
        ("Grant Dependency %", "High reliance on grants = vulnerable to funding shocks."),
    ]
    for feat, desc in guide:
        st.markdown(f"**{feat}** — {desc}", unsafe_allow_html=True)


def _risk_histogram(df: pd.DataFrame, tm: dict) -> None:
    proba = pd.to_numeric(df.get("AtRiskProba", pd.Series(dtype=float)), errors="coerce").dropna()
    if proba.empty:
        st.info("AtRiskProba column not available.")
        return

    threshold = tm.get("decision_threshold", 0.36)
    n_flagged = int((proba >= threshold).sum())
    n_total = len(proba)

    fig = go.Figure()

    # Safe region
    safe = proba[proba < threshold]
    risky = proba[proba >= threshold]

    fig.add_trace(go.Histogram(
        x=safe, name="Not Flagged",
        marker_color="#2ecc71", opacity=0.8,
        xbins=dict(start=0, end=1, size=0.02),
        hovertemplate="Prob: %{x:.2f}<br>Count: %{y:,}<extra></extra>",
    ))
    fig.add_trace(go.Histogram(
        x=risky, name="Flagged At Risk",
        marker_color="#e74c3c", opacity=0.8,
        xbins=dict(start=0, end=1, size=0.02),
        hovertemplate="Prob: %{x:.2f}<br>Count: %{y:,}<extra></extra>",
    ))
    fig.add_vline(
        x=threshold, line_dash="dash", line_color="#333333",
        annotation_text=f"Threshold ({threshold})",
        annotation_position="top right",
        annotation_font_size=12,
    )
    fig.update_layout(
        barmode="overlay",
        xaxis_title="P(At Risk) from XGBoost",
        yaxis_title="Number of Organizations",
        legend=dict(x=0.65, y=0.99),
        margin=dict(t=10, b=10, l=10, r=10),
        height=300,
        plot_bgcolor="#f9f9f9",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"**{n_flagged:,}** of **{n_total:,}** orgs flagged at risk (threshold = {threshold})")


def _score_vs_proba(df: pd.DataFrame, tm: dict) -> None:
    score = pd.to_numeric(df.get("ResilienceScore", pd.Series(dtype=float)), errors="coerce")
    proba = pd.to_numeric(df.get("AtRiskProba", pd.Series(dtype=float)), errors="coerce")
    tier = df.get("ResilienceTier", pd.Series("Watch", index=df.index))

    mask = score.notna() & proba.notna()
    plot_df = pd.DataFrame({
        "ResilienceScore": score[mask].values,
        "AtRiskProba": proba[mask].values,
        "Tier": tier[mask].values if hasattr(tier[mask], "values") else tier[mask],
    })

    # Downsample if too many points
    if len(plot_df) > 5000:
        plot_df = plot_df.sample(5000, random_state=42)

    thresh_score = tm.get("threshold_resilience_score", 14.6)
    decision_threshold = tm.get("decision_threshold", 0.36)

    color_map = {"Stable": "#2ecc71", "Watch": "#f39c12", "At Risk": "#e74c3c"}

    fig = px.scatter(
        plot_df, x="ResilienceScore", y="AtRiskProba",
        color="Tier", color_discrete_map=color_map,
        opacity=0.4,
        labels={"ResilienceScore": "Rule-Based Resilience Score (0–100)", "AtRiskProba": "P(At Risk) from XGBoost"},
    )
    fig.add_hline(
        y=decision_threshold, line_dash="dash", line_color="#333",
        annotation_text=f"Decision threshold ({decision_threshold})",
        annotation_font_size=11,
    )
    fig.add_vline(
        x=thresh_score, line_dash="dot", line_color="#9b59b6",
        annotation_text=f"Score threshold (~{thresh_score:.1f})",
        annotation_font_size=11,
        annotation_position="top left",
    )
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=300,
        plot_bgcolor="#f9f9f9",
        legend=dict(x=0.75, y=0.99),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        f"Orgs with a ResilienceScore below **{thresh_score:.1f}** "
        f"have >50% model-estimated probability of financial distress."
    )


def _threshold_analysis(tm: dict) -> None:
    temporal = tm.get("metrics_temporal", {})
    tuned = tm.get("metrics_temporal_tuned", {})
    threshold = tm.get("decision_threshold", 0.36)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**At default threshold (0.5)**")
        if temporal:
            st.markdown(f"- Precision: `{temporal.get('precision_at_risk', 'N/A'):.1%}`")
            st.markdown(f"- Recall: `{temporal.get('recall_at_risk', 'N/A'):.1%}`")
            st.markdown(f"- F1: `{temporal.get('f1_at_risk', 'N/A'):.1%}`")

    with col2:
        st.markdown(f"**At tuned threshold ({threshold})**")
        if tuned:
            st.markdown(f"- Precision: `{tuned.get('precision_at_risk', 'N/A'):.1%}`")
            st.markdown(f"- Recall: `{tuned.get('recall_at_risk', 'N/A'):.1%}`")
            st.markdown(f"- F1: `{tuned.get('f1_at_risk', 'N/A'):.1%}`")

    st.info(
        f"**Why threshold {threshold}?** The model was calibrated to maximize Fβ (β=1.4), "
        "which weights recall more heavily than precision. For funders and capacity builders, "
        "it is better to flag a few extra organizations (lower precision) than to miss "
        "truly at-risk nonprofits (high recall)."
    )
