# Product Requirements Document (PRD)
## Nonprofit Financial Resilience Analytics Platform
### Aggie Hacks 2026

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Business Context & Problem Definition](#2-business-context--problem-definition)
3. [Data Overview](#3-data-overview)
4. [Solution Architecture Overview](#4-solution-architecture-overview)
5. [Module 1: Data Ingestion & Feature Engineering](#5-module-1-data-ingestion--feature-engineering)
6. [Module 2: Peer Benchmarking Framework](#6-module-2-peer-benchmarking-framework)
7. [Module 3: Resilience Prediction Model](#7-module-3-resilience-prediction-model)
8. [Module 4: Financial Risk Simulation](#8-module-4-financial-risk-simulation)
9. [Module 5: High-Impact Discovery ("Hidden Gems")](#9-module-5-high-impact-discovery-hidden-gems)
10. [Module 6: Dashboard & Storytelling](#10-module-6-dashboard--storytelling)
11. [Evaluation & Success Criteria](#11-evaluation--success-criteria)
12. [Implementation Roadmap](#12-implementation-roadmap)
13. [Appendix: Column Data Dictionary](#13-appendix-column-data-dictionary)

---

## 1. Executive Summary

**Goal:** Build an end-to-end analytics solution that uses IRS Form 990 data (tax years 2016–2020) to help nonprofit leaders, funders, and capacity builders answer three questions:

1. **Who is thriving?** — Identify financially durable nonprofits and the factors that make them resilient.
2. **Who is at risk?** — Detect organizations vulnerable to funding shocks and identify intervention thresholds.
3. **Who deserves attention?** — Surface "hidden gem" nonprofits where a donation can create outsized community impact.

The solution consists of four analytical modules (Peer Benchmarking, Resilience Prediction, Financial Risk Simulation, High-Impact Discovery) supported by a data pipeline and presented through an interactive dashboard.

**Target User:** Fairlight Advisors and similar nonprofit capacity-building consultancies who advise funders on where to allocate philanthropic capital.

---

## 2. Business Context & Problem Definition

### 2.1 The Nonprofit Landscape Problem

The U.S. nonprofit sector has hundreds of thousands of public charities. Despite IRS Form 990 being publicly available, nonprofit leaders and funders lack **accessible, decision-ready tools** to:
- Assess financial resilience
- Benchmark against peers
- Identify where targeted support has the greatest impact

### 2.2 Specific Business Questions We Answer

| # | Question | Module |
|---|----------|--------|
| 1 | Which nonprofits are most likely to remain financially stable during funding fluctuations? | Resilience Prediction |
| 2 | How does a nonprofit's financial health compare to meaningful peers? | Peer Benchmarking |
| 3 | What happens if a specific revenue stream drops by X%? | Financial Risk Simulation |
| 4 | Which small/mid-size nonprofits deliver disproportionate community value? | High-Impact Discovery |

### 2.3 Stakeholder Value

- **Funders:** Know where donations create the most impact; avoid funding organizations about to fail.
- **Nonprofit Leaders:** Understand their financial position relative to peers; plan for funding shocks.
- **Fairlight Advisors:** Provide data-driven recommendations to clients with transparent scoring.

### 2.4 Judging Criteria Alignment

| Criteria | Weight | How We Address It |
|----------|--------|-------------------|
| Peer Benchmarking (10pts) | 10% | Module 2 — explicit peer group definition by sector, size, geography |
| Business Solution (10pts) | 10% | Clear problem definition, objectives, success criteria in this PRD |
| Financial Insights (10pts) | 10% | Revenue decomposition, reserve analysis, shock modeling |
| Depth of Solution (10pts) | 10% | Four interconnected modules with composite scoring |
| Tool Accuracy (10pts) | 10% | Transparent feature engineering, validated against raw data |
| Model Development (10pts) | 10% | EDA-driven model selection with justification and metrics |
| Results (10pts) | 10% | Clear visualizations, threshold tables, actionable recommendations |
| Level of Insights (10pts) | 10% | Non-obvious findings: hidden gems, tipping points, recovery pathways |
| Business Storytelling (20pts) | 20% | Interactive dashboard + presentation narrative |

---

## 3. Data Overview

### 3.1 Source Files

The data lives in `data/data_csv/` and consists of three CSV files parsed from IRS Form 990 XML filings:

| File | Rows | Tax Years Covered |
|------|------|-------------------|
| `2019_990.csv` | 5,308 | 2016, 2017, 2018 |
| `2020_990.csv` | 2,773 | 2017, 2018, 2019 |
| `2021_990.csv` | 24,374 | 2018, 2019, 2020 |
| **Total** | **32,455** | **2016–2020 (5 years)** |

Additionally, ~17,000+ raw XML files exist in `2024_TEOS_XML_*` folders that can be parsed for 2022 data using the existing `parse_990.py` script if needed.

### 3.2 Data Structure

Each row = one nonprofit (identified by EIN) for one tax year. Key: every row contains **Current Year (CY)** and **Prior Year (PY)** figures, effectively giving two years of data per filing.

**Unique EINs:** ~30,305 total
- 28,251 EINs appear in only 1 tax year
- 1,986 EINs appear in 2 tax years
- 68 EINs appear in 3+ tax years

**Geographic Coverage:** 56 states/territories. Top states: CA (3,542), NY (2,795), TX (1,687), PA (1,615), FL (1,442).

**All Form Types:** 990 (standard full form — all 32,455 rows).

### 3.3 Raw Column Inventory (36 columns)

See [Appendix](#13-appendix-column-data-dictionary) for full definitions. The columns group into:

| Category | Columns |
|----------|---------|
| **Identity** | EIN, OrgName, State, City, ZIP, TaxYear, TaxPeriodEnd, FormType, FormationYr, Mission |
| **Workforce** | Employees, Volunteers |
| **Revenue** | GrossReceipts, TotalRevenueCY/PY, ContributionsGrantsCY/PY, ProgramServiceRevCY/PY, InvestmentIncomeCY, OtherRevenueCY, GovernmentGrantsAmt |
| **Expenses** | TotalExpensesCY/PY, SalariesCY, FundraisingExpCY, ProgramSvcExpenses |
| **Net** | NetRevenueCY/PY |
| **Balance Sheet** | TotalAssetsEOY/BOY, TotalLiabilitiesEOY/BOY, NetAssetsEOY/BOY |
| **Meta** | SourceFile |

### 3.4 Key Data Statistics (2020 file sample)

| Metric | Min | Median | Mean | Max |
|--------|-----|--------|------|-----|
| TotalRevenueCY | $1.0M | $3.3M | $7.8M | $80.0M |
| TotalExpensesCY | $10.6K | $3.1M | $7.3M | $96.5M |
| ContributionsGrantsCY | $0 | $1.3M | $3.3M | $78.5M |
| TotalAssetsEOY | $0 | $4.1M | $15.8M | $1.66B |
| NetAssetsEOY | -$967M | $2.5M | $10.0M | $1.08B |
| Employees | 0 | 45 | 120 | 6,397 |

**GovernmentGrantsAmt** is null for 46% of rows (1,282 of 2,773 in 2020 file) — this is expected since not all nonprofits receive government grants.

---

## 4. Solution Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA PIPELINE (Module 1)                      │
│  Raw CSVs → Clean → Merge → Feature Engineering → Master Table  │
└─────────────┬───────────────────────────────────────────────────┘
              │
    ┌─────────┼─────────┬──────────────┬──────────────┐
    ▼         ▼         ▼              ▼              ▼
┌────────┐ ┌────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐
│Module 2│ │Module 3│ │  Module 4  │ │  Module 5  │ │ Module 6 │
│  Peer  │ │Resili- │ │   Risk     │ │High-Impact │ │Dashboard │
│Benchmrk│ │ence    │ │Simulation  │ │ Discovery  │ │& Story   │
│        │ │Predict │ │            │ │            │ │          │
└────────┘ └────────┘ └────────────┘ └────────────┘ └──────────┘
```

**Tech Stack:**
- **Language:** Python 3.10+
- **Data:** pandas, numpy
- **ML:** scikit-learn, XGBoost (or LightGBM)
- **Visualization:** plotly, matplotlib, seaborn
- **Dashboard:** Streamlit (or Plotly Dash)
- **Notebook:** Jupyter for EDA and model development

---

## 5. Module 1: Data Ingestion & Feature Engineering

### 5.1 Purpose

Load all three CSV files, clean them, merge into a single master DataFrame, and compute derived financial metrics that power all downstream modules.

### 5.2 Step-by-Step Implementation

#### Step 1: Load and Concatenate CSVs

```python
import pandas as pd
import numpy as np

files = [
    'data/data_csv/2019_990.csv',
    'data/data_csv/2020_990.csv',
    'data/data_csv/2021_990.csv'
]
df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
```

#### Step 2: Deduplicate

Some EIN+TaxYear combinations may appear in multiple CSV files (the files overlap on tax years). Keep the most recent filing:

```python
df = df.sort_values('TaxPeriodEnd', ascending=False)
df = df.drop_duplicates(subset=['EIN', 'TaxYear'], keep='first')
```

#### Step 3: Data Cleaning

```python
# Convert TaxYear and FormationYr to integers
df['TaxYear'] = pd.to_numeric(df['TaxYear'], errors='coerce').astype('Int64')
df['FormationYr'] = pd.to_numeric(df['FormationYr'], errors='coerce').astype('Int64')

# Fill GovernmentGrantsAmt nulls with 0 (absence = no government grants)
df['GovernmentGrantsAmt'] = df['GovernmentGrantsAmt'].fillna(0)

# Remove rows where TotalRevenueCY is null or zero (can't compute ratios)
df = df[df['TotalRevenueCY'].notna() & (df['TotalRevenueCY'] != 0)]

# Ensure no negative employees/volunteers
df['Employees'] = df['Employees'].clip(lower=0)
df['Volunteers'] = df['Volunteers'].clip(lower=0)
```

#### Step 4: Compute Derived Features

These are the **engineered features** that power all four analytical modules. Each feature has a clear financial interpretation.

##### 4a. Revenue Composition Ratios

These tell us *where the money comes from* — critical for understanding dependency risk.

```python
# What fraction of revenue comes from contributions/grants?
# High values (>0.8) = heavy donor dependency
df['GrantDependencyPct'] = df['ContributionsGrantsCY'] / df['TotalRevenueCY']

# What fraction comes from program services (earned revenue)?
# Higher = more self-sustaining
df['ProgramRevenuePct'] = df['ProgramServiceRevCY'] / df['TotalRevenueCY']

# What fraction comes from investments?
df['InvestmentRevenuePct'] = df['InvestmentIncomeCY'] / df['TotalRevenueCY']

# What fraction comes from government grants specifically?
df['GovGrantPct'] = df['GovernmentGrantsAmt'] / df['TotalRevenueCY']
```

**Why these matter:** A nonprofit that gets 90% of revenue from one source is fragile. Revenue diversification is a key resilience indicator.

##### 4b. Expense Efficiency Ratios

These tell us *how well the money is spent*.

```python
# Program Expense Ratio: what % of spending goes to actual programs?
# Industry standard: >75% is good, <65% raises questions
df['ProgramExpenseRatio'] = df['ProgramSvcExpenses'] / df['TotalExpensesCY']

# Fundraising Efficiency: what % of spending goes to fundraising?
# Lower is generally better; >25% is a red flag
df['FundraisingRatio'] = df['FundraisingExpCY'] / df['TotalExpensesCY']

# Salary Ratio: what % of spending is salaries?
df['SalaryRatio'] = df['SalariesCY'] / df['TotalExpensesCY']
```

##### 4c. Financial Health Indicators

```python
# Surplus Margin: is the org running a surplus or deficit?
# Positive = surplus, negative = deficit
# Healthy range: 0% to 10%
df['SurplusMargin'] = df['NetRevenueCY'] / df['TotalRevenueCY']

# Operating Reserve Months: how many months could the org survive
# with no new revenue? (Net Assets / Monthly Expenses)
# 3-6 months is healthy; <1 month is critical
df['OperatingReserveMonths'] = np.where(
    df['TotalExpensesCY'] > 0,
    df['NetAssetsEOY'] / (df['TotalExpensesCY'] / 12),
    np.nan
)

# Debt Ratio: what fraction of assets are financed by debt?
# Lower is better; >0.5 means more debt than equity
df['DebtRatio'] = np.where(
    df['TotalAssetsEOY'] > 0,
    df['TotalLiabilitiesEOY'] / df['TotalAssetsEOY'],
    np.nan
)

# Current Ratio proxy (Assets / Liabilities)
# >1.0 means assets exceed liabilities
df['AssetLiabilityRatio'] = np.where(
    df['TotalLiabilitiesEOY'] > 0,
    df['TotalAssetsEOY'] / df['TotalLiabilitiesEOY'],
    np.nan
)
```

##### 4d. Growth & Trend Metrics

```python
# Revenue Growth: year-over-year change
# Positive = growing, negative = shrinking
df['RevenueGrowthPct'] = np.where(
    df['TotalRevenuePY'].abs() > 0,
    (df['TotalRevenueCY'] - df['TotalRevenuePY']) / df['TotalRevenuePY'].abs(),
    np.nan
)

# Expense Growth
df['ExpenseGrowthPct'] = np.where(
    df['TotalExpensesPY'].abs() > 0,
    (df['TotalExpensesCY'] - df['TotalExpensesPY']) / df['TotalExpensesPY'].abs(),
    np.nan
)

# Contribution Growth
df['ContributionGrowthPct'] = np.where(
    df['ContributionsGrantsPY'].abs() > 0,
    (df['ContributionsGrantsCY'] - df['ContributionsGrantsPY']) / df['ContributionsGrantsPY'].abs(),
    np.nan
)

# Net Asset Growth (balance sheet health trend)
df['NetAssetGrowthPct'] = np.where(
    df['NetAssetsBOY'].abs() > 0,
    (df['NetAssetsEOY'] - df['NetAssetsBOY']) / df['NetAssetsBOY'].abs(),
    np.nan
)
```

##### 4e. Organization Characteristics

```python
# Organization Age
df['OrgAge'] = df['TaxYear'] - df['FormationYr']
df['OrgAge'] = df['OrgAge'].clip(lower=0)  # no negative ages

# Size Category based on total revenue
df['SizeCategory'] = pd.cut(
    df['TotalRevenueCY'],
    bins=[0, 500_000, 1_000_000, 5_000_000, 10_000_000, 50_000_000, float('inf')],
    labels=['<500K', '500K-1M', '1M-5M', '5M-10M', '10M-50M', '50M+']
)

# Revenue per Employee (productivity proxy)
df['RevenuePerEmployee'] = np.where(
    df['Employees'] > 0,
    df['TotalRevenueCY'] / df['Employees'],
    np.nan
)
```

##### 4f. Clip Extreme Outliers

```python
# Cap ratio features at reasonable bounds to prevent model distortion
ratio_cols = [
    'GrantDependencyPct', 'ProgramRevenuePct', 'InvestmentRevenuePct',
    'GovGrantPct', 'ProgramExpenseRatio', 'FundraisingRatio', 'SalaryRatio',
    'SurplusMargin', 'DebtRatio'
]
for col in ratio_cols:
    df[col] = df[col].clip(-2, 2)  # allow some negative but cap extremes

df['OperatingReserveMonths'] = df['OperatingReserveMonths'].clip(-120, 120)
df['RevenueGrowthPct'] = df['RevenueGrowthPct'].clip(-5, 5)
df['ExpenseGrowthPct'] = df['ExpenseGrowthPct'].clip(-5, 5)
```

#### Step 5: Save the Master Table

```python
df.to_csv('data/master_990.csv', index=False)
print(f"Master table: {len(df)} rows, {len(df.columns)} columns")
```

### 5.3 Output

A single `master_990.csv` file with ~30,000+ rows and ~50+ columns (36 original + ~15 engineered features) that serves as input to all downstream modules.

---

## 6. Module 2: Peer Benchmarking Framework

### 6.1 Purpose

Compare any nonprofit's financial health to a **meaningful peer group** — organizations that are similar enough that comparison is fair. This directly addresses the judging criterion: *"does the team define the baseline or peer nonprofits?"*

### 6.2 Defining Peer Groups

A peer group is defined by **three dimensions**:

| Dimension | How We Segment | Rationale |
|-----------|---------------|-----------|
| **Sector/Mission** | K-means clustering on Mission text (TF-IDF) OR manual NTEE code grouping | Comparing a hospital to a food bank is meaningless |
| **Size** | Revenue-based size buckets: <500K, 500K-1M, 1M-5M, 5M-10M, 10M-50M, 50M+ | A $50M org operates differently than a $500K org |
| **Geography** | State-level grouping | Cost of living and funding landscapes vary by state |

#### Step 1: Create Sector Clusters from Mission Text

Since we don't have NTEE codes in the data, we derive sector from the `Mission` field:

```python
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

# Clean mission text
missions = df['Mission'].fillna('').str.lower().str.strip()

# TF-IDF vectorization (convert text to numbers)
tfidf = TfidfVectorizer(max_features=500, stop_words='english', min_df=5)
mission_vectors = tfidf.fit_transform(missions)

# Cluster into ~15-20 sector groups
kmeans = KMeans(n_clusters=15, random_state=42, n_init=10)
df['SectorCluster'] = kmeans.fit_predict(mission_vectors)

# Manually inspect top terms per cluster to assign labels
for i in range(15):
    cluster_missions = missions[df['SectorCluster'] == i]
    # Look at most common words to name each cluster
    # e.g., Cluster 0 = "Education", Cluster 1 = "Healthcare", etc.
```

**Alternative (simpler) approach:** Use keyword matching on Mission text:

```python
def classify_sector(mission):
    m = str(mission).lower()
    if any(w in m for w in ['school', 'education', 'student', 'university', 'college']):
        return 'Education'
    elif any(w in m for w in ['health', 'hospital', 'medical', 'clinic', 'patient']):
        return 'Healthcare'
    elif any(w in m for w in ['housing', 'shelter', 'homeless']):
        return 'Housing & Shelter'
    elif any(w in m for w in ['food', 'hunger', 'meal', 'nutrition']):
        return 'Food & Nutrition'
    elif any(w in m for w in ['art', 'museum', 'cultural', 'theater', 'music']):
        return 'Arts & Culture'
    elif any(w in m for w in ['environment', 'conservation', 'wildlife', 'nature']):
        return 'Environment'
    elif any(w in m for w in ['youth', 'child', 'children', 'kid']):
        return 'Youth Services'
    elif any(w in m for w in ['church', 'faith', 'ministry', 'religious', 'worship']):
        return 'Religious'
    elif any(w in m for w in ['community', 'civic', 'neighborhood']):
        return 'Community Development'
    elif any(w in m for w in ['research', 'science', 'technology']):
        return 'Research & Science'
    else:
        return 'Other/General'

df['Sector'] = df['Mission'].apply(classify_sector)
```

#### Step 2: Assign Peer Group ID

```python
# Each org's peer group = Sector + SizeCategory + State
df['PeerGroupID'] = df['Sector'] + '_' + df['SizeCategory'].astype(str) + '_' + df['State']
```

#### Step 3: Compute Peer Benchmarks

For each peer group, compute the 25th, 50th (median), and 75th percentile of key metrics:

```python
benchmark_metrics = [
    'ProgramExpenseRatio', 'FundraisingRatio', 'SurplusMargin',
    'OperatingReserveMonths', 'DebtRatio', 'GrantDependencyPct',
    'ProgramRevenuePct', 'RevenueGrowthPct', 'RevenuePerEmployee'
]

peer_stats = df.groupby('PeerGroupID')[benchmark_metrics].describe(
    percentiles=[0.25, 0.5, 0.75]
)

# For each org, compute a Z-score relative to their peer group
for metric in benchmark_metrics:
    group_mean = df.groupby('PeerGroupID')[metric].transform('mean')
    group_std = df.groupby('PeerGroupID')[metric].transform('std')
    df[f'{metric}_ZScore'] = (df[metric] - group_mean) / group_std.replace(0, np.nan)
```

#### Step 4: Flag Deviations

```python
# Flag orgs that are >1.5 standard deviations from peer median
for metric in benchmark_metrics:
    z_col = f'{metric}_ZScore'
    df[f'{metric}_Flag'] = np.where(
        df[z_col].abs() > 1.5,
        np.where(df[z_col] > 0, 'Above Peer Norm', 'Below Peer Norm'),
        'Within Norm'
    )
```

### 6.3 Output

- **Peer Group Summary Table:** For each peer group, median and IQR of all benchmark metrics.
- **Individual Org Scorecard:** For any EIN, show where it stands vs. peers on every metric (percentile rank + flag).
- **Top Performers List:** Orgs in the top 10% of their peer group on program efficiency + surplus margin.

### 6.4 Visualization

- **Radar/Spider Chart:** Show one org's metrics vs. peer median across 6-8 dimensions.
- **Box Plots:** Distribution of each metric within a peer group, with the selected org highlighted.
- **Heatmap:** Peer group × metric showing which sectors/sizes are strongest/weakest.

---

## 7. Module 3: Resilience Prediction Model

### 7.1 Purpose

Build a predictive model/scoring system that identifies which nonprofits are most likely to remain financially stable during funding fluctuations. This is the **core ML component**.

### 7.2 Defining "Resilience" (The Target Variable)

Since we don't have a direct "this org failed" label, we must **construct the target variable** from observable financial outcomes. We define resilience as a composite of observable financial health indicators:

#### Approach A: Binary Classification — "At Risk" vs. "Stable"

An organization is labeled **"At Risk" (1)** if ANY of these are true:
- `SurplusMargin < -0.10` (running a deficit of more than 10%)
- `OperatingReserveMonths < 1` (less than 1 month of reserves)
- `NetAssetGrowthPct < -0.20` (net assets declined by more than 20%)
- `RevenueGrowthPct < -0.25` (revenue dropped by more than 25%)

Otherwise labeled **"Stable" (0)**.

```python
df['AtRisk'] = (
    (df['SurplusMargin'] < -0.10) |
    (df['OperatingReserveMonths'] < 1) |
    (df['NetAssetGrowthPct'] < -0.20) |
    (df['RevenueGrowthPct'] < -0.25)
).astype(int)

print(f"At Risk: {df['AtRisk'].mean():.1%}")
```

#### Approach B: Continuous Resilience Score (0–100)

A weighted composite score (no ML needed — rule-based):

| Component | Max Points | Calculation |
|-----------|-----------|-------------|
| Operating Reserves | 30 | min(OperatingReserveMonths / 12, 1) × 30 |
| Revenue Diversification | 20 | (1 − GrantDependencyPct) × 20 |
| Program Efficiency | 20 | ProgramExpenseRatio × 20 |
| Surplus Margin | 15 | clip(SurplusMargin × 100, 0, 15) |
| Low Debt | 15 | max((1 − DebtRatio) × 15, 0) |
| **Total** | **100** | |

```python
df['ResilienceScore'] = (
    np.clip(df['OperatingReserveMonths'] / 12, 0, 1) * 30 +
    np.clip(1 - df['GrantDependencyPct'], 0, 1) * 20 +
    np.clip(df['ProgramExpenseRatio'], 0, 1) * 20 +
    np.clip(df['SurplusMargin'] * 100, 0, 15) +
    np.clip((1 - df['DebtRatio']) * 15, 0, 15)
).round(1)
```

**Recommendation:** Use **both**. The Resilience Score is interpretable for the dashboard. The binary "At Risk" label is the ML classification target.

### 7.3 Feature Selection

Features for the ML model (input variables — what the model uses to predict):

```python
feature_cols = [
    # Revenue composition
    'GrantDependencyPct', 'ProgramRevenuePct', 'InvestmentRevenuePct', 'GovGrantPct',
    # Expense efficiency
    'ProgramExpenseRatio', 'FundraisingRatio', 'SalaryRatio',
    # Financial health
    'SurplusMargin', 'OperatingReserveMonths', 'DebtRatio', 'AssetLiabilityRatio',
    # Growth trends
    'RevenueGrowthPct', 'ExpenseGrowthPct', 'ContributionGrowthPct', 'NetAssetGrowthPct',
    # Org characteristics
    'OrgAge', 'Employees',
    # Scale (log-transformed to handle skew)
    'LogRevenue', 'LogAssets'
]

# Log-transform skewed dollar amounts
df['LogRevenue'] = np.log1p(df['TotalRevenueCY'].clip(lower=0))
df['LogAssets'] = np.log1p(df['TotalAssetsEOY'].clip(lower=0))
```

### 7.4 Exploratory Data Analysis (EDA) — Do This Before Modeling

This step is critical for the judging criterion: *"What EDA led to this choice?"*

#### EDA Checklist:

1. **Distribution plots** for every feature (histograms + box plots)
2. **Correlation heatmap** — which features are highly correlated? (drop redundant ones)
3. **Target variable balance** — what % is At Risk vs. Stable? If imbalanced (>70/30), use SMOTE or class weights.
4. **Feature vs. Target** — box plots of each feature split by AtRisk=0 vs. AtRisk=1. Which features show the biggest separation?
5. **Missing value analysis** — which features have >20% missing? Decide: impute or drop.
6. **Outlier analysis** — scatter plots of key features; identify and handle extreme values.

```python
import matplotlib.pyplot as plt
import seaborn as sns

# Correlation heatmap
plt.figure(figsize=(14, 10))
corr = df[feature_cols].corr()
sns.heatmap(corr, annot=True, fmt='.2f', cmap='RdBu_r', center=0)
plt.title('Feature Correlation Matrix')
plt.tight_layout()
plt.savefig('outputs/eda_correlation_heatmap.png')

# Target balance
print(df['AtRisk'].value_counts(normalize=True))

# Feature importance preview: box plots
fig, axes = plt.subplots(4, 4, figsize=(20, 16))
for ax, col in zip(axes.flat, feature_cols[:16]):
    df.boxplot(column=col, by='AtRisk', ax=ax)
    ax.set_title(col)
plt.tight_layout()
plt.savefig('outputs/eda_feature_vs_target.png')
```

### 7.5 Model Training

#### Step 1: Prepare Data

```python
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

# Drop rows with missing target
model_df = df[df['AtRisk'].notna()].copy()

X = model_df[feature_cols]
y = model_df['AtRisk']

# Impute missing values with median
imputer = SimpleImputer(strategy='median')
X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=feature_cols, index=X.index)

# Scale features (important for logistic regression; optional for tree models)
scaler = StandardScaler()
X_scaled = pd.DataFrame(scaler.fit_transform(X_imputed), columns=feature_cols, index=X.index)

# Train/test split (80/20)
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.2, random_state=42, stratify=y
)
```

#### Step 2: Train Multiple Models and Compare

```python
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import (
    classification_report, roc_auc_score, confusion_matrix,
    precision_recall_curve, roc_curve
)
import xgboost as xgb

models = {
    'Logistic Regression': LogisticRegression(
        class_weight='balanced', max_iter=1000, random_state=42
    ),
    'Random Forest': RandomForestClassifier(
        n_estimators=200, class_weight='balanced', random_state=42
    ),
    'Gradient Boosting': GradientBoostingClassifier(
        n_estimators=200, learning_rate=0.1, max_depth=5, random_state=42
    ),
    'XGBoost': xgb.XGBClassifier(
        n_estimators=200, learning_rate=0.1, max_depth=5,
        scale_pos_weight=(y_train == 0).sum() / (y_train == 1).sum(),
        random_state=42, eval_metric='logloss'
    )
}

results = {}
for name, model in models.items():
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]

    auc = roc_auc_score(y_test, y_prob)
    report = classification_report(y_test, y_pred, output_dict=True)

    results[name] = {
        'AUC-ROC': auc,
        'Precision (At Risk)': report['1']['precision'],
        'Recall (At Risk)': report['1']['recall'],
        'F1 (At Risk)': report['1']['f1-score'],
        'Accuracy': report['accuracy']
    }
    print(f"\n{name}:")
    print(f"  AUC-ROC: {auc:.4f}")
    print(classification_report(y_test, y_pred))

results_df = pd.DataFrame(results).T
print(results_df.to_string())
```

#### Step 3: Feature Importance Analysis

```python
# Use the best-performing model (likely XGBoost or Random Forest)
best_model = models['XGBoost']  # or whichever scored highest

# Feature importance
importances = pd.Series(
    best_model.feature_importances_, index=feature_cols
).sort_values(ascending=False)

plt.figure(figsize=(10, 8))
importances.plot(kind='barh')
plt.title('Feature Importance — Resilience Prediction')
plt.xlabel('Importance Score')
plt.tight_layout()
plt.savefig('outputs/feature_importance.png')
```

#### Step 4: Cross-Validation

```python
from sklearn.model_selection import cross_val_score

cv_scores = cross_val_score(best_model, X_scaled, y, cv=5, scoring='roc_auc')
print(f"5-Fold CV AUC: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
```

### 7.6 Model Justification (for judges)

Document why you chose the final model:

1. **EDA showed** that features like OperatingReserveMonths and SurplusMargin have the strongest separation between At Risk and Stable groups.
2. **Tree-based models** (XGBoost/Random Forest) outperform logistic regression because the relationships are non-linear (e.g., reserves matter more below 3 months than above 12).
3. **Class weighting** was used because At Risk orgs are a minority class.
4. **Feature importance** confirms financial intuition: reserves, surplus margin, and grant dependency are top predictors.

### 7.7 Output

- **Trained model** saved as a pickle file
- **Resilience Score** (0–100) for every org in the dataset
- **Risk Classification** (At Risk / Stable) with probability
- **Feature importance ranking** with business interpretation
- **Threshold analysis:** At what Resilience Score does the probability of being At Risk exceed 50%?

---

## 8. Module 4: Financial Risk Simulation

### 8.1 Purpose

Simulate "what if" funding shock scenarios to assess nonprofit vulnerability and model recovery pathways. This answers: *"What happens if government grants drop 30%?"*

### 8.2 Revenue Stream Classification

First, classify each org's revenue by type using the available columns:

```python
df['Rev_Contributions'] = df['ContributionsGrantsCY'] - df['GovernmentGrantsAmt']
df['Rev_GovGrants'] = df['GovernmentGrantsAmt']
df['Rev_ProgramService'] = df['ProgramServiceRevCY']
df['Rev_Investment'] = df['InvestmentIncomeCY']
df['Rev_Other'] = df['OtherRevenueCY']

# Verify: these should sum to approximately TotalRevenueCY
df['Rev_Sum_Check'] = (
    df['Rev_Contributions'] + df['Rev_GovGrants'] +
    df['Rev_ProgramService'] + df['Rev_Investment'] + df['Rev_Other']
)
```

### 8.3 Shock Scenarios

Define a set of realistic funding shock scenarios:

| Scenario | Description | Implementation |
|----------|-------------|----------------|
| **Grant Shock 30%** | 30% reduction in all contributions/grants | Reduce ContributionsGrantsCY by 30% |
| **Gov Grant Shock 50%** | 50% cut in government grants | Reduce GovernmentGrantsAmt by 50% |
| **Program Revenue Shock 25%** | 25% drop in program service revenue (e.g., pandemic) | Reduce ProgramServiceRevCY by 25% |
| **Investment Shock 40%** | 40% drop in investment income (market crash) | Reduce InvestmentIncomeCY by 40% |
| **Combined Recession** | 20% drop in all revenue streams simultaneously | Reduce TotalRevenueCY by 20% |

#### Implementation:

```python
def simulate_shock(df, scenario_name, adjustments):
    """
    Simulate a funding shock and compute post-shock financials.

    Parameters:
    - df: master DataFrame
    - scenario_name: string label for the scenario
    - adjustments: dict of {column_name: multiplier}
      e.g., {'ContributionsGrantsCY': 0.70} means 30% reduction

    Returns: DataFrame with post-shock columns added
    """
    sim = df.copy()

    # Apply revenue adjustments
    total_loss = 0
    for col, multiplier in adjustments.items():
        original = sim[col].fillna(0)
        shocked = original * multiplier
        loss = original - shocked
        total_loss += loss
        sim[f'PostShock_{col}'] = shocked

    # Post-shock total revenue
    sim['PostShock_TotalRevenue'] = sim['TotalRevenueCY'] - total_loss

    # Post-shock net revenue (revenue minus expenses, expenses unchanged)
    sim['PostShock_NetRevenue'] = sim['PostShock_TotalRevenue'] - sim['TotalExpensesCY']

    # Post-shock surplus margin
    sim['PostShock_SurplusMargin'] = np.where(
        sim['PostShock_TotalRevenue'] > 0,
        sim['PostShock_NetRevenue'] / sim['PostShock_TotalRevenue'],
        np.nan
    )

    # Months of reserves to cover the deficit
    sim['MonthsToInsolvency'] = np.where(
        sim['PostShock_NetRevenue'] < 0,
        sim['NetAssetsEOY'] / (sim['PostShock_NetRevenue'].abs() / 12),
        np.inf  # not insolvent
    )
    sim['MonthsToInsolvency'] = sim['MonthsToInsolvency'].clip(lower=0, upper=120)

    # Classification
    sim['PostShock_Status'] = np.where(
        sim['PostShock_NetRevenue'] >= 0, 'Survives (Surplus)',
        np.where(
            sim['MonthsToInsolvency'] > 12, 'Stressed (>12mo reserves)',
            np.where(
                sim['MonthsToInsolvency'] > 3, 'At Risk (3-12mo reserves)',
                'Critical (<3mo reserves)'
            )
        )
    )

    sim['Scenario'] = scenario_name
    return sim

# Run all scenarios
scenarios = {
    'Grant Shock (-30%)': {'ContributionsGrantsCY': 0.70},
    'Gov Grant Shock (-50%)': {'GovernmentGrantsAmt': 0.50},
    'Program Rev Shock (-25%)': {'ProgramServiceRevCY': 0.75},
    'Investment Shock (-40%)': {'InvestmentIncomeCY': 0.60},
    'Combined Recession (-20%)': {
        'ContributionsGrantsCY': 0.80,
        'ProgramServiceRevCY': 0.80,
        'InvestmentIncomeCY': 0.80,
        'GovernmentGrantsAmt': 0.80
    }
}

all_sims = []
for name, adjustments in scenarios.items():
    sim_result = simulate_shock(df, name, adjustments)
    all_sims.append(sim_result)

sim_df = pd.concat(all_sims, ignore_index=True)
```

### 8.4 Recovery Pathway Modeling

For organizations that fall into deficit under a shock, estimate how long recovery takes:

```python
def estimate_recovery(row, annual_recovery_rate=0.05):
    """
    Given a post-shock deficit, estimate years to recover assuming
    the org can grow revenue by `annual_recovery_rate` per year
    while holding expenses flat.
    """
    if row['PostShock_NetRevenue'] >= 0:
        return 0  # no recovery needed

    deficit = abs(row['PostShock_NetRevenue'])
    revenue = row['PostShock_TotalRevenue']
    expenses = row['TotalExpensesCY']

    years = 0
    cumulative_surplus = 0
    while cumulative_surplus < deficit and years < 20:
        years += 1
        revenue *= (1 + annual_recovery_rate)
        annual_surplus = revenue - expenses
        if annual_surplus > 0:
            cumulative_surplus += annual_surplus

    return years if years < 20 else None  # None = may not recover

sim_df['RecoveryYears'] = sim_df.apply(estimate_recovery, axis=1)
```

### 8.5 Output

- **Vulnerability Matrix:** For each scenario × peer group, what % of orgs are Critical / At Risk / Stressed / Surviving.
- **Individual Org Stress Test:** For any EIN, show post-shock financials under each scenario.
- **Recovery Timeline:** Estimated years to recover for each org under each scenario.
- **Threshold Discovery:** At what grant dependency level does a 30% grant shock become fatal? (e.g., "Orgs with >70% grant dependency and <3 months reserves have 80% chance of going critical under a 30% grant shock.")

### 8.6 Visualization

- **Waterfall chart:** Show revenue breakdown before/after shock for a selected org.
- **Sankey diagram:** Flow of orgs from pre-shock status to post-shock status.
- **Scatter plot:** Grant Dependency % (x) vs. Months to Insolvency (y), colored by post-shock status.

---

## 9. Module 5: High-Impact Discovery ("Hidden Gems")

### 9.1 Purpose

Identify nonprofits that deliver **disproportionate community value relative to their budget** — organizations where a donation can create outsized impact.

### 9.2 Defining "Impact Efficiency"

Since we don't have direct outcome data (lives saved, students graduated), we use financial proxies for impact:

#### Impact Efficiency Score (composite):

| Component | Weight | Metric | Rationale |
|-----------|--------|--------|-----------|
| Program Efficiency | 25% | ProgramExpenseRatio | Higher = more money goes to programs |
| Growth Trajectory | 20% | RevenueGrowthPct | Growing orgs are expanding their reach |
| Leverage Ratio | 20% | ProgramSvcExpenses / ContributionsGrantsCY | How much program spending per dollar of donations |
| Community Reach | 15% | (Employees + Volunteers) / TotalRevenueCY × 1M | People mobilized per $1M revenue |
| Financial Sustainability | 20% | ResilienceScore (from Module 3) | Sustainable orgs deliver long-term impact |

```python
# Normalize each component to 0-1 scale using percentile rank
from scipy.stats import percentileofscore

def percentile_rank(series):
    return series.rank(pct=True)

df['Impact_ProgramEff'] = percentile_rank(df['ProgramExpenseRatio'])
df['Impact_Growth'] = percentile_rank(df['RevenueGrowthPct'])

df['ProgramLeverage'] = np.where(
    df['ContributionsGrantsCY'] > 0,
    df['ProgramSvcExpenses'] / df['ContributionsGrantsCY'],
    np.nan
)
df['Impact_Leverage'] = percentile_rank(df['ProgramLeverage'])

df['CommunityReach'] = (df['Employees'].fillna(0) + df['Volunteers'].fillna(0)) / (df['TotalRevenueCY'] / 1_000_000)
df['Impact_Reach'] = percentile_rank(df['CommunityReach'])

df['Impact_Sustainability'] = percentile_rank(df['ResilienceScore'])

# Weighted composite
df['ImpactEfficiencyScore'] = (
    0.25 * df['Impact_ProgramEff'] +
    0.20 * df['Impact_Growth'] +
    0.20 * df['Impact_Leverage'] +
    0.15 * df['Impact_Reach'] +
    0.20 * df['Impact_Sustainability']
) * 100
```

### 9.3 Identifying "Hidden Gems"

A **Hidden Gem** is an org that scores high on Impact Efficiency but is **small or mid-sized** (not already well-known/well-funded):

```python
# Hidden Gems: High impact efficiency + small/mid revenue + positive growth
hidden_gems = df[
    (df['ImpactEfficiencyScore'] > df['ImpactEfficiencyScore'].quantile(0.80)) &
    (df['TotalRevenueCY'] < df['TotalRevenueCY'].quantile(0.50)) &
    (df['RevenueGrowthPct'] > 0) &
    (df['ResilienceScore'] > 40)  # not at immediate risk
].sort_values('ImpactEfficiencyScore', ascending=False)

print(f"Hidden Gems identified: {len(hidden_gems)}")
```

### 9.4 "Donation Tipping Point" Analysis

For each hidden gem, estimate the donation amount that would move them to the next resilience tier:

```python
def donation_tipping_point(row):
    """
    Calculate how much additional funding would bring this org's
    operating reserves from current level to 6 months.
    """
    current_reserves_months = row['OperatingReserveMonths']
    monthly_expenses = row['TotalExpensesCY'] / 12

    if current_reserves_months >= 6:
        return 0  # already healthy

    months_needed = 6 - max(current_reserves_months, 0)
    donation_needed = months_needed * monthly_expenses
    return round(donation_needed, 0)

hidden_gems['DonationToStabilize'] = hidden_gems.apply(donation_tipping_point, axis=1)
```

### 9.5 Output

- **Hidden Gems Leaderboard:** Top 50 orgs ranked by Impact Efficiency Score, with their sector, state, revenue, and donation tipping point.
- **Impact vs. Budget Scatter:** All orgs plotted with budget (x) vs. impact score (y), hidden gems highlighted.
- **Donation ROI Table:** For each hidden gem, show "a $X donation would bring reserves from Y months to 6 months."

---

## 10. Module 6: Dashboard & Storytelling

### 10.1 Purpose

Present all insights through an interactive dashboard that a non-technical funder or nonprofit leader can use. This addresses the 20% Business Storytelling criterion.

### 10.2 Dashboard Pages (Streamlit)

#### Page 1: Executive Overview
- Total nonprofits analyzed, by state and sector
- Distribution of Resilience Scores (histogram)
- Key stat cards: % At Risk, % Thriving, Average Resilience Score
- Map visualization: average resilience by state

#### Page 2: Peer Benchmarking Tool
- **Inputs:** Select a specific org (by name or EIN), or select a peer group
- **Output:** Radar chart comparing org to peer median; table of all metrics with percentile ranks and flags
- Box plots showing where the org falls within its peer distribution

#### Page 3: Resilience Explorer
- Scatter plot: Resilience Score vs. Revenue, colored by sector
- Feature importance bar chart from the ML model
- Threshold table: "If your operating reserves are below X months, you have Y% probability of financial distress"
- Filterable table of all orgs with their resilience scores and risk classifications

#### Page 4: Stress Test Simulator
- **Inputs:** Select a scenario (or create custom: choose revenue stream and % reduction)
- **Output:** Before/after waterfall chart; vulnerability breakdown pie chart
- Aggregate view: what % of orgs in each sector survive each scenario

#### Page 5: Hidden Gems Finder
- **Inputs:** Filter by state, sector, size range
- **Output:** Ranked table of hidden gems with Impact Efficiency Score, donation tipping point
- Scatter plot: budget vs. impact with highlighted gems

### 10.3 Implementation Skeleton

```python
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Nonprofit Resilience Analytics", layout="wide")

# Load data
@st.cache_data
def load_data():
    return pd.read_csv('data/master_990.csv')

df = load_data()

# Sidebar navigation
page = st.sidebar.selectbox("Navigate", [
    "Executive Overview",
    "Peer Benchmarking",
    "Resilience Explorer",
    "Stress Test Simulator",
    "Hidden Gems Finder"
])

if page == "Executive Overview":
    st.title("Nonprofit Financial Resilience Dashboard")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Nonprofits", f"{len(df):,}")
    col2.metric("% At Risk", f"{df['AtRisk'].mean():.1%}")
    col3.metric("Avg Resilience Score", f"{df['ResilienceScore'].mean():.1f}")
    col4.metric("States Covered", df['State'].nunique())

    # Resilience distribution
    fig = px.histogram(df, x='ResilienceScore', nbins=50,
                       title='Distribution of Resilience Scores')
    st.plotly_chart(fig, use_container_width=True)

    # Map
    state_avg = df.groupby('State')['ResilienceScore'].mean().reset_index()
    fig_map = px.choropleth(
        state_avg, locations='State', locationmode='USA-states',
        color='ResilienceScore', scope='usa',
        title='Average Resilience Score by State'
    )
    st.plotly_chart(fig_map, use_container_width=True)

# ... (similar implementation for other pages)
```

### 10.4 Presentation Narrative Structure

For the final presentation (slides), follow this story arc:

1. **The Problem** (1 slide): Nonprofits operate in the dark about their financial resilience.
2. **Our Approach** (1 slide): Four-module analytics platform using 7 years of IRS 990 data.
3. **Key Finding 1 — Peer Benchmarking** (2 slides): "We identified X peer groups. Here's how sectors compare."
4. **Key Finding 2 — Resilience Drivers** (2 slides): "The #1 predictor of resilience is operating reserves. Orgs with <3 months reserves are 4x more likely to be at risk."
5. **Key Finding 3 — Stress Test Results** (2 slides): "Under a 30% grant shock, X% of orgs become critical. Government-grant-dependent orgs are most vulnerable."
6. **Key Finding 4 — Hidden Gems** (2 slides): "We found X hidden gems. A $Y average donation could stabilize Z organizations."
7. **Recommendations for Fairlight Advisors** (1 slide): Actionable next steps.
8. **Demo** (live dashboard walkthrough).

---

## 11. Evaluation & Success Criteria

### 11.1 Model Evaluation Metrics

| Metric | Target | Why |
|--------|--------|-----|
| AUC-ROC | > 0.75 | Overall discrimination ability |
| Precision (At Risk) | > 0.60 | When we say "at risk," we want to be right |
| Recall (At Risk) | > 0.70 | We want to catch most at-risk orgs |
| F1 (At Risk) | > 0.65 | Balance of precision and recall |
| 5-Fold CV AUC | > 0.72 | Ensures model generalizes |

### 11.2 Business Evaluation

- **Peer groups make intuitive sense** — a hospital is grouped with hospitals, not food banks.
- **Resilience scores align with known outcomes** — spot-check orgs with very low scores to confirm they show financial distress signals.
- **Stress test results are plausible** — orgs heavily dependent on grants should be most affected by grant shocks.
- **Hidden gems are genuinely small, efficient, and growing** — not just data artifacts.

### 11.3 Validation Approach

Since we have multi-year data, use **temporal validation**:
- Train the model on 2016–2018 data
- Predict 2019–2020 outcomes
- Check: did orgs we predicted as "At Risk" in 2018 actually show financial deterioration in 2019–2020?

```python
# Temporal validation
train_df = df[df['TaxYear'] <= 2018]
test_df = df[df['TaxYear'] >= 2019]

# Train on earlier years, predict on later years
# This is the most honest evaluation for time-series financial data
```

---

## 12. Implementation Roadmap

### Phase 1: Data Pipeline (Estimated: 3–4 hours)

| Step | Task | Output |
|------|------|--------|
| 1.1 | Load and concatenate all 3 CSV files | Combined DataFrame |
| 1.2 | Deduplicate EIN+TaxYear combinations | Clean DataFrame |
| 1.3 | Handle missing values and data types | Cleaned DataFrame |
| 1.4 | Compute all derived features (Section 5.4) | `master_990.csv` |
| 1.5 | Initial EDA: distributions, correlations, missing values | EDA notebook/plots |

### Phase 2: Peer Benchmarking (Estimated: 2–3 hours)

| Step | Task | Output |
|------|------|--------|
| 2.1 | Classify sectors from Mission text | Sector column |
| 2.2 | Define peer groups (Sector × Size × State) | PeerGroupID column |
| 2.3 | Compute peer group statistics (median, IQR) | Peer stats table |
| 2.4 | Compute Z-scores and deviation flags | Benchmark columns |
| 2.5 | Build radar chart and box plot visualizations | Benchmark visuals |

### Phase 3: Resilience Model (Estimated: 3–4 hours)

| Step | Task | Output |
|------|------|--------|
| 3.1 | Define target variable (AtRisk binary + ResilienceScore) | Target columns |
| 3.2 | Full EDA on features vs. target | EDA plots |
| 3.3 | Train 4 models, compare metrics | Model comparison table |
| 3.4 | Select best model, analyze feature importance | Final model + importance plot |
| 3.5 | Cross-validation and temporal validation | Validation metrics |
| 3.6 | Threshold analysis | Threshold table |

### Phase 4: Risk Simulation (Estimated: 2–3 hours)

| Step | Task | Output |
|------|------|--------|
| 4.1 | Classify revenue streams | Revenue breakdown columns |
| 4.2 | Implement shock simulation function | `simulate_shock()` |
| 4.3 | Run all 5 scenarios | Simulation results table |
| 4.4 | Recovery pathway estimation | Recovery years column |
| 4.5 | Vulnerability threshold analysis | Threshold findings |

### Phase 5: Hidden Gems (Estimated: 2 hours)

| Step | Task | Output |
|------|------|--------|
| 5.1 | Compute Impact Efficiency Score components | Score columns |
| 5.2 | Identify hidden gems (high impact + small budget) | Hidden gems list |
| 5.3 | Donation tipping point analysis | Tipping point table |

### Phase 6: Dashboard & Presentation (Estimated: 3–4 hours)

| Step | Task | Output |
|------|------|--------|
| 6.1 | Build Streamlit app with 5 pages | `app.py` |
| 6.2 | Create all interactive visualizations | Dashboard |
| 6.3 | Prepare presentation slides | Slide deck |
| 6.4 | Practice narrative and demo | Presentation ready |

**Total Estimated Time: 15–20 hours**

---

## 13. Appendix: Column Data Dictionary

### Original Columns (from CSV)

| Column | Type | Description |
|--------|------|-------------|
| `EIN` | string | Employer Identification Number — unique ID for each nonprofit |
| `OrgName` | string | Legal name of the organization |
| `State` | string | 2-letter state abbreviation |
| `City` | string | City name |
| `ZIP` | string | ZIP code |
| `TaxYear` | int | The tax year this filing covers (e.g., 2018) |
| `TaxPeriodEnd` | date | End date of the tax period (e.g., 2019-06-30) |
| `FormType` | string | Always "990" in this dataset |
| `FormationYr` | int | Year the organization was formed/incorporated |
| `Mission` | string | Free-text description of the organization's mission |
| `Employees` | float | Total number of employees |
| `Volunteers` | float | Total number of volunteers |
| `GrossReceipts` | float | Total gross receipts (all money received) |
| `TotalRevenueCY` | float | Total revenue for the current (filing) year |
| `TotalRevenuePY` | float | Total revenue for the prior year |
| `ContributionsGrantsCY` | float | Contributions and grants received — current year |
| `ContributionsGrantsPY` | float | Contributions and grants received — prior year |
| `ProgramServiceRevCY` | float | Revenue from program services (earned income) — current year |
| `ProgramServiceRevPY` | float | Revenue from program services — prior year |
| `InvestmentIncomeCY` | float | Income from investments — current year |
| `OtherRevenueCY` | float | Other revenue — current year |
| `GovernmentGrantsAmt` | float | Government grants specifically (subset of contributions). NULL = not reported / not applicable |
| `TotalExpensesCY` | float | Total expenses — current year |
| `TotalExpensesPY` | float | Total expenses — prior year |
| `SalariesCY` | float | Salaries, compensation, and employee benefits — current year |
| `FundraisingExpCY` | float | Fundraising expenses — current year |
| `ProgramSvcExpenses` | float | Total program service expenses — current year |
| `NetRevenueCY` | float | Revenue minus expenses — current year (positive = surplus) |
| `NetRevenuePY` | float | Revenue minus expenses — prior year |
| `TotalAssetsEOY` | float | Total assets at end of year |
| `TotalAssetsBOY` | float | Total assets at beginning of year |
| `TotalLiabilitiesEOY` | float | Total liabilities at end of year |
| `TotalLiabilitiesBOY` | float | Total liabilities at beginning of year |
| `NetAssetsEOY` | float | Net assets (assets minus liabilities) at end of year |
| `NetAssetsBOY` | float | Net assets at beginning of year |
| `SourceFile` | string | Name of the XML file this record was parsed from |

### Engineered Features (computed in Module 1)

| Feature | Formula | Interpretation |
|---------|---------|----------------|
| `GrantDependencyPct` | ContributionsGrantsCY / TotalRevenueCY | % of revenue from grants/donations. High = fragile |
| `ProgramRevenuePct` | ProgramServiceRevCY / TotalRevenueCY | % of revenue earned from programs. High = self-sustaining |
| `InvestmentRevenuePct` | InvestmentIncomeCY / TotalRevenueCY | % of revenue from investments |
| `GovGrantPct` | GovernmentGrantsAmt / TotalRevenueCY | % of revenue from government grants |
| `ProgramExpenseRatio` | ProgramSvcExpenses / TotalExpensesCY | % of spending on programs. >75% is good |
| `FundraisingRatio` | FundraisingExpCY / TotalExpensesCY | % of spending on fundraising. <15% is good |
| `SalaryRatio` | SalariesCY / TotalExpensesCY | % of spending on salaries |
| `SurplusMargin` | NetRevenueCY / TotalRevenueCY | Profit margin equivalent. Positive = surplus |
| `OperatingReserveMonths` | NetAssetsEOY / (TotalExpensesCY / 12) | Months the org could survive with no revenue |
| `DebtRatio` | TotalLiabilitiesEOY / TotalAssetsEOY | Fraction of assets financed by debt |
| `AssetLiabilityRatio` | TotalAssetsEOY / TotalLiabilitiesEOY | Assets per dollar of liabilities |
| `RevenueGrowthPct` | (CY − PY) / |PY| | Year-over-year revenue change |
| `ExpenseGrowthPct` | (CY − PY) / |PY| | Year-over-year expense change |
| `ContributionGrowthPct` | (CY − PY) / |PY| | Year-over-year contribution change |
| `NetAssetGrowthPct` | (EOY − BOY) / |BOY| | Balance sheet health trend |
| `OrgAge` | TaxYear − FormationYr | Years since formation |
| `SizeCategory` | Revenue-based bins | <500K, 500K-1M, 1M-5M, 5M-10M, 10M-50M, 50M+ |
| `RevenuePerEmployee` | TotalRevenueCY / Employees | Productivity proxy |
| `LogRevenue` | log(1 + TotalRevenueCY) | Log-transformed revenue for modeling |
| `LogAssets` | log(1 + TotalAssetsEOY) | Log-transformed assets for modeling |
| `ResilienceScore` | Weighted composite (0–100) | Overall financial resilience rating |
| `AtRisk` | Binary (0/1) | Classification target for ML model |

---

## File Structure

```
aggie_hacks_2026/
├── PRD.md                          # This document
├── data/
│   ├── data_csv/
│   │   ├── 2019_990.csv            # Raw data (TY 2016-2018)
│   │   ├── 2020_990.csv            # Raw data (TY 2017-2019)
│   │   └── 2021_990.csv            # Raw data (TY 2018-2020)
│   └── master_990.csv              # Output of Module 1
├── notebooks/
│   ├── 01_data_pipeline.ipynb      # Module 1: Load, clean, feature engineering
│   ├── 02_eda.ipynb                # Exploratory Data Analysis
│   ├── 03_peer_benchmarking.ipynb  # Module 2: Peer groups and benchmarks
│   ├── 04_resilience_model.ipynb   # Module 3: ML model training
│   ├── 05_risk_simulation.ipynb    # Module 4: Shock scenarios
│   └── 06_hidden_gems.ipynb        # Module 5: Impact discovery
├── src/
│   ├── data_pipeline.py            # Module 1 as reusable functions
│   ├── peer_benchmark.py           # Module 2 functions
│   ├── resilience_model.py         # Module 3 functions
│   ├── risk_simulation.py          # Module 4 functions
│   └── hidden_gems.py              # Module 5 functions
├── app.py                          # Module 6: Streamlit dashboard
├── outputs/
│   ├── eda_correlation_heatmap.png
│   ├── feature_importance.png
│   └── ...                         # All generated plots
├── models/
│   └── resilience_model.pkl        # Saved trained model
├── parse_990.py                    # Existing XML parser
└── requirements.txt                # Python dependencies
```

### requirements.txt

```
pandas>=2.0
numpy>=1.24
scikit-learn>=1.3
xgboost>=2.0
matplotlib>=3.7
seaborn>=0.12
plotly>=5.15
streamlit>=1.28
scipy>=1.11
```
