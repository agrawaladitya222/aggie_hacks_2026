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

    plot_df["_TotalRevenueFmt"] = (
        plot_df["TotalRevenueCY"]
        .apply(lambda x: f"${x:,.0f}" if pd.notna(x) else "N/A")
    )
    plot_df["_SurplusMarginFmt"] = (
        plot_df["SurplusMargin"]
        .apply(lambda x: f"{x * 100:.1f}%" if pd.notna(x) else "N/A")
    )
    plot_df["_GrantDependencyFmt"] = (
        plot_df["GrantDependency"]
        .apply(lambda x: f"{x * 100:.1f}%" if pd.notna(x) else "N/A")
    )

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
                    "NTEEMajorSector",
                    "_SurplusMarginFmt",
                    "_GrantDependencyFmt",
                    "ResilienceTier",
                ]].values,
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
