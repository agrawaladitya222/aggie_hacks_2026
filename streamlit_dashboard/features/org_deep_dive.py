"""Tab 5: Organization Deep Dive — full diagnostic for a single nonprofit."""

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

LOWER_IS_BETTER = {"FundraisingRatio", "DebtRatio", "GrantDependencyPct"}

FLAG_EXPLANATIONS = {
    "GrantDependencyPct": "Grant dependency is significantly {dir} peers — {implication}.",
    "ProgramExpenseRatio": "Mission spending is significantly {dir} peers — {implication}.",
    "FundraisingRatio": "Fundraising overhead is significantly {dir} peers — {implication}.",
    "SurplusMargin": "Financial surplus/deficit is significantly {dir} peers — {implication}.",
    "OperatingReserveMonths": "Operating runway is significantly {dir} peers — {implication}.",
    "DebtRatio": "Debt burden is significantly {dir} peers — {implication}.",
    "ProgramRevenuePct": "Earned revenue share is significantly {dir} peers — {implication}.",
    "RevenueGrowthPct": "Revenue growth is significantly {dir} peers — {implication}.",
    "RevenuePerEmployee": "Revenue per employee is significantly {dir} peers — {implication}.",
}

IMPLICATIONS = {
    "GrantDependencyPct": {
        "high": "high reliance on grant funding creates vulnerability to funding shocks",
        "low": "strong revenue diversification reduces grant concentration risk",
    },
    "ProgramExpenseRatio": {
        "high": "most spending is going directly to mission delivery — efficiency leader",
        "low": "overhead may be crowding out mission-critical spending",
    },
    "FundraisingRatio": {
        "high": "high cost to raise each dollar — examine fundraising ROI",
        "low": "lean and efficient fundraising operations",
    },
    "SurplusMargin": {
        "high": "building financial reserves and stability",
        "low": "persistent deficits risk depleting reserves",
    },
    "OperatingReserveMonths": {
        "high": "strong cash runway — resilient to revenue disruption",
        "low": "limited runway — vulnerable to any funding gap",
    },
    "DebtRatio": {
        "high": "high leverage poses solvency risk if revenues decline",
        "low": "minimal debt — strong balance sheet",
    },
    "RevenueGrowthPct": {
        "high": "expanding organizational capacity and impact",
        "low": "declining revenue may signal mission or market challenges",
    },
}


def render(df: pd.DataFrame) -> None:
    st.header("Organization Deep Dive")
    st.caption(
        "Look up any nonprofit for a full diagnostic: financial profile, "
        "model risk score, peer comparisons, key flags, and historical trends."
    )

    if df.empty:
        st.warning("No organizations match the current filters.")
        return

    # ── Search ────────────────────────────────────────────────────────────────
    search_col, year_col = st.columns([3, 1])
    with search_col:
        org_options = sorted(df["OrgName"].dropna().unique().tolist())
        selected_org = st.selectbox("Search organization by name:", org_options, key="deepdive_org")

    org_data = df[df["OrgName"] == selected_org].sort_values("TaxYear")
    if org_data.empty:
        st.warning("Organization not found.")
        return

    available_years = sorted(org_data["TaxYear"].dropna().unique().astype(int).tolist())
    with year_col:
        selected_year = st.selectbox("Tax Year:", available_years[::-1], key="deepdive_year")

    row = org_data[org_data["TaxYear"] == selected_year]
    if row.empty:
        row = org_data.iloc[[-1]]
    row = row.iloc[0]

    st.divider()

    # ── Profile + Gauge ───────────────────────────────────────────────────────
    col_profile, col_gauge = st.columns([1, 1])

    with col_profile:
        _profile_card(row)

    with col_gauge:
        _resilience_gauge(row)

    st.divider()

    # ── Flag Callouts ─────────────────────────────────────────────────────────
    st.subheader("Peer Comparison Flags")
    _flag_callouts(row)

    st.divider()

    # ── Radar Chart ───────────────────────────────────────────────────────────
    col_radar, col_financials = st.columns(2)

    with col_radar:
        st.subheader("Peer Benchmarking Radar")
        peer_id = str(row.get("PeerGroupID", ""))
        peers = df[df["PeerGroupID"] == peer_id] if peer_id else pd.DataFrame()
        _peer_radar(row, peers)

    with col_financials:
        st.subheader("Key Financial Ratios")
        _financial_summary(row, peers)

    st.divider()

    # ── Historical Trends ─────────────────────────────────────────────────────
    if len(available_years) > 1:
        st.subheader("Historical Trends")
        _historical_trends(org_data)
    else:
        st.info("Only one year of data available for this organization.")


# ─────────────────────────── helpers ─────────────────────────────────────────

def _fmt(v, pct=False, dollar=False) -> str:
    if pd.isna(v):
        return "N/A"
    if pct:
        return f"{v * 100:.1f}%"
    if dollar:
        if abs(v) >= 1e6:
            return f"${v/1e6:.2f}M"
        if abs(v) >= 1e3:
            return f"${v/1e3:.0f}K"
        return f"${v:.0f}"
    return str(v)


def _profile_card(row: pd.Series) -> None:
    st.markdown(f"### {row.get('OrgName', 'Unknown')}")
    cols = st.columns(2)
    fields = [
        ("EIN", str(row.get("EIN", "N/A"))),
        ("State", str(row.get("State", "N/A"))),
        ("City", str(row.get("City", "N/A"))),
        ("Sector", str(row.get("Sector", "N/A"))),
        ("Size Category", str(row.get("SizeCategory", "N/A"))),
        ("Tax Year", str(int(row["TaxYear"])) if pd.notna(row.get("TaxYear")) else "N/A"),
        ("Org Age", f"{int(row['OrgAge'])} years" if pd.notna(row.get("OrgAge")) else "N/A"),
        ("Employees", f"{int(row['Employees']):,}" if pd.notna(row.get("Employees")) and row.get("Employees") > 0 else "N/A"),
        ("Total Revenue", _fmt(pd.to_numeric(row.get("TotalRevenueCY"), errors="coerce"), dollar=True)),
        ("Total Assets", _fmt(pd.to_numeric(row.get("TotalAssetsEOY"), errors="coerce"), dollar=True)),
        ("Net Assets", _fmt(pd.to_numeric(row.get("NetAssetsEOY"), errors="coerce"), dollar=True)),
    ]
    for i, (label, value) in enumerate(fields):
        with cols[i % 2]:
            st.markdown(f"**{label}:** {value}")

    mission = str(row.get("Mission", ""))
    if mission and mission not in ("nan", "None", ""):
        st.markdown(f"**Mission:** _{mission[:300]}{'…' if len(mission) > 300 else ''}_")


def _resilience_gauge(row: pd.Series) -> None:
    score = pd.to_numeric(row.get("ResilienceScore"), errors="coerce")
    proba = pd.to_numeric(row.get("AtRiskProba"), errors="coerce")
    predicted = pd.to_numeric(row.get("AtRiskPredicted"), errors="coerce")
    tier = str(row.get("ResilienceTier", "Watch"))

    score_val = float(score) if pd.notna(score) else 50.0
    tier_color = {"Stable": "#2ecc71", "Watch": "#f39c12", "At Risk": "#e74c3c"}.get(tier, "#aaa")

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score_val,
        number={"suffix": " / 100", "font": {"size": 32}},
        delta={"reference": 50, "increasing": {"color": "#2ecc71"}, "decreasing": {"color": "#e74c3c"}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": tier_color, "thickness": 0.3},
            "steps": [
                {"range": [0, 30], "color": "rgba(231,76,60,0.15)"},
                {"range": [30, 60], "color": "rgba(243,156,18,0.15)"},
                {"range": [60, 100], "color": "rgba(46,204,113,0.15)"},
            ],
            "threshold": {
                "line": {"color": "#333", "width": 3},
                "thickness": 0.75,
                "value": score_val,
            },
        },
        title={"text": f"Resilience Score<br><span style='font-size:14px;color:{tier_color}'>{tier}</span>"},
    ))
    fig.update_layout(
        height=260,
        margin=dict(t=30, b=10, l=20, r=20),
    )
    st.plotly_chart(fig, use_container_width=True)

    # Model risk probability
    if pd.notna(proba):
        risk_label = "AT RISK" if pd.notna(predicted) and predicted == 1 else "NOT AT RISK"
        risk_color = "#e74c3c" if predicted == 1 else "#2ecc71"
        st.markdown(
            f"**Model Assessment:** "
            f"<span style='color:{risk_color};font-weight:bold'>{risk_label}</span> "
            f"(P(At Risk) = {proba:.1%})",
            unsafe_allow_html=True,
        )
    peer_id = str(row.get("PeerGroupID", ""))
    if peer_id:
        st.caption(f"Peer group: {peer_id}")


def _flag_callouts(row: pd.Series) -> None:
    flag_cols = [f"{m}_Flag" for m in BENCHMARK_METRICS if f"{m}_Flag" in row.index]
    if not flag_cols:
        st.info("Peer flag data not available.")
        return

    below = [fc.replace("_Flag", "") for fc in flag_cols if str(row.get(fc)) == "Below Peer Norm"]
    above = [fc.replace("_Flag", "") for fc in flag_cols if str(row.get(fc)) == "Above Peer Norm"]
    within = [fc.replace("_Flag", "") for fc in flag_cols if str(row.get(fc)) == "Within Norm"]

    if below:
        st.error("**Areas of concern (Below Peer Norm):**")
        for metric in below:
            impl = IMPLICATIONS.get(metric, {})
            implication = impl.get("low" if metric not in LOWER_IS_BETTER else "high", "review needed")
            direction = "lower than" if metric not in LOWER_IS_BETTER else "higher than"
            z = pd.to_numeric(row.get(f"{metric}_ZScore"), errors="coerce")
            z_str = f" (Z = {z:.2f})" if pd.notna(z) else ""
            st.markdown(
                f"- **{METRIC_LABELS.get(metric, metric)}**{z_str}: "
                f"This org is {direction} peers — {implication}."
            )

    if above:
        st.success("**Strengths (Above Peer Norm):**")
        for metric in above:
            impl = IMPLICATIONS.get(metric, {})
            implication = impl.get("high" if metric not in LOWER_IS_BETTER else "low", "strong performance")
            direction = "higher than" if metric not in LOWER_IS_BETTER else "lower than"
            z = pd.to_numeric(row.get(f"{metric}_ZScore"), errors="coerce")
            z_str = f" (Z = {z:.2f})" if pd.notna(z) else ""
            st.markdown(
                f"- **{METRIC_LABELS.get(metric, metric)}**{z_str}: "
                f"This org is {direction} peers — {implication}."
            )

    if not below and not above:
        st.info(f"This organization is within peer norms on all {len(within)} benchmark metrics.")


def _peer_radar(row: pd.Series, peers: pd.DataFrame) -> None:
    available_metrics = [m for m in BENCHMARK_METRICS if f"{m}_ZScore" in row.index]
    if not available_metrics:
        st.info("Z-score columns not available.")
        return

    categories = [METRIC_LABELS.get(m, m) for m in available_metrics]
    categories_closed = categories + [categories[0]]

    org_z = [
        float(np.clip(pd.to_numeric(row.get(f"{m}_ZScore", 0), errors="coerce") or 0, -3, 3))
        for m in available_metrics
    ]
    org_z_display = [-v if m in LOWER_IS_BETTER else v for m, v in zip(available_metrics, org_z)]
    org_z_closed = org_z_display + [org_z_display[0]]

    peer_z_closed = [0] * len(org_z_closed)  # Peer median is always 0 by definition

    org_name = str(row.get("OrgName", "This Org"))[:25]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=peer_z_closed, theta=categories_closed,
        fill="toself", name="Peer Median (0)",
        line_color="#aaaaaa", fillcolor="rgba(170,170,170,0.15)",
    ))
    fig.add_trace(go.Scatterpolar(
        r=org_z_closed, theta=categories_closed,
        fill="toself", name=org_name,
        line_color="#4a90d9", fillcolor="rgba(74,144,217,0.25)",
    ))
    fig.update_layout(
        polar=dict(radialaxis=dict(range=[-3, 3], tickfont_size=9, showticklabels=True)),
        showlegend=True,
        margin=dict(t=20, b=20, l=20, r=20),
        height=340,
        title=dict(text="Outward = stronger than peers", font_size=11, x=0.5),
    )
    st.plotly_chart(fig, use_container_width=True)

    if not peers.empty:
        st.caption(f"Peer group: {len(peers):,} organizations in same sector × size × state")


def _financial_summary(row: pd.Series, peers: pd.DataFrame) -> None:
    metrics_display = [
        ("Program Expense Ratio", "ProgramExpenseRatio", True, False),
        ("Surplus Margin", "SurplusMargin", True, False),
        ("Grant Dependency %", "GrantDependencyPct", True, False),
        ("Operating Reserve Months", "OperatingReserveMonths", False, False),
        ("Debt Ratio", "DebtRatio", True, False),
        ("Revenue Growth %", "RevenueGrowthPct", True, False),
        ("Fundraising Ratio", "FundraisingRatio", True, False),
        ("Revenue / Employee", "RevenuePerEmployee", False, True),
    ]

    data = []
    for label, col, pct, dollar in metrics_display:
        val = pd.to_numeric(row.get(col), errors="coerce")
        if not peers.empty and col in peers.columns:
            peer_med = pd.to_numeric(peers[col], errors="coerce").median()
            peer_fmt = _fmt(peer_med, pct=pct, dollar=dollar)
        else:
            peer_fmt = "N/A"
        data.append({
            "Metric": label,
            "This Org": _fmt(val, pct=pct, dollar=dollar),
            "Peer Median": peer_fmt,
        })

    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True, height=300)


def _historical_trends(org_data: pd.DataFrame) -> None:
    org_data = org_data.sort_values("TaxYear")
    years = pd.to_numeric(org_data["TaxYear"], errors="coerce")

    tabs = st.tabs(["Revenue & Expenses", "Surplus & Reserves", "Risk Score Over Time"])

    with tabs[0]:
        rev = pd.to_numeric(org_data["TotalRevenueCY"], errors="coerce")
        exp = pd.to_numeric(org_data["TotalExpensesCY"], errors="coerce")
        grants = pd.to_numeric(org_data["ContributionsGrantsCY"], errors="coerce")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=years, y=rev, name="Total Revenue",
            mode="lines+markers", line=dict(color="#4a90d9", width=2.5),
            hovertemplate="Revenue: $%{y:,.0f}<extra></extra>",
        ))
        fig.add_trace(go.Scatter(
            x=years, y=exp, name="Total Expenses",
            mode="lines+markers", line=dict(color="#e74c3c", width=2.5, dash="dot"),
            hovertemplate="Expenses: $%{y:,.0f}<extra></extra>",
        ))
        fig.add_trace(go.Bar(
            x=years, y=grants, name="Grants/Contributions",
            marker_color="rgba(39,174,96,0.4)",
            hovertemplate="Grants: $%{y:,.0f}<extra></extra>",
        ))
        fig.update_layout(
            xaxis_title="Tax Year", yaxis_title="Dollars",
            yaxis_tickprefix="$",
            margin=dict(t=10, b=10), height=280,
            plot_bgcolor="#f9f9f9", hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)

    with tabs[1]:
        sm = pd.to_numeric(org_data["SurplusMargin"], errors="coerce") * 100
        rm = pd.to_numeric(org_data["OperatingReserveMonths"], errors="coerce").clip(-120, 120)
        score = pd.to_numeric(org_data["ResilienceScore"], errors="coerce")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=years, y=sm, name="Surplus Margin %",
            mode="lines+markers", line=dict(color="#9b59b6", width=2.5),
            hovertemplate="Surplus: %{y:.1f}%<extra></extra>",
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="#888")
        fig.add_hline(y=-10, line_dash="dot", line_color="#e74c3c",
                      annotation_text="At-Risk threshold (−10%)", annotation_position="bottom right")
        fig.update_layout(
            xaxis_title="Tax Year", yaxis_title="Surplus Margin (%)",
            yaxis_ticksuffix="%",
            margin=dict(t=10, b=10), height=240,
            plot_bgcolor="#f9f9f9",
        )
        st.plotly_chart(fig, use_container_width=True)

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=years, y=rm, name="Reserve Months",
            mode="lines+markers", line=dict(color="#27ae60", width=2.5),
            hovertemplate="Reserve Months: %{y:.1f}<extra></extra>",
        ))
        fig2.add_hline(y=1, line_dash="dot", line_color="#e74c3c",
                       annotation_text="At-Risk threshold (1 month)")
        fig2.add_hline(y=6, line_dash="dot", line_color="#f39c12",
                       annotation_text="Watch threshold (6 months)")
        fig2.update_layout(
            xaxis_title="Tax Year", yaxis_title="Operating Reserve Months",
            margin=dict(t=10, b=10), height=240,
            plot_bgcolor="#f9f9f9",
        )
        st.plotly_chart(fig2, use_container_width=True)

    with tabs[2]:
        score = pd.to_numeric(org_data["ResilienceScore"], errors="coerce")
        proba = pd.to_numeric(org_data.get("AtRiskProba", pd.Series(dtype=float)), errors="coerce") * 100

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=years, y=score, name="Resilience Score (0–100)",
            mode="lines+markers", line=dict(color="#4a90d9", width=2.5),
            hovertemplate="Score: %{y:.1f}<extra></extra>",
        ))
        if proba.notna().any():
            fig.add_trace(go.Scatter(
                x=years, y=proba, name="P(At Risk) %",
                mode="lines+markers", line=dict(color="#e74c3c", width=2.5, dash="dot"),
                yaxis="y2",
                hovertemplate="P(At Risk): %{y:.1f}%<extra></extra>",
            ))
        fig.update_layout(
            xaxis_title="Tax Year",
            yaxis=dict(title="Resilience Score", range=[0, 100]),
            yaxis2=dict(title="P(At Risk) %", overlaying="y", side="right", range=[0, 100]),
            margin=dict(t=10, b=10), height=280,
            plot_bgcolor="#f9f9f9", hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True)
