"""
EDA Script 1: Data Overview & Distribution Analysis
=====================================================
Decisions justified by this script:
  1. Why 2018-2024 panel (not all years)  → Fig 1: Data volume by tax year
  2. Why log-transform revenue & assets   → Fig 2: Raw vs log distribution comparison
  3. Why these 6 size bins               → Fig 3: Revenue CDF with bin boundaries + AtRisk rate by size
  4. Why median imputation (not drop)    → Fig 4: Missing value heatmap across key features
  5. Why clip/winsorize outliers         → Fig 5: Raw ratio distributions showing extremes

Outputs saved to: outputs/eda/01_data_overview/
"""

from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ── Config ───────────────────────────────────────────────────────────────────
MASTER_CSV = Path("data/master_990.csv")
OUT_DIR = Path("outputs/eda/01_data_overview")
OUT_DIR.mkdir(parents=True, exist_ok=True)
PALETTE = "muted"
sns.set_theme(style="whitegrid", palette=PALETTE, font_scale=1.1)

# ── Load data ─────────────────────────────────────────────────────────────────
if not MASTER_CSV.exists():
    print("master_990.csv not found — running data pipeline first...")
    from src.data_pipeline import run_data_pipeline
    df = run_data_pipeline()
else:
    df = pd.read_csv(MASTER_CSV, low_memory=False)

print(f"Loaded {len(df):,} rows, {df['EIN'].nunique():,} unique orgs, "
      f"tax years {df['TaxYear'].min()}–{df['TaxYear'].max()}")

# ── Add AtRisk label if not present ──────────────────────────────────────────
if "AtRisk" not in df.columns:
    df["AtRisk"] = (
        (df["SurplusMargin"] < -0.10)
        | (df["OperatingReserveMonths"] < 1)
        | (df["NetAssetGrowthPct"] < -0.20)
        | (df["RevenueGrowthPct"] < -0.25)
    ).astype(int)

# ─────────────────────────────────────────────────────────────────────────────
# FIG 1: Data volume by tax year
# Decision: Include 2018–2024; exclude 2016–2017 (tiny, unrepresentative)
# ─────────────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
counts = df["TaxYear"].value_counts().sort_index()
bars = ax.bar(counts.index.astype(str), counts.values,
              color=sns.color_palette(PALETTE, len(counts)))
ax.set_title("Fig 1 — Form 990 Filings by Tax Year\n"
             "(justifies 2018–2024 panel; 2018 is sparse due to IRS batch coverage)",
             fontsize=11)
ax.set_xlabel("Tax Year")
ax.set_ylabel("Number of Filings")
for bar, val in zip(bars, counts.values):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 400,
            f"{val:,}", ha="center", va="bottom", fontsize=9)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
plt.tight_layout()
plt.savefig(OUT_DIR / "fig1_filings_by_year.png", dpi=150)
plt.close()
print("Saved fig1_filings_by_year.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 2: Raw revenue vs log-revenue distribution
# Decision: Use LogRevenue and LogAssets as model features (not raw dollar amounts)
# because raw distributions are heavily right-skewed — violates assumptions of
# distance-based and linear models; log makes the scale comparable across orgs.
# ─────────────────────────────────────────────────────────────────────────────
sample = df[df["TotalRevenueCY"] < df["TotalRevenueCY"].quantile(0.995)].copy()
fig, axes = plt.subplots(2, 2, figsize=(12, 8))
fig.suptitle("Fig 2 — Raw vs Log-Transformed Revenue & Assets\n"
             "(justifies using LogRevenue & LogAssets as model features)", fontsize=11)

axes[0, 0].hist(sample["TotalRevenueCY"] / 1e6, bins=80, color="#4878CF", edgecolor="none")
axes[0, 0].set_title("Total Revenue (raw, $M)")
axes[0, 0].set_xlabel("Revenue ($M)")
axes[0, 0].set_ylabel("Count")
axes[0, 0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:.0f}M"))

axes[0, 1].hist(np.log1p(sample["TotalRevenueCY"]), bins=80, color="#4878CF", edgecolor="none")
axes[0, 1].set_title("Log(1 + Total Revenue)  ← used in model")
axes[0, 1].set_xlabel("log1p(Revenue)")
axes[0, 1].set_ylabel("Count")

asset_sample = df[df["TotalAssetsEOY"].between(0, df["TotalAssetsEOY"].quantile(0.995))]
axes[1, 0].hist(asset_sample["TotalAssetsEOY"] / 1e6, bins=80, color="#6ACC65", edgecolor="none")
axes[1, 0].set_title("Total Assets (raw, $M)")
axes[1, 0].set_xlabel("Assets ($M)")
axes[1, 0].set_ylabel("Count")
axes[1, 0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:.0f}M"))

axes[1, 1].hist(np.log1p(asset_sample["TotalAssetsEOY"].clip(lower=0)), bins=80,
                color="#6ACC65", edgecolor="none")
axes[1, 1].set_title("Log(1 + Total Assets)  ← used in model")
axes[1, 1].set_xlabel("log1p(Assets)")
axes[1, 1].set_ylabel("Count")

for ax in axes.flat:
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
plt.tight_layout()
plt.savefig(OUT_DIR / "fig2_log_transform_justification.png", dpi=150)
plt.close()
print("Saved fig2_log_transform_justification.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 3: Revenue CDF with size-bin boundaries + AtRisk rate by size category
# Decision: The 6 revenue bins (<500K, 500K-1M, 1M-5M, 5M-10M, 10M-50M, 50M+)
# are not arbitrary — AtRisk rates differ meaningfully across them, proving
# that size is a real driver of risk (smaller = more at-risk).
# ─────────────────────────────────────────────────────────────────────────────
SIZE_BINS = [0, 500_000, 1_000_000, 5_000_000, 10_000_000, 50_000_000, np.inf]
SIZE_LABELS = ["<500K", "500K-1M", "1M-5M", "5M-10M", "10M-50M", "50M+"]

if "SizeCategory" not in df.columns:
    df["SizeCategory"] = pd.cut(df["TotalRevenueCY"], bins=SIZE_BINS, labels=SIZE_LABELS)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
fig.suptitle("Fig 3 — Revenue Distribution & AtRisk Rate by Size Category\n"
             "(justifies 6 revenue-based size bins for peer grouping)", fontsize=11)

# CDF
rev_sorted = np.sort(df["TotalRevenueCY"].clip(upper=50_000_000))
cdf = np.arange(1, len(rev_sorted) + 1) / len(rev_sorted)
axes[0].plot(rev_sorted / 1e6, cdf, color="#4878CF", linewidth=1.5)
for boundary in SIZE_BINS[1:-1]:
    axes[0].axvline(boundary / 1e6, color="red", linestyle="--", linewidth=0.9, alpha=0.7)
axes[0].set_xlabel("Total Revenue ($M, capped at $50M)")
axes[0].set_ylabel("Cumulative Fraction of Orgs")
axes[0].set_title("Revenue CDF with Size-Bin Cutoffs")
axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x:.0f}M"))
# Annotate last bin
axes[0].text(48, 0.05, "50M+", color="red", fontsize=8, ha="right")

# AtRisk rate by size
at_risk_by_size = (
    df.groupby("SizeCategory", observed=True)["AtRisk"]
    .agg(["mean", "count"])
    .reset_index()
)
at_risk_by_size.columns = ["SizeCategory", "AtRiskRate", "Count"]
colors = ["#d62728" if r > 0.25 else "#1f77b4" for r in at_risk_by_size["AtRiskRate"]]
bars = axes[1].bar(at_risk_by_size["SizeCategory"], at_risk_by_size["AtRiskRate"] * 100, color=colors)
axes[1].set_xlabel("Revenue Size Category")
axes[1].set_ylabel("% At-Risk Organizations")
axes[1].set_title("At-Risk Rate by Size Category")
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
for bar, row in zip(bars, at_risk_by_size.itertuples()):
    axes[1].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                 f"n={row.Count:,}", ha="center", va="bottom", fontsize=8)

plt.tight_layout()
plt.savefig(OUT_DIR / "fig3_size_bins_justification.png", dpi=150)
plt.close()
print("Saved fig3_size_bins_justification.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 4: Missing value rates for key model features
# Decision: Use median imputation (not row-dropping) because missingness is
# spread unevenly across features and dropping rows would lose substantial data.
# ─────────────────────────────────────────────────────────────────────────────
FEATURE_COLS = [
    "GrantDependencyPct", "ProgramRevenuePct", "InvestmentRevenuePct", "GovGrantPct",
    "ProgramExpenseRatio", "FundraisingRatio", "SalaryRatio", "DebtRatio",
    "AssetLiabilityRatio", "ExpenseGrowthPct", "ContributionGrowthPct",
    "OrgAge", "Employees", "LogRevenue", "LogAssets",
    "OperatingReserveMonths", "SurplusMargin", "RevenueGrowthPct", "NetAssetGrowthPct"
]
available = [c for c in FEATURE_COLS if c in df.columns]
miss_pct = df[available].isna().mean().sort_values(ascending=False) * 100
miss_pct = miss_pct[miss_pct > 0]

fig, ax = plt.subplots(figsize=(10, max(4, len(miss_pct) * 0.4 + 1)))
if len(miss_pct) > 0:
    colors = ["#d62728" if v > 20 else "#ff7f0e" if v > 5 else "#1f77b4" for v in miss_pct]
    bars = ax.barh(miss_pct.index, miss_pct.values, color=colors)
    ax.axvline(5, color="orange", linestyle="--", linewidth=1, label="5% threshold")
    ax.axvline(20, color="red", linestyle="--", linewidth=1, label="20% threshold")
    ax.set_xlabel("% Missing")
    ax.set_title("Fig 4 — Missing Value Rates for Model Features\n"
                 "(justifies median imputation over row-dropping; "
                 "dropping rows would lose significant data)", fontsize=11)
    ax.legend(fontsize=9)
    for bar, val in zip(bars, miss_pct.values):
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", fontsize=9)
else:
    ax.text(0.5, 0.5, "No missing values in key features\n(pipeline already cleaned data)",
            ha="center", va="center", transform=ax.transAxes, fontsize=12)
    ax.set_title("Fig 4 — Missing Value Rates (post-pipeline)")

plt.tight_layout()
plt.savefig(OUT_DIR / "fig4_missing_values.png", dpi=150)
plt.close()
print("Saved fig4_missing_values.png")

# ─────────────────────────────────────────────────────────────────────────────
# FIG 5: Raw ratio distributions showing extreme outliers before clipping
# Decision: Clip ratios to [-2, 2] and growth metrics to [-5, 5] because
# extreme outliers (data errors, unusual events) would dominate model training.
# ─────────────────────────────────────────────────────────────────────────────
RATIO_COLS = ["GrantDependencyPct", "ProgramExpenseRatio", "SurplusMargin",
              "DebtRatio", "FundraisingRatio", "SalaryRatio"]
available_ratios = [c for c in RATIO_COLS if c in df.columns]

fig, axes = plt.subplots(2, 3, figsize=(15, 8))
fig.suptitle("Fig 5 — Key Financial Ratio Distributions (post-clipping to [-2, 2])\n"
             "(justifies outlier clipping — raw values contain data errors beyond ±2)",
             fontsize=11)

for ax, col in zip(axes.flat, available_ratios):
    data = df[col].dropna()
    # Show a dashed line for the clip boundaries
    ax.hist(data.clip(-2, 2), bins=80, color="#4878CF", edgecolor="none", alpha=0.85)
    pct_outside = ((df[col] < -2) | (df[col] > 2)).mean() * 100
    ax.axvline(-2, color="red", linestyle="--", linewidth=1, alpha=0.7)
    ax.axvline(2, color="red", linestyle="--", linewidth=1, alpha=0.7)
    ax.set_title(f"{col}\n({pct_outside:.1f}% outside ±2 clip bounds)")
    ax.set_xlabel("Value")
    ax.set_ylabel("Count")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

# Remove unused axes
for ax in axes.flat[len(available_ratios):]:
    ax.set_visible(False)

plt.tight_layout()
plt.savefig(OUT_DIR / "fig5_ratio_distributions.png", dpi=150)
plt.close()
print("Saved fig5_ratio_distributions.png")

print(f"\nAll figures saved to {OUT_DIR}/")
print("\nKey statistics for slide deck:")
print(f"  Total organizations (unique EINs): {df['EIN'].nunique():,}")
print(f"  Total filings (rows): {len(df):,}")
print(f"  Tax years covered: {sorted(df['TaxYear'].dropna().unique().tolist())}")
print(f"  Overall At-Risk rate: {df['AtRisk'].mean():.1%}")
print(f"  Sectors represented: {df['Sector'].nunique()}")
print(f"  States represented: {df['State'].nunique() if 'State' in df.columns else 'N/A'}")
