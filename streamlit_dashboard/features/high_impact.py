"""Tab 4: High-Impact Discovery — surface 'hidden gem' nonprofits for funders."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Impact Efficiency score weights
_WEIGHTS = {
    "ProgramExpenseRatio": 0.35,    # Most important: mission focus
    "FundraisingRatio": -0.20,      # Lower fundraising overhead = more efficient (inverted)
    "ContributionGrowthPct": 0.20,  # Positive momentum
    "SurplusMargin": 0.15,          # Financially healthy
    "RevenueGrowthPct": 0.10,       # Growing impact
}


def compute_impact_efficiency(df: pd.DataFrame) -> pd.Series:
    """
    Composite Impact Efficiency score (0–100) for identifying hidden gems.
    Only organizations not predicted At Risk are eligible.
    """
    score = pd.Series(0.0, index=df.index)
    for col, weight in _WEIGHTS.items():
        if col not in df.columns:
            continue
        val = pd.to_numeric(df[col], errors="coerce")
        # Normalize each column to 0–1 using quantile-based clipping
        p5, p95 = val.quantile(0.05), val.quantile(0.95)
        if p95 > p5:
            norm = (val.clip(p5, p95) - p5) / (p95 - p5)
        else:
            norm = pd.Series(0.5, index=df.index)
        score += weight * norm

    # Rescale to 0–100
    s_min, s_max = score.min(), score.max()
    if s_max > s_min:
        score = (score - s_min) / (s_max - s_min) * 100
    return score.round(1)


def render(df: pd.DataFrame) -> None:
    st.header("High-Impact Discovery — Hidden Gems")
    st.caption(
        "Identifies nonprofits that deliver disproportionate community value relative "
        "to their budget. Hidden gems are mission-efficient, financially stable, "
        "showing momentum, and often overlooked by funders due to their small size."
    )

    if df.empty:
        st.warning("No organizations match the current filters.")
        return

    # Compute impact efficiency
    df = df.copy()
    df["ImpactEfficiency"] = compute_impact_efficiency(df)

    # Hidden gems = financially stable (model) + small/mid + high efficiency
    at_risk_pred = pd.to_numeric(df["AtRiskPredicted"], errors="coerce").fillna(1)
    rev = pd.to_numeric(df["TotalRevenueCY"], errors="coerce")
    df["_IsHiddenGem"] = (at_risk_pred == 0) & (rev < 5_000_000)

    # ── Definition callout ────────────────────────────────────────────────────
    n_gems = int(df["_IsHiddenGem"].sum())
    n_stable = int((at_risk_pred == 0).sum())
    total = len(df)
    st.info(
        f"**{n_gems:,}** hidden gem candidates identified out of **{total:,}** organizations "
        f"({n_stable:,} financially stable). Criteria: model-predicted **Not At Risk** + "
        f"revenue **< $5M** + ranked by Impact Efficiency score."
    )

    # ── Scoring methodology expander ─────────────────────────────────────────
    with st.expander("How is Impact Efficiency scored?"):
        st.markdown("""
        | Component | Weight | Direction |
        |-----------|--------|-----------|
        | Program Expense Ratio | 35% | Higher = better (mission focus) |
        | Fundraising Ratio | 20% | **Lower = better** (efficient fundraising) |
        | Contribution Growth % | 20% | Higher = better (donor momentum) |
        | Surplus Margin | 15% | Higher = better (financial health) |
        | Revenue Growth % | 10% | Higher = better (expanding impact) |

        Scores are normalized to 0–100 within the filtered dataset. Only organizations
        **not flagged at risk by the model** are eligible for the Hidden Gems table.
        """)

    st.divider()

    # ── Row 1: Scatter + Sector spotlight ────────────────────────────────────
    col_scatter, col_sector = st.columns([2, 1])

    with col_scatter:
        st.subheader("Efficiency vs. Contribution Growth")
        _impact_scatter(df)

    with col_sector:
        st.subheader("Hidden Gems by Sector")
        _sector_spotlight(df)

    st.divider()

    # ── Top gems table ────────────────────────────────────────────────────────
    st.subheader("Top Hidden Gem Organizations")
    _top_gems_table(df)

    st.divider()

    # ── Revenue efficiency distribution ───────────────────────────────────────
    st.subheader("Program Impact per Dollar by Sector")
    _program_efficiency_bars(df)


# ─────────────────────────── helpers ─────────────────────────────────────────

def _impact_scatter(df: pd.DataFrame) -> None:
    per = pd.to_numeric(df["ProgramExpenseRatio"], errors="coerce")
    cg = pd.to_numeric(df["ContributionGrowthPct"], errors="coerce")
    rev = pd.to_numeric(df["TotalRevenueCY"], errors="coerce")
    at_risk_pred = pd.to_numeric(df["AtRiskPredicted"], errors="coerce")

    mask = per.notna() & cg.notna() & rev.notna()
    plot_df = pd.DataFrame({
        "ProgramExpenseRatio": per[mask].values,
        "ContributionGrowthPct": cg[mask].clip(-1, 2).values,
        "TotalRevenueCY": rev[mask].values,
        "AtRiskPredicted": at_risk_pred[mask].values,
        "ImpactEfficiency": df["ImpactEfficiency"][mask].values,
        "OrgName": df["OrgName"][mask].values,
        "Sector": df["Sector"][mask].values,
        "State": df["State"][mask].values,
    })

    # Downsample if needed
    if len(plot_df) > 6000:
        plot_df = plot_df.sample(6000, random_state=42)

    plot_df["_StatusLabel"] = plot_df["AtRiskPredicted"].map({0: "Not At Risk", 1: "At Risk"})
    plot_df["_DotSize"] = np.log10(plot_df["TotalRevenueCY"].clip(lower=1)) * 3

    fig = go.Figure()
    for status, color in [("Not At Risk", "#2ecc71"), ("At Risk", "#e74c3c")]:
        sub = plot_df[plot_df["_StatusLabel"] == status]
        fig.add_trace(go.Scatter(
            x=sub["ProgramExpenseRatio"],
            y=sub["ContributionGrowthPct"],
            mode="markers",
            name=status,
            marker=dict(
                size=sub["_DotSize"].clip(4, 18),
                color=color,
                opacity=0.6,
                line=dict(width=0.3, color="white"),
            ),
            customdata=sub[["OrgName", "Sector", "State", "ImpactEfficiency"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Sector: %{customdata[1]} · State: %{customdata[2]}<br>"
                "Program Ratio: %{x:.1%}<br>"
                "Contribution Growth: %{y:.1%}<br>"
                "Impact Efficiency: %{customdata[3]:.1f}<extra></extra>"
            ),
        ))

    # Annotate quadrant
    fig.add_annotation(
        x=0.9, y=0.3, xref="paper", yref="paper",
        text="Hidden Gem Zone", showarrow=False,
        font=dict(size=12, color="#27ae60"),
        bgcolor="rgba(255,255,255,0.8)",
    )
    fig.update_layout(
        xaxis_title="Program Expense Ratio (mission efficiency)",
        yaxis_title="Contribution Growth (YoY)",
        xaxis=dict(tickformat=".0%"),
        yaxis=dict(tickformat=".0%"),
        legend=dict(x=0.01, y=0.99),
        margin=dict(t=10, b=10, l=10, r=10),
        height=380,
        plot_bgcolor="#f9f9f9",
        hovermode="closest",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Dot size = revenue (log scale). Top-right quadrant (high program ratio, growing contributions) "
        "= highest-impact hidden gems."
    )


def _sector_spotlight(df: pd.DataFrame) -> None:
    gems = df[df["_IsHiddenGem"]].copy()
    if gems.empty:
        st.info("No hidden gems in current filter.")
        return

    sector_counts = gems["Sector"].value_counts().reset_index()
    sector_counts.columns = ["Sector", "Hidden Gems"]
    sector_counts = sector_counts.sort_values("Hidden Gems", ascending=True)

    fig = go.Figure(go.Bar(
        x=sector_counts["Hidden Gems"],
        y=sector_counts["Sector"],
        orientation="h",
        marker_color="#27ae60",
        text=sector_counts["Hidden Gems"],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Hidden Gems: %{x:,}<extra></extra>",
    ))
    fig.update_layout(
        xaxis_title="# Hidden Gems",
        yaxis_title="",
        margin=dict(t=10, b=10, l=10, r=40),
        height=max(260, len(sector_counts) * 30),
        plot_bgcolor="#f9f9f9",
    )
    st.plotly_chart(fig, use_container_width=True)


def _top_gems_table(df: pd.DataFrame) -> None:
    gems = df[df["_IsHiddenGem"]].copy()
    if gems.empty:
        st.info("No hidden gems match current filters.")
        return

    top_n = st.slider("Show top N hidden gems", 10, min(100, len(gems)), 25, key="gems_n")
    top = gems.nlargest(top_n, "ImpactEfficiency")

    display_cols = {
        "OrgName": "Organization",
        "State": "State",
        "Sector": "Sector",
        "SizeCategory": "Size",
        "TaxYear": "Year",
        "ImpactEfficiency": "Impact Score",
        "ProgramExpenseRatio": "Program %",
        "SurplusMargin": "Surplus Margin",
        "ContributionGrowthPct": "Contribution Growth",
        "ResilienceScore": "Resilience Score",
        "AtRiskProba": "Risk Proba",
        "TotalRevenueCY": "Revenue",
    }

    available = {k: v for k, v in display_cols.items() if k in top.columns}
    table = top[list(available.keys())].rename(columns=available).reset_index(drop=True)

    # Format columns
    if "Program %" in table.columns:
        table["Program %"] = table["Program %"].apply(lambda x: f"{x:.1%}" if pd.notna(x) else "N/A")
    if "Surplus Margin" in table.columns:
        table["Surplus Margin"] = table["Surplus Margin"].apply(lambda x: f"{x:.1%}" if pd.notna(x) else "N/A")
    if "Contribution Growth" in table.columns:
        table["Contribution Growth"] = table["Contribution Growth"].apply(lambda x: f"{x:.1%}" if pd.notna(x) else "N/A")
    if "Risk Proba" in table.columns:
        table["Risk Proba"] = table["Risk Proba"].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
    if "Revenue" in table.columns:
        table["Revenue"] = table["Revenue"].apply(
            lambda x: f"${x/1e6:.2f}M" if pd.notna(x) and x >= 1e6 else (
                f"${x/1e3:.0f}K" if pd.notna(x) else "N/A"
            )
        )

    st.dataframe(table, use_container_width=True, height=400)

    # Download
    csv = top[list(available.keys())].rename(columns=available).to_csv(index=False)
    st.download_button(
        "Download Hidden Gems CSV",
        data=csv,
        file_name="hidden_gems.csv",
        mime="text/csv",
    )


def _program_efficiency_bars(df: pd.DataFrame) -> None:
    per = pd.to_numeric(df["ProgramExpenseRatio"], errors="coerce")
    plot_df = df.copy()
    plot_df["_per"] = per
    plot_df["_tier"] = df["ResilienceTier"]

    sector_agg = (
        plot_df.groupby(["Sector", "_tier"], observed=True)["_per"]
        .median()
        .reset_index()
        .rename(columns={"_per": "Median Program %", "_tier": "Resilience Tier"})
    )
    sector_agg["Median Program %"] = sector_agg["Median Program %"] * 100

    TIER_COLORS = {"Stable": "#2ecc71", "Watch": "#f39c12", "At Risk": "#e74c3c"}

    fig = px.bar(
        sector_agg, x="Sector", y="Median Program %",
        color="Resilience Tier",
        barmode="group",
        color_discrete_map=TIER_COLORS,
        labels={"Median Program %": "Median Program Expense Ratio (%)"},
        category_orders={"Resilience Tier": ["Stable", "Watch", "At Risk"]},
    )
    fig.update_layout(
        xaxis_tickangle=-35,
        margin=dict(t=10, b=10, l=10, r=10),
        height=300,
        plot_bgcolor="#f9f9f9",
        legend_title="Resilience Tier",
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Median share of expenses going to mission programs by sector and tier. "
        "Stable orgs consistently outperform At-Risk orgs on mission focus."
    )
