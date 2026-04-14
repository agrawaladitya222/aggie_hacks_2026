from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(page_title="Nonprofit Resilience Analytics", layout="wide")


@st.cache_data
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    master = pd.read_csv("data/master_990.csv", low_memory=False)
    peers = pd.read_csv("data/peer_group_stats.csv", low_memory=False)
    sims = pd.read_csv("data/simulation_results.csv", low_memory=False)
    metrics_path = Path("artifacts/train_metrics.json")
    metrics = {}
    if metrics_path.exists():
        metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    return master, peers, sims, metrics


def executive_page(df: pd.DataFrame) -> None:
    st.title("Nonprofit Financial Resilience Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Nonprofits", f"{len(df):,}")
    c2.metric("% At Risk", f"{df['AtRisk'].mean():.1%}")
    c3.metric("Avg Resilience", f"{df['ResilienceScore'].mean():.1f}")
    c4.metric("States", int(df["State"].nunique()))

    hist = px.histogram(df, x="ResilienceScore", nbins=50, title="Resilience Score Distribution")
    st.plotly_chart(hist, use_container_width=True)

    state_avg = df.groupby("State", as_index=False)["ResilienceScore"].mean()
    choropleth = px.choropleth(
        state_avg,
        locations="State",
        locationmode="USA-states",
        color="ResilienceScore",
        scope="usa",
        title="Average Resilience Score by State",
    )
    st.plotly_chart(choropleth, use_container_width=True)


def peer_page(df: pd.DataFrame) -> None:
    st.title("Peer Benchmarking")
    org = st.selectbox("Select organization", sorted(df["OrgName"].dropna().unique())[:5000])
    row = df[df["OrgName"] == org].iloc[0]
    peer_id = row["PeerGroupID"]
    peer_df = df[df["PeerGroupID"] == peer_id]
    metrics = ["ProgramExpenseRatio", "FundraisingRatio", "SurplusMargin", "OperatingReserveMonths", "DebtRatio"]
    med = peer_df[metrics].median()
    vals = [row[m] for m in metrics]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=vals, theta=metrics, fill="toself", name="Selected Org"))
    fig.add_trace(go.Scatterpolar(r=[med[m] for m in metrics], theta=metrics, fill="toself", name="Peer Median"))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True)
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(peer_df[["OrgName", "State", "ResilienceScore"] + metrics].head(200), use_container_width=True)


def resilience_page(df: pd.DataFrame, metrics: dict) -> None:
    st.title("Resilience Explorer")
    scatter = px.scatter(
        df.sample(min(len(df), 5000), random_state=42),
        x="LogRevenue",
        y="ResilienceScore",
        color="Sector",
        hover_data=["OrgName", "State"],
        title="Resilience vs Revenue (sampled)",
    )
    st.plotly_chart(scatter, use_container_width=True)
    if metrics:
        st.subheader("Model Snapshot")
        st.json(metrics)
    st.dataframe(df[["EIN", "OrgName", "State", "Sector", "ResilienceScore", "AtRisk", "AtRiskProbability"]].head(200))


def simulation_page(sims: pd.DataFrame) -> None:
    st.title("Stress Test Simulator")
    scenario = st.selectbox("Scenario", sorted(sims["Scenario"].unique()))
    sdf = sims[sims["Scenario"] == scenario]
    status_dist = sdf["PostShock_Status"].value_counts(normalize=True).reset_index()
    pie = px.pie(status_dist, names="PostShock_Status", values="proportion", title=f"Post-shock status: {scenario}")
    st.plotly_chart(pie, use_container_width=True)
    sector = (
        sdf.groupby(["Sector", "PostShock_Status"], as_index=False)
        .size()
        .pivot(index="Sector", columns="PostShock_Status", values="size")
        .fillna(0)
    )
    st.dataframe(sector.head(50), use_container_width=True)


def gems_page() -> None:
    st.title("Hidden Gems Finder")
    gems = pd.read_csv("data/hidden_gems.csv", low_memory=False)
    state_options = ["All"] + sorted(gems["State"].dropna().unique().tolist())
    sel_state = st.selectbox("State", state_options)
    if sel_state != "All":
        gems = gems[gems["State"] == sel_state]
    st.dataframe(gems.head(300), use_container_width=True)
    fig = px.scatter(
        gems,
        x="TotalRevenueCY",
        y="ImpactEfficiencyScore",
        color="Sector",
        hover_data=["OrgName", "DonationToStabilize"],
        title="Budget vs Impact Efficiency",
    )
    st.plotly_chart(fig, use_container_width=True)


def main() -> None:
    df, _peers, sims, metrics = load_data()
    page = st.sidebar.selectbox(
        "Navigate",
        [
            "Executive Overview",
            "Peer Benchmarking",
            "Resilience Explorer",
            "Stress Test Simulator",
            "Hidden Gems Finder",
        ],
    )
    if page == "Executive Overview":
        executive_page(df)
    elif page == "Peer Benchmarking":
        peer_page(df)
    elif page == "Resilience Explorer":
        resilience_page(df, metrics)
    elif page == "Stress Test Simulator":
        simulation_page(sims)
    else:
        gems_page()


if __name__ == "__main__":
    main()
