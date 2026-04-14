"""
EDA Script 2: Sector & Peer Group Analysis
===========================================
Decisions justified by this script:
  1. Why define peers by Sector + Size + State (not one dimension alone)
       → Fig 1: Key metrics vary dramatically across NTEE sectors
       → Fig 2: Key metrics also vary across size categories
       → Fig 3: Sector × size interaction shows combined grouping captures more variance
  2. Why sector matters for risk (different baseline risk profiles)
       → Fig 4: AtRisk rate by sector — not all sectors fail equally
  3. Why government grant dependency is a distinct risk dimension
       → Fig 5: GovGrantPct distribution by sector + correlation with AtRisk

Outputs saved to: outputs/eda/02_sector_peer_analysis/
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ── Config ───────────────────────────────────────────────────────────────────
MASTER_CSV = Path("data/master_990.csv")
OUT_DIR = Path("outputs/eda/02_sector_peer_analysis")
OUT_DIR.mkdir(parents=True, exist_ok=True)
sns.set_theme(style="whitegrid", font_scale=1.05)

# ── Load data ─────────────────────────────────────────────────────────────────
if not MASTER_CSV.exists():
    from src.data_pipeline import run_data_pipeline
    df = run_data_pipeline()
else:
    df = pd.read_csv(MASTER_CSV, low_memory=False)

if "AtRisk" not in df.columns:
    df["AtRisk"] = (
        (df["SurplusMargin"] < -0.10)
        | (df["OperatingReserveMonths"] < 1)
        | (df["NetAssetGrowthPct"] < -0.20)
        | (df["RevenueGrowthPct"] < -0.25)
    ).astype(int)

# Keep only sectors with enough observations for clear visuals
MIN_SECTOR_N = 500
sector_counts = df["Sector"].value_counts()
top_sectors = sector_counts[sector_counts >= MIN_SECTOR_N].index.tolist()
df_top = df[df["Sector"].isin(top_sectors)].copy()

SIZE_ORDER = ["<500K", "500K-1M", "1M-5M", "5M-10M", "10M-50M", "50M+"]
if "SizeCategory" in df_top.columns:
    df_top["SizeCategory"] = pd.Categorical(
        df_top["SizeCategory"].astype(str), categories=SIZE_ORDER, ordered=True
    )

# ─────────────────────────────────────────────────────────────────────────────
# FIG 1: Key metrics vary dramatically across sectors
# Decision: Sector alone explains a large share of variance in financial ratios —
# you cannot benchmark an education nonprofit against a hospital.
# ─────────────────────────────────────────────────────────────────────────────
SECTOR_METRICS = [
    ("GrantDependencyPct", "Grant Dependency %", "Ratio"),
    ("OperatingReserveMonths", "Operating Reserve (months)", "Months"),
    ("ProgramExpenseRatio", "Program Expense Ratio", "Ratio"),
    ("SurplusMargin", "Surplus Margin", "Ratio"),
]

fig, axes = plt.subplots(2, 2, figsize=(16, 11))
fig.suptitle("Fig 1 — Key Financial Metrics by Sector\n"
             "(justifies sector-based peer grouping: metrics vary dramatically across sectors)",
             fontsize=12, y=1.01)

for ax, (col, label, unit) in zip(axes.flat, SECTOR_METRICS):
    plot_df = df_top[[col, "Sector"]].dropna()
    # Clip for visual clarity
    clip_hi = plot_df[col].quantile(0.95)
    clip_lo = plot_df[col].quantile(0.05)
    plot_df[col] = plot_df[col].clip(clip_lo, clip_hi)
    order = plot_df.groupby("Sector")[col].median().sort_values().index.tolist()
    sns.boxplot(data=plot_df, x=col, y="Sector", order=order, ax=ax,
                palette="muted", fliersize=1.5, linewidth=0.8)
    ax.set_title(label)
    ax.set_xlabel(unit)
    ax.set_ylabel("")

plt.tight_layout()
plt.savefig(OUT_DIR / "fig1_metrics_by_sector.png", dpi=150, bbox_inches="tight")
plt.close()
print("Saved fig1_metrics_by_sector.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 2: Key metrics vary across size categories
# Decision: Even within a sector, larger orgs have different financial profiles
# (more reserves, lower grant dependency) — justifies adding size to peer group.
# ─────────────────────────────────────────────────────────────────────────────
SIZE_METRICS = [
    ("OperatingReserveMonths", "Operating Reserve (months)"),
    ("GrantDependencyPct", "Grant Dependency %"),
    ("SurplusMargin", "Surplus Margin"),
    ("DebtRatio", "Debt Ratio"),
]

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("Fig 2 — Key Financial Metrics by Size Category\n"
             "(justifies size-based peer grouping: larger orgs have structurally different finances)",
             fontsize=12)

for ax, (col, label) in zip(axes.flat, SIZE_METRICS):
    plot_df = df_top[[col, "SizeCategory"]].dropna()
    clip_hi = plot_df[col].quantile(0.95)
    clip_lo = plot_df[col].quantile(0.05)
    plot_df[col] = plot_df[col].clip(clip_lo, clip_hi)
    available_sizes = [s for s in SIZE_ORDER if s in plot_df["SizeCategory"].unique()]
    sns.boxplot(data=plot_df, x="SizeCategory", y=col, order=available_sizes,
                ax=ax, palette="Blues", fliersize=1.5, linewidth=0.8)
    ax.set_title(label)
    ax.set_xlabel("Revenue Size Category")
    ax.set_ylabel("")
    ax.tick_params(axis="x", rotation=30)

plt.tight_layout()
plt.savefig(OUT_DIR / "fig2_metrics_by_size.png", dpi=150)
plt.close()
print("Saved fig2_metrics_by_size.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 3: Sector × Size interaction heatmap (OperatingReserveMonths median)
# Decision: The combination of sector + size creates distinct peer cells —
# Education-Large is very different from Education-Small or Healthcare-Large.
# ─────────────────────────────────────────────────────────────────────────────
pivot_df = df_top.dropna(subset=["OperatingReserveMonths", "SizeCategory"])
pivot = pivot_df.pivot_table(
    values="OperatingReserveMonths",
    index="Sector",
    columns="SizeCategory",
    aggfunc="median",
)
# Reorder columns
col_order = [c for c in SIZE_ORDER if c in pivot.columns]
pivot = pivot[col_order]
# Keep sectors with most complete rows
pivot = pivot.dropna(thresh=3)

fig, ax = plt.subplots(figsize=(13, max(6, len(pivot) * 0.5 + 1)))
sns.heatmap(
    pivot, annot=True, fmt=".1f", cmap="YlOrRd_r",
    linewidths=0.5, ax=ax,
    cbar_kws={"label": "Median Operating Reserve (months)"}
)
ax.set_title("Fig 3 — Median Operating Reserve Months: Sector × Size\n"
             "(each cell is a distinct peer group; combined grouping captures both dimensions)",
             fontsize=11)
ax.set_xlabel("Revenue Size Category")
ax.set_ylabel("Sector")
plt.tight_layout()
plt.savefig(OUT_DIR / "fig3_sector_size_heatmap.png", dpi=150)
plt.close()
print("Saved fig3_sector_size_heatmap.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 4: AtRisk rate by sector
# Decision: Not all sectors are equally at-risk — this confirms that sector-
# specific baselines are needed (benchmarking cross-sector would be misleading).
# ─────────────────────────────────────────────────────────────────────────────
at_risk_sector = (
    df_top.groupby("Sector")["AtRisk"]
    .agg(["mean", "count", "sum"])
    .reset_index()
    .rename(columns={"mean": "AtRiskRate", "count": "Total", "sum": "AtRiskCount"})
    .sort_values("AtRiskRate", ascending=True)
)

fig, ax = plt.subplots(figsize=(10, max(5, len(at_risk_sector) * 0.45 + 1)))
overall_rate = df["AtRisk"].mean()
colors = ["#d62728" if r > overall_rate else "#1f77b4" for r in at_risk_sector["AtRiskRate"]]
bars = ax.barh(at_risk_sector["Sector"], at_risk_sector["AtRiskRate"] * 100, color=colors)
ax.axvline(overall_rate * 100, color="black", linestyle="--", linewidth=1.5,
           label=f"Overall avg: {overall_rate:.1%}")
ax.set_xlabel("% At-Risk Organizations")
ax.set_title("Fig 4 — At-Risk Rate by Sector\n"
             "(justifies sector-specific benchmarks; at-risk rates span a wide range across sectors)",
             fontsize=11)
ax.legend(fontsize=9)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
for bar, row in zip(bars, at_risk_sector.itertuples()):
    ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
            f"n={row.Total:,}", va="center", fontsize=8)
plt.tight_layout()
plt.savefig(OUT_DIR / "fig4_at_risk_by_sector.png", dpi=150)
plt.close()
print("Saved fig4_at_risk_by_sector.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 5: Government grant dependency — a distinct funding risk dimension
# Decision: GovGrantPct is a real, sector-varying risk factor (government funding
# is subject to policy changes) and must be tracked as its own feature, not
# collapsed into total grant dependency.
# ─────────────────────────────────────────────────────────────────────────────
# Panel A: GovGrantPct distribution by top sectors
gov_sectors = (
    df_top.groupby("Sector")["GovGrantPct"].median().sort_values(ascending=False).head(10).index
)
gov_df = df_top[df_top["Sector"].isin(gov_sectors)][["Sector", "GovGrantPct"]].dropna()
gov_df = gov_df[gov_df["GovGrantPct"] > 0]  # Only orgs that receive gov grants

# Panel B: AtRisk rate by GovGrantPct quintile
df_gov = df_top[df_top["GovGrantPct"] > 0].copy()
df_gov["GovGrantQuintile"] = pd.qcut(df_gov["GovGrantPct"], q=5,
                                      labels=["Q1\n(lowest)", "Q2", "Q3", "Q4", "Q5\n(highest)"])
gov_risk = df_gov.groupby("GovGrantQuintile", observed=True)["AtRisk"].mean().reset_index()

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("Fig 5 — Government Grant Dependency by Sector & Its Impact on Risk\n"
             "(justifies GovGrantPct as a separate feature from GrantDependencyPct)", fontsize=11)

order_sectors = (
    gov_df.groupby("Sector")["GovGrantPct"].median().sort_values(ascending=False).index.tolist()
)
sns.boxplot(data=gov_df, x="GovGrantPct", y="Sector", order=order_sectors,
            ax=axes[0], palette="Oranges", fliersize=1.5, linewidth=0.8)
axes[0].set_title("Gov Grant % by Sector (orgs receiving gov grants)")
axes[0].set_xlabel("Gov Grants / Total Revenue")
axes[0].set_ylabel("")

bar_colors = ["#ff7f0e" if i >= 3 else "#1f77b4" for i in range(5)]
axes[1].bar(gov_risk["GovGrantQuintile"].astype(str),
            gov_risk["AtRisk"] * 100, color=bar_colors)
axes[1].set_title("At-Risk Rate by Gov Grant Dependency Quintile\n(among grant-receiving orgs)")
axes[1].set_xlabel("Gov Grant Dependency Quintile")
axes[1].set_ylabel("% At-Risk")
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))

plt.tight_layout()
plt.savefig(OUT_DIR / "fig5_gov_grant_risk.png", dpi=150)
plt.close()
print("Saved fig5_gov_grant_risk.png")

print(f"\nAll figures saved to {OUT_DIR}/")
print("\nKey statistics for slide deck:")
print(f"  Sectors analyzed: {len(top_sectors)}")
print(f"  Sector with highest AtRisk rate: "
      f"{at_risk_sector.sort_values('AtRiskRate', ascending=False).iloc[0]['Sector']} "
      f"({at_risk_sector.sort_values('AtRiskRate', ascending=False).iloc[0]['AtRiskRate']:.1%})")
print(f"  Sector with lowest AtRisk rate: "
      f"{at_risk_sector.sort_values('AtRiskRate').iloc[0]['Sector']} "
      f"({at_risk_sector.sort_values('AtRiskRate').iloc[0]['AtRiskRate']:.1%})")
print(f"  Range of AtRisk rates across sectors: "
      f"{at_risk_sector['AtRiskRate'].min():.1%} – {at_risk_sector['AtRiskRate'].max():.1%}")
