from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from src.risk_simulation import estimate_recovery, simulate_shock

# ---------------------------------------------------------------------------
# Page config & global styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Nonprofit Financial Resilience",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
/* ---- Top-level metrics ---- */
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #f8f9fc 0%, #eef1f8 100%);
    border: 1px solid #dde2ec;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04);
}
[data-testid="stMetricLabel"] {
    font-size: 0.85rem !important;
    color: #5a6577 !important;
    font-weight: 500 !important;
}
[data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 700 !important;
    color: #1a2332 !important;
}

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a2332 0%, #243447 100%);
}
section[data-testid="stSidebar"] .stMarkdown p,
section[data-testid="stSidebar"] .stMarkdown li,
section[data-testid="stSidebar"] label {
    color: #cdd5df !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #ffffff !important;
}
/* ---- Sidebar radio button navigation text ---- */
section[data-testid="stSidebar"] [data-testid="stRadio"] label p,
section[data-testid="stSidebar"] [data-testid="stRadio"] label span,
section[data-testid="stSidebar"] [data-baseweb="radio"] label,
section[data-testid="stSidebar"] div[role="radiogroup"] label,
section[data-testid="stSidebar"] div[role="radiogroup"] p {
    color: #ffffff !important;
}

/* ---- Insight callout boxes ---- */
.insight-box {
    background: #f0f7ff;
    border-left: 4px solid #3b82f6;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 12px 0 20px 0;
    font-size: 0.95rem;
    line-height: 1.5;
}
.insight-box-warn {
    background: #fff8f0;
    border-left: 4px solid #f59e0b;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 12px 0 20px 0;
    font-size: 0.95rem;
    line-height: 1.5;
}
.insight-box-good {
    background: #f0fdf4;
    border-left: 4px solid #22c55e;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 12px 0 20px 0;
    font-size: 0.95rem;
    line-height: 1.5;
}

/* ---- Section headers ---- */
.section-header {
    font-size: 1.1rem;
    font-weight: 600;
    color: #374151;
    border-bottom: 2px solid #e5e7eb;
    padding-bottom: 6px;
    margin: 28px 0 14px 0;
}

/* ---- Health badge ---- */
.health-badge {
    display: inline-block;
    padding: 4px 14px;
    border-radius: 20px;
    font-weight: 600;
    font-size: 0.85rem;
}
.health-good { background: #dcfce7; color: #166534; }
.health-ok   { background: #fef9c3; color: #854d0e; }
.health-bad  { background: #fee2e2; color: #991b1b; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

FRIENDLY_METRIC_NAMES = {
    "ProgramExpenseRatio": "Program Spending %",
    "FundraisingRatio": "Fundraising Cost %",
    "SurplusMargin": "Surplus / Deficit Margin",
    "OperatingReserveMonths": "Months of Reserves",
    "DebtRatio": "Debt-to-Asset Ratio",
    "GrantDependencyPct": "Grant Dependency %",
    "ProgramRevenuePct": "Earned Revenue %",
    "RevenueGrowthPct": "Revenue Growth %",
    "RevenuePerEmployee": "Revenue per Employee",
}

METRIC_EXPLANATIONS = {
    "Program Spending %": "What share of every dollar goes directly to programs and services (higher is better; 75%+ is the industry standard).",
    "Fundraising Cost %": "What share of spending goes to fundraising (lower is better; above 25% is a red flag).",
    "Surplus / Deficit Margin": "Whether the organization is bringing in more than it spends. Positive = surplus, negative = deficit.",
    "Months of Reserves": "How many months the organization could operate with zero new revenue (3-6 months is healthy).",
    "Debt-to-Asset Ratio": "What fraction of assets are financed by debt (lower is better; above 0.5 means more debt than equity).",
    "Grant Dependency %": "How much revenue comes from grants and donations (above 80% = heavy dependency on donors).",
    "Earned Revenue %": "How much revenue is earned through programs and services (higher = more self-sustaining).",
    "Revenue Growth %": "Year-over-year revenue change (positive = growing).",
    "Revenue per Employee": "How much revenue each employee generates (a rough productivity measure).",
}

STATUS_COLORS = {
    "Survives (Surplus)": "#22c55e",
    "Stressed (>12mo reserves)": "#eab308",
    "At Risk (3-12mo reserves)": "#f97316",
    "Critical (<3mo reserves)": "#ef4444",
}

STATUS_ORDER = [
    "Critical (<3mo reserves)",
    "At Risk (3-12mo reserves)",
    "Stressed (>12mo reserves)",
    "Survives (Surplus)",
]


def _classify_status(total_revenue: float, total_expenses: float, net_assets: float) -> tuple[str, float]:
    """Return (status_label, months_to_insolvency) using the same logic as simulate_shock."""
    if pd.isna(total_revenue) or pd.isna(total_expenses):
        return "Survives (Surplus)", float("inf")
    net = total_revenue - total_expenses
    if net >= 0:
        return "Survives (Surplus)", float("inf")
    monthly_deficit = abs(net) / 12.0
    if monthly_deficit <= 0 or pd.isna(net_assets):
        return "Survives (Surplus)", float("inf")
    months = max(0.0, min(120.0, net_assets / monthly_deficit))
    if months > 12:
        return "Stressed (>12mo reserves)", months
    if months > 3:
        return "At Risk (3-12mo reserves)", months
    return "Critical (<3mo reserves)", months


def _fmt_dollars(val: float) -> str:
    if abs(val) >= 1_000_000:
        return f"${val / 1_000_000:,.1f}M"
    if abs(val) >= 1_000:
        return f"${val / 1_000:,.0f}K"
    return f"${val:,.0f}"


def _resilience_label(score: float) -> tuple[str, str]:
    if score >= 70:
        return "Strong", "health-good"
    if score >= 40:
        return "Moderate", "health-ok"
    return "At Risk", "health-bad"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    master = pd.read_csv("data/master_990.csv", low_memory=False)
    peers = pd.read_csv("data/peer_group_stats.csv", low_memory=False)
    sims = pd.read_csv("data/simulation_results.csv", low_memory=False)
    metrics_path = Path("artifacts/train_metrics.json")
    metrics: dict = {}
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    return master, peers, sims, metrics


# ---------------------------------------------------------------------------
# PAGE 1 — Executive Overview
# ---------------------------------------------------------------------------
def executive_page(df: pd.DataFrame) -> None:
    st.title("Nonprofit Financial Resilience Dashboard")
    st.markdown(
        "A data-driven look at the financial health of **{:,}** U.S. nonprofits "
        "across **{:,}** states and territories, using IRS Form 990 filings "
        "from **2018 – 2024**.".format(len(df), int(df["State"].nunique()))
    )

    # --- Top-line KPIs ---
    at_risk_pct = df["AtRisk"].mean()
    thriving_pct = (df["ResilienceScore"] >= 70).mean()
    avg_score = df["ResilienceScore"].mean()
    median_reserves = df["OperatingReserveMonths"].median()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Nonprofits Analyzed", f"{len(df):,}")
    c2.metric("At-Risk Rate", f"{at_risk_pct:.1%}")
    c3.metric("Financially Strong (score 70+)", f"{thriving_pct:.1%}")
    c4.metric("Median Months of Reserves", f"{median_reserves:.1f}")

    # Key insight callout
    if at_risk_pct > 0.20:
        st.markdown(
            f'<div class="insight-box-warn">'
            f"<strong>Key finding:</strong> About <strong>1 in {int(round(1/at_risk_pct))}</strong> nonprofits "
            f"show signs of financial distress — running large deficits, shrinking revenue, "
            f"or dangerously low reserves. Targeted support could prevent closures."
            f"</div>",
            unsafe_allow_html=True,
        )

    # --- Resilience distribution ---
    st.markdown('<div class="section-header">How Resilient Are U.S. Nonprofits?</div>', unsafe_allow_html=True)

    col_hist, col_explain = st.columns([3, 1])
    with col_hist:
        hist_df = df.copy()
        hist_df["Health Tier"] = pd.cut(
            hist_df["ResilienceScore"],
            bins=[0, 40, 70, 100],
            labels=["At Risk (0-40)", "Moderate (40-70)", "Strong (70-100)"],
        )
        color_map = {
            "At Risk (0-40)": "#ef4444",
            "Moderate (40-70)": "#eab308",
            "Strong (70-100)": "#22c55e",
        }
        hist = px.histogram(
            hist_df,
            x="ResilienceScore",
            color="Health Tier",
            color_discrete_map=color_map,
            nbins=50,
            labels={"ResilienceScore": "Resilience Score (0–100)", "count": "Number of Nonprofits"},
        )
        hist.update_layout(
            bargap=0.05,
            legend_title_text="",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            yaxis_title="Number of Nonprofits",
            margin=dict(t=10),
        )
        st.plotly_chart(hist, use_container_width=True)

    with col_explain:
        st.markdown("**What is the Resilience Score?**")
        st.markdown(
            "A 0–100 composite rating based on five financial fundamentals:\n\n"
            "- **Operating reserves** (30 pts)\n"
            "- **Revenue diversification** (20 pts)\n"
            "- **Program spending efficiency** (20 pts)\n"
            "- **Surplus margin** (15 pts)\n"
            "- **Low debt** (15 pts)\n\n"
            "Higher scores mean the organization is better positioned "
            "to weather funding disruptions."
        )

    # --- Geographic view ---
    st.markdown('<div class="section-header">Resilience Across the Country</div>', unsafe_allow_html=True)

    state_avg = df.groupby("State", as_index=False).agg(
        AvgResilience=("ResilienceScore", "mean"),
        Count=("EIN", "count"),
        AtRiskPct=("AtRisk", "mean"),
    )
    state_avg["Label"] = state_avg.apply(
        lambda r: f"{r['State']}: Score {r['AvgResilience']:.0f} | {r['AtRiskPct']:.0%} at risk | {r['Count']:,} orgs",
        axis=1,
    )
    score_min = max(state_avg["AvgResilience"].min() - 2, 50)
    score_max = min(state_avg["AvgResilience"].max() + 2, 100)
    choropleth = px.choropleth(
        state_avg,
        locations="State",
        locationmode="USA-states",
        color="AvgResilience",
        scope="usa",
        color_continuous_scale="RdYlGn",
        range_color=(score_min, score_max),
        hover_name="Label",
        labels={"AvgResilience": "Avg. Resilience Score"},
    )
    choropleth.update_layout(
        margin=dict(l=0, r=0, t=10, b=0),
        coloraxis_colorbar=dict(title="Score", thickness=15),
        geo=dict(bgcolor="rgba(0,0,0,0)"),
    )
    st.plotly_chart(choropleth, use_container_width=True)

    # --- Sector breakdown ---
    st.markdown('<div class="section-header">How Different Sectors Compare</div>', unsafe_allow_html=True)

    sector_stats = (
        df.groupby("Sector", as_index=False)
        .agg(
            Count=("EIN", "count"),
            AvgResilience=("ResilienceScore", "mean"),
            AtRiskPct=("AtRisk", "mean"),
            MedianReserves=("OperatingReserveMonths", "median"),
        )
        .sort_values("AvgResilience", ascending=True)
    )

    bar = px.bar(
        sector_stats,
        y="Sector",
        x="AvgResilience",
        orientation="h",
        color="AvgResilience",
        color_continuous_scale="RdYlGn",
        labels={"AvgResilience": "Average Resilience Score", "Sector": ""},
        hover_data={"Count": True, "AtRiskPct": ":.1%", "MedianReserves": ":.1f"},
    )
    bar.update_layout(
        showlegend=False,
        coloraxis_showscale=False,
        margin=dict(t=10),
        yaxis=dict(tickfont=dict(size=12)),
        height=max(400, len(sector_stats) * 30),
    )
    st.plotly_chart(bar, use_container_width=True)

    strongest = sector_stats.iloc[-1]
    weakest = sector_stats.iloc[0]
    st.markdown(
        f'<div class="insight-box">'
        f"<strong>Sector comparison:</strong> <em>{strongest['Sector']}</em> has the highest average "
        f"resilience ({strongest['AvgResilience']:.0f}/100), while <em>{weakest['Sector']}</em> "
        f"scores lowest ({weakest['AvgResilience']:.0f}/100) with {weakest['AtRiskPct']:.0%} of organizations at risk."
        f"</div>",
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# PAGE 2 — Peer Benchmarking
# ---------------------------------------------------------------------------
def peer_page(df: pd.DataFrame) -> None:
    st.title("Peer Benchmarking")
    st.markdown(
        "Compare any nonprofit's financial health against **similar organizations** "
        "(same sector, size, and state). See where it excels and where it needs improvement."
    )

    org_names = sorted(df["OrgName"].dropna().unique().tolist())
    org = st.selectbox(
        "Search for an organization",
        org_names,
        help="Type a name to search. We'll compare it to organizations of the same type, size, and location.",
    )
    if not org:
        return

    row = df[df["OrgName"] == org].iloc[0]
    peer_id = row["PeerGroupID"]
    peer_df = df[df["PeerGroupID"] == peer_id]

    # Organization snapshot
    st.markdown('<div class="section-header">Organization Snapshot</div>', unsafe_allow_html=True)

    label, css_class = _resilience_label(row["ResilienceScore"])
    col_info, col_score = st.columns([3, 1])
    with col_info:
        st.markdown(f"**{row['OrgName']}**")
        st.markdown(
            f"**Location:** {row.get('City', '—')}, {row['State']} &nbsp;|&nbsp; "
            f"**Sector:** {row['Sector']} &nbsp;|&nbsp; "
            f"**Size:** {row['SizeCategory']} &nbsp;|&nbsp; "
            f"**Peer group:** {peer_df.shape[0]:,} similar organizations"
        )
    with col_score:
        score_val = row["ResilienceScore"]
        score_display = f"{score_val:.0f}" if pd.notna(score_val) else "N/A"
        st.markdown(
            f'<div style="text-align:center">'
            f'<span style="font-size:2.4rem; font-weight:700; color:#1a2332">{score_display}</span>'
            f'<span style="font-size:1rem; color:#6b7280">/100</span><br/>'
            f'<span class="health-badge {css_class}">{label}</span>'
            f"</div>",
            unsafe_allow_html=True,
        )

    # Radar chart with friendly names
    metrics = [
        "ProgramExpenseRatio",
        "FundraisingRatio",
        "SurplusMargin",
        "OperatingReserveMonths",
        "DebtRatio",
    ]
    friendly = [FRIENDLY_METRIC_NAMES[m] for m in metrics]
    med = peer_df[metrics].median()

    # Metrics where a LOWER value is better (invert so the radar chart reads intuitively:
    # a larger spoke = doing better than peers, smaller spoke = doing worse).
    LOWER_IS_BETTER = {"FundraisingRatio", "DebtRatio"}

    def _normalize(vals, meds, metric_names):
        normed_vals = []
        normed_meds = []
        for v, m, mn in zip(vals, meds, metric_names):
            ref = max(abs(m), 0.001)
            if mn in LOWER_IS_BETTER:
                if abs(m) < 0.001 and abs(v) < 0.001:
                    # Both org and median are effectively zero — genuinely equal
                    normed = 1.0
                elif abs(m) < 0.001:
                    # Peer median is ~0 but org has non-zero cost → worse than peers
                    normed = 0.0
                else:
                    # Normal case: invert so lower cost → larger spoke (better)
                    normed = max(0.0, 2.0 - v / ref)
            else:
                normed = v / ref
            normed_vals.append(normed)
            normed_meds.append(1.0)
        return normed_vals, normed_meds

    vals = [row[m] for m in metrics]
    nv, nm = _normalize(vals, [med[m] for m in metrics], metrics)

    st.markdown('<div class="section-header">How Does This Organization Compare?</div>', unsafe_allow_html=True)

    col_radar, col_detail = st.columns([2, 1])
    with col_radar:
        fig = go.Figure()
        fig.add_trace(
            go.Scatterpolar(
                r=nv + [nv[0]],
                theta=friendly + [friendly[0]],
                fill="toself",
                name=org[:30],
                fillcolor="rgba(59,130,246,0.15)",
                line=dict(color="#3b82f6", width=2),
            )
        )
        fig.add_trace(
            go.Scatterpolar(
                r=nm + [nm[0]],
                theta=friendly + [friendly[0]],
                fill="toself",
                name="Peer Median",
                fillcolor="rgba(156,163,175,0.1)",
                line=dict(color="#9ca3af", width=2, dash="dot"),
            )
        )
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=False)),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
            margin=dict(t=30, b=60),
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_detail:
        st.markdown("**Metric-by-Metric Breakdown**")
        for m, fn in zip(metrics, friendly):
            org_val = row[m]
            peer_med = med[m]
            if pd.isna(org_val):
                continue

            pctile = row.get(f"{m}_PeerPctile", None)
            flag = row.get(f"{m}_Flag", "Within Norm")

            if m in ("FundraisingRatio", "DebtRatio"):
                icon = "🟢" if org_val <= peer_med else "🔴"
            else:
                icon = "🟢" if org_val >= peer_med else "🔴"

            pctile_str = f" (top {(1 - pctile):.0%})" if pctile and not pd.isna(pctile) else ""
            st.markdown(f"{icon} **{fn}**: {org_val:.2f} vs. peer median {peer_med:.2f}{pctile_str}")

        st.markdown("---")
        st.markdown(
            "_🟢 = better than peers &nbsp;|&nbsp; 🔴 = below peers_",
        )

    # Expandable explanations
    with st.expander("What do these metrics mean?"):
        for fn, expl in METRIC_EXPLANATIONS.items():
            st.markdown(f"- **{fn}:** {expl}")

    # Peer comparison table
    st.markdown('<div class="section-header">Full Peer Group</div>', unsafe_allow_html=True)
    display_cols = ["OrgName", "State", "ResilienceScore"] + metrics
    rename_map = {m: FRIENDLY_METRIC_NAMES[m] for m in metrics}
    peer_display = peer_df[display_cols].rename(columns=rename_map).head(200)
    st.dataframe(
        peer_display.style.format(
            {FRIENDLY_METRIC_NAMES[m]: "{:.2f}" for m in metrics} | {"ResilienceScore": "{:.0f}"}
        ),
        use_container_width=True,
        height=400,
    )


# ---------------------------------------------------------------------------
# PAGE 3 — Resilience Explorer
# ---------------------------------------------------------------------------
def resilience_page(df: pd.DataFrame, metrics: dict) -> None:
    st.title("Resilience Explorer")
    st.markdown(
        "Understand **what drives financial resilience** and explore individual organizations. "
        "Use the filters to find nonprofits that match your criteria."
    )

    # Risk tier summary
    st.markdown('<div class="section-header">Risk Tiers at a Glance</div>', unsafe_allow_html=True)

    tiers = {
        "Strong (70–100)": (df["ResilienceScore"] >= 70).sum(),
        "Moderate (40–70)": ((df["ResilienceScore"] >= 40) & (df["ResilienceScore"] < 70)).sum(),
        "At Risk (0–40)": (df["ResilienceScore"] < 40).sum(),
    }
    tier_colors = {"Strong (70–100)": "#22c55e", "Moderate (40–70)": "#eab308", "At Risk (0–40)": "#ef4444"}

    t1, t2, t3 = st.columns(3)
    for col, (tier_name, count) in zip([t1, t2, t3], tiers.items()):
        pct = count / len(df)
        col.metric(tier_name, f"{count:,}", f"{pct:.1%} of all nonprofits")

    # What drives resilience?
    if metrics and "feature_importances" in metrics:
        st.markdown(
            '<div class="section-header">What Drives Financial Resilience?</div>',
            unsafe_allow_html=True,
        )

        imp = metrics["feature_importances"]
        imp_df = pd.DataFrame(
            [
                {"Factor": FRIENDLY_METRIC_NAMES.get(k, k.replace("_", " ").title()), "Importance": v}
                for k, v in imp.items()
            ]
        ).sort_values("Importance", ascending=True)

        top_10 = imp_df.tail(10)

        col_chart, col_text = st.columns([2, 1])
        with col_chart:
            fig = px.bar(
                top_10,
                y="Factor",
                x="Importance",
                orientation="h",
                color="Importance",
                color_continuous_scale="Blues",
                labels={"Importance": "Relative Importance", "Factor": ""},
            )
            fig.update_layout(
                showlegend=False,
                coloraxis_showscale=False,
                margin=dict(t=10),
                height=350,
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_text:
            top3 = imp_df.tail(3)["Factor"].tolist()[::-1]
            st.markdown("**Key takeaway:**")
            st.markdown(
                f"The three strongest predictors of financial resilience are "
                f"**{top3[0]}**, **{top3[1]}**, and **{top3[2]}**.\n\n"
                f"Organizations that maintain healthy surpluses, steady revenue growth, "
                f"and adequate cash reserves are far more likely to survive funding disruptions."
            )

    # Interactive scatter
    st.markdown('<div class="section-header">Explore Individual Organizations</div>', unsafe_allow_html=True)

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        sectors = ["All Sectors"] + sorted(df["Sector"].dropna().unique().tolist())
        sel_sector = st.selectbox("Filter by sector", sectors, key="res_sector")
    with col_f2:
        sizes = ["All Sizes"] + sorted(df["SizeCategory"].dropna().unique().tolist())
        sel_size = st.selectbox("Filter by Revenue", sizes, key="res_size")
    with col_f3:
        states_list = ["All States"] + sorted(df["State"].dropna().unique().tolist())
        sel_state = st.selectbox("Filter by state", states_list, key="res_state")

    filtered = df.copy()
    if sel_sector != "All Sectors":
        filtered = filtered[filtered["Sector"] == sel_sector]
    if sel_size != "All Sizes":
        filtered = filtered[filtered["SizeCategory"] == sel_size]
    if sel_state != "All States":
        filtered = filtered[filtered["State"] == sel_state]

    sample = filtered.sample(min(len(filtered), 5000), random_state=42) if len(filtered) > 0 else filtered

    if len(sample) > 0:
        sample["Revenue"] = sample["TotalRevenueCY"].apply(_fmt_dollars)
        sample["Health"] = sample["ResilienceScore"].apply(lambda s: _resilience_label(s)[0])

        scatter = px.scatter(
            sample,
            x="TotalRevenueCY",
            y="ResilienceScore",
            color="Health",
            color_discrete_map={"Strong": "#22c55e", "Moderate": "#eab308", "At Risk": "#ef4444"},
            hover_data={"OrgName": True, "State": True, "Revenue": True, "TotalRevenueCY": False},
            labels={
                "TotalRevenueCY": "Total Revenue",
                "ResilienceScore": "Resilience Score (0–100)",
            },
            log_x=True,
            opacity=0.6,
        )
        scatter.update_layout(
            legend_title_text="",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            margin=dict(t=30),
            height=450,
        )
        st.plotly_chart(scatter, use_container_width=True)

    # Searchable table
    st.markdown("**Browse organizations:**")
    show_cols = ["OrgName", "State", "Sector", "SizeCategory", "ResilienceScore", "AtRisk", "AtRiskProbability"]
    rename = {
        "OrgName": "Organization",
        "SizeCategory": "Size",
        "ResilienceScore": "Resilience Score",
        "AtRisk": "At Risk?",
        "AtRiskProbability": "Risk Probability",
    }
    display_df = (
        filtered[show_cols]
        .rename(columns=rename)
        .sort_values("Resilience Score", ascending=True)
        .head(500)
    )
    display_df["At Risk?"] = display_df["At Risk?"].map({0: "No", 1: "Yes"})
    st.dataframe(
        display_df.style.format({"Resilience Score": "{:.0f}", "Risk Probability": "{:.1%}"}),
        use_container_width=True,
        height=400,
    )


# ---------------------------------------------------------------------------
# PAGE 4 — Stress Test Simulator
# ---------------------------------------------------------------------------
def simulation_page(master: pd.DataFrame) -> None:
    st.title("Stress Test Simulator")
    st.markdown(
        "See how nonprofits would fare under **real-world funding disruptions** — "
        "from government grant cuts to economic recessions. Adjust the sliders to customize each scenario."
    )

    SCENARIO_OPTIONS: dict[str, dict] = {
        "Grant Shock": {
            "description": (
                "What if private donations and grants dried up? Simulates a major donor withdrawal or economic downturn. "
                "<br><strong>Affected stream:</strong> Private contributions & grants only. "
                "Organizations that don't rely on donations are unaffected."
            ),
            "streams": {
                "ContributionsGrantsCY": ("Donations & grants drop", 30),
            },
        },
        "Gov Grant Shock": {
            "description": (
                "What if government funding was cut? Models policy changes or budget sequestration. "
                "<br><strong>Affected stream:</strong> Government grants only — organizations without government funding are entirely unaffected, "
                "which is why a large government cut can show fewer at-risk nonprofits than a smaller across-the-board recession."
            ),
            "streams": {
                "GovernmentGrantsAmt": ("Government grants drop", 50),
            },
        },
        "Program Revenue Shock": {
            "description": (
                "What if earned revenue from programs fell? Simulates reduced demand or pandemic-like service disruptions. "
                "<br><strong>Affected stream:</strong> Program service revenue only. Fee-for-service and tuition-dependent nonprofits bear the full impact."
            ),
            "streams": {
                "ProgramServiceRevCY": ("Program service revenue drop", 25),
            },
        },
        "Investment Shock": {
            "description": (
                "What if investment returns dropped? Models a stock market crash affecting endowment-dependent organizations. "
                "<br><strong>Affected stream:</strong> Investment income only. Most small nonprofits have negligible endowments, so impact is concentrated among larger organizations."
            ),
            "streams": {
                "InvestmentIncomeCY": ("Investment income drop", 40),
            },
        },
        "Combined Recession": {
            "description": (
                "What if all revenue sources dropped simultaneously? Models a broad economic recession. "
                "<br><strong>Affected streams:</strong> All four revenue streams drop together — "
                "which is why this typically affects more nonprofits than a larger shock to a single stream."
            ),
            "streams": {
                "ContributionsGrantsCY": ("Donations & grants drop", 20),
                "GovernmentGrantsAmt": ("Government grants drop", 20),
                "ProgramServiceRevCY": ("Program revenue drop", 20),
                "InvestmentIncomeCY": ("Investment income drop", 20),
            },
        },
    }

    scenario = st.selectbox("Choose a scenario to explore", list(SCENARIO_OPTIONS.keys()))
    config = SCENARIO_OPTIONS[scenario]

    st.markdown(f'<div class="insight-box">{config["description"]}</div>', unsafe_allow_html=True)

    # Sliders — one per affected revenue stream
    st.markdown('<div class="section-header">Customize Shock Intensity</div>', unsafe_allow_html=True)
    streams = config["streams"]

    # Sync checkbox — only shown when there are multiple streams (Combined Recession)
    sync = False
    if len(streams) > 1:
        sync = st.checkbox(
            "Sync all sliders — drag one to update all streams equally",
            value=True,
            key=f"sync_{scenario}",
        )

    adjustments: dict[str, float] = {}

    if sync and len(streams) > 1:
        sync_val_key = f"sync_val_{scenario}"
        slider_keys = {col: f"shock_{scenario}_{col}" for col in streams}

        # Initialize sync value from existing slider state or defaults
        if sync_val_key not in st.session_state:
            first_col = next(iter(streams))
            st.session_state[sync_val_key] = st.session_state.get(
                slider_keys[first_col], next(iter(streams.values()))[1]
            )

        # Detect if any slider was moved (differs from last synced value) and update sync_val
        for col_name, key in slider_keys.items():
            if key in st.session_state and st.session_state[key] != st.session_state[sync_val_key]:
                st.session_state[sync_val_key] = st.session_state[key]
                break

        # Force all slider session state values to the synced value before rendering
        for key in slider_keys.values():
            st.session_state[key] = st.session_state[sync_val_key]

        slider_cols = st.columns(len(streams))
        for i, (col_name, (label, _default)) in enumerate(streams.items()):
            drop_pct = slider_cols[i].slider(
                label,
                min_value=0,
                max_value=100,
                step=5,
                format="%d%%",
                key=slider_keys[col_name],
            )
            adjustments[col_name] = 1.0 - drop_pct / 100.0
    else:
        slider_cols = st.columns(len(streams))
        for i, (col_name, (label, default)) in enumerate(streams.items()):
            drop_pct = slider_cols[i].slider(
                label,
                min_value=0,
                max_value=100,
                value=default,
                step=5,
                format="%d%%",
                key=f"shock_{scenario}_{col_name}",
            )
            adjustments[col_name] = 1.0 - drop_pct / 100.0

    # Run simulation live on master data
    required_cols = [
        "EIN", "OrgName", "Sector", "State", "SizeCategory",
        "ContributionsGrantsCY", "GovernmentGrantsAmt", "ProgramServiceRevCY",
        "InvestmentIncomeCY", "TotalRevenueCY", "TotalExpensesCY", "NetAssetsEOY",
    ]
    sim_input = master[[c for c in required_cols if c in master.columns]].copy()
    sdf = simulate_shock(sim_input, scenario, adjustments)
    sdf["RecoveryYears"] = sdf.apply(estimate_recovery, axis=1)

    # Pre-shock baseline: classify each org using the same logic as simulate_shock,
    # and add helper columns used by the Company Drill-Down tab.
    _pre_classes = sdf.apply(
        lambda r: _classify_status(
            r.get("TotalRevenueCY", np.nan),
            r.get("TotalExpensesCY", np.nan),
            r.get("NetAssetsEOY", np.nan),
        ),
        axis=1,
    )
    sdf["PreShock_Status"] = [s for s, _ in _pre_classes]
    sdf["PreShock_MonthsToInsolvency"] = [m for _, m in _pre_classes]
    _tier_index = {s: i for i, s in enumerate(STATUS_ORDER)}
    sdf["PreShock_Tier"] = sdf["PreShock_Status"].map(_tier_index)
    sdf["PostShock_Tier"] = sdf["PostShock_Status"].map(_tier_index)
    sdf["TierDowngrade"] = sdf["PreShock_Tier"] - sdf["PostShock_Tier"]
    sdf["RevenueLostPct"] = np.where(
        sdf["TotalRevenueCY"] > 0,
        (sdf["TotalRevenueCY"] - sdf["PostShock_TotalRevenue"]) / sdf["TotalRevenueCY"],
        0.0,
    )

    # Compute revenue impact stats
    valid = sdf[sdf["TotalRevenueCY"] > 0]
    if len(valid) > 0:
        avg_revenue_lost = valid["RevenueLostPct"].mean()
        pct_with_any_loss = (valid["RevenueLostPct"] > 0).mean()
    else:
        avg_revenue_lost = 0.0
        pct_with_any_loss = 0.0

    # Split display into two tabs: aggregate view + per-company drill-down.
    tab_overall, tab_company = st.tabs(["Overall Impact", "Company Drill-Down"])

    with tab_company:
        _render_company_drilldown(sdf=sdf, scenario=scenario, config=config)

    # Everything rendered below this point goes into the "Overall Impact" tab.
    # We push the tab onto Streamlit's render stack manually so we don't have to
    # re-indent the pre-existing aggregate rendering code. The matching __exit__
    # at the bottom of this function pops the tab off the stack.
    tab_overall.__enter__()

    # Impact summary
    st.markdown('<div class="section-header">Overall Impact</div>', unsafe_allow_html=True)

    status_counts = sdf["PostShock_Status"].value_counts()
    total = len(sdf)

    ordered_statuses = [
        "Critical (<3mo reserves)",
        "At Risk (3-12mo reserves)",
        "Stressed (>12mo reserves)",
        "Survives (Surplus)",
    ]

    m1, m2, m3, m4 = st.columns(4)
    for col, status in zip([m1, m2, m3, m4], ordered_statuses):
        count = status_counts.get(status, 0)
        pct = count / total if total else 0
        short_label = status.split("(")[0].strip()
        col.metric(short_label, f"{count:,}", f"{pct:.1%}")

    critical_pct = status_counts.get("Critical (<3mo reserves)", 0) / total if total else 0
    at_risk_pct = status_counts.get("At Risk (3-12mo reserves)", 0) / total if total else 0
    combined_danger = critical_pct + at_risk_pct
    st.markdown(
        f'<div class="insight-box-warn">'
        f"<strong>Impact:</strong> Under this scenario, <strong>{combined_danger:.1%}</strong> of nonprofits "
        f"would face serious financial distress (critical or at risk). That's roughly "
        f"<strong>{int(round(combined_danger * total)):,}</strong> organizations that could struggle to "
        f"maintain services. "
        f"On average, nonprofits would lose <strong>{avg_revenue_lost:.1%} of their total revenue</strong> "
        f"({pct_with_any_loss:.0%} of organizations are directly exposed to this shock)."
        f"</div>",
        unsafe_allow_html=True,
    )

    # Status distribution chart
    col_pie, col_bar = st.columns(2)

    with col_pie:
        status_dist = sdf["PostShock_Status"].value_counts().reset_index()
        status_dist.columns = ["Status", "Count"]
        fig_pie = px.pie(
            status_dist,
            names="Status",
            values="Count",
            color="Status",
            color_discrete_map=STATUS_COLORS,
            hole=0.4,
        )
        fig_pie.update_layout(
            margin=dict(t=10),
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        )
        fig_pie.update_traces(textposition="inside", textinfo="percent+label")
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_bar:
        sector_impact = (
            sdf.groupby(["Sector", "PostShock_Status"], as_index=False)
            .size()
        )
        sector_totals = sdf.groupby("Sector").size().reset_index(name="Total")
        sector_impact = sector_impact.merge(sector_totals, on="Sector")
        sector_impact["Percentage"] = sector_impact["size"] / sector_impact["Total"]

        fig_bar = px.bar(
            sector_impact,
            y="Sector",
            x="Percentage",
            color="PostShock_Status",
            orientation="h",
            color_discrete_map=STATUS_COLORS,
            category_orders={
                "PostShock_Status": [
                    "Critical (<3mo reserves)",
                    "At Risk (3-12mo reserves)",
                    "Stressed (>12mo reserves)",
                    "Survives (Surplus)",
                ]
            },
            labels={"Percentage": "Share of Sector", "PostShock_Status": "Post-Shock Status", "Sector": ""},
            barmode="stack",
        )
        fig_bar.update_layout(
            legend_title_text="",
            legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
            margin=dict(t=10),
            height=max(350, sdf["Sector"].nunique() * 28),
            xaxis_tickformat=".0%",
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    # Most Exposed Sectors — top 3 by dependency on shocked stream
    SCENARIO_DEP_COL: dict[str, str | list[str]] = {
        "Grant Shock": "GrantDependencyPct",
        "Gov Grant Shock": "GovGrantPct",
        "Program Revenue Shock": "ProgramRevenuePct",
        "Investment Shock": "InvestmentRevenuePct",
        "Combined Recession": ["GrantDependencyPct", "GovGrantPct", "ProgramRevenuePct", "InvestmentRevenuePct"],
    }

    STREAM_LABELS = {
        "GovernmentGrantsAmt": "Government Grants",
        "ContributionsGrantsCY": "Private Donations & Grants",
        "ProgramServiceRevCY": "Program Service Revenue",
        "InvestmentIncomeCY": "Investment Income",
        "OtherRevenueCY": "Other Revenue",
    }

    dep_col = SCENARIO_DEP_COL.get(scenario)

    if dep_col is not None and "Sector" in master.columns:
        st.markdown('<div class="section-header">Most Exposed Sectors — Funding Stream Breakdown</div>', unsafe_allow_html=True)

        sector_base = master[master["TotalRevenueCY"] > 0].copy()

        # Compute dependency per sector
        if isinstance(dep_col, list):
            sector_base["_dep"] = sector_base[dep_col].mean(axis=1)
            dep_label = "Avg. Dependency on Shocked Streams"
        else:
            sector_base["_dep"] = sector_base[dep_col]
            dep_label = f"Avg. {STREAM_LABELS.get(list(config['streams'].keys())[0], dep_col)} Dependency"

        sector_dep = (
            sector_base.groupby("Sector")["_dep"]
            .mean()
            .sort_values(ascending=False)
            .head(3)
        )
        top3_sectors = sector_dep.index.tolist()

        # Build funding stream breakdown for those 3 sectors
        stream_cols = list(STREAM_LABELS.keys())
        available_streams = [c for c in stream_cols if c in master.columns]

        breakdown_rows = []
        for sec in top3_sectors:
            sec_data = sector_base[sector_base["Sector"] == sec]
            total_rev = sec_data["TotalRevenueCY"].mean()
            for col in available_streams:
                avg_amt = sec_data[col].fillna(0).mean()
                pct = avg_amt / total_rev if total_rev > 0 else 0
                breakdown_rows.append({
                    "Sector": sec,
                    "Stream": STREAM_LABELS[col],
                    "Pct": pct,
                    "IsShocked": col in config["streams"],
                })

        breakdown_df = pd.DataFrame(breakdown_rows)

        # Color palette: shocked stream gets a vivid accent, others get muted blues/grays
        STREAM_COLORS = {
            "Government Grants": "#ef4444",
            "Private Donations & Grants": "#f97316",
            "Program Service Revenue": "#6366f1",
            "Investment Income": "#14b8a6",
            "Other Revenue": "#94a3b8",
        }
        shocked_stream_names = {STREAM_LABELS[c] for c in config["streams"] if c in STREAM_LABELS}

        fig_breakdown = px.bar(
            breakdown_df,
            x="Pct",
            y="Sector",
            color="Stream",
            orientation="h",
            barmode="stack",
            color_discrete_map=STREAM_COLORS,
            labels={"Pct": "Share of Total Revenue", "Stream": "Revenue Stream", "Sector": ""},
            text=breakdown_df["Pct"].apply(lambda v: f"{v:.0%}" if v >= 0.05 else ""),
        )
        fig_breakdown.update_traces(textposition="inside", insidetextanchor="middle")
        fig_breakdown.update_layout(
            margin=dict(t=30, b=10),
            xaxis_tickformat=".0%",
            height=260,
            legend=dict(orientation="h", yanchor="bottom", y=-0.55, xanchor="center", x=0.5),
            legend_title_text="",
        )
        st.plotly_chart(fig_breakdown, use_container_width=True)

        # Dependency callout
        dep_lines = []
        for sec in top3_sectors:
            dep_pct = sector_dep[sec]
            shocked_names = " & ".join(shocked_stream_names) if shocked_stream_names else "shocked streams"
            dep_lines.append(f"<strong>{sec}</strong> ({dep_pct:.0%} {shocked_names} dependency)")
        st.markdown(
            f'<div class="insight-box-warn">'
            f"<strong>Hardest-hit sectors:</strong> {' — '.join(dep_lines)}. "
            f"These sectors face the greatest direct revenue loss because of their reliance on the shocked funding stream."
            f"</div>",
            unsafe_allow_html=True,
        )

    # Recovery timeline
    recovery_data = sdf[sdf["RecoveryYears"].notna() & (sdf["RecoveryYears"] > 0)]
    if len(recovery_data) > 0:
        st.markdown('<div class="section-header">Recovery Timeline</div>', unsafe_allow_html=True)
        avg_recovery = recovery_data["RecoveryYears"].mean()
        med_recovery = recovery_data["RecoveryYears"].median()
        st.markdown(
            f"For organizations that would go into deficit, the **median recovery time** is "
            f"**{med_recovery:.1f} years** (average: {avg_recovery:.1f} years), assuming a 5% annual revenue recovery rate."
        )

        fig_recov = px.histogram(
            recovery_data,
            x="RecoveryYears",
            nbins=20,
            labels={"RecoveryYears": "Years to Recover", "count": "Number of Organizations"},
            color_discrete_sequence=["#6366f1"],
        )
        fig_recov.update_layout(margin=dict(t=10), yaxis_title="Number of Organizations")
        st.plotly_chart(fig_recov, use_container_width=True)

    # Pop the "Overall Impact" tab off Streamlit's render stack (pairs with the
    # tab_overall.__enter__() call above).
    tab_overall.__exit__(None, None, None)


def _status_badge_html(status: str) -> str:
    color = STATUS_COLORS.get(status, "#6b7280")
    short = status.split("(")[0].strip()
    return (
        f'<span style="display:inline-block; padding:4px 12px; border-radius:20px; '
        f'background:{color}22; color:{color}; font-weight:700; font-size:0.85rem; '
        f'border:1px solid {color}55">{short}</span>'
    )


def _render_company_drilldown(sdf: pd.DataFrame, scenario: str, config: dict) -> None:
    st.markdown(
        '<div class="insight-box">'
        "Explore how this scenario affects a <strong>specific organization</strong>. "
        "Adjust the shock sliders above and see the org-level impact update live — "
        "including status changes, revenue loss by stream, and projected recovery timeline."
        "</div>",
        unsafe_allow_html=True,
    )

    STREAM_LABELS_DRILL = {
        "GovernmentGrantsAmt": "Government Grants",
        "ContributionsGrantsCY": "Private Donations & Grants",
        "ProgramServiceRevCY": "Program Service Revenue",
        "InvestmentIncomeCY": "Investment Income",
    }
    STREAM_COLORS_DRILL = {
        "Government Grants": "#ef4444",
        "Private Donations & Grants": "#f97316",
        "Program Service Revenue": "#6366f1",
        "Investment Income": "#14b8a6",
    }
    shocked_cols = set(config["streams"].keys())

    # ------------------------------------------------------------------
    # Most Affected Organizations — discovery table (shown by default)
    # ------------------------------------------------------------------
    st.markdown('<div class="section-header">Most Affected Organizations</div>', unsafe_allow_html=True)
    st.markdown(
        "Sorted by the size of the status downgrade under this scenario, then by revenue lost. "
        "Click any row's **Select** button below the table to drill into a specific organization."
    )

    affected = sdf[(sdf["TierDowngrade"] > 0) | (sdf["RevenueLostPct"] > 0)].copy()
    affected = affected.sort_values(
        by=["TierDowngrade", "RevenueLostPct", "RecoveryYears"],
        ascending=[False, False, False],
    ).head(20)

    if len(affected) > 0:
        table_df = pd.DataFrame({
            "Organization": affected["OrgName"],
            "Sector": affected.get("Sector", ""),
            "State": affected.get("State", ""),
            "Status Change": affected["PreShock_Status"].str.split("(").str[0].str.strip()
                + " → "
                + affected["PostShock_Status"].str.split("(").str[0].str.strip(),
            "Revenue Lost": affected["RevenueLostPct"].apply(lambda v: f"{v:.1%}"),
            "Recovery": affected["RecoveryYears"].apply(
                lambda v: f"{v:.1f} yrs" if pd.notna(v) else "20+ yrs"
            ),
        })
        st.dataframe(table_df, use_container_width=True, hide_index=True, height=300)
    else:
        st.info("No organizations are meaningfully affected by this scenario.")

    # ------------------------------------------------------------------
    # Org selector
    # ------------------------------------------------------------------
    st.markdown('<div class="section-header">Select an Organization</div>', unsafe_allow_html=True)

    if "Sector" in sdf.columns:
        sectors = ["All sectors"] + sorted(sdf["Sector"].dropna().unique().tolist())
        col_sector, col_search = st.columns([1, 2])
        sector_filter = col_sector.selectbox("Filter by sector", sectors, key=f"drill_sector_{scenario}")
        if sector_filter != "All sectors":
            org_pool = sdf[sdf["Sector"] == sector_filter]
        else:
            org_pool = sdf
    else:
        col_search = st.container()
        org_pool = sdf

    # Default to the most-affected org in the current pool
    default_org = None
    if len(affected) > 0:
        candidates = affected[affected["OrgName"].isin(org_pool["OrgName"])]
        if len(candidates) > 0:
            default_org = candidates.iloc[0]["OrgName"]
    if default_org is None and len(org_pool) > 0:
        default_org = org_pool.iloc[0]["OrgName"]

    org_names = org_pool["OrgName"].dropna().sort_values().unique().tolist()
    if not org_names:
        st.info("No organizations match this filter.")
        return

    default_idx = org_names.index(default_org) if default_org in org_names else 0
    selected_name = col_search.selectbox(
        "Organization",
        org_names,
        index=default_idx,
        key=f"drill_org_{scenario}",
    )

    sel_rows = sdf[sdf["OrgName"] == selected_name]
    if len(sel_rows) == 0:
        st.warning("Could not find that organization in the simulation results.")
        return
    row = sel_rows.iloc[0]

    # ------------------------------------------------------------------
    # Header: Status change + org meta
    # ------------------------------------------------------------------
    pre_status = row["PreShock_Status"]
    post_status = row["PostShock_Status"]
    tier_drop = int(row["TierDowngrade"]) if pd.notna(row["TierDowngrade"]) else 0

    if tier_drop > 0:
        delta_text = f'<span style="color:#b91c1c; font-weight:700">↓ Downgraded {tier_drop} tier{"s" if tier_drop > 1 else ""}</span>'
    elif tier_drop < 0:
        delta_text = '<span style="color:#166534; font-weight:700">↑ Improved</span>'
    else:
        delta_text = '<span style="color:#6b7280; font-weight:600">No status change</span>'

    sector_txt = row.get("Sector", "—") or "—"
    state_txt = row.get("State", "—") or "—"
    size_txt = row.get("SizeCategory", "") or ""

    st.markdown(
        f"""<div style="background:#f8f9fc; border:1px solid #dde2ec; border-radius:12px; padding:18px 22px; margin:8px 0 18px 0">
          <div style="font-size:1.15rem; font-weight:700; color:#1a2332; margin-bottom:4px">{selected_name}</div>
          <div style="font-size:0.85rem; color:#6b7280; margin-bottom:14px">
            {sector_txt} · {state_txt}{f" · {size_txt}" if size_txt else ""}
          </div>
          <div style="display:flex; align-items:center; gap:12px; flex-wrap:wrap">
            <div style="font-size:0.8rem; color:#6b7280">Current</div>
            {_status_badge_html(pre_status)}
            <div style="font-size:1.2rem; color:#9ca3af">→</div>
            <div style="font-size:0.8rem; color:#6b7280">Post-shock</div>
            {_status_badge_html(post_status)}
            <div style="margin-left:8px">{delta_text}</div>
          </div>
        </div>""",
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # Key metrics row
    # ------------------------------------------------------------------
    pre_rev = float(row.get("TotalRevenueCY", 0) or 0)
    post_rev = float(row.get("PostShock_TotalRevenue", 0) or 0)
    rev_lost_pct = float(row.get("RevenueLostPct", 0) or 0)
    rev_lost_dollars = pre_rev - post_rev
    months_post = row.get("MonthsToInsolvency", np.inf)
    recovery_yrs = row.get("RecoveryYears", np.nan)

    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    mcol1.metric("Revenue Lost", _fmt_dollars(rev_lost_dollars), f"-{rev_lost_pct:.1%}")
    post_rev_delta_pct = ((post_rev / pre_rev) - 1.0) if pre_rev > 0 else 0.0
    mcol2.metric(
        "Post-Shock Revenue",
        _fmt_dollars(post_rev),
        f"{post_rev_delta_pct:.1%} vs pre-shock",
    )
    if pd.notna(months_post) and np.isfinite(months_post):
        months_label = f"{months_post:.1f} mo" if months_post < 120 else "120+ mo"
    else:
        months_label = "Surplus"
    mcol3.metric("Months to Insolvency", months_label, help="How long cash reserves would last at the post-shock deficit rate.")
    if pd.notna(recovery_yrs) and recovery_yrs > 0:
        recov_label = f"{recovery_yrs:.1f} yrs"
    elif pd.notna(recovery_yrs) and recovery_yrs == 0:
        recov_label = "No deficit"
    else:
        recov_label = "20+ yrs"
    mcol4.metric("Recovery Time", recov_label, help="Years to rebuild reserves assuming 5% annual revenue recovery.")

    # ------------------------------------------------------------------
    # Revenue stream breakdown: pre vs post
    # ------------------------------------------------------------------
    st.markdown('<div class="section-header">Revenue Stream Impact</div>', unsafe_allow_html=True)

    stream_rows = []
    for col, label in STREAM_LABELS_DRILL.items():
        if col not in sdf.columns:
            continue
        pre_val = float(row.get(col, 0) or 0)
        post_col = f"PostShock_{col}"
        if post_col in sdf.columns:
            post_val = float(row.get(post_col, pre_val) or 0)
        else:
            post_val = pre_val
        stream_rows.append({
            "Stream": label,
            "Pre-Shock": pre_val,
            "Post-Shock": post_val,
            "IsShocked": col in shocked_cols,
        })

    if stream_rows:
        stream_df = pd.DataFrame(stream_rows)
        long_df = stream_df.melt(
            id_vars=["Stream", "IsShocked"],
            value_vars=["Pre-Shock", "Post-Shock"],
            var_name="Phase",
            value_name="Amount",
        )
        fig_streams = px.bar(
            long_df,
            x="Amount",
            y="Stream",
            color="Phase",
            barmode="group",
            orientation="h",
            color_discrete_map={"Pre-Shock": "#94a3b8", "Post-Shock": "#1e3a8a"},
            labels={"Amount": "Revenue ($)", "Stream": ""},
        )
        fig_streams.update_layout(
            margin=dict(t=10, b=80),
            height=max(260, len(stream_rows) * 70),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=-0.45,
                xanchor="center",
                x=0.5,
                traceorder="normal",
            ),
            legend_title_text="",
        )
        fig_streams.update_xaxes(
            tickfont=dict(color="#374151"),
            title_font=dict(color="#1f2937"),
        )
        fig_streams.update_yaxes(
            tickfont=dict(color="#374151"),
            title_font=dict(color="#1f2937"),
        )
        st.plotly_chart(fig_streams, use_container_width=True)

        # Narrative callout about which streams drove the impact
        shocked_impact = [
            (r["Stream"], r["Pre-Shock"] - r["Post-Shock"])
            for r in stream_rows
            if r["IsShocked"] and (r["Pre-Shock"] - r["Post-Shock"]) > 0
        ]
        if shocked_impact and pre_rev > 0:
            parts = [
                f"<strong>{name}</strong> ({(loss / pre_rev):.1%} of total revenue, {_fmt_dollars(loss)} lost)"
                for name, loss in sorted(shocked_impact, key=lambda x: -x[1])
            ]
            st.markdown(
                f'<div class="insight-box-warn">'
                f"<strong>Why this org is affected:</strong> The shock hits " + " and ".join(parts) + ". "
                f"That's a {rev_lost_pct:.1%} total revenue hit, which drives the status change above."
                f"</div>",
                unsafe_allow_html=True,
            )
        elif rev_lost_pct == 0:
            st.markdown(
                '<div class="insight-box-good">'
                "<strong>No direct exposure:</strong> This organization doesn't rely on any of the "
                "shocked revenue streams, so its financial position is unchanged under this scenario."
                "</div>",
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# PAGE 5 — Hidden Gems Finder
# ---------------------------------------------------------------------------
TIER_ORDER = [
    "Top 25 Priority",
    "Priority Shortlist",
    "Extended Shortlist",
    "Broader Universe",
    "Already Stable",
]

TIER_COLORS = {
    "Top 25 Priority": "#dc2626",
    "Priority Shortlist": "#f59e0b",
    "Extended Shortlist": "#3b82f6",
    "Broader Universe": "#94a3b8",
    "Already Stable": "#22c55e",
}


def _fmt_roi(val: float) -> str:
    if pd.isna(val):
        return "N/A"
    return f"${val:,.2f}" if val < 100 else f"${val:,.0f}"


def gems_page() -> None:
    st.title("Priority Investment Shortlist")
    st.markdown(
        "A ranked, **cost-efficiency-driven** shortlist of small-but-mighty nonprofits where "
        "a targeted donation would produce the highest mission ROI. Each organization is scored "
        "on how much program activity is **protected per dollar donated**, then grouped into "
        "prioritization tiers for funders like Fairlight."
    )

    gems = pd.read_csv("data/hidden_gems.csv", low_memory=False)

    # Back-compat: older CSVs may not have the new columns. If so, fall back gracefully.
    has_tiers = "PriorityTier" in gems.columns and "CostEfficiencyScore" in gems.columns
    if not has_tiers:
        st.warning(
            "The hidden-gems dataset needs to be regenerated. Run `python run_all.py` to compute "
            "the new Cost-Efficiency Score, ROI, and Priority Tier columns."
        )
        return

    needs_funding = gems[gems["DonationToStabilize"] > 0].copy()

    # ------------------------------------------------------------------
    # TIER SELECTOR — primary control
    # ------------------------------------------------------------------
    st.markdown('<div class="section-header">Choose a Prioritization Tier</div>', unsafe_allow_html=True)

    tier_options = [
        ("Top 25 Priority", "Top 25 — Immediate funding focus"),
        ("Priority Shortlist", "Top 100 — Priority shortlist"),
        ("Extended Shortlist", "Top 500 — Extended shortlist"),
        ("Broader Universe", "Full universe (all gems)"),
    ]
    tier_counts_map = {
        "Top 25 Priority": (gems["PriorityTier"] == "Top 25 Priority").sum(),
        "Priority Shortlist": gems["PriorityTier"].isin(["Top 25 Priority", "Priority Shortlist"]).sum(),
        "Extended Shortlist": gems["PriorityTier"].isin(
            ["Top 25 Priority", "Priority Shortlist", "Extended Shortlist"]
        ).sum(),
        "Broader Universe": len(needs_funding),
    }
    tier_labels = [f"{lbl}  ·  {tier_counts_map[key]:,} orgs" for key, lbl in tier_options]
    idx = st.radio(
        "Tier",
        options=list(range(len(tier_options))),
        format_func=lambda i: tier_labels[i],
        horizontal=True,
        label_visibility="collapsed",
        key="gems_tier_idx",
    )
    active_tier_key, _ = tier_options[idx]

    # Build active subset based on cumulative tier definition
    if active_tier_key == "Top 25 Priority":
        active = gems[gems["PriorityTier"] == "Top 25 Priority"].copy()
    elif active_tier_key == "Priority Shortlist":
        active = gems[gems["PriorityTier"].isin(["Top 25 Priority", "Priority Shortlist"])].copy()
    elif active_tier_key == "Extended Shortlist":
        active = gems[
            gems["PriorityTier"].isin(["Top 25 Priority", "Priority Shortlist", "Extended Shortlist"])
        ].copy()
    else:
        active = needs_funding.copy()

    active = active.sort_values("PriorityRank").reset_index(drop=True)

    # ------------------------------------------------------------------
    # TOP-LINE KPIs — ROI-focused
    # ------------------------------------------------------------------
    total_donation = active["DonationToStabilize"].sum()
    total_impact = active["AnnualProgramImpact"].sum()
    median_roi = active["ProgramImpactPerDollar"].median()
    portfolio_roi = total_impact / total_donation if total_donation > 0 else np.nan

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Organizations in Tier", f"{len(active):,}")
    k2.metric(
        "Total Funding to Stabilize",
        _fmt_dollars(total_donation),
        help="Sum of DonationToStabilize across every org in this tier — the check a funder would write to bring all of them to 6-month reserves.",
    )
    k3.metric(
        "Annual Mission Impact Protected",
        _fmt_dollars(total_impact),
        help="Combined yearly program spending of every org in the tier — the mission activity that would be preserved if all were stabilized.",
    )
    if pd.notna(portfolio_roi):
        k4.metric(
            "Portfolio ROI",
            f"${portfolio_roi:,.1f} / $1",
            help="For every $1 a funder donates across this tier, $X of annual mission work is protected. Portfolio-level cost efficiency.",
        )
    else:
        k4.metric("Portfolio ROI", "N/A")

    roi_text = f"${median_roi:,.1f}" if pd.notna(median_roi) else "N/A"
    st.markdown(
        f'<div class="insight-box-good">'
        f"<strong>How this shortlist is built:</strong> every candidate is ranked on "
        f"<em>Cost-Efficiency Score</em> (0–100) — a weighted blend of <strong>mission ROI (40%)</strong>, "
        f"overall impact quality (30%), revenue growth (15%), and funding urgency (15%). "
        f"Median mission ROI in this tier: <strong>{roi_text} of annual program activity protected per $1 donated</strong>."
        f"</div>",
        unsafe_allow_html=True,
    )

    # ------------------------------------------------------------------
    # FILTERS
    # ------------------------------------------------------------------
    st.markdown('<div class="section-header">Refine Your Shortlist</div>', unsafe_allow_html=True)
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        state_options = ["All States"] + sorted(active["State"].dropna().unique().tolist())
        sel_state = st.selectbox("State", state_options, key="gems_state")
    with col_f2:
        sector_options = ["All Sectors"] + sorted(active["Sector"].dropna().unique().tolist())
        sel_sector = st.selectbox("Sector", sector_options, key="gems_sector")
    with col_f3:
        # Donation-to-stabilize budget filter — funders often want a per-org ceiling.
        # IMPORTANT: default to the TRUE max so no orgs are filtered out by default.
        # Using a percentile here silently drops the most expensive orgs — which are
        # often the highest-ranked on mission impact.
        if len(active) > 0 and active["DonationToStabilize"].max() > 0:
            true_max = float(active["DonationToStabilize"].max())
            # Round ceiling up to a clean step for UI tidiness
            step = 5_000 if true_max < 1_000_000 else 25_000
            donation_ceiling = int(np.ceil(true_max / step) * step)
            donation_ceiling = max(donation_ceiling, 10_000)
            max_budget = st.slider(
                "Max donation per org",
                min_value=0,
                max_value=donation_ceiling,
                value=donation_ceiling,
                step=step,
                format="$%d",
                help="Skip orgs whose stabilization cost exceeds this ceiling. Defaults to no cap.",
                key=f"gems_budget_cap_{active_tier_key}",
            )
        else:
            max_budget = None

    filtered = active.copy()
    if sel_state != "All States":
        filtered = filtered[filtered["State"] == sel_state]
    if sel_sector != "All Sectors":
        filtered = filtered[filtered["Sector"] == sel_sector]
    if max_budget is not None:
        filtered = filtered[filtered["DonationToStabilize"] <= max_budget]

    st.markdown(f"**Showing {len(filtered):,} organizations** matching your filters")

    if "gems_selected_org" not in st.session_state:
        st.session_state.gems_selected_org = None
    selected_name = st.session_state.gems_selected_org

    # ------------------------------------------------------------------
    # TOP 6 CARDS — ranked by CostEfficiencyScore
    # ------------------------------------------------------------------
    if len(filtered) > 0:
        top_gems = filtered.head(6)
        cols = st.columns(3)
        for i, (_, gem) in enumerate(top_gems.iterrows()):
            with cols[i % 3]:
                rl, rc = _resilience_label(gem["ResilienceScore"])
                roi_val = gem.get("ProgramImpactPerDollar", np.nan)
                roi_display = f"${roi_val:,.1f}" if pd.notna(roi_val) else "—"
                donation_text = (
                    f'{_fmt_dollars(gem["DonationToStabilize"])} to reach 6-month reserves'
                )
                rank_val = gem.get("PriorityRank", None)
                rank_text = f"#{int(rank_val)}" if pd.notna(rank_val) else "—"
                ce_val = gem.get("CostEfficiencyScore", np.nan)
                ce_display = f"{ce_val:.0f}/100" if pd.notna(ce_val) else "—"

                is_card_selected = selected_name == gem["OrgName"]
                card_border = "2px solid #3b82f6" if is_card_selected else "1px solid #e5e7eb"
                card_bg = "#f0f7ff" if is_card_selected else "#fafbfc"
                st.markdown(
                    f"""<div style="background:{card_bg}; border:{card_border}; border-radius:12px; padding:16px; margin-bottom:4px">
                    <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:4px">
                        <div style="font-weight:700; font-size:1rem; color:#1a2332; flex:1">{gem['OrgName'][:50]}</div>
                        <div style="font-size:0.7rem; color:#ffffff; background:#1a2332; padding:3px 8px; border-radius:10px; margin-left:8px">{rank_text}</div>
                    </div>
                    <div style="font-size:0.8rem; color:#6b7280; margin-bottom:10px">{gem.get('City', '')} {gem['State']} · {gem['Sector']}</div>
                    <div style="background:#ecfdf5; border:1px solid #a7f3d0; border-radius:8px; padding:8px 10px; margin-bottom:10px">
                        <div style="font-size:0.72rem; color:#047857; text-transform:uppercase; letter-spacing:0.04em; font-weight:600">Mission ROI</div>
                        <div style="font-size:1.15rem; font-weight:700; color:#065f46">{roi_display} <span style="font-size:0.75rem; font-weight:500; color:#047857">of programs / $1 donated</span></div>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-bottom:8px">
                        <div><span style="font-size:0.72rem; color:#9ca3af">Cost-Eff. Score</span><br/><strong>{ce_display}</strong></div>
                        <div><span style="font-size:0.72rem; color:#9ca3af">Resilience</span><br/><span class="health-badge {rc}">{rl}</span></div>
                    </div>
                    <div style="font-size:0.8rem; color:#374151; margin-top:6px">💡 {donation_text}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                btn_label = "✕ Close Breakdown" if is_card_selected else "📊 Score Breakdown"
                if st.button(btn_label, key=f"gem_btn_{i}", use_container_width=True):
                    st.session_state.gems_selected_org = None if is_card_selected else gem["OrgName"]
                    st.rerun()

    # ------------------------------------------------------------------
    # SCORE BREAKDOWN PANEL — Cost-Efficiency Score components
    # ------------------------------------------------------------------
    selected_name = st.session_state.get("gems_selected_org")
    if selected_name:
        sel_rows = filtered[filtered["OrgName"] == selected_name]
        if len(sel_rows) == 0:
            sel_rows = gems[gems["OrgName"] == selected_name]
        if len(sel_rows) > 0:
            sel = sel_rows.iloc[0]
            prog_impact = sel.get("AnnualProgramImpact", np.nan)
            donation = sel.get("DonationToStabilize", np.nan)
            roi_val = sel.get("ProgramImpactPerDollar", np.nan)
            growth = sel.get("RevenueGrowthPct", np.nan)
            resilience = sel.get("ResilienceScore", np.nan)
            reserves = sel.get("OperatingReserveMonths", np.nan)
            impact_score = sel.get("ImpactEfficiencyScore", np.nan)
            ce_score = sel.get("CostEfficiencyScore", np.nan)
            roi_pctile = sel.get("ROI_Percentile", np.nan)
            rank_val = sel.get("PriorityRank", np.nan)

            def _sc(val, good_thresh, warn_thresh):
                if val is None or (isinstance(val, float) and np.isnan(val)):
                    return "#9ca3af"
                return "#22c55e" if val >= good_thresh else "#f59e0b" if val >= warn_thresh else "#ef4444"

            roi_color = _sc(roi_pctile, 0.75, 0.50)
            impact_color = _sc(impact_score, 80, 60)
            growth_color = _sc(growth, 0.05, 0.0)
            urgency_color = _sc(12 - (reserves or 0), 9, 6)  # low reserves ⇒ urgent ⇒ warmer

            reserve_txt = f"{reserves:.1f} mo" if pd.notna(reserves) else "N/A"
            roi_detail = (
                f"${prog_impact:,.0f} of annual programs / ${donation:,.0f} stabilization → ${roi_val:,.2f} per $1"
                if pd.notna(roi_val) else "Org is already stable — no stabilization donation required."
            )
            roi_pctile_txt = f"top {(1 - roi_pctile):.0%} among all candidates" if pd.notna(roi_pctile) else "—"

            components_html = "".join([
                f"""<div style="display:flex; align-items:flex-start; gap:14px; padding:10px 0; border-bottom:1px solid #f3f4f6">
                  <div style="min-width:52px; text-align:center; padding-top:2px">
                    <div style="font-size:1.05rem; font-weight:700; color:{color}">{weight}%</div>
                    <div style="font-size:0.7rem; color:#9ca3af">weight</div>
                  </div>
                  <div style="flex:1">
                    <div style="font-weight:600; color:#1a2332; font-size:0.9rem">{label}
                      <span style="font-weight:400; color:#6b7280; font-size:0.82rem">&nbsp;→&nbsp;{value}</span>
                    </div>
                    <div style="font-size:0.8rem; color:#6b7280; margin-top:2px">{detail}</div>
                    <div style="font-size:0.75rem; color:{color}; margin-top:2px">📌 {benchmark}</div>
                  </div>
                </div>"""
                for label, weight, value, detail, benchmark, color in [
                    (
                        "Mission ROI", 40,
                        f"${roi_val:,.2f} / $1" if pd.notna(roi_val) else "N/A",
                        roi_detail,
                        roi_pctile_txt,
                        roi_color,
                    ),
                    (
                        "Impact Efficiency Score", 30,
                        f"{impact_score:.0f}/100" if pd.notna(impact_score) else "N/A",
                        "The original Impact Efficiency composite (program spending, growth, leverage, reach, sustainability).",
                        "80+ is exceptional; already filtered to top 20% of all nonprofits",
                        impact_color,
                    ),
                    (
                        "Revenue Growth Momentum", 15,
                        f"{growth:+.1%}" if pd.notna(growth) else "N/A",
                        "Year-over-year revenue change — indicates whether donor dollars amplify expansion or merely sustain.",
                        "Positive growth confirms trajectory; >5% is strong momentum",
                        growth_color,
                    ),
                    (
                        "Funding Urgency", 15,
                        reserve_txt,
                        "Inverse of operating reserve months. Orgs with shorter runway score higher — a donation matters more to them.",
                        "<3 months reserves = high urgency; 3–6 = moderate; 6+ = low urgency",
                        urgency_color,
                    ),
                ]
            ])

            ce_txt = f"{ce_score:.0f}/100" if pd.notna(ce_score) else "N/A"
            rank_txt = f"#{int(rank_val)}" if pd.notna(rank_val) else "N/A"
            st.markdown(
                f"""<div style="background:#f8f9fc; border:1px solid #dde2ec; border-radius:12px; padding:20px; margin:8px 0 20px 0">
                  <div style="display:flex; justify-content:space-between; align-items:baseline; margin-bottom:2px">
                    <div style="font-size:1.05rem; font-weight:700; color:#1a2332">Cost-Efficiency Breakdown — {sel['OrgName']}</div>
                    <div style="font-size:0.85rem; color:#1a2332">Rank {rank_txt} · Score {ce_txt}</div>
                  </div>
                  <div style="font-size:0.82rem; color:#6b7280; margin-bottom:14px">
                    Each factor is percentile-ranked across all candidates, then combined using the weights below to produce the 0–100 Cost-Efficiency Score used for prioritization.
                  </div>
                  {components_html}
                </div>""",
                unsafe_allow_html=True,
            )
            if st.button("✕ Clear selection", key="gems_clear_sel"):
                st.session_state.gems_selected_org = None
                st.rerun()

    # ------------------------------------------------------------------
    # ROI SCATTER — Donation cost vs. program impact protected
    # ------------------------------------------------------------------
    st.markdown('<div class="section-header">Cost vs. Mission Impact Protected</div>', unsafe_allow_html=True)

    if len(filtered) > 0:
        plot_df = filtered[filtered["DonationToStabilize"] > 0].head(3000).copy()
        plot_df["DonationFmt"] = plot_df["DonationToStabilize"].apply(_fmt_dollars)
        plot_df["ImpactFmt"] = plot_df["AnnualProgramImpact"].apply(_fmt_dollars)
        plot_df["ROIFmt"] = plot_df["ProgramImpactPerDollar"].apply(lambda v: f"${v:,.2f} / $1" if pd.notna(v) else "N/A")

        if len(plot_df) > 0:
            fig = px.scatter(
                plot_df,
                x="DonationToStabilize",
                y="AnnualProgramImpact",
                color="PriorityTier",
                size="CostEfficiencyScore",
                size_max=22,
                category_orders={"PriorityTier": TIER_ORDER},
                color_discrete_map=TIER_COLORS,
                hover_data={
                    "OrgName": True,
                    "Sector": True,
                    "State": True,
                    "DonationFmt": True,
                    "ImpactFmt": True,
                    "ROIFmt": True,
                    "DonationToStabilize": False,
                    "AnnualProgramImpact": False,
                    "CostEfficiencyScore": ":.0f",
                    "PriorityTier": False,
                },
                labels={
                    "DonationToStabilize": "Donation to Stabilize (cost)",
                    "AnnualProgramImpact": "Annual Program Activity Protected",
                    "PriorityTier": "Priority Tier",
                },
                log_x=True,
                log_y=True,
                opacity=0.72,
            )

            # Reference lines: $1 → $1 of programs, and $1 → $10 of programs
            if len(plot_df) > 0:
                x_min = plot_df["DonationToStabilize"].min()
                x_max = plot_df["DonationToStabilize"].max()
                x_ref = np.array([max(x_min, 1), x_max])
                for mult, label in [(1, "1× (break-even)"), (10, "10× leverage"), (100, "100× leverage")]:
                    fig.add_trace(go.Scatter(
                        x=x_ref,
                        y=x_ref * mult,
                        mode="lines",
                        name=label,
                        line=dict(color="#9ca3af", width=1, dash="dot"),
                        showlegend=True,
                        hoverinfo="skip",
                    ))

            fig.update_layout(
                legend_title_text="",
                legend=dict(orientation="h", yanchor="top", y=-0.22, xanchor="center", x=0.5),
                margin=dict(t=10, b=80),
                height=520,
            )
            st.caption(
                "Each dot is one organization. X-axis = cost to stabilize; Y-axis = annual program activity protected. "
                "Points far above the 1× line deliver the highest mission ROI per dollar. Click any dot to pin its score breakdown."
            )
            chart_event = st.plotly_chart(fig, use_container_width=True, on_select="rerun", selection_mode="points")
            if chart_event and chart_event.selection and chart_event.selection.points:
                pt = chart_event.selection.points[0]
                sel_x = pt.get("x")
                sel_y = pt.get("y")
                if sel_x is not None and sel_y is not None:
                    match = plot_df[
                        (plot_df["DonationToStabilize"] == sel_x)
                        & (abs(plot_df["AnnualProgramImpact"] - sel_y) < 0.01)
                    ]
                    if len(match) > 0:
                        new_org = match.iloc[0]["OrgName"]
                        if st.session_state.get("gems_selected_org") != new_org:
                            st.session_state.gems_selected_org = new_org
                            st.rerun()

    # ------------------------------------------------------------------
    # RANKED TABLE — sorted by PriorityRank
    # ------------------------------------------------------------------
    st.markdown('<div class="section-header">Ranked List</div>', unsafe_allow_html=True)
    table_cols = [
        "PriorityRank", "OrgName", "State", "Sector",
        "CostEfficiencyScore", "ProgramImpactPerDollar",
        "DonationToStabilize", "AnnualProgramImpact",
        "ImpactEfficiencyScore", "ResilienceScore",
        "OperatingReserveMonths", "RevenueGrowthPct",
    ]
    available_cols = [c for c in table_cols if c in filtered.columns]
    rename_map = {
        "PriorityRank": "Rank",
        "OrgName": "Organization",
        "CostEfficiencyScore": "Cost-Eff. Score",
        "ProgramImpactPerDollar": "ROI ($ programs / $1)",
        "DonationToStabilize": "Donation to Stabilize",
        "AnnualProgramImpact": "Annual Program Impact",
        "ImpactEfficiencyScore": "Impact Score",
        "ResilienceScore": "Resilience",
        "OperatingReserveMonths": "Reserve Months",
        "RevenueGrowthPct": "Revenue Growth",
    }
    display = (
        filtered[available_cols]
        .rename(columns=rename_map)
        .sort_values("Rank")
        .head(500)
    )

    selected_name = st.session_state.get("gems_selected_org")
    if selected_name and "Organization" in display.columns:
        is_sel = display["Organization"] == selected_name
        display = pd.concat([display[is_sel], display[~is_sel]], ignore_index=True)

    def _highlight_selected_row(row: pd.Series) -> list[str]:
        if selected_name and row.get("Organization") == selected_name:
            return ["background-color: #fef3c7; font-weight: bold"] * len(row)
        return [""] * len(row)

    st.dataframe(
        display.style
        .apply(_highlight_selected_row, axis=1)
        .format(
            {
                "Cost-Eff. Score": "{:.0f}",
                "ROI ($ programs / $1)": "${:,.2f}",
                "Donation to Stabilize": "${:,.0f}",
                "Annual Program Impact": "${:,.0f}",
                "Impact Score": "{:.0f}",
                "Resilience": "{:.0f}",
                "Reserve Months": "{:.1f}",
                "Revenue Growth": "{:+.1%}",
            }
        ),
        use_container_width=True,
        height=420,
    )

    # ------------------------------------------------------------------
    # EXPORT — let funders take the shortlist with them
    # ------------------------------------------------------------------
    if len(display) > 0:
        csv_bytes = display.to_csv(index=False).encode("utf-8")
        st.download_button(
            "📥 Download this shortlist (CSV)",
            data=csv_bytes,
            file_name=f"priority_shortlist_{active_tier_key.lower().replace(' ', '_')}.csv",
            mime="text/csv",
            help="Download the current filtered, ranked list for offline review.",
        )


# ---------------------------------------------------------------------------
# PAGE 6 — Brand Map
# ---------------------------------------------------------------------------
_TIER_COLORS = {
    "Stable": "#2ecc71",
    "Watch": "#f39c12",
    "At Risk": "#e74c3c",
}
_TIER_ORDER = ["Stable", "Watch", "At Risk"]


@st.cache_data
def _prepare_brand_map_df(df: pd.DataFrame) -> pd.DataFrame:
    """Pre-compute all expensive columns once at load time."""
    out = df[df["ProgramSvcExpenses"].notna() & (df["ProgramSvcExpenses"] > 0)].copy()

    # ResilienceTier
    if "ResilienceScore" in out.columns:
        out["ResilienceTier"] = pd.cut(
            out["ResilienceScore"],
            bins=[-np.inf, 40, 70, np.inf],
            labels=["At Risk", "Watch", "Stable"],
        ).astype(str)
    else:
        conditions = [
            (out["OperatingReserveMonths"] >= 6) & (out["SurplusMargin"] >= 0),
            (out["OperatingReserveMonths"] >= 3) | (out["SurplusMargin"] >= -0.05),
        ]
        out["ResilienceTier"] = np.select(conditions, ["Stable", "Watch"], default="At Risk")

    # Dot size: log-scaled from revenue (5–25 range)
    log_rev = np.log1p(out["TotalRevenueCY"].clip(lower=0))
    log_max = log_rev.max() if log_rev.max() > 0 else 1
    out["DotSize"] = (log_rev / log_max * 20 + 5).fillna(5)

    # Vectorised hover formatting (no .apply loops)
    rev = out["TotalRevenueCY"]
    out["_RevFmt"] = np.where(rev.notna(), "$" + rev.map("{:,.0f}".format), "N/A")

    sur = out["SurplusMargin"] * 100
    out["_SurplusFmt"] = np.where(sur.notna(), sur.map("{:.1f}%".format), "N/A")

    gd = out["GrantDependencyPct"] * 100
    out["_GrantDepFmt"] = np.where(gd.notna(), gd.map("{:.1f}%".format), "N/A")

    out["_ReservesCapped"] = out["OperatingReserveMonths"].clip(upper=36)

    return out


def brand_map_page(df: pd.DataFrame) -> None:
    st.title("Brand Map: Mission Efficiency vs. Financial Runway")
    st.markdown("Mapping nonprofit financial health across two dimensions: **mission spending efficiency** and **operational runway**.")
    st.caption("Each circle is one nonprofit. Bigger circles are larger organizations by annual revenue. Color shows financial resilience tier.")

    with st.expander("What do the hover fields mean?"):
        st.markdown(
            "**Surplus Margin** — the percentage of revenue left over after expenses. "
            "A positive number means the organization is bringing in more than it spends (a surplus). "
            "A negative number means it is spending more than it earns (a deficit).\n\n"
            "**Resilience Tier** — a summary rating based on reserves, revenue mix, program spending, surplus, and debt:\n"
            "- 🟢 **Stable** — financially healthy, likely to weather a funding disruption\n"
            "- 🟡 **Watch** — showing early warning signs; not in crisis but worth monitoring\n"
            "- 🔴 **At Risk** — low reserves, deficits, or heavy dependency on a single funding source\n\n"
            "**Grant Dependency** — the share of revenue coming from grants and donations. "
            "Organizations above 80% are heavily reliant on donor goodwill and vulnerable if a major grant is lost."
        )

    # Pre-processed base (cached — runs once per session)
    base_df = _prepare_brand_map_df(df)

    # ---------- Filters ----------
    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
    with col_f1:
        sectors = ["All Sectors"] + sorted(base_df["Sector"].dropna().unique().tolist())
        sel_sector = st.selectbox("Sector", sectors, key="bm_sector")
    with col_f2:
        states_list = ["All States"] + sorted(base_df["State"].dropna().unique().tolist())
        sel_state = st.selectbox("State", states_list, key="bm_state")
    with col_f3:
        _size_order = ["500K-1M", "1M-5M", "5M-10M", "10M-50M", "50M+"]
        sizes = ["All Sizes"] + [s for s in _size_order if s in base_df["SizeCategory"].values]
        sel_size = st.selectbox("Size", sizes, key="bm_size")
    with col_f4:
        years = sorted(base_df["TaxYear"].dropna().unique().astype(int).tolist(), reverse=True)
        sel_year = st.selectbox("Tax Year", years, key="bm_year")
    with col_f5:
        _tier_labels = {
            "All Tiers":  "All Tiers",
            "🟢  Stable":  "Stable",
            "🟡  Watch":   "Watch",
            "🔴  At Risk": "At Risk",
        }
        sel_tier_label = st.selectbox("Resilience Tier", list(_tier_labels.keys()), key="bm_tier")
        sel_tier = _tier_labels[sel_tier_label]

    # ---------- Cheap boolean filter on pre-processed df ----------
    mask = pd.Series(True, index=base_df.index)
    if sel_sector != "All Sectors":
        mask &= base_df["Sector"] == sel_sector
    if sel_state != "All States":
        mask &= base_df["State"] == sel_state
    if sel_size != "All Sizes":
        mask &= base_df["SizeCategory"] == sel_size
    mask &= base_df["TaxYear"] == int(sel_year)
    if sel_tier != "All Tiers":
        mask &= base_df["ResilienceTier"] == sel_tier
    plot_df = base_df[mask]

    if plot_df.empty:
        st.warning("No organizations match the current filters.")
        return

    # Sample for performance
    sample = plot_df.sample(min(len(plot_df), 8000), random_state=42)

    # Sector average reference point (computed on full filtered set for accuracy)
    avg_x = plot_df["ProgramExpenseRatio"].median()
    avg_y = plot_df["_ReservesCapped"].median()

    # Dot size: wider range so small vs large orgs are visually distinct
    log_rev = np.log1p(sample["TotalRevenueCY"].clip(lower=0))
    log_min, log_max = log_rev.min(), log_rev.max()
    span = log_max - log_min if log_max > log_min else 1
    dot_sizes = ((log_rev - log_min) / span * 28 + 4)  # range 4–32

    # ---------- Build figure ----------
    fig = go.Figure()

    for tier in _TIER_ORDER:
        mask_t = sample["ResilienceTier"] == tier
        subset = sample[mask_t]
        if subset.empty:
            continue
        customdata = np.stack([
            subset["OrgName"].fillna("Unknown"),
            subset["State"].fillna(""),
            subset["_RevFmt"],
            subset["Sector"].fillna(""),
            subset["_SurplusFmt"],
            subset["_GrantDepFmt"],
            subset["ResilienceTier"],
        ], axis=-1)
        fig.add_trace(go.Scatter(
            x=subset["ProgramExpenseRatio"],
            y=subset["_ReservesCapped"],
            mode="markers",
            name=tier,
            marker=dict(
                color=_TIER_COLORS[tier],
                size=dot_sizes[mask_t],
                opacity=0.7,
                line=dict(width=1.5, color="#333333"),
            ),
            customdata=customdata,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "State: %{customdata[1]}<br>"
                "Total Revenue: %{customdata[2]}<br>"
                "NTEE Sector: %{customdata[3]}<br>"
                "Surplus Margin: %{customdata[4]}<br>"
                "Grant Dependency: %{customdata[5]}<br>"
                "Resilience Tier: %{customdata[6]}"
                "<extra></extra>"
            ),
        ))

    # --- Sector average crosshairs (no diamond marker) ---
    fig.add_shape(type="line", xref="x", yref="paper", x0=avg_x, x1=avg_x, y0=0, y1=1,
                  line=dict(color="#6366f1", width=2.5, dash="dash"))
    fig.add_shape(type="line", xref="paper", yref="y", x0=0, x1=1, y0=avg_y, y1=avg_y,
                  line=dict(color="#6366f1", width=2.5, dash="dash"))
    # --- Quadrant labels ---
    _dark_mode = st.get_option("theme.base") == "dark"
    _ql_text_color = "#f0f0f0" if _dark_mode else "#111111"
    _ql_bg_color   = "rgba(30,30,40,0.90)" if _dark_mode else "rgba(255,255,255,0.92)"
    _ql_style = dict(showarrow=False, font=dict(size=11, color=_ql_text_color, weight="bold"),
                     bgcolor=_ql_bg_color, borderpad=5, xref="paper", yref="paper")
    fig.add_annotation(x=0.02, y=0.98, xanchor="left",  yanchor="top",
                       text="<b>Low efficiency</b><br>Well-resourced", **_ql_style)
    fig.add_annotation(x=0.98, y=0.98, xanchor="right", yanchor="top",
                       text="<b>High efficiency</b><br>Well-resourced", **_ql_style)
    fig.add_annotation(x=0.02, y=0.02, xanchor="left",  yanchor="bottom",
                       text="<b>Low efficiency</b><br>Fragile", **_ql_style)
    fig.add_annotation(x=0.98, y=0.02, xanchor="right", yanchor="bottom",
                       text="<b>High efficiency</b><br>Fragile", **_ql_style)

    fig.update_layout(
        xaxis_title=dict(text="Program Expense Ratio  (how much of every dollar goes to mission)", font=dict(color="#111111", size=13)),
        yaxis_title=dict(text="Operating Reserve Months  (months of runway without new funding)", font=dict(color="#111111", size=13)),
        legend_title_text="Resilience Tier",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            font=dict(color="#111111", size=13),
            title=dict(text="Resilience Tier", font=dict(color="#111111", size=13)),
            bgcolor="#ffffff",
            bordercolor="#333333",
            borderwidth=1,
        ),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(color="#111111"),
        xaxis=dict(
            gridcolor="#cccccc",
            gridwidth=1,
            zerolinecolor="#555555",
            zerolinewidth=2,
            linecolor="#333333",
            linewidth=2,
            tickformat=".0%",
            tickfont=dict(color="#333333"),
        ),
        yaxis=dict(
            gridcolor="#cccccc",
            gridwidth=1,
            zerolinecolor="#555555",
            zerolinewidth=2,
            linecolor="#333333",
            linewidth=2,
            tickfont=dict(color="#333333"),
        ),
        hoverlabel=dict(bgcolor="#f9f9f9", font_color="#222222", bordercolor="#444444"),
        hovermode="closest",
        margin=dict(t=60, b=60),
        height=580,
    )

    st.plotly_chart(fig, use_container_width=True)
    st.markdown(f'<p style="color:#6366f1; font-size:0.85rem;">Median: {avg_x:.0%} program efficiency · {avg_y:.1f} months of reserves</p>', unsafe_allow_html=True)

    # ---------- Quadrant insights ----------
    if len(plot_df) > 50:
        med_x = plot_df["ProgramExpenseRatio"].median()

        # Bottom-right: high efficiency, low reserves (Danger Zone — efficient but fragile)
        danger_zone = plot_df[
            (plot_df["ProgramExpenseRatio"] >= med_x)
            & (plot_df["_ReservesCapped"] < 3)
        ]
        if len(danger_zone) > 0:
            st.markdown(
                f'<div class="insight-box-warn">'
                f"<strong>Danger Zone (bottom-right):</strong> <strong>{len(danger_zone):,}</strong> orgs "
                f"are highly mission-focused but have <strong>under 3 months of reserves</strong> "
                f"— efficient but one funding cut away from crisis."
                f"</div>",
                unsafe_allow_html=True,
            )

        # Top-left: low efficiency, well-resourced — underperforming despite resources
        low_eff_resourced = plot_df[
            (plot_df["ProgramExpenseRatio"] < med_x)
            & (plot_df["_ReservesCapped"] >= avg_y)
        ]
        if len(low_eff_resourced) > 0:
            st.markdown(
                f'<div class="insight-box">'
                f"<strong>Underutilized Resources (top-left):</strong> <strong>{len(low_eff_resourced):,}</strong> orgs "
                f"have strong reserves but spend <strong>below the median</strong> on programs — well-funded but not fully directing dollars to mission."
                f"</div>",
                unsafe_allow_html=True,
            )

        # Bottom cluster: negative or near-zero reserves — most distressed
        critical = plot_df[plot_df["OperatingReserveMonths"] < 0]
        if len(critical) > 0:
            st.markdown(
                f'<div class="insight-box-warn">'
                f"<strong>Critical (below Y=0):</strong> <strong>{len(critical):,}</strong> orgs show "
                f"<strong>negative reserve months</strong> — they are already spending down net assets and face imminent insolvency without intervention."
                f"</div>",
                unsafe_allow_html=True,
            )

    # ---------- Tier summary ----------
    st.markdown('<div class="section-header">Tier Breakdown (Filtered View)</div>', unsafe_allow_html=True)

    tier_counts = plot_df["ResilienceTier"].value_counts()
    tc1, tc2, tc3 = st.columns(3)
    for col, tier in zip([tc1, tc2, tc3], _TIER_ORDER):
        count = tier_counts.get(tier, 0)
        pct = count / len(plot_df) if len(plot_df) > 0 else 0
        color = _TIER_COLORS[tier]
        col.markdown(
            f"""<div style="background:{color}22; border:2px solid {color}; border-radius:12px; padding:18px 20px;">
                <div style="color:#000000; font-size:0.85rem; font-weight:500; margin-bottom:4px;">{tier}</div>
                <div style="color:#000000; font-size:1.9rem; font-weight:700; line-height:1.1;">{count:,}</div>
                <div style="color:#000000; font-size:0.82rem; margin-top:4px;">{pct:.1%} of filtered orgs</div>
            </div>""",
            unsafe_allow_html=True,
        )

    # ---------- Data table ----------
    with st.expander("Browse organizations in this view"):
        table_cols = ["OrgName", "State", "Sector", "SizeCategory", "TotalRevenueCY",
                      "ProgramExpenseRatio", "OperatingReserveMonths", "SurplusMargin",
                      "GrantDependencyPct", "ResilienceTier"]
        rename_map = {
            "OrgName": "Organization", "SizeCategory": "Size",
            "TotalRevenueCY": "Annual Revenue",
            "ProgramExpenseRatio": "Program Spending %",
            "OperatingReserveMonths": "Reserve Months",
            "SurplusMargin": "Surplus Margin",
            "GrantDependencyPct": "Grant Dependency %",
            "ResilienceTier": "Tier",
        }
        display = (
            plot_df[[c for c in table_cols if c in plot_df.columns]]
            .rename(columns=rename_map)
            .sort_values("Reserve Months")
            .head(400)
        )
        st.dataframe(
            display.style.format({
                "Annual Revenue": "${:,.0f}",
                "Program Spending %": "{:.1%}",
                "Reserve Months": "{:.1f}",
                "Surplus Margin": "{:.1%}",
                "Grant Dependency %": "{:.1%}",
            }),
            use_container_width=True,
            height=380,
        )


# ---------------------------------------------------------------------------
# Main navigation
# ---------------------------------------------------------------------------
def main() -> None:
    df, _peers, sims, metrics = load_data()

    st.sidebar.markdown("## Navigation")
    page = st.sidebar.radio(
        "Go to",
        [
            "Executive Overview",
            "Peer Benchmarking",
            "Resilience Explorer",
            "Stress Test Simulator",
            "Hidden Gems Finder",
            "Brand Map",
        ],
        label_visibility="collapsed",
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        "**About this tool**\n\n"
        "Built for Aggie Hacks 2026. Analyzes IRS Form 990 data "
        "for each tax year (2018–2024) to help funders and nonprofit leaders make "
        "data-driven decisions."
    )
    st.sidebar.markdown(
        f"*{len(df):,} records · {int(df['State'].nunique())} states & territories*"
    )

    if page == "Executive Overview":
        executive_page(df)
    elif page == "Peer Benchmarking":
        peer_page(df)
    elif page == "Resilience Explorer":
        resilience_page(df, metrics)
    elif page == "Stress Test Simulator":
        simulation_page(df)
    elif page == "Hidden Gems Finder":
        gems_page()
    else:
        brand_map_page(df)


if __name__ == "__main__":
    main()
