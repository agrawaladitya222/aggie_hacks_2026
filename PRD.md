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

**Goal:** Build an end-to-end analytics solution that uses IRS **Form 990** (standard full form) data spanning **tax years 2018–2024** (seven years) to help nonprofit leaders, funders, and capacity builders answer three questions:

1. **Who is thriving?** — Identify financially durable nonprofits and the factors that make them resilient.
2. **Who is at risk?** — Detect organizations vulnerable to funding shocks and identify intervention thresholds.
3. **Who deserves attention?** — Surface "hidden gem" nonprofits where a donation can create outsized community impact.

The solution consists of four analytical modules (Peer Benchmarking, Resilience Prediction, Financial Risk Simulation, High-Impact Discovery) supported by a data pipeline and presented through an interactive dashboard.

**Target User:** Fairlight Advisors and similar nonprofit capacity-building consultancies who advise funders on where to allocate philanthropic capital.

**Current Starting Point:** Eight pre-parsed CSV files totaling ~362,000 rows (before deduplication) are already in `data/data_csv/`. Each file already includes an `NTEE_CD` column (sector classification codes) — no additional joining or XML parsing is needed. Additional 2024-era extract files may be added later and will be automatically picked up by the pipeline.

---

## 2. Business Context & Problem Definition

### 2.1 The Nonprofit Landscape Problem

The U.S. nonprofit sector has hundreds of thousands of public charities. Despite IRS Form 990 being publicly available, nonprofit leaders and funders lack **accessible, decision-ready tools** to:
- Assess financial resilience
- Benchmark against peers
- Identify where targeted support has the greatest impact

**Scope:** This project focuses on **Form 990** (standard full form) filers — U.S. 501(c)(3) public charities. We exclude Form 990-EZ (short form for smaller orgs) and Form 990-PF (private foundations), as specified in the hackathon problem statement.

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

| Category | Criteria | Weight | How We Address It |
|----------|----------|--------|-------------------|
| **Business Insights (40%)** | Peer Benchmarking (10pts) | 10% | Module 2 — explicit peer group definition by NTEE sector, size, geography |
| | Business Solution (10pts) | 10% | Clear problem definition, objectives, success criteria in this PRD |
| | Financial Insights (10pts) | 10% | Revenue decomposition, reserve analysis, shock modeling |
| | Depth of Solution (10pts) | 10% | Four interconnected modules with composite scoring |
| **Data Analysis (20%)** | Tool Accuracy & Precision (10pts) | 10% | Transparent feature engineering, validated against raw data; code matches stated insights |
| | Model Development (10pts) | 10% | EDA-driven model selection with justification and metrics; feature selection with business intuition |
| **Solution Development (20%)** | Results (10pts) | 10% | Clear visualizations, threshold tables, actionable recommendations |
| | Level of Insights (10pts) | 10% | Non-obvious findings: hidden gems, tipping points, recovery pathways; insights beyond intuition |
| **Business Storytelling (20%)** | Presentation & Narrative (20pts) | 20% | Interactive dashboard + engaging presentation; lead with business impact, not technical methods |

---

## 3. Data Overview

### 3.1 Source Files

**All data lives in `data/data_csv/`** as pre-parsed CSV files extracted from IRS Form 990 XML filings (990 full form only — 990-EZ and 990-PF excluded). Each file represents a single IRS bulk-download release batch. File names follow the pattern `YYYY_990.csv` or `YYYY_N_990.csv`, where `YYYY` is the IRS release year and `N` is the batch number within that release.

**Important:** The IRS release year in the filename does *not* equal the tax year of the filings inside. Each file can contain filings spanning two to three different tax years. The pipeline concatenates all files and deduplicates by `(EIN, TaxYear)`.

| File | Rows | TaxYears Contained | Notes |
|------|------|--------------------|-------|
| `2019_990.csv` | 5,308 | 2016 (22), 2017 (2,843), 2018 (2,443) | Oldest batch |
| `2020_990.csv` | 2,773 | 2017 (31), 2018 (2,654), 2019 (88) | Small batch |
| `2021_990.csv` | 24,374 | 2018 (96), 2019 (10,632), 2020 (13,646) | |
| `2022_1_990.csv` | 103,926 | 2018 (216), 2019 (26,653), 2020 (61,850), 2021 (15,207) | Largest single batch |
| `2022_2_990.csv` | 14,401 | 2019 (131), 2020 (8,548), 2021 (5,722) | |
| `2023_1_990.csv` | 104,159 | 2020 (1,189), 2021 (46,795), 2022 (56,175) | |
| `2023_2_990.csv` | 3,787 | 2020 (21), 2021 (81), 2022 (3,685) | Small supplemental |
| `2025_990.csv` | 103,456 | 2021 (9), 2022 (1,124), 2023 (37,754), 2024 (64,569) | Most recent; contains 2024 data |
| **Total (pre-dedup)** | **362,184** | | |
| **Total (post-dedup)** | **344,265** | **2016–2024** | After keeping latest filing per EIN+TaxYear |

**Future additions:** Additional 2024 extract files may be added to `data/data_csv/` following the same naming convention. The pipeline's glob pattern (`data/data_csv/*_990.csv` or `data/data_csv/*990*.csv`) will automatically pick them up. No code changes should be needed.

### 3.2 Seven-Year Analysis Panel

The hackathon calls for "seven years of Form 990 data." After concatenation and dedup, we filter to **TaxYear 2018–2024** — the seven most recent years with meaningful data volume:

| TaxYear | Rows (post-dedup) |
|---------|-------------------|
| 2018 | 5,343 |
| 2019 | 30,192 |
| 2020 | 76,698 |
| 2021 | 67,097 |
| 2022 | 60,418 |
| 2023 | 37,409 |
| 2024 | 64,214 |
| **Total** | **~341,371** |

TaxYears 2016 (22 rows) and 2017 (2,872 rows) are excluded from the analysis panel due to very low coverage but are retained in the raw load for completeness.

**Note on volume imbalance:** TaxYear 2018 has far fewer filings (~5K) than other years (~30–77K). This is because the 2018 tax-year filings were captured by fewer IRS release batches in our dataset. Keep this in mind during temporal analyses — 2018 is useful for trend context but should not be weighted equally.

### 3.3 Data Structure

Each row = one nonprofit (identified by EIN) for one tax year. Every row contains **Current Year (CY)** and **Prior Year (PY)** figures as reported on the Form 990, effectively giving two years of financial data per filing.

**37 columns** in each CSV (see [Appendix](#13-appendix-column-data-dictionary) for full definitions). All files share the same schema.

### 3.4 Key Data Statistics (post-dedup, full panel)

| Metric | Min | Median | Mean | Max |
|--------|-----|--------|------|-----|
| TotalRevenueCY | $1.0M | $3.1M | $7.7M | $80.0M |
| TotalExpensesCY | -$353M | $2.7M | $7.1M | $1.38B |
| ContributionsGrantsCY | -$3.5M | $1.1M | $3.1M | $80.4M |
| TotalAssetsEOY | -$98.1M | $4.5M | $20.1M | $10.1B |
| NetAssetsEOY | -$1.30B | $2.9M | $11.9M | $10.1B |
| Employees | 0 | 23 | 85 | 999,999 |

**Data quality flags visible in these stats:**
- **Negative TotalExpensesCY** and negative asset values exist → need to handle in cleaning (see Module 1, Step 3).
- **Employees max = 999,999** → sentinel/placeholder value → cap or null out during cleaning.
- **GovernmentGrantsAmt** is null for a large fraction of rows — expected since not all nonprofits receive government grants (fill with 0).

### 3.5 NTEE Code Coverage

Every CSV already includes an `NTEE_CD` column (sector classification codes pre-joined from IRS TEOS data). No additional NTEE lookup or joining step is needed.

| File | NTEE Match Rate |
|------|-----------------|
| `2019_990.csv` | 4,152 / 5,308 (78.2%) |
| `2020_990.csv` | 2,149 / 2,773 (77.5%) |
| `2021_990.csv` | 16,528 / 24,374 (67.8%) |
| `2022_1_990.csv` | 71,916 / 103,926 (69.2%) |
| `2022_2_990.csv` | 9,963 / 14,401 (69.2%) |
| `2023_1_990.csv` | 73,108 / 104,159 (70.2%) |
| `2023_2_990.csv` | 2,650 / 3,787 (70.0%) |
| `2025_990.csv` | 74,957 / 103,456 (72.5%) |
| **Combined** | **255,423 / 362,184 (70.5%)** |

For the ~30% of records without an NTEE code, we use Mission-text keyword classification as a fallback (see Module 2, Section 6.2).

### 3.6 Entity Coverage Summary

- **135,062 unique EINs** across the full dataset
- **59 states/territories** represented
- **Top 5 states:** CA (38,726), NY (29,356), TX (19,201), PA (16,767), FL (16,072)
- **EIN multi-year appearances:**
  - 1 year only: 32,888 EINs (24%)
  - 2 years: 30,715 EINs (23%)
  - 3 years: 40,326 EINs (30%)
  - 4 years: 27,067 EINs (20%)
  - 5+ years: 4,066 EINs (3%)

**Implication for modeling:** ~73% of EINs appear in 2+ years, providing meaningful longitudinal signal for trend features (revenue growth, net asset change). The 24% with only 1 year of data can still be analyzed cross-sectionally but will lack CY vs. PY intra-filing growth metrics for validation across filings.

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

**Dependencies:** Module 1 must run first. Modules 2–4 depend on Module 1 output and can be developed in parallel. Module 5 depends on Module 3 (uses the ResilienceScore). Module 6 depends on all other modules.

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

Load all CSV files from `data/data_csv/`, clean them, merge into a single master DataFrame, filter to the **2018–2024** analysis panel, derive sector labels from the pre-existing `NTEE_CD` column (with Mission-text fallback), and compute derived financial metrics that power all downstream modules.

### 5.2 Inputs & Outputs

- **Input:** All `*990*.csv` files in `data/data_csv/` (currently 8 files, ~362K rows)
- **Output:** `data/master_990.csv` — a single deduplicated, cleaned, feature-enriched CSV (~341K rows, ~55+ columns)

### 5.3 Step-by-Step Implementation

#### Step 1: Load and Concatenate CSVs

```python
import pandas as pd
import numpy as np
import glob

files = sorted(glob.glob('data/data_csv/*990*.csv'))
print(f"Found {len(files)} files: {[f.split('/')[-1] for f in files]}")

df = pd.concat([pd.read_csv(f, low_memory=False) for f in files], ignore_index=True)
print(f"Combined: {len(df)} rows")
```

**Why `*990*.csv`?** This glob pattern matches both `YYYY_990.csv` and `YYYY_N_990.csv` naming conventions, and will also pick up any future files following either pattern (e.g., `2024_1_990.csv`).

#### Step 2: Deduplicate

Some EIN+TaxYear combinations appear in multiple CSV files (the IRS release batches overlap on tax years). Keep the most recent filing:

```python
df = df.sort_values('TaxPeriodEnd', ascending=False)
df = df.drop_duplicates(subset=['EIN', 'TaxYear'], keep='first')
print(f"After dedup: {len(df)} rows, {df['EIN'].nunique()} unique EINs")
```

#### Step 3: Filter to Analysis Panel

```python
df['TaxYear'] = pd.to_numeric(df['TaxYear'], errors='coerce').astype('Int64')

# Keep 2018–2024 (seven-year panel)
df = df[df['TaxYear'].between(2018, 2024)]
print(f"After panel filter (2018–2024): {len(df)} rows")
print(df['TaxYear'].value_counts().sort_index())
```

#### Step 4: Data Cleaning

```python
df['FormationYr'] = pd.to_numeric(df['FormationYr'], errors='coerce').astype('Int64')

# GovernmentGrantsAmt: null means no government grants received
df['GovernmentGrantsAmt'] = df['GovernmentGrantsAmt'].fillna(0)

# Remove rows where TotalRevenueCY is null or zero (can't compute ratios)
df = df[df['TotalRevenueCY'].notna() & (df['TotalRevenueCY'] != 0)]

# Cap clearly invalid Employees values (999999 = sentinel)
df.loc[df['Employees'] > 50000, 'Employees'] = np.nan
df['Employees'] = df['Employees'].clip(lower=0)
df['Volunteers'] = df['Volunteers'].clip(lower=0)

# Flag and handle negative TotalExpensesCY (data entry errors)
neg_expenses_count = (df['TotalExpensesCY'] < 0).sum()
print(f"Rows with negative TotalExpensesCY: {neg_expenses_count} — setting to NaN")
df.loc[df['TotalExpensesCY'] < 0, 'TotalExpensesCY'] = np.nan

# Remove rows with null TotalExpensesCY after correction (can't compute expense ratios)
df = df[df['TotalExpensesCY'].notna() & (df['TotalExpensesCY'] > 0)]

print(f"After cleaning: {len(df)} rows")
```

#### Step 5: Compute Derived Features

These are the **engineered features** that power all four analytical modules. Each feature has a clear financial interpretation.

##### 5a. Revenue Composition Ratios

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

##### 5b. Expense Efficiency Ratios

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

##### 5c. Financial Health Indicators

```python
# Surplus Margin: is the org running a surplus or deficit?
# Positive = surplus, negative = deficit. Healthy range: 0% to 10%
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

##### 5d. Growth & Trend Metrics

These leverage the CY/PY (Current Year / Prior Year) pairs on each Form 990 filing.

```python
# Revenue Growth: year-over-year change
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

##### 5e. Organization Characteristics

```python
# Organization Age
df['OrgAge'] = df['TaxYear'] - df['FormationYr']
df['OrgAge'] = df['OrgAge'].clip(lower=0)

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

# Log-transform skewed dollar amounts for modeling
df['LogRevenue'] = np.log1p(df['TotalRevenueCY'].clip(lower=0))
df['LogAssets'] = np.log1p(df['TotalAssetsEOY'].clip(lower=0))
```

##### 5f. Sector Classification (from pre-existing NTEE_CD)

The `NTEE_CD` column is already present in every CSV. We map it to human-readable sector labels and fall back to Mission-text keywords for the ~30% of rows missing NTEE.

```python
NTEE_SECTOR_MAP = {
    'A': 'Arts, Culture & Humanities',
    'B': 'Education',
    'C': 'Environment & Animals',
    'D': 'Environment & Animals',
    'E': 'Healthcare',
    'F': 'Mental Health & Crisis',
    'G': 'Diseases & Medical Research',
    'H': 'Diseases & Medical Research',
    'I': 'Crime & Legal',
    'J': 'Employment & Jobs',
    'K': 'Food, Agriculture & Nutrition',
    'L': 'Housing & Shelter',
    'M': 'Public Safety & Disaster Relief',
    'N': 'Recreation & Sports',
    'O': 'Youth Development',
    'P': 'Human Services',
    'Q': 'International Affairs',
    'R': 'Civil Rights & Advocacy',
    'S': 'Community Improvement',
    'T': 'Philanthropy & Grantmaking',
    'U': 'Science & Technology',
    'V': 'Social Science Research',
    'W': 'Public Policy',
    'X': 'Religion',
    'Y': 'Mutual Benefit',
    'Z': 'Unknown / Unclassified',
}

def sector_from_ntee(ntee_code):
    if pd.isna(ntee_code) or len(str(ntee_code).strip()) == 0:
        return None
    return NTEE_SECTOR_MAP.get(str(ntee_code).strip()[0].upper(), 'Other')

def classify_sector_from_mission(mission):
    m = str(mission).lower()
    if any(w in m for w in ['school', 'education', 'student', 'university', 'college']):
        return 'Education'
    elif any(w in m for w in ['health', 'hospital', 'medical', 'clinic', 'patient']):
        return 'Healthcare'
    elif any(w in m for w in ['housing', 'shelter', 'homeless']):
        return 'Housing & Shelter'
    elif any(w in m for w in ['food', 'hunger', 'meal', 'nutrition']):
        return 'Food, Agriculture & Nutrition'
    elif any(w in m for w in ['art', 'museum', 'cultural', 'theater', 'music']):
        return 'Arts, Culture & Humanities'
    elif any(w in m for w in ['environment', 'conservation', 'wildlife', 'nature']):
        return 'Environment & Animals'
    elif any(w in m for w in ['youth', 'child', 'children', 'kid']):
        return 'Youth Development'
    elif any(w in m for w in ['church', 'faith', 'ministry', 'religious', 'worship']):
        return 'Religion'
    elif any(w in m for w in ['community', 'civic', 'neighborhood']):
        return 'Community Improvement'
    elif any(w in m for w in ['research', 'science', 'technology']):
        return 'Science & Technology'
    else:
        return 'Human Services'

df['Sector'] = df['NTEE_CD'].apply(sector_from_ntee)
mask_no_sector = df['Sector'].isna()
df.loc[mask_no_sector, 'Sector'] = df.loc[mask_no_sector, 'Mission'].apply(
    classify_sector_from_mission
)

# NTEE major group as a categorical feature for modeling
df['NTEEMajorGroup'] = df['NTEE_CD'].str[0].str.upper().where(df['NTEE_CD'].notna())
```

##### 5g. Clip Extreme Outliers

```python
ratio_cols = [
    'GrantDependencyPct', 'ProgramRevenuePct', 'InvestmentRevenuePct',
    'GovGrantPct', 'ProgramExpenseRatio', 'FundraisingRatio', 'SalaryRatio',
    'SurplusMargin', 'DebtRatio'
]
for col in ratio_cols:
    df[col] = df[col].clip(-2, 2)

df['OperatingReserveMonths'] = df['OperatingReserveMonths'].clip(-120, 120)
df['RevenueGrowthPct'] = df['RevenueGrowthPct'].clip(-5, 5)
df['ExpenseGrowthPct'] = df['ExpenseGrowthPct'].clip(-5, 5)
```

#### Step 6: Save the Master Table

```python
df.to_csv('data/master_990.csv', index=False)
print(f"Master table: {len(df)} rows, {len(df.columns)} columns")
print(f"TaxYear range: {df['TaxYear'].min()} – {df['TaxYear'].max()}")
print(f"Unique EINs: {df['EIN'].nunique()}")
```

### 5.4 Validation Checklist (before moving to Module 2)

Run these checks after building the master table to catch issues early:

| # | Check | Expected | Action if Failed |
|---|-------|----------|-----------------|
| 1 | No duplicate (EIN, TaxYear) pairs | 0 duplicates | Re-run dedup |
| 2 | All TaxYear values in 2018–2024 | True | Re-run filter |
| 3 | All ratio columns between -2 and 2 | True | Re-run clipping |
| 4 | Every row has a non-null Sector | True | Debug fallback logic |
| 5 | TotalRevenueCY > 0 for all rows | True | Re-run cleaning filter |
| 6 | TotalExpensesCY > 0 for all rows | True | Re-run cleaning filter |
| 7 | Column count ≈ 55+ | True | Check feature engineering steps |
| 8 | No Employees > 50,000 | True | Re-run sentinel cap |

```python
assert df.duplicated(subset=['EIN', 'TaxYear']).sum() == 0, "Duplicates found!"
assert df['TaxYear'].between(2018, 2024).all(), "TaxYear out of range!"
assert df['Sector'].notna().all(), "Missing Sector values!"
assert (df['TotalRevenueCY'] > 0).all(), "Non-positive revenue rows!"
assert (df['TotalExpensesCY'] > 0).all(), "Non-positive expense rows!"
print("All validation checks passed.")
```

### 5.5 Output

A single `data/master_990.csv` file with ~340,000 rows and ~55+ columns (37 original + ~18 engineered features) that serves as input to all downstream modules.

---

## 6. Module 2: Peer Benchmarking Framework

### 6.1 Purpose

Compare any nonprofit's financial health to a **meaningful peer group** — organizations that are similar enough that comparison is fair. This directly addresses the judging criterion: *"does the team define the baseline or peer nonprofits?"*

### 6.2 Inputs & Outputs

- **Input:** `data/master_990.csv` (output of Module 1)
- **Output:** Updated master table with peer group IDs, Z-scores, and deviation flags; peer group summary statistics table

### 6.3 Defining Peer Groups

A peer group is defined by **three dimensions**:

| Dimension | How We Segment | Rationale |
|-----------|---------------|-----------|
| **Sector** | NTEE major category (primary); Mission-text keyword fallback for the ~30% of orgs missing NTEE | Comparing a hospital to a food bank is meaningless |
| **Size** | Revenue-based size buckets: <500K, 500K-1M, 1M-5M, 5M-10M, 10M-50M, 50M+ | A $50M org operates differently than a $500K org |
| **Geography** | State-level grouping | Cost of living and funding landscapes vary by state |

**Why NTEE first?** NTEE codes are IRS-assigned standard classifications that are consistent, auditable, and recognized industry-wide. Using them produces peer groups that judges and Fairlight Advisors will immediately understand (e.g., "E-series = Healthcare"). The Mission-text fallback (defined in Module 1, Step 5f) ensures full coverage.

### 6.4 Step-by-Step Implementation

#### Step 1: Load Master Table

```python
import pandas as pd
import numpy as np

df = pd.read_csv('data/master_990.csv', low_memory=False)
```

#### Step 2: Assign Peer Group ID

```python
df['PeerGroupID'] = df['Sector'] + '_' + df['SizeCategory'].astype(str) + '_' + df['State']
print(f"Unique peer groups: {df['PeerGroupID'].nunique()}")
```

**Peer group size check:** If any peer group has fewer than 5 members, it's too small for meaningful percentile comparisons. Merge undersized groups by dropping the State dimension (Sector + Size only) or the Size dimension (Sector + State only) — whichever produces a larger group.

```python
peer_counts = df['PeerGroupID'].value_counts()
small_groups = peer_counts[peer_counts < 5].index
print(f"Peer groups with <5 members: {len(small_groups)}")

# Fallback: use Sector + Size only for orgs in small peer groups
df['PeerGroupID_Fallback'] = df['Sector'] + '_' + df['SizeCategory'].astype(str)
df.loc[df['PeerGroupID'].isin(small_groups), 'PeerGroupID'] = (
    df.loc[df['PeerGroupID'].isin(small_groups), 'PeerGroupID_Fallback']
)
df = df.drop(columns=['PeerGroupID_Fallback'])
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
for metric in benchmark_metrics:
    z_col = f'{metric}_ZScore'
    df[f'{metric}_Flag'] = np.where(
        df[z_col].abs() > 1.5,
        np.where(df[z_col] > 0, 'Above Peer Norm', 'Below Peer Norm'),
        'Within Norm'
    )
```

#### Step 5: Compute Peer Percentile Ranks

```python
for metric in benchmark_metrics:
    df[f'{metric}_PeerPctile'] = df.groupby('PeerGroupID')[metric].rank(pct=True)
```

#### Step 6: Save Updated Master Table

```python
df.to_csv('data/master_990.csv', index=False)

# Also save peer group summary stats as a separate reference table
peer_summary = df.groupby('PeerGroupID')[benchmark_metrics].agg(['median', 'mean', 'std', 'count'])
peer_summary.to_csv('data/peer_group_stats.csv')
print(f"Peer stats saved: {len(peer_summary)} groups")
```

### 6.5 Output

- **Updated `data/master_990.csv`** with peer group ID, Z-scores, deviation flags, and percentile ranks for every org.
- **`data/peer_group_stats.csv`:** For each peer group, median, mean, std, and count for all benchmark metrics.

### 6.6 Visualization (build during Module 6, but design now)

- **Radar/Spider Chart:** Show one org's metrics vs. peer median across 6–8 dimensions.
- **Box Plots:** Distribution of each metric within a peer group, with the selected org highlighted.
- **Heatmap:** Peer group × metric showing which sectors/sizes are strongest/weakest.

---

## 7. Module 3: Resilience Prediction Model

### 7.1 Purpose

Build a predictive model/scoring system that identifies which nonprofits are most likely to remain financially stable during funding fluctuations. This is the **core ML component**.

### 7.2 Inputs & Outputs

- **Input:** `data/master_990.csv` (with peer benchmarks from Module 2)
- **Output:** Updated master table with `ResilienceScore` and `AtRisk` columns; trained model artifact saved as a joblib file; feature importance analysis

### 7.3 Defining "Resilience" (The Target Variable)

Since we don't have a direct "this org failed" label, we **construct the target variable** from observable financial outcomes. We define resilience through two complementary approaches:

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

**Use both.** The ResilienceScore is interpretable for the dashboard and presentation. The binary AtRisk label is the ML classification target.

### 7.4 Feature Selection

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
    'LogRevenue', 'LogAssets',
]

# NTEE major group as one-hot encoded features
ntee_dummies = pd.get_dummies(df['NTEEMajorGroup'], prefix='NTEE', dummy_na=False)
feature_cols += list(ntee_dummies.columns)
df = pd.concat([df, ntee_dummies], axis=1)
```

### 7.5 Exploratory Data Analysis (EDA) — Do This Before Modeling

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
corr = df[feature_cols[:19]].corr()  # exclude one-hot NTEE for readability
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

### 7.6 Model Training

#### Step 1: Prepare Data

```python
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.impute import SimpleImputer

model_df = df[df['AtRisk'].notna()].copy()

X = model_df[feature_cols]
y = model_df['AtRisk']

imputer = SimpleImputer(strategy='median')
X_imputed = pd.DataFrame(imputer.fit_transform(X), columns=feature_cols, index=X.index)

scaler = StandardScaler()
X_scaled = pd.DataFrame(scaler.fit_transform(X_imputed), columns=feature_cols, index=X.index)

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
best_model = models['XGBoost']  # or whichever scored highest

importances = pd.Series(
    best_model.feature_importances_, index=feature_cols
).sort_values(ascending=False)

plt.figure(figsize=(10, 8))
importances.head(20).plot(kind='barh')
plt.title('Top 20 Feature Importances — Resilience Prediction')
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

#### Step 5: Save Artifacts

```python
import joblib
import json

joblib.dump({
    'model': best_model,
    'imputer': imputer,
    'scaler': scaler,
    'feature_cols': feature_cols
}, 'artifacts/resilience_classifier.joblib')

metrics = {
    'best_model': 'XGBoost',
    'auc_roc': float(results_df.loc['XGBoost', 'AUC-ROC']),
    'cv_auc_mean': float(cv_scores.mean()),
    'cv_auc_std': float(cv_scores.std()),
    'feature_importances': importances.head(20).to_dict()
}
with open('artifacts/train_metrics.json', 'w') as f:
    json.dump(metrics, f, indent=2)
```

### 7.7 Model Justification (for judges)

Document why you chose the final model:

1. **EDA showed** that features like OperatingReserveMonths and SurplusMargin have the strongest separation between At Risk and Stable groups.
2. **Tree-based models** (XGBoost/Random Forest) outperform logistic regression because the relationships are non-linear (e.g., reserves matter more below 3 months than above 12).
3. **Class weighting** was used because At Risk orgs are a minority class.
4. **Feature importance** confirms financial intuition: reserves, surplus margin, and grant dependency are top predictors.

### 7.8 Output

- **Updated `data/master_990.csv`** with `ResilienceScore` (0–100) and `AtRisk` (0/1) for every org
- **`artifacts/resilience_classifier.joblib`:** Fitted model pipeline (model + imputer + scaler + feature list)
- **`artifacts/train_metrics.json`:** Performance metrics, feature importances, decision threshold
- **`outputs/feature_importance.png`** and **`outputs/eda_*.png`:** Visualizations

---

## 8. Module 4: Financial Risk Simulation

### 8.1 Purpose

Simulate "what if" funding shock scenarios to assess nonprofit vulnerability and model recovery pathways. This answers: *"What happens if government grants drop 30%?"*

### 8.2 Inputs & Outputs

- **Input:** `data/master_990.csv` (with ResilienceScore from Module 3)
- **Output:** Simulation results table (`data/simulation_results.csv`); vulnerability matrices by scenario and peer group

### 8.3 Revenue Stream Classification

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

### 8.4 Shock Scenarios

Define a set of realistic funding shock scenarios:

| Scenario | Description | Implementation |
|----------|-------------|----------------|
| **Grant Shock 30%** | 30% reduction in all contributions/grants | Reduce ContributionsGrantsCY by 30% |
| **Gov Grant Shock 50%** | 50% cut in government grants | Reduce GovernmentGrantsAmt by 50% |
| **Program Revenue Shock 25%** | 25% drop in program service revenue (e.g., pandemic) | Reduce ProgramServiceRevCY by 25% |
| **Investment Shock 40%** | 40% drop in investment income (market crash) | Reduce InvestmentIncomeCY by 40% |
| **Combined Recession** | 20% drop in all revenue streams simultaneously | Reduce all revenue columns by 20% |

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

    total_loss = 0
    for col, multiplier in adjustments.items():
        original = sim[col].fillna(0)
        shocked = original * multiplier
        loss = original - shocked
        total_loss += loss
        sim[f'PostShock_{col}'] = shocked

    sim['PostShock_TotalRevenue'] = sim['TotalRevenueCY'] - total_loss
    sim['PostShock_NetRevenue'] = sim['PostShock_TotalRevenue'] - sim['TotalExpensesCY']

    sim['PostShock_SurplusMargin'] = np.where(
        sim['PostShock_TotalRevenue'] > 0,
        sim['PostShock_NetRevenue'] / sim['PostShock_TotalRevenue'],
        np.nan
    )

    sim['MonthsToInsolvency'] = np.where(
        sim['PostShock_NetRevenue'] < 0,
        sim['NetAssetsEOY'] / (sim['PostShock_NetRevenue'].abs() / 12),
        np.inf
    )
    sim['MonthsToInsolvency'] = sim['MonthsToInsolvency'].clip(lower=0, upper=120)

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

### 8.5 Recovery Pathway Modeling

For organizations that fall into deficit under a shock, estimate how long recovery takes:

```python
def estimate_recovery(row, annual_recovery_rate=0.05):
    if row['PostShock_NetRevenue'] >= 0:
        return 0

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

    return years if years < 20 else None

sim_df['RecoveryYears'] = sim_df.apply(estimate_recovery, axis=1)
```

### 8.6 Threshold Discovery

This is where non-obvious insights emerge — critical for the "Level of Insights" judging criterion:

```python
# For the Grant Shock scenario, find the grant dependency threshold
# where the probability of going critical exceeds 50%
grant_shock = sim_df[sim_df['Scenario'] == 'Grant Shock (-30%)'].copy()
grant_shock['IsCritical'] = (grant_shock['PostShock_Status'] == 'Critical (<3mo reserves)').astype(int)

# Bin by GrantDependencyPct and compute critical rate
grant_shock['DepBucket'] = pd.cut(grant_shock['GrantDependencyPct'], bins=10)
threshold_analysis = grant_shock.groupby('DepBucket')['IsCritical'].mean()
print("Grant Dependency vs. Critical Rate:")
print(threshold_analysis)

# Cross-tabulate with OperatingReserveMonths for 2D threshold map
grant_shock['ReserveBucket'] = pd.cut(
    grant_shock['OperatingReserveMonths'],
    bins=[0, 1, 3, 6, 12, 120],
    labels=['<1mo', '1-3mo', '3-6mo', '6-12mo', '12mo+']
)
heatmap_data = grant_shock.pivot_table(
    values='IsCritical', index='DepBucket', columns='ReserveBucket', aggfunc='mean'
)
```

### 8.7 Save Simulation Results

```python
# Save a summary per scenario (not the full duplicated dataset)
summary_cols = ['EIN', 'OrgName', 'Sector', 'State', 'SizeCategory',
                'Scenario', 'PostShock_TotalRevenue', 'PostShock_NetRevenue',
                'PostShock_SurplusMargin', 'MonthsToInsolvency',
                'PostShock_Status', 'RecoveryYears']
sim_df[summary_cols].to_csv('data/simulation_results.csv', index=False)
```

### 8.8 Output

- **`data/simulation_results.csv`:** Post-shock financials for every org under each scenario.
- **Vulnerability Matrix:** For each scenario × peer group, what % of orgs are Critical / At Risk / Stressed / Surviving.
- **Threshold Discovery Table:** Grant dependency and reserve combinations mapped to critical rates.
- **Recovery Timeline:** Estimated years to recover for each org under each scenario.

### 8.9 Visualization (build during Module 6, but design now)

- **Waterfall chart:** Show revenue breakdown before/after shock for a selected org.
- **Sankey diagram:** Flow of orgs from pre-shock status to post-shock status.
- **Scatter plot:** Grant Dependency % (x) vs. Months to Insolvency (y), colored by post-shock status.

---

## 9. Module 5: High-Impact Discovery ("Hidden Gems")

### 9.1 Purpose

Identify nonprofits that deliver **disproportionate community value relative to their budget** — organizations where a donation can create outsized impact.

### 9.2 Inputs & Outputs

- **Input:** `data/master_990.csv` (with ResilienceScore from Module 3 and peer benchmarks from Module 2)
- **Output:** Hidden gems list; Impact Efficiency Scores appended to master table

### 9.3 Defining "Impact Efficiency"

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

df['CommunityReach'] = (
    df['Employees'].fillna(0) + df['Volunteers'].fillna(0)
) / (df['TotalRevenueCY'] / 1_000_000)
df['Impact_Reach'] = percentile_rank(df['CommunityReach'])

df['Impact_Sustainability'] = percentile_rank(df['ResilienceScore'])

df['ImpactEfficiencyScore'] = (
    0.25 * df['Impact_ProgramEff'] +
    0.20 * df['Impact_Growth'] +
    0.20 * df['Impact_Leverage'] +
    0.15 * df['Impact_Reach'] +
    0.20 * df['Impact_Sustainability']
) * 100
```

### 9.4 Identifying "Hidden Gems"

A **Hidden Gem** is an org that scores high on Impact Efficiency but is **small or mid-sized** (not already well-known/well-funded):

```python
hidden_gems = df[
    (df['ImpactEfficiencyScore'] > df['ImpactEfficiencyScore'].quantile(0.80)) &
    (df['TotalRevenueCY'] < df['TotalRevenueCY'].quantile(0.50)) &
    (df['RevenueGrowthPct'] > 0) &
    (df['ResilienceScore'] > 40)
].sort_values('ImpactEfficiencyScore', ascending=False)

print(f"Hidden Gems identified: {len(hidden_gems)}")
```

### 9.5 "Donation Tipping Point" Analysis

For each hidden gem, estimate the donation amount that would move them to the next resilience tier:

```python
def donation_tipping_point(row):
    current_reserves_months = row['OperatingReserveMonths']
    monthly_expenses = row['TotalExpensesCY'] / 12

    if current_reserves_months >= 6:
        return 0

    months_needed = 6 - max(current_reserves_months, 0)
    donation_needed = months_needed * monthly_expenses
    return round(donation_needed, 0)

hidden_gems['DonationToStabilize'] = hidden_gems.apply(donation_tipping_point, axis=1)
```

### 9.6 Save Results

```python
# Save hidden gems as a standalone leaderboard
gem_cols = ['EIN', 'OrgName', 'State', 'City', 'Sector', 'SizeCategory',
            'TotalRevenueCY', 'ImpactEfficiencyScore', 'ResilienceScore',
            'ProgramExpenseRatio', 'RevenueGrowthPct', 'OperatingReserveMonths',
            'DonationToStabilize', 'Mission']
hidden_gems[gem_cols].to_csv('data/hidden_gems.csv', index=False)

# Also save ImpactEfficiencyScore back to master table
df.to_csv('data/master_990.csv', index=False)
```

### 9.7 Output

- **`data/hidden_gems.csv`:** Top hidden gems ranked by Impact Efficiency Score, with sector, state, revenue, and donation tipping point.
- **Updated `data/master_990.csv`:** ImpactEfficiencyScore appended for all orgs.
- **Donation ROI Table:** For each hidden gem, "a $X donation would bring reserves from Y months to 6 months."

---

## 10. Module 6: Dashboard & Storytelling

### 10.1 Purpose

Present all insights through an interactive dashboard that a non-technical funder or nonprofit leader can use. This addresses the 20% Business Storytelling criterion.

### 10.2 Inputs

- `data/master_990.csv` (final version with all scores)
- `data/peer_group_stats.csv` (Module 2)
- `data/simulation_results.csv` (Module 4)
- `data/hidden_gems.csv` (Module 5)
- `artifacts/train_metrics.json` (Module 3)

### 10.3 Dashboard Pages (Streamlit)

#### Page 1: Executive Overview
- Total nonprofits analyzed, by state and NTEE sector
- Distribution of Resilience Scores (histogram)
- Key stat cards: % At Risk, % Thriving, Average Resilience Score
- Map visualization: average resilience by state

#### Page 2: Peer Benchmarking Tool
- **Inputs:** Select a specific org (by name or EIN), or select a peer group (by NTEE sector, size, state)
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

### 10.4 Implementation Skeleton

```python
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Nonprofit Resilience Analytics", layout="wide")

@st.cache_data
def load_data():
    return pd.read_csv('data/master_990.csv', low_memory=False)

df = load_data()

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

    fig = px.histogram(df, x='ResilienceScore', nbins=50,
                       title='Distribution of Resilience Scores')
    st.plotly_chart(fig, use_container_width=True)

    state_avg = df.groupby('State')['ResilienceScore'].mean().reset_index()
    fig_map = px.choropleth(
        state_avg, locations='State', locationmode='USA-states',
        color='ResilienceScore', scope='usa',
        title='Average Resilience Score by State'
    )
    st.plotly_chart(fig_map, use_container_width=True)

# ... (similar implementation for other pages)
```

### 10.5 Presentation Narrative Structure

For the final presentation (slides), follow this story arc:

1. **The Problem** (1 slide): Nonprofits operate in the dark about their financial resilience.
2. **Our Approach** (1 slide): Four-module analytics platform using **seven years** of IRS Form 990 data (**2018–2024**), enriched with NTEE sector classifications.
3. **Key Finding 1 — Peer Benchmarking** (2 slides): "We used NTEE codes to define X sector-based peer groups. Here's how sectors compare."
4. **Key Finding 2 — Resilience Drivers** (2 slides): "The #1 predictor of resilience is operating reserves. Orgs with <3 months reserves are Nx more likely to be at risk."
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

- **Peer groups make intuitive sense** — NTEE-based sectors ensure a hospital (E-series) is grouped with hospitals, not food banks (K-series). Mission-text fallback orgs should land in plausible sectors.
- **Resilience scores align with known outcomes** — spot-check orgs with very low scores to confirm they show financial distress signals.
- **Stress test results are plausible** — orgs heavily dependent on grants should be most affected by grant shocks.
- **Hidden gems are genuinely small, efficient, and growing** — not just data artifacts.

### 11.3 Temporal Validation Approach

Since we have multi-year data (2018–2024), use **temporal validation** to test whether the model's predictions hold over time:

- **Train** on earlier years in the panel (e.g., **2018–2021**)
- **Test/predict** on later years (e.g., **2022–2024**)
- **Check:** Did orgs flagged "At Risk" in the train era show deterioration in the test era?

This is the most honest evaluation for time-series financial data and directly demonstrates to judges that the model generalizes.

```python
train_df = df[df['TaxYear'] <= 2021]
test_df = df[df['TaxYear'] >= 2022]
print(f"Temporal split — Train: {len(train_df)} rows (2018–2021), Test: {len(test_df)} rows (2022–2024)")
```

**Fallback:** If class balance is poor in either split, adjust the boundary (e.g., train on 2018–2022, test on 2023–2024). Keep the principle: "train on past, test on future."

---

## 12. Implementation Roadmap

### Phase 1: Data Pipeline — Module 1 (Estimated: 2–3 hours)

| Step | Task | Output |
|------|------|--------|
| 1.1 | Load and concatenate all `*990*.csv` files | Combined DataFrame (~362K rows) |
| 1.2 | Deduplicate EIN+TaxYear combinations | Deduplicated DataFrame (~344K rows) |
| 1.3 | Filter to TaxYear 2018–2024 panel | Analysis DataFrame (~341K rows) |
| 1.4 | Handle missing values, data types, sentinels | Cleaned DataFrame |
| 1.5 | Compute all derived features (Section 5.3, Steps 5a–5g) | Feature-enriched DataFrame |
| 1.6 | Run validation checklist (Section 5.4) | All checks pass |
| 1.7 | Save `data/master_990.csv` | Master table on disk |
| 1.8 | Initial EDA: distributions, correlations, missing values | EDA notebook/plots |

**Prerequisite:** None — this is the starting module.

### Phase 2: Peer Benchmarking — Module 2 (Estimated: 2–3 hours)

| Step | Task | Output |
|------|------|--------|
| 2.1 | Load master table; assign PeerGroupID (Sector × Size × State) | PeerGroupID column |
| 2.2 | Handle small peer groups (<5 members) with fallback | Cleaned peer groups |
| 2.3 | Compute peer group statistics (median, IQR) | `data/peer_group_stats.csv` |
| 2.4 | Compute Z-scores, deviation flags, and percentile ranks | Benchmark columns |
| 2.5 | Save updated master table | Updated `data/master_990.csv` |
| 2.6 | Build radar chart and box plot visualizations | Benchmark visuals |

**Prerequisite:** Module 1 complete.

### Phase 3: Resilience Model — Module 3 (Estimated: 3–4 hours)

| Step | Task | Output |
|------|------|--------|
| 3.1 | Define target variable (AtRisk binary + ResilienceScore) | Target columns |
| 3.2 | Full EDA on features vs. target | EDA plots |
| 3.3 | Train 4 models, compare metrics | Model comparison table |
| 3.4 | Select best model, analyze feature importance | Final model + importance plot |
| 3.5 | Cross-validation and temporal validation | Validation metrics |
| 3.6 | Threshold analysis | Threshold table |
| 3.7 | Save model artifacts | `artifacts/` directory |

**Prerequisite:** Module 2 complete (peer Z-scores may be used as features).

### Phase 4: Risk Simulation — Module 4 (Estimated: 2–3 hours)

| Step | Task | Output |
|------|------|--------|
| 4.1 | Classify revenue streams | Revenue breakdown columns |
| 4.2 | Implement shock simulation function | `simulate_shock()` |
| 4.3 | Run all 5 scenarios | Simulation results |
| 4.4 | Recovery pathway estimation | Recovery years column |
| 4.5 | Vulnerability threshold analysis | Threshold findings |
| 4.6 | Save `data/simulation_results.csv` | Simulation data on disk |

**Prerequisite:** Module 3 complete (uses ResilienceScore for context).

### Phase 5: Hidden Gems — Module 5 (Estimated: 2 hours)

| Step | Task | Output |
|------|------|--------|
| 5.1 | Compute Impact Efficiency Score components | Score columns |
| 5.2 | Identify hidden gems (high impact + small budget) | Hidden gems list |
| 5.3 | Donation tipping point analysis | Tipping point table |
| 5.4 | Save `data/hidden_gems.csv` and update master table | Data on disk |

**Prerequisite:** Module 3 complete (uses ResilienceScore as a component).

### Phase 6: Dashboard & Presentation — Module 6 (Estimated: 3–4 hours)

| Step | Task | Output |
|------|------|--------|
| 6.1 | Build Streamlit app with 5 pages | `app.py` |
| 6.2 | Create all interactive visualizations | Dashboard |
| 6.3 | Prepare presentation slides | Slide deck |
| 6.4 | Practice narrative and demo | Presentation ready |

**Prerequisite:** Modules 2–5 complete.

**Total Estimated Time: 14–19 hours**

---

## 13. Appendix: Column Data Dictionary

### Original Columns (37 columns in each CSV)

| Column | Type | Description |
|--------|------|-------------|
| `EIN` | string | Employer Identification Number — unique ID for each nonprofit |
| `OrgName` | string | Legal name of the organization |
| `State` | string | 2-letter state abbreviation |
| `City` | string | City name |
| `ZIP` | string | ZIP code |
| `TaxYear` | int | The tax year this filing covers (analysis panel: 2018–2024) |
| `TaxPeriodEnd` | date | End date of the tax period (e.g., 2024-06-30) |
| `FormType` | string | Always "990" in this dataset |
| `FormationYr` | int | Year the organization was formed/incorporated |
| `Mission` | string | Free-text description of the organization's mission |
| `NTEE_CD` | string | National Taxonomy of Exempt Entities code (e.g., `B42`, `E62`). Pre-joined from IRS TEOS bulk data. NULL for ~30% of records — use Mission-text fallback for sector classification. The first character is the major-group letter (A–Z). |
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
| `RevenueGrowthPct` | (CY − PY) / \|PY\| | Year-over-year revenue change |
| `ExpenseGrowthPct` | (CY − PY) / \|PY\| | Year-over-year expense change |
| `ContributionGrowthPct` | (CY − PY) / \|PY\| | Year-over-year contribution change |
| `NetAssetGrowthPct` | (EOY − BOY) / \|BOY\| | Balance sheet health trend |
| `OrgAge` | TaxYear − FormationYr | Years since formation |
| `SizeCategory` | Revenue-based bins | <500K, 500K-1M, 1M-5M, 5M-10M, 10M-50M, 50M+ |
| `RevenuePerEmployee` | TotalRevenueCY / Employees | Productivity proxy |
| `LogRevenue` | log(1 + TotalRevenueCY) | Log-transformed revenue for modeling |
| `LogAssets` | log(1 + TotalAssetsEOY) | Log-transformed assets for modeling |
| `Sector` | NTEE major-group label; Mission-text fallback | Readable sector name for peer grouping and display |
| `NTEEMajorGroup` | First character of NTEE_CD (A–Z) | Categorical feature for ML models (one-hot encoded) |
| `ResilienceScore` | Weighted composite (0–100) | Overall financial resilience rating (Module 3) |
| `AtRisk` | Binary (0/1) | Classification target for ML model (Module 3) |
| `ImpactEfficiencyScore` | Weighted composite (0–100) | Impact-per-dollar rating (Module 5) |

---

## File Structure

```
aggie_hacks_2026/
├── PRD.md                          # This document
├── data/
│   ├── data_csv/
│   │   ├── 2019_990.csv            # IRS release batch (TaxYears 2016–2018)
│   │   ├── 2020_990.csv            # (TaxYears 2017–2019)
│   │   ├── 2021_990.csv            # (TaxYears 2018–2020)
│   │   ├── 2022_1_990.csv          # (TaxYears 2018–2021)
│   │   ├── 2022_2_990.csv          # (TaxYears 2019–2021)
│   │   ├── 2023_1_990.csv          # (TaxYears 2020–2022)
│   │   ├── 2023_2_990.csv          # (TaxYears 2020–2022)
│   │   ├── 2025_990.csv            # (TaxYears 2021–2024)
│   │   └── <future 2024 batches>   # Drop here; pipeline auto-detects
│   ├── master_990.csv              # Output of Module 1
│   ├── peer_group_stats.csv        # Output of Module 2
│   ├── simulation_results.csv      # Output of Module 4
│   └── hidden_gems.csv             # Output of Module 5
├── notebooks/
│   ├── 01_data_pipeline.ipynb      # Module 1: Load, clean, feature engineering
│   ├── 02_eda.ipynb                # Exploratory Data Analysis
│   ├── 03_peer_benchmarking.ipynb  # Module 2: Peer groups and benchmarks
│   ├── 04_resilience_model.ipynb   # Module 3: ML model training
│   ├── 05_risk_simulation.ipynb    # Module 4: Shock scenarios
│   └── 06_hidden_gems.ipynb        # Module 5: Impact discovery
├── src/
│   ├── data_pipeline.py            # Module 1 as reusable functions
│   ├── peers.py                    # Module 2: Peer Z-scores and benchmarks
│   ├── resilience_model.py         # Module 3 functions
│   ├── risk_simulation.py          # Module 4 functions
│   └── hidden_gems.py             # Module 5 functions
├── artifacts/
│   ├── resilience_classifier.joblib  # Fitted sklearn Pipeline (Module 3)
│   └── train_metrics.json          # Metrics, importances, decision threshold
├── app.py                          # Module 6: Streamlit dashboard
├── outputs/
│   ├── eda_correlation_heatmap.png
│   ├── feature_importance.png
│   └── ...                         # All generated plots
├── requirements.txt                # Python dependencies
└── README.md                       # (optional) Quick-start guide
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
joblib>=1.3
```
