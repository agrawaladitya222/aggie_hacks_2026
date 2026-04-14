# Streamlit Dashboard — Full Pipeline Summary
## Nonprofit Brand Map for Fairlight Advisors

---

## Purpose
A Streamlit web app that gives Fairlight Advisors a visual, decision-ready tool
to assess nonprofit financial health at a glance. Built on IRS Form 990 data.

---

## Project Structure

```
nonprofit_dashboard/
│
├── data/
│   ├── 2019_990.csv          ← already includes NTEE codes
│   ├── 2020_990.csv          ← already includes NTEE codes
│   └── 2021_990.csv          ← already includes NTEE codes
│
├── src/
│   ├── data_loader.py         ← loads + stacks CSVs, deduplicates
│   ├── feature_engineering.py ← computes all metrics
│   └── filters.py             ← applies user sidebar selections
│
├── features/
│   └── brand_map.py           ← brand map figure builder (Plotly)
│
└── app.py                     ← Streamlit entry point
```

---

## Pipeline Flow

```
data_loader.py
    → loads 2019, 2020, 2021 CSVs
    → stacks into one master DataFrame
    → deduplicates on EIN + TaxYear (keep most recent)
    → NO NTEE join needed — already in CSVs
         ↓
feature_engineering.py
    → computes all metrics (see below)
    → cached with @st.cache_data (runs once at load)
         ↓
filters.py
    → takes enriched DataFrame + sidebar params
    → returns filtered subset
    → called every time user changes sidebar
         ↓
features/brand_map.py
    → takes filtered DataFrame
    → returns Plotly scatter figure
    → no Streamlit code inside — pure data → figure
         ↓
app.py
    → Streamlit layout + sidebar controls
    → calls chain above
    → renders figure with st.plotly_chart()
```

---

## Feature Engineering — Full List

### Group 1 — Efficiency Metrics
| Feature | Formula | Scaling |
|---|---|---|
| Program Expense Ratio | `ProgramSvcExpenses / TotalExpensesCY` | 0–100%, natural |
| Fundraising Overhead | `FundraisingExpCY / TotalExpensesCY` | 0–100%, natural |
| Salary Ratio | `SalariesCY / TotalExpensesCY` | 0–100%, natural |
| Admin Overhead | `1 - ProgramRatio - FundraisingOverhead` | 0–100%, natural |

### Group 2 — Financial Stability Metrics
| Feature | Formula | Scaling |
|---|---|---|
| Operating Reserve Months | `NetAssetsEOY / (TotalExpensesCY / 12)` | Raw, no cap |
| Surplus Margin | `NetRevenueCY / TotalRevenueCY` | Raw, can be negative |
| Debt Ratio | `TotalLiabilitiesEOY / TotalAssetsEOY` | 0–100%, natural |
| Asset Growth | `(TotalAssetsEOY - TotalAssetsBOY) / abs(TotalAssetsBOY)` | Raw, can be negative |

### Group 3 — Revenue Diversification Metrics
| Feature | Formula | Scaling |
|---|---|---|
| Grant Dependency | `ContributionsGrantsCY / TotalRevenueCY` | 0–100%, natural |
| Earned Revenue % | `ProgramServiceRevCY / TotalRevenueCY` | 0–100%, natural |
| Investment Income % | `InvestmentIncomeCY / TotalRevenueCY` | 0–100%, natural |
| Revenue Concentration | `max(grants, earned, investment) / TotalRevenueCY` | 0–100%, natural |

### Group 4 — Growth Metrics (YoY, using CY/PY fields already in data)
| Feature | Formula | Scaling |
|---|---|---|
| Revenue Growth YoY | `(TotalRevenueCY - TotalRevenuePY) / abs(TotalRevenuePY)` | Raw, can be negative |
| Expense Growth YoY | `(TotalExpensesCY - TotalExpensesPY) / abs(TotalExpensesPY)` | Raw, can be negative |
| Net Asset Growth | `(NetAssetsEOY - NetAssetsBOY) / abs(NetAssetsBOY)` | Raw, can be negative |
| Contribution Growth | `(ContributionsGrantsCY - ContributionsGrantsPY) / abs(ContributionsGrantsPY)` | Raw, can be negative |

### Group 5 — Classification / Categorical
| Feature | Source | Values |
|---|---|---|
| Size Bucket | `TotalRevenueCY` | Small ($0–5M) / Mid ($5–20M) / Large ($20M+) |
| NTEE Major Sector | First letter of `ntee_code` | A–Z |
| Resilience Tier | Rule-based (see below) | Stable / Watch / At Risk |
| State | Already in data | 2-letter code |
| Org Age | `TaxYear - FormationYr` | Years |

### Resilience Tier Logic
```
Stable   → ReserveMonths > 6   AND SurplusMargin > 0%
Watch    → ReserveMonths 1–6   OR  SurplusMargin between -10% and 0%
At Risk  → ReserveMonths < 1   OR  SurplusMargin < -10%  OR  DebtRatio > 0.8
```

### Dot Size Scaling
```
DotSize = log10(TotalRevenueCY)  ← log scale so $1M and $80M orgs are readable
```

---

## Data Exclusions (Feature Engineering Layer)

| Condition | Action | Reason |
|---|---|---|
| `ProgramSvcExpenses` is null | Exclude from brand map | Can't compute X axis — investigate later |
| `TotalExpensesCY` is zero or null | Exclude entirely | Can't compute any ratios |
| `TotalRevenueCY` is zero or null | Exclude entirely | Can't compute revenue metrics |

Note: Zero `ProgramSvcExpenses` (not null) is kept and plots at X=0 — meaningful signal, not an error.

---

## Brand Map Design (Phase 1 — Snapshot View)

| Element | Value | Notes |
|---|---|---|
| X axis | Program Expense Ratio | "How much of every dollar goes to mission?" |
| Y axis | Operating Reserve Months | "How many months can they operate without new funding?" |
| Dot size | log10(TotalRevenueCY) | Bigger org = bigger dot |
| Dot color | Resilience Tier | 🟢 Stable / 🟡 Watch / 🔴 At Risk |
| Axes | Fixed — not user-selectable | Keeps it simple for non-technical users |
| Scaling | No caps, no transformations | Let outliers tell their story naturally |

### Hover Tooltip Shows
- Org name
- State
- Total Revenue
- NTEE Sector
- Surplus Margin
- Grant Dependency %
- Resilience Tier

---

## Sidebar Filters (User Parameters)
- Year (2019 / 2020 / 2021) — snapshot view
- State (All or single state)
- NTEE Sector (All or single sector)
- Revenue Size Bucket (All / Small / Mid / Large)

---

## Scaling Philosophy
- Ratios (0–1) → displayed as 0–100%, no transformation
- Reserve months → raw, no cap. High reserves = meaningful signal, not outlier
- Growth metrics → raw, can be negative
- Revenue for dot size → log10 scale for readability

---

## Future Features (Phase 2+)
- Time progression / animation (2019 → 2020 → 2021 dot movement)
- Time series view (trend per org or sector over years)
- Peer benchmarking table (Z-score comparison)
- Funding shock simulation (30%/50% grant loss)

---

## Key Design Decisions
- One feature per script in `features/` folder — easy to extend
- Feature engineering runs once, cached — fast user experience
- No NTEE join needed — already in CSVs
- Fixed axes — non-technical audience
- Null ProgramSvcExpenses excluded, not imputed — investigate later
- No revenue filter applied — full range kept, filter manually post-analysis
