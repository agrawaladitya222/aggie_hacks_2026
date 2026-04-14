"""Tab 1: Executive Overview — sector health at a glance."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from features.brand_map import build_brand_map

_TIER_COLORS = {"Stable": "#2ecc71", "Watch": "#f39c12", "At Risk": "#e74c3c"}
_SECTOR_COLOR = "#4a90d9"


def render(df: pd.DataFrame) -> None:
    st.header("Executive Overview")
    st.caption(
        "Sector-level financial health across all filtered nonprofits using "
        "IRS Form 990 data (7 years) and XGBoost resilience predictions."
    )

    if df.empty:
        st.warning("No organizations match the current filters.")
        return

    rev = pd.to_numeric(df["TotalRevenueCY"], errors="coerce")
    at_risk_pred = pd.to_numeric(df["AtRiskPredicted"], errors="coerce")
    score = pd.to_numeric(df["ResilienceScore"], errors="coerce")
    reserve = pd.to_numeric(df["OperatingReserveMonths"], errors="coerce")

    n_total = len(df)
    n_at_risk = int(at_risk_pred.sum())
    pct_at_risk = n_at_risk / n_total * 100 if n_total else 0
    median_score = score.median()
    median_reserve = reserve.clip(-120, 120).median()

    # ── KPI Row ──────────────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Organizations", f"{n_total:,}")
    c2.metric(
        "Model-Predicted At Risk",
        f"{n_at_risk:,}",
        delta=f"{pct_at_risk:.1f}% of total",
        delta_color="inverse",
    )
    c3.metric("Median Resilience Score", f"{median_score:.1f} / 100")
    c4.metric("Median Reserve Months", f"{median_reserve:.1f} mo")
    c5.metric(
        "Total Revenue (Median)",
        _fmt_dollars(rev.median()),
    )

    st.divider()

    # ── Row 1: Donut + At-Risk by Sector ─────────────────────────────────────
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.subheader("At-Risk Distribution")
        _donut_chart(df)

    with col_right:
        st.subheader("At-Risk Rate by Sector")
        _sector_bar(df)

    st.divider()

    # ── Row 2: State choropleth + Time trend ─────────────────────────────────
    col_map, col_trend = st.columns([2, 1])

    with col_map:
        st.subheader("At-Risk Rate by State")
        _state_choropleth(df)

    with col_trend:
        st.subheader("Trend Over Time")
        _time_trend(df)

    st.divider()

    # ── Row 3: Size breakdown + Revenue composition ───────────────────────────
    col_sz, col_rev = st.columns(2)

    with col_sz:
        st.subheader("At-Risk Rate by Organization Size")
        _size_breakdown(df)

    with col_rev:
        st.subheader("Revenue Mix (Median by Tier)")
        _revenue_composition(df)

    st.divider()

    # ── Brand Map ────────────────────────────────────────────────────────────
    st.subheader("Financial Position Map")
    st.caption(
        "X: Program Expense Ratio (mission efficiency) · "
        "Y: Operating Reserve Months (runway) · "
        "Dot size: Revenue · Color: Resilience Tier"
    )
    n_brand = int((~df["_exclude_brand_map"]).sum()) if "_exclude_brand_map" in df.columns else n_total
    if n_brand == 0:
        st.info("No organizations with valid Program Expense data in current filter.")
    else:
        fig = build_brand_map(df)
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────── helpers ─────────────────────────────────────────

def _fmt_dollars(v) -> str:
    if pd.isna(v):
        return "N/A"
    if abs(v) >= 1e9:
        return f"${v/1e9:.1f}B"
    if abs(v) >= 1e6:
        return f"${v/1e6:.1f}M"
    if abs(v) >= 1e3:
        return f"${v/1e3:.0f}K"
    return f"${v:.0f}"


def _donut_chart(df: pd.DataFrame) -> None:
    at_risk_pred = pd.to_numeric(df["AtRiskPredicted"], errors="coerce")
    counts = at_risk_pred.value_counts().reindex([0, 1], fill_value=0)
    labels = ["Not At Risk", "At Risk"]
    values = [int(counts[0]), int(counts[1])]
    colors = [_TIER_COLORS["Stable"], _TIER_COLORS["At Risk"]]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        hole=0.55,
        marker_colors=colors,
        textinfo="percent+label",
        textfont_size=13,
        hovertemplate="%{label}: %{value:,} orgs (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),
        height=260,
        annotations=[dict(
            text=f"{values[1]:,}<br><span style='font-size:12px'>At Risk</span>",
            x=0.5, y=0.5, font_size=18, showarrow=False,
        )],
    )
    st.plotly_chart(fig, use_container_width=True)


def _sector_bar(df: pd.DataFrame) -> None:
    at_risk_pred = pd.to_numeric(df["AtRiskPredicted"], errors="coerce")
    grp = df.copy()
    grp["_at_risk"] = at_risk_pred
    sector_stats = (
        grp.groupby("Sector", observed=True)
        .agg(total=("_at_risk", "count"), at_risk=("_at_risk", "sum"))
        .reset_index()
    )
    sector_stats["pct"] = sector_stats["at_risk"] / sector_stats["total"] * 100
    sector_stats = sector_stats.sort_values("pct", ascending=True)

    fig = go.Figure(go.Bar(
        x=sector_stats["pct"],
        y=sector_stats["Sector"],
        orientation="h",
        marker_color=[
            "#e74c3c" if p >= 40 else "#f39c12" if p >= 20 else "#2ecc71"
            for p in sector_stats["pct"]
        ],
        text=[f"{p:.1f}%" for p in sector_stats["pct"]],
        textposition="outside",
        customdata=sector_stats[["total", "at_risk"]].values,
        hovertemplate=(
            "<b>%{y}</b><br>"
            "At Risk: %{customdata[1]:,} of %{customdata[0]:,}<br>"
            "Rate: %{x:.1f}%<extra></extra>"
        ),
    ))
    fig.update_layout(
        xaxis_title="% At Risk (model-predicted)",
        yaxis_title="",
        xaxis=dict(range=[0, sector_stats["pct"].max() * 1.25]),
        margin=dict(t=10, b=10, l=10, r=60),
        height=max(280, len(sector_stats) * 28),
        plot_bgcolor="#f9f9f9",
    )
    st.plotly_chart(fig, use_container_width=True)


def _state_choropleth(df: pd.DataFrame) -> None:
    at_risk_pred = pd.to_numeric(df["AtRiskPredicted"], errors="coerce")
    grp = df.copy()
    grp["_at_risk"] = at_risk_pred
    state_stats = (
        grp.groupby("State", observed=True)
        .agg(total=("_at_risk", "count"), at_risk=("_at_risk", "sum"))
        .reset_index()
    )
    state_stats["pct"] = state_stats["at_risk"] / state_stats["total"] * 100

    fig = px.choropleth(
        state_stats,
        locations="State",
        locationmode="USA-states",
        color="pct",
        scope="usa",
        color_continuous_scale=["#2ecc71", "#f39c12", "#e74c3c"],
        range_color=[0, min(80, state_stats["pct"].max())],
        labels={"pct": "% At Risk"},
        hover_name="State",
        hover_data={"total": True, "at_risk": True, "pct": ":.1f"},
        custom_data=["total", "at_risk"],
    )
    fig.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "At Risk: %{customdata[1]:,} of %{customdata[0]:,}<br>"
            "Rate: %{z:.1f}%<extra></extra>"
        )
    )
    fig.update_layout(
        coloraxis_colorbar=dict(title="% At Risk", ticksuffix="%"),
        margin=dict(t=10, b=10, l=0, r=0),
        height=340,
    )
    st.plotly_chart(fig, use_container_width=True)


def _time_trend(df: pd.DataFrame) -> None:
    at_risk_pred = pd.to_numeric(df["AtRiskPredicted"], errors="coerce")
    score = pd.to_numeric(df["ResilienceScore"], errors="coerce")
    grp = df.copy()
    grp["_at_risk"] = at_risk_pred
    grp["_score"] = score
    grp["_year"] = pd.to_numeric(grp["TaxYear"], errors="coerce")

    yearly = (
        grp.groupby("_year", observed=True)
        .agg(
            pct_at_risk=("_at_risk", lambda x: x.mean() * 100),
            median_score=("_score", "median"),
        )
        .reset_index()
        .sort_values("_year")
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=yearly["_year"], y=yearly["pct_at_risk"],
        name="% At Risk",
        line=dict(color="#e74c3c", width=2.5),
        mode="lines+markers",
        yaxis="y1",
        hovertemplate="Year %{x}: %{y:.1f}% At Risk<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=yearly["_year"], y=yearly["median_score"],
        name="Median Score",
        line=dict(color="#4a90d9", width=2.5, dash="dot"),
        mode="lines+markers",
        yaxis="y2",
        hovertemplate="Year %{x}: Score %{y:.1f}<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="Tax Year",
        yaxis=dict(
            title=dict(text="% At Risk", font=dict(color="#e74c3c")),
            tickfont=dict(color="#e74c3c"),
        ),
        yaxis2=dict(
            title=dict(text="Median Resilience Score", font=dict(color="#4a90d9")),
            tickfont=dict(color="#4a90d9"),
            overlaying="y", side="right",
        ),
        legend=dict(x=0.01, y=0.99),
        margin=dict(t=10, b=10, l=10, r=10),
        height=280,
        plot_bgcolor="#f9f9f9",
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True)


def _size_breakdown(df: pd.DataFrame) -> None:
    SIZE_ORDER = ["<500K", "500K-1M", "1M-5M", "5M-10M", "10M-50M", "50M+"]
    at_risk_pred = pd.to_numeric(df["AtRiskPredicted"], errors="coerce")
    grp = df.copy()
    grp["_at_risk"] = at_risk_pred
    size_stats = (
        grp.groupby("SizeCategory", observed=True)
        .agg(total=("_at_risk", "count"), at_risk=("_at_risk", "sum"))
        .reset_index()
    )
    size_stats["pct"] = size_stats["at_risk"] / size_stats["total"] * 100
    size_stats["SizeCategory"] = pd.Categorical(size_stats["SizeCategory"], categories=SIZE_ORDER, ordered=True)
    size_stats = size_stats.sort_values("SizeCategory")

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=size_stats["SizeCategory"].astype(str),
        y=size_stats["at_risk"],
        name="At Risk",
        marker_color="#e74c3c",
        customdata=size_stats[["total", "pct"]].values,
        hovertemplate="<b>%{x}</b><br>At Risk: %{y:,}<br>Total: %{customdata[0]:,}<br>Rate: %{customdata[1]:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Bar(
        x=size_stats["SizeCategory"].astype(str),
        y=size_stats["total"] - size_stats["at_risk"],
        name="Not At Risk",
        marker_color="#2ecc71",
        hovertemplate="<b>%{x}</b><br>Not At Risk: %{y:,}<extra></extra>",
    ))
    fig.update_layout(
        barmode="stack",
        xaxis_title="Revenue Size Category",
        yaxis_title="Number of Organizations",
        legend=dict(x=0.75, y=0.99),
        margin=dict(t=10, b=10, l=10, r=10),
        height=280,
        plot_bgcolor="#f9f9f9",
    )
    st.plotly_chart(fig, use_container_width=True)


def _revenue_composition(df: pd.DataFrame) -> None:
    tiers = ["Stable", "Watch", "At Risk"]
    cols = {
        "Grants/Contributions": "GrantDependencyPct",
        "Program Revenue": "ProgramRevenuePct",
        "Gov Grants": "GovGrantPct",
        "Investment Income": "InvestmentRevenuePct",
    }
    rows = []
    for tier in tiers:
        sub = df[df["ResilienceTier"] == tier]
        if sub.empty:
            continue
        for label, col in cols.items():
            if col in sub.columns:
                med = pd.to_numeric(sub[col], errors="coerce").median()
                rows.append({"Tier": tier, "Stream": label, "Median %": round(med * 100, 1)})

    if not rows:
        st.info("Insufficient data for revenue composition.")
        return

    plot_df = pd.DataFrame(rows)
    fig = px.bar(
        plot_df, x="Tier", y="Median %", color="Stream",
        barmode="group",
        color_discrete_sequence=px.colors.qualitative.Set2,
        labels={"Median %": "Median % of Revenue"},
        category_orders={"Tier": tiers},
    )
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=280,
        plot_bgcolor="#f9f9f9",
        legend=dict(font_size=11),
    )
    st.plotly_chart(fig, use_container_width=True)
