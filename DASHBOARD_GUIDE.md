# Nonprofit Financial Resilience Dashboard — User Guide

A comprehensive guide to navigating and interpreting every page of the dashboard.
The dashboard is built on IRS Form 990 filings from **2018 – 2024** covering tens of
thousands of U.S. nonprofits.

---

## Table of Contents

1. [How to Navigate](#how-to-navigate)
2. [The Resilience Score — What It Is and How It Works](#the-resilience-score)
3. [Page 1 — Executive Overview](#page-1--executive-overview)
4. [Page 2 — Peer Benchmarking](#page-2--peer-benchmarking)
5. [Page 3 — Resilience Explorer](#page-3--resilience-explorer)
6. [Page 4 — Stress Test Simulator](#page-4--stress-test-simulator)
7. [Page 5 — Hidden Gems Finder](#page-5--hidden-gems-finder)
8. [Metric Reference](#metric-reference)

---

## How to Navigate

The left sidebar contains the navigation menu. Click any of the five page names to
switch pages:

- Executive Overview
- Peer Benchmarking
- Resilience Explorer
- Stress Test Simulator
- Hidden Gems Finder

The sidebar also shows the total number of organizations and states included in the
dataset at the bottom.

---

## The Resilience Score

The **Resilience Score** is a 0–100 composite rating that summarizes how well an
organization is positioned to survive a major funding disruption. It is built from
five financial fundamentals, each weighted by how strongly it predicts financial
distress:

| Component | Weight | What it measures |
|---|---|---|
| Operating Reserves | 30 pts | How many months of expenses are held in reserve |
| Revenue Diversification | 20 pts | How spread out the income sources are |
| Program Spending Efficiency | 20 pts | What fraction of spending goes to actual programs |
| Surplus Margin | 15 pts | Whether the org is running a surplus or deficit |
| Low Debt | 15 pts | How much of total assets are financed by debt |

**Score tiers:**

| Score range | Label | Meaning |
|---|---|---|
| 70 – 100 | Strong | Well-positioned; can weather most disruptions |
| 40 – 69 | Moderate | Some vulnerabilities; improvement is advisable |
| 0 – 39 | At Risk | Significant financial stress; closure risk is elevated |

A score of **N/A** means the organization's 990 filing had insufficient data to
calculate one or more of the underlying metrics (e.g., missing revenue or expense
fields). This is common for very small nonprofits or organizations in their first or
final year of filing.

---

## Page 1 — Executive Overview

**Purpose:** A high-level snapshot of the financial health of the entire nonprofit
sector across the U.S.

### Top-line KPIs (four metric cards)

| Card | What it shows |
|---|---|
| Total Nonprofits Analyzed | The number of organizations in the dataset |
| At-Risk Rate | The percentage of organizations classified as financially at risk (Resilience Score below 40, or flagged by the model as likely to face distress) |
| Financially Strong (score 70+) | The percentage of organizations with a Resilience Score of 70 or above |
| Median Months of Reserves | The median across all organizations of how many months they could operate using only existing reserves, with no new revenue |

If more than 20% of nonprofits are at risk, an orange callout banner appears
highlighting how many organizations are showing signs of financial distress.

### Section: How Resilient Are U.S. Nonprofits?

A histogram showing the full distribution of Resilience Scores across all
organizations. Bars are color-coded:

- **Red** — At Risk (score 0–40)
- **Yellow/amber** — Moderate (score 40–70)
- **Green** — Strong (score 70–100)

The shape of the distribution tells you how the sector is doing overall. A
right-skewed distribution (most mass toward higher scores) is healthy; a
left-skewed one indicates widespread distress.

To the right of the histogram is a reminder of what goes into the Resilience Score
and how the point weights break down.

### Section: Resilience Across the Country

A choropleth (heat map) of the U.S. showing the **average Resilience Score by
state**, using a red-yellow-green color scale. Darker green = stronger average
financial health; darker red = weaker.

Hover over any state to see:
- The state abbreviation and average score
- The percentage of organizations in that state classified as at risk
- The total number of organizations analyzed in that state

This is useful for identifying geographic patterns — e.g., whether certain regions
consistently have more financially stressed nonprofits.

### Section: How Different Sectors Compare

A horizontal bar chart ranking every nonprofit sector by its **average Resilience
Score**, sorted from lowest (top) to highest (bottom). Bars are color-coded on the
same red-yellow-green scale.

Hover over a bar to see the sector's count of organizations, at-risk percentage, and
median months of reserves.

A blue insight callout below the chart names the strongest and weakest-performing
sectors and gives their scores and at-risk rates.

---

## Page 2 — Peer Benchmarking

**Purpose:** Understand how a specific organization compares to its peers —
nonprofits of the same sector, size category, and state.

### Organization Search

Type any organization name into the search box. The dropdown shows all organizations
in the dataset. Start typing to filter the list. Once selected, the page populates
with data for that organization.

### Organization Snapshot

Displays the selected organization's:
- Name, city, state, sector, and size category
- How many similar organizations are in its peer group
- Its Resilience Score (shown as a large number out of 100) with a color-coded
  health badge: **Strong** (green), **Moderate** (yellow), or **At Risk** (red)
- If the score is unavailable due to missing data it displays as **N/A**

### Section: How Does This Organization Compare?

This section contains two parts side by side.

**Left — Spider (Radar) Chart**

A radar chart with five axes, one for each key financial metric. There are two traces:

- **Blue filled polygon** — the selected organization
- **Grey dashed polygon** — the peer group median

**How to read it:** On every axis, a **larger spoke means the organization is doing
better than its peers**. This is true for all five metrics, including Fundraising
Cost % and Debt-to-Asset Ratio (where the raw values are inverted so that a lower
cost or lower debt still appears as a larger spoke).

If the blue polygon extends beyond the grey polygon on an axis, the organization
outperforms its peers on that dimension. If the blue polygon is smaller than grey,
the organization is underperforming on that dimension.

**Right — Metric-by-Metric Breakdown**

A bullet list comparing the organization's value to the peer group median for each
metric:

- **Green circle** = the organization is doing better than peers on this metric
- **Red circle** = the organization is doing worse than peers on this metric

For each metric you also see the raw value, the peer median, and (where available)
the organization's percentile rank within its peer group.

Below the list, an expandable section ("What do these metrics mean?") provides plain-
English definitions of all nine metrics.

### Section: Full Peer Group

A scrollable table of all organizations in the same peer group (up to 200 rows),
showing name, state, Resilience Score, and the five benchmarked metrics. Use this to
see the full range of performance within the peer group, or to identify other
organizations with similar characteristics.

---

## Page 3 — Resilience Explorer

**Purpose:** Understand what drives financial resilience sector-wide, and browse or
filter the full list of organizations by sector, size, and state.

### Section: Risk Tiers at a Glance

Three metric cards showing how many organizations fall into each tier:

| Tier | Score range |
|---|---|
| Strong | 70 – 100 |
| Moderate | 40 – 70 |
| At Risk | 0 – 40 |

Each card also shows that tier's share of the total dataset.

### Section: What Drives Financial Resilience?

A horizontal bar chart showing the **relative importance of each financial factor**
in predicting whether an organization will be financially resilient. These importances
come from a trained machine learning model (a gradient-boosted classifier fit on the
990 data).

A longer, darker bar means that metric is a stronger predictor of resilience. The
text panel to the right names the three most influential factors and summarizes the
takeaway.

This section only appears if the model has been trained and the feature importances
file (`artifacts/train_metrics.json`) is present.

### Section: Explore Individual Organizations

**Filters** — Three dropdowns let you narrow the dataset by:
- **Sector** — e.g., Health, Education, Human Services
- **Size** — Small, Medium, Large (based on annual revenue)
- **State** — any U.S. state or territory

**Scatter plot** — After filtering, a scatter plot appears with:
- **X-axis** — Total annual revenue (log scale, since revenues span several orders
  of magnitude)
- **Y-axis** — Resilience Score (0–100)
- **Color** — Health tier (green = Strong, amber = Moderate, red = At Risk)

Hover over any dot to see the organization name, state, and formatted revenue. This
is useful for spotting whether larger organizations tend to be more resilient within
a sector, or finding outliers (e.g., high-revenue organizations that are still at risk).

**Browse organizations table** — A sortable table of up to 500 organizations matching
the current filters, sorted from lowest to highest Resilience Score by default.
Columns include organization name, state, sector, size, score, at-risk flag (Yes/No),
and the model's estimated probability that the organization will face financial distress.

---

## Page 4 — Stress Test Simulator

**Purpose:** Model how nonprofits would fare under specific real-world funding shocks,
from grant cuts to market crashes.

### Scenario Selector

Choose one of five pre-modeled scenarios from the dropdown:

| Scenario | What it simulates |
|---|---|
| Grant Shock (-30%) | Donations and grants drop 30% — models a major donor withdrawal or economic downturn |
| Gov Grant Shock (-50%) | Government funding is cut in half — models policy changes or budget sequestration |
| Program Rev Shock (-25%) | Earned program revenue falls 25% — models reduced demand or pandemic-like disruptions |
| Investment Shock (-40%) | Investment returns drop 40% — models a stock market crash hitting endowment-funded orgs |
| Combined Recession (-20%) | All revenue sources drop 20% simultaneously — models a broad economic recession |

A blue callout box beneath the selector describes the selected scenario in more detail.

### Section: Overall Impact

Four metric cards show the number (and percentage) of organizations that land in each
post-shock status category:

| Status | Meaning |
|---|---|
| Critical (<3 months reserves) | Would exhaust reserves in under 3 months — immediate closure risk |
| At Risk (3–12 months reserves) | Reserves depleted within the year — serious distress |
| Stressed (>12 months reserves) | Would dip into reserves but survive long-term |
| Survives (Surplus) | Absorbs the shock and remains in surplus |

An orange impact banner always appears below the cards, stating the combined
percentage of organizations that would face serious distress (Critical + At Risk) and
the estimated count.

### Section: Status Distribution Charts

**Left — Donut chart**

Shows the overall share of organizations in each post-shock status category,
color-coded:
- Red = Critical
- Orange = At Risk
- Yellow = Stressed
- Green = Survives

**Right — Stacked bar chart by sector**

Shows how each sector breaks down across the four status categories. This reveals
which sectors are most exposed to a given type of shock — for example, arts
organizations might be more vulnerable to a grant shock than a healthcare org with
steady earned revenue.

### Section: Recovery Timeline

For organizations that would go into deficit under the scenario, this section shows
the estimated number of years to return to pre-shock revenue levels (assuming a 5%
annual recovery rate). A histogram displays the distribution of recovery times, and
text above it states the median and mean recovery years.

This section only appears if any organizations in the scenario are projected to go
into deficit.

---

## Page 5 — Hidden Gems Finder

**Purpose:** Identify small but high-impact nonprofits that are excellent candidates
for targeted philanthropic investment.

A "Hidden Gem" is defined as an organization that:
- Scores in the **top 20%** for impact efficiency (program output relative to budget)
- Has a **below-median budget** for its sector and size class
- Is financially sustainable (not in critical distress) and shows growth

### Top-line Stats

Three metric cards:
- **Hidden Gems Identified** — total number of qualifying organizations
- **Median Donation to Stabilize** — the median dollar amount needed to bring
  organizations' reserves up to a healthy 6-month level
- **Avg. Impact Efficiency Score** — the average efficiency score across all gems (0–100)

A green callout box explains the Hidden Gem criteria in plain terms.

### Section: Find Gems That Match Your Interests

Three filters:
- **State** — narrow to a specific state
- **Sector** — narrow to a specific nonprofit sector
- **Max donation to stabilize** — a slider filtering by the maximum donation amount
  needed to bring an organization to 6 months of reserves (set to the 95th percentile
  by default)

The text below the filters shows how many organizations match the current filter
combination.

### Top 6 Gems Cards

The six highest-scoring organizations matching the filters are displayed as cards,
each showing:
- Organization name, location, and sector
- **Impact Efficiency Score** (0–100) — how much program output the org delivers
  per dollar of budget relative to peers
- **Resilience** health badge (Strong / Moderate / At Risk)
- The estimated donation needed to bring the organization to 6 months of reserves
  (or "Already stable" if reserves are sufficient)

### Section: Budget vs. Impact Efficiency (Scatter Plot)

A scatter plot with:
- **X-axis** — Total annual revenue (log scale)
- **Y-axis** — Impact Efficiency Score (0–100)
- **Color** — Sector
- **Dot size** — Resilience Score (larger dot = more resilient)

Hover over any dot for the organization name, formatted revenue, donation needed, and
resilience score. The chart helps identify whether the highest-impact organizations
cluster at a particular budget level, and which sectors produce the most efficient
small organizations.

### Section: Full List

A table of all hidden gems matching the current filters (up to 300 rows), showing:
- Organization name and state
- Annual revenue
- Impact Efficiency Score
- Resilience Score
- Program Spending % (share of budget going to programs)
- Revenue Growth (year-over-year)
- Reserve Months
- Donation to Stabilize ($ amount to reach 6-month reserves)

---

## Metric Reference

The following metrics are used throughout the dashboard. All are derived from IRS
Form 990 filings.

| Metric | Formula / Source | What "good" looks like |
|---|---|---|
| **Program Spending %** | Program expenses ÷ total expenses | 75%+ is the sector standard; higher is better |
| **Fundraising Cost %** | Fundraising expenses ÷ total expenses | Below 25%; lower is better |
| **Surplus / Deficit Margin** | (Total revenue − total expenses) ÷ total revenue | Positive = surplus; negative = deficit |
| **Months of Reserves** | Net assets ÷ (total expenses ÷ 12) | 3–6 months is healthy; higher is better |
| **Debt-to-Asset Ratio** | Total liabilities ÷ total assets | Below 0.5; lower is better |
| **Grant Dependency %** | (Grants + donations) ÷ total revenue | Below 80% reduces donor-concentration risk |
| **Earned Revenue %** | Program service revenue ÷ total revenue | Higher = more self-sustaining |
| **Revenue Growth %** | (Current year revenue − prior year) ÷ prior year | Positive = growing |
| **Revenue per Employee** | Total revenue ÷ number of employees | A rough productivity measure; higher is better |
| **Impact Efficiency Score** | Composite of program spending %, revenue growth, and reserve adequacy relative to peers | 0–100; higher is better (used on Hidden Gems page) |
| **At Risk Probability** | Output of a trained gradient-boosted classifier | 0–100%; higher = greater predicted risk of financial distress |
