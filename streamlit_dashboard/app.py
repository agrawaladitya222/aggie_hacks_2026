"""Streamlit entry point — Nonprofit Brand Map for Fairlight Advisors."""

import streamlit as st

from src.data_loader import load_data
from src.feature_engineering import engineer_features
from src.filters import (
    apply_filters,
    available_resilience_tiers,
    available_size_buckets,
    available_states,
    available_years,
    ntee_sector_display_options,
)
from features.brand_map import build_brand_map

st.set_page_config(
    page_title="Nonprofit Brand Map — Fairlight Advisors",
    layout="wide",
)


@st.cache_data
def get_data():
    raw = load_data()
    return engineer_features(raw)


df = get_data()

# --- Sidebar ---
st.sidebar.header("Filters")

years = available_years(df)
year_options = ["All"] + [str(y) for y in years]
year_sel = st.sidebar.selectbox("Tax Year", year_options)
year = int(year_sel) if year_sel != "All" else None

states = available_states(df)
state_options = ["All"] + states
state_sel = st.sidebar.selectbox("State", state_options)
state = state_sel if state_sel != "All" else None

ntee_options = ntee_sector_display_options(df)  # {"B — Education": "B", ...}
sector_sel = st.sidebar.selectbox("NTEE Major Sector", ["All"] + list(ntee_options.keys()))
ntee_sector = ntee_options[sector_sel] if sector_sel != "All" else None

size_buckets = available_size_buckets(df)
size_options = ["All"] + size_buckets
size_sel = st.sidebar.selectbox("Revenue Size", size_options)
size_bucket = size_sel if size_sel != "All" else None

tiers = available_resilience_tiers(df)
tier_options = ["All"] + tiers
tier_sel = st.sidebar.selectbox("Resilience Tier", tier_options)
resilience_tier = tier_sel if tier_sel != "All" else None

# --- Filter ---
filtered = apply_filters(
    df,
    year=year,
    state=state,
    ntee_sector=ntee_sector,
    size_bucket=size_bucket,
    resilience_tier=resilience_tier,
)

# --- Main ---
st.title("Nonprofit Brand Map")
st.caption(
    "X axis: Program Expense Ratio · "
    "Y axis: Operating Reserve Months · "
    "Dot size: Revenue (log scale) · "
    "Color: Resilience Tier"
)

n_total = len(filtered)
n_brand_map = int((~filtered["_exclude_brand_map"]).sum())

col1, col2, col3 = st.columns(3)
col1.metric("Orgs shown", f"{n_total:,}")
col2.metric("On brand map", f"{n_brand_map:,}")
col3.metric(
    "At Risk",
    f"{int((filtered['ResilienceTier'] == 'At Risk').sum()):,}",
)

if n_brand_map == 0:
    st.warning("No organizations match the current filters with valid Program Expense data.")
else:
    fig = build_brand_map(filtered)
    st.plotly_chart(fig, width="stretch")

# TODO: add insights to the nonprofit brand map
# TODO: add metrics tab

# st.divider()
# st.subheader("Metric Definitions")

# col_a, col_b = st.columns(2)

# with col_a:
#     st.markdown("**Efficiency**")
#     st.markdown("Program Expense Ratio — share of spending that goes directly to programs")
#     st.latex(r"\frac{\text{ProgramSvcExpenses}}{\text{TotalExpensesCY}}")

#     st.markdown("Fundraising Overhead — share of spending on fundraising")
#     st.latex(r"\frac{\text{FundraisingExpCY}}{\text{TotalExpensesCY}}")

#     st.markdown("Salary Ratio — share of spending on salaries")
#     st.latex(r"\frac{\text{SalariesCY}}{\text{TotalExpensesCY}}")

#     st.markdown("Admin Overhead — remainder after programs and fundraising")
#     st.latex(r"1 - \text{ProgramExpenseRatio} - \text{FundraisingOverhead}")

#     st.markdown("**Financial Stability**")
#     st.markdown("Operating Reserve Months — months the org can run with no new revenue")
#     st.latex(r"\frac{\text{NetAssetsEOY}}{\text{TotalExpensesCY} / 12}")

#     st.markdown("Surplus Margin — whether the org ran a surplus or deficit")
#     st.latex(r"\frac{\text{NetRevenueCY}}{\text{TotalRevenueCY}}")

#     st.markdown("Debt Ratio — fraction of assets financed by debt")
#     st.latex(r"\frac{\text{TotalLiabilitiesEOY}}{\text{TotalAssetsEOY}}")

#     st.markdown("Asset Growth — year-over-year change in total assets")
#     st.latex(r"\frac{\text{TotalAssetsEOY} - \text{TotalAssetsBOY}}{|\text{TotalAssetsBOY}|}")

# with col_b:
#     st.markdown("**Revenue Diversification**")
#     st.markdown("Grant Dependency — share of revenue from contributions and grants")
#     st.latex(r"\frac{\text{ContributionsGrantsCY}}{\text{TotalRevenueCY}}")

#     st.markdown("Earned Revenue % — share of revenue from program services")
#     st.latex(r"\frac{\text{ProgramServiceRevCY}}{\text{TotalRevenueCY}}")

#     st.markdown("Investment Income % — share of revenue from investments")
#     st.latex(r"\frac{\text{InvestmentIncomeCY}}{\text{TotalRevenueCY}}")

#     st.markdown("Revenue Concentration — share held by the single largest revenue stream")
#     st.latex(r"\frac{\max(\text{Grants},\ \text{Earned},\ \text{Investment})}{\text{TotalRevenueCY}}")

#     st.markdown("**Growth (Year-over-Year)**")
#     st.markdown("Revenue Growth — change in total revenue vs prior year")
#     st.latex(r"\frac{\text{TotalRevenueCY} - \text{TotalRevenuePY}}{|\text{TotalRevenuePY}|}")

#     st.markdown("Expense Growth — change in total expenses vs prior year")
#     st.latex(r"\frac{\text{TotalExpensesCY} - \text{TotalExpensesPY}}{|\text{TotalExpensesPY}|}")

#     st.markdown("Net Asset Growth — change in net assets over the year")
#     st.latex(r"\frac{\text{NetAssetsEOY} - \text{NetAssetsBOY}}{|\text{NetAssetsBOY}|}")

#     st.markdown("Contribution Growth — change in grants/contributions vs prior year")
#     st.latex(r"\frac{\text{ContributionsGrantsCY} - \text{ContributionsGrantsPY}}{|\text{ContributionsGrantsPY}|}")

#     st.markdown("**Resilience Tier**")
#     st.markdown(
#         "🟢 **Stable** — Reserve Months > 6 and Surplus Margin > 0%  \n"
#         "🟡 **Watch** — Reserve Months 1–6 or Surplus Margin between −10% and 0%  \n"
#         "🔴 **At Risk** — Reserve Months < 1, Surplus Margin < −10%, or Debt Ratio > 0.8"
#     )
