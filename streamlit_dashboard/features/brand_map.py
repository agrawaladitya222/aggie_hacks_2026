"""Build the brand map Plotly figure. Pure data → figure, no Streamlit code."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

_TIER_COLORS = {
    "Stable": "#2ecc71",
    "Watch": "#f39c12",
    "At Risk": "#e74c3c",
}
_TIER_ORDER = ["Stable", "Watch", "At Risk"]


def build_brand_map(df: pd.DataFrame) -> go.Figure:
    """
    Return a Plotly scatter figure for the brand map.

    Expects the output of feature_engineering.engineer_features() (already filtered).
    Rows with null ProgramSvcExpenses (_exclude_brand_map == True) are dropped here.
    """
    plot_df = df[~df["_exclude_brand_map"]].copy().reset_index(drop=True)

    # Use pre-formatted columns if available (added by feature_engineering.engineer_features)
    if "_TotalRevenueFmt" not in plot_df.columns:
        plot_df["_TotalRevenueFmt"] = (
            pd.to_numeric(plot_df["TotalRevenueCY"], errors="coerce")
            .apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
        )
    if "_SurplusMarginFmt" not in plot_df.columns:
        plot_df["_SurplusMarginFmt"] = (
            pd.to_numeric(plot_df["SurplusMargin"], errors="coerce")
            .apply(lambda x: f"{x * 100:.1f}%" if pd.notna(x) else "N/A")
        )
    # GrantDependencyPct is the column name in master_990.csv
    grant_col = "GrantDependencyPct" if "GrantDependencyPct" in plot_df.columns else "GrantDependency"
    if "_GrantDependencyFmt" not in plot_df.columns:
        plot_df["_GrantDependencyFmt"] = (
            pd.to_numeric(plot_df.get(grant_col, pd.Series(dtype=float)), errors="coerce")
            .apply(lambda x: f"{x * 100:.1f}%" if pd.notna(x) else "N/A")
        )
    # Sector: use mission-based Sector (master_990) or NTEEMajorSector fallback
    sector_col = "Sector" if "Sector" in plot_df.columns else "NTEEMajorSector"
    plot_df["_SectorDisplay"] = plot_df.get(sector_col, "N/A").fillna("N/A")

    fig = go.Figure()

    for tier in _TIER_ORDER:
        subset = plot_df[plot_df["ResilienceTier"] == tier]
        if subset.empty:
            continue

        fig.add_trace(
            go.Scatter(
                x=subset["ProgramExpenseRatio"],
                y=subset["OperatingReserveMonths"],
                mode="markers",
                name=tier,
                marker=dict(
                    size=subset["DotSize"] * 4,
                    color=_TIER_COLORS[tier],
                    opacity=0.75,
                    line=dict(width=0.5, color="white"),
                ),
                customdata=subset[[
                    "OrgName",
                    "State",
                    "_TotalRevenueFmt",
                    "_SectorDisplay",
                    "_SurplusMarginFmt",
                    "_GrantDependencyFmt",
                    "ResilienceTier",
                ]].values,
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>"
                    "State: %{customdata[1]}<br>"
                    "Total Revenue: %{customdata[2]}<br>"
                    "Sector: %{customdata[3]}<br>"
                    "Surplus Margin: %{customdata[4]}<br>"
                    "Grant Dependency: %{customdata[5]}<br>"
                    "Resilience Tier: %{customdata[6]}"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_layout(
        xaxis_title="Program Expense Ratio  (how much of every dollar goes to mission)",
        yaxis_title="Operating Reserve Months  (months of runway without new funding)",
        legend_title="Resilience Tier",
        legend=dict(
            font=dict(size=14, color="#111111"),
            title_font=dict(size=15, color="#111111"),
            bgcolor="#f5f5f5",
            bordercolor="#aaaaaa",
            borderwidth=1,
        ),
        plot_bgcolor="#f9f9f9",
        paper_bgcolor="white",
        hovermode="closest",
        xaxis=dict(
            showgrid=True,
            gridcolor="#bbbbbb",
            gridwidth=1,
            linecolor="#444444",
            linewidth=1,
            tickfont=dict(color="#222222"),
            title_font=dict(color="#222222"),
            zeroline=True,
            zerolinecolor="#888888",
            zerolinewidth=1,
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="#bbbbbb",
            gridwidth=1,
            linecolor="#444444",
            linewidth=1,
            tickfont=dict(color="#222222"),
            title_font=dict(color="#222222"),
            zeroline=True,
            zerolinecolor="#888888",
            zerolinewidth=1,
        ),
    )

    return fig
