"""Tab 3: Peer Benchmarking — compare orgs against their sector/size/state peers."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

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

METRIC_LABELS = {
    "ProgramExpenseRatio": "Program Expense Ratio",
    "FundraisingRatio": "Fundraising Ratio",
    "SurplusMargin": "Surplus Margin",
    "OperatingReserveMonths": "Reserve Months",
    "DebtRatio": "Debt Ratio",
    "GrantDependencyPct": "Grant Dependency %",
    "ProgramRevenuePct": "Program Revenue %",
    "RevenueGrowthPct": "Revenue Growth %",
    "RevenuePerEmployee": "Revenue / Employee",
}

# For these metrics, lower = better (inverted for radar visualization)
LOWER_IS_BETTER = {"FundraisingRatio", "DebtRatio", "GrantDependencyPct"}

FLAG_COLORS = {
    "Above Peer Norm": "#2ecc71",
    "Within Norm": "#aaaaaa",
    "Below Peer Norm": "#e74c3c",
}


def render(df: pd.DataFrame) -> None:
    st.header("Peer Benchmarking")
    st.caption(
        "Each nonprofit is compared against peers in the same mission sector, "
        "revenue size band, and state. Z-scores measure deviation from the peer group mean."
    )

    if df.empty:
        st.warning("No organizations match the current filters.")
        return

    # ── Peer Group Summary Table ──────────────────────────────────────────────
    st.subheader("Peer Group Summary")
    _peer_group_table(df)
    st.divider()

    # ── Deviation Flag Heatmap ────────────────────────────────────────────────
    st.subheader("Sector-Level Deviation Heatmap")
    st.caption("Shows what fraction of organizations in each sector are 'Below Peer Norm' per metric.")
    _deviation_heatmap(df)
    st.divider()

    # ── Org-Level Radar + Box Plot ────────────────────────────────────────────
    col_radar, col_box = st.columns([1, 1])

    with col_radar:
        st.subheader("Organization Radar Chart")
        _org_radar(df)

    with col_box:
        st.subheader("Peer Group Distribution")
        _metric_boxplot(df)


# ─────────────────────────── helpers ─────────────────────────────────────────

def _peer_group_table(df: pd.DataFrame) -> None:
    at_risk = pd.to_numeric(df["AtRiskPredicted"], errors="coerce")
    score = pd.to_numeric(df["ResilienceScore"], errors="coerce")
    rev = pd.to_numeric(df["TotalRevenueCY"], errors="coerce")

    grp = df.copy()
    grp["_ar"] = at_risk
    grp["_score"] = score
    grp["_rev"] = rev

    peer_agg = (
        grp.groupby("PeerGroupID", observed=True)
        .agg(
            Orgs=("_ar", "count"),
            Pct_At_Risk=("_ar", lambda x: round(x.mean() * 100, 1)),
            Median_Score=("_score", lambda x: round(x.median(), 1)),
            Median_Revenue=("_rev", "median"),
        )
        .reset_index()
        .rename(columns={
            "PeerGroupID": "Peer Group",
            "Pct_At_Risk": "% At Risk",
            "Median_Score": "Median Resilience Score",
            "Median_Revenue": "Median Revenue",
        })
        .sort_values("% At Risk", ascending=False)
    )
    peer_agg["Median Revenue"] = peer_agg["Median Revenue"].apply(
        lambda x: f"${x/1e6:.1f}M" if pd.notna(x) and x >= 1e6 else (
            f"${x/1e3:.0f}K" if pd.notna(x) else "N/A"
        )
    )

    top_n = st.slider("Show top N peer groups by At-Risk rate", 10, min(100, len(peer_agg)), 25)
    st.dataframe(
        peer_agg.head(top_n).reset_index(drop=True),
        use_container_width=True,
        height=300,
    )


def _deviation_heatmap(df: pd.DataFrame) -> None:
    flag_cols = [f"{m}_Flag" for m in BENCHMARK_METRICS if f"{m}_Flag" in df.columns]
    if not flag_cols:
        st.info("Peer flag columns not available in data.")
        return

    sectors = sorted(df["Sector"].dropna().unique())
    rows = []
    for sector in sectors:
        sub = df[df["Sector"] == sector]
        row = {"Sector": sector}
        for fc in flag_cols:
            metric = fc.replace("_Flag", "")
            below_pct = (sub[fc] == "Below Peer Norm").mean() * 100
            row[METRIC_LABELS.get(metric, metric)] = round(below_pct, 1)
        rows.append(row)

    heat_df = pd.DataFrame(rows).set_index("Sector")

    fig = go.Figure(go.Heatmap(
        z=heat_df.values,
        x=heat_df.columns.tolist(),
        y=heat_df.index.tolist(),
        colorscale=[[0, "#2ecc71"], [0.4, "#f39c12"], [1, "#e74c3c"]],
        zmin=0, zmax=60,
        text=[[f"{v:.0f}%" for v in row] for row in heat_df.values],
        texttemplate="%{text}",
        textfont_size=11,
        hovertemplate="<b>%{y}</b> · %{x}<br>Below peer norm: %{z:.1f}%<extra></extra>",
        colorbar=dict(title="% Below Norm", ticksuffix="%"),
    ))
    fig.update_layout(
        xaxis_title="",
        yaxis_title="",
        margin=dict(t=10, b=10, l=10, r=10),
        height=max(300, len(sectors) * 26 + 60),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Values show % of orgs in each sector scoring 'Below Peer Norm' (Z-score < –1.5). Higher = more systemic weakness.")


def _org_radar(df: pd.DataFrame) -> None:
    z_cols = [f"{m}_ZScore" for m in BENCHMARK_METRICS if f"{m}_ZScore" in df.columns]
    available_metrics = [m for m in BENCHMARK_METRICS if f"{m}_ZScore" in df.columns]

    if not z_cols:
        st.info("Z-score columns not available.")
        return

    # Select org
    latest = df.sort_values("TaxYear", ascending=False).drop_duplicates("EIN")
    org_options = latest["OrgName"].dropna().sort_values().tolist()
    if not org_options:
        st.info("No organizations available.")
        return

    selected = st.selectbox("Select organization for radar:", org_options, key="radar_org")
    org_row = latest[latest["OrgName"] == selected]

    if org_row.empty:
        st.info("Organization not found.")
        return

    org_row = org_row.iloc[0]
    peer_id = org_row["PeerGroupID"]
    peers = df[df["PeerGroupID"] == peer_id]

    categories = [METRIC_LABELS.get(m, m) for m in available_metrics]
    categories_closed = categories + [categories[0]]

    # Org z-scores (clipped to [-3, 3] for display)
    org_z = [
        float(np.clip(pd.to_numeric(org_row.get(f"{m}_ZScore", 0), errors="coerce") or 0, -3, 3))
        for m in available_metrics
    ]
    # Invert for "lower is better" metrics so outward = better
    org_z_display = [
        -v if available_metrics[i] in LOWER_IS_BETTER else v
        for i, v in enumerate(org_z)
    ]
    org_z_closed = org_z_display + [org_z_display[0]]

    # Peer median z-scores (should be ~0 by definition, but useful for comparison)
    peer_z = [
        float(np.clip(pd.to_numeric(peers[f"{m}_ZScore"], errors="coerce").median() or 0, -3, 3))
        for m in available_metrics
    ]
    peer_z_display = [
        -v if available_metrics[i] in LOWER_IS_BETTER else v
        for i, v in enumerate(peer_z)
    ]
    peer_z_closed = peer_z_display + [peer_z_display[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=peer_z_closed, theta=categories_closed,
        fill="toself", name="Peer Median",
        line_color="#aaaaaa", fillcolor="rgba(170,170,170,0.15)",
        opacity=0.8,
    ))
    fig.add_trace(go.Scatterpolar(
        r=org_z_closed, theta=categories_closed,
        fill="toself", name=selected[:30],
        line_color="#4a90d9", fillcolor="rgba(74,144,217,0.25)",
        opacity=0.9,
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(range=[-3, 3], tickfont_size=10, showticklabels=True),
        ),
        showlegend=True,
        legend=dict(x=0.75, y=0.01),
        margin=dict(t=20, b=20, l=20, r=20),
        height=360,
        title=dict(text="Outward = Better than peers", font_size=11, x=0.5),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Show flags
    flag_cols = [f"{m}_Flag" for m in available_metrics if f"{m}_Flag" in df.columns]
    below = [(METRIC_LABELS.get(fc.replace("_Flag", ""), fc), org_row.get(fc, "N/A"))
             for fc in flag_cols if org_row.get(fc) == "Below Peer Norm"]
    above = [(METRIC_LABELS.get(fc.replace("_Flag", ""), fc), org_row.get(fc, "N/A"))
             for fc in flag_cols if org_row.get(fc) == "Above Peer Norm"]

    if below:
        st.markdown("**Below peer norm:** " + ", ".join(f"`{m}`" for m, _ in below))
    if above:
        st.markdown("**Above peer norm:** " + ", ".join(f"`{m}`" for m, _ in above))

    peer_count = len(peers)
    st.caption(f"Peer group: **{peer_id}** ({peer_count:,} orgs)")


def _metric_boxplot(df: pd.DataFrame) -> None:
    available = [m for m in BENCHMARK_METRICS if m in df.columns]
    if not available:
        st.info("Benchmark metric columns not available.")
        return

    metric_sel = st.selectbox(
        "Metric to compare across sectors:",
        options=available,
        format_func=lambda x: METRIC_LABELS.get(x, x),
        key="box_metric",
    )

    val = pd.to_numeric(df[metric_sel], errors="coerce")
    plot_df = df[["Sector", "ResilienceTier"]].copy()
    plot_df["value"] = val
    plot_df = plot_df.dropna(subset=["value"])

    # Clip outliers for display
    p1, p99 = plot_df["value"].quantile([0.01, 0.99])
    plot_df["value"] = plot_df["value"].clip(p1, p99)

    TIER_COLORS = {"Stable": "#2ecc71", "Watch": "#f39c12", "At Risk": "#e74c3c"}

    fig = px.box(
        plot_df, x="Sector", y="value",
        color="ResilienceTier",
        color_discrete_map=TIER_COLORS,
        labels={"value": METRIC_LABELS.get(metric_sel, metric_sel), "Sector": ""},
        category_orders={"ResilienceTier": ["Stable", "Watch", "At Risk"]},
        points=False,
    )
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=360,
        plot_bgcolor="#f9f9f9",
        xaxis_tickangle=-35,
        legend_title="Resilience Tier",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(f"Distribution of **{METRIC_LABELS.get(metric_sel, metric_sel)}** by sector and resilience tier (1st–99th percentile).")
