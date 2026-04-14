"""Streamlit entry point — Nonprofit Financial Resilience Analytics for Fairlight Advisors."""

import streamlit as st

from src.data_loader import load_data, load_train_metrics
from src.feature_engineering import engineer_features
from src.filters import (
    apply_filters,
    available_resilience_tiers,
    available_sectors,
    available_size_categories,
    available_states,
    available_years,
)
from features import overview, model_insights, peer_benchmarking, high_impact, org_deep_dive

st.set_page_config(
    page_title="Nonprofit Resilience Analytics — Fairlight Advisors",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS for a polished look ────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 1.4rem; }
[data-testid="stMetricLabel"] { font-size: 0.82rem; color: #555; }
.stTabs [data-baseweb="tab-list"] { gap: 6px; }
.stTabs [data-baseweb="tab"] { padding: 6px 16px; border-radius: 6px 6px 0 0; }
.block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner="Loading master dataset…")
def get_data():
    raw = load_data()
    return engineer_features(raw)


@st.cache_data(show_spinner=False)
def get_metrics():
    return load_train_metrics()


df_full = get_data()
train_metrics = get_metrics()

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.image(
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8e/IRS_logo.svg/200px-IRS_logo.svg.png",
    width=60,
)
st.sidebar.title("Filters")
st.sidebar.caption("Applied across all tabs")

years = available_years(df_full)
year_options = ["All"] + [str(y) for y in years]
year_sel = st.sidebar.selectbox("Tax Year", year_options)
year = int(year_sel) if year_sel != "All" else None

states = available_states(df_full)
state_options = ["All"] + states
state_sel = st.sidebar.selectbox("State", state_options)
state = state_sel if state_sel != "All" else None

sectors = available_sectors(df_full)
sector_options = ["All"] + sectors
sector_sel = st.sidebar.selectbox("Mission Sector", sector_options)
sector = sector_sel if sector_sel != "All" else None

size_cats = available_size_categories(df_full)
size_options = ["All"] + size_cats
size_sel = st.sidebar.selectbox("Revenue Size", size_options)
size_cat = size_sel if size_sel != "All" else None

tiers = available_resilience_tiers(df_full)
tier_options = ["All"] + tiers
tier_sel = st.sidebar.selectbox("Resilience Tier", tier_options)
resilience_tier = tier_sel if tier_sel != "All" else None

st.sidebar.divider()
st.sidebar.caption(f"**{len(df_full):,}** total organizations loaded")

# ── Filter ────────────────────────────────────────────────────────────────────
df = apply_filters(
    df_full,
    year=year,
    state=state,
    sector=sector,
    size_category=size_cat,
    resilience_tier=resilience_tier,
)

st.sidebar.caption(f"**{len(df):,}** match current filters")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("Nonprofit Financial Resilience Analytics")
st.caption(
    "Powered by 7 years of IRS Form 990 data · XGBoost At-Risk Classifier (Temporal ROC-AUC ≈ 0.92) · "
    "Peer benchmarking across sector × size × state groups"
)

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 Executive Overview",
    "🤖 Resilience Model",
    "🔍 Peer Benchmarking",
    "💎 Hidden Gems",
    "🏢 Org Deep Dive",
])

with tab1:
    overview.render(df)

with tab2:
    model_insights.render(df, train_metrics)

with tab3:
    peer_benchmarking.render(df)

with tab4:
    high_impact.render(df)

with tab5:
    org_deep_dive.render(df)
