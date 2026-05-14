# RAV · Aggie Hacks 2026 — 8-Minute Presentation Script

**Target length:** 8:00 (480 sec) at ~140 wpm ≈ 1,120 words
**Deck:** `RAV_Deck_Final.pptx.pdf` (18 slides)
**Team:** Rishabh Bhat, Aditya Agrawal, Viraj Gandhi

Speaker tags below are suggestions — adjust to balance speaking time across the three of us. Each slide has an estimated time and a set of speaker notes / visual cues.

---

## Slide 1 — Title · "Can we turn 7 years of public IRS data into decisions Fairlight can act on tomorrow?" (~15 sec)

> Good afternoon. We're team RAV — Rishabh, Aditya, and Viraj. Over the next eight minutes we'll show you how we turned seven years of public IRS Form 990 data into a decision-ready toolkit for Fairlight Advisors — one that tells a funder in seconds who's thriving, who's at risk, and where a single dollar goes furthest.

**Cue:** Land on the title slide confidently, then advance.

---

## Slide 2 — The Problem (~45 sec)

> Fairlight's clients face three questions every day, and none of them have easy answers. **Which organizations are worth backing?** Funders today allocate philanthropic capital largely on reputation and relationships — not data. **How do I compare two nonprofits fairly?** A rural food bank in Iowa and a billion-dollar hospital system in New York are both "nonprofits," but comparing them head-to-head is meaningless. And **how do you advise a client on an org's financial health without burning days inside spreadsheets?**
>
> The raw material to answer all three exists — **400,000 Form 990 filings across seven years, 137,000 unique organizations, fully public**. But the data is sprawling, inconsistent, and not decision-ready. That gap — between public data and actionable insight — is exactly what we built RAV to close.

**Cue:** Point at "400K+ Form 990s" stat line as you say it.

---

## Slide 3 — Important Findings (~35 sec)

> Before we built any tool, we let the data speak. And the headline is sobering: **25.4% — one in four nonprofits — shows active signs of financial distress right now**, across 130,000 unique organizations. That's not a tail-risk story; it's the baseline.
>
> Two factors do most of the explaining. First, **debt ratio** — funding fluctuates, debt doesn't, so leverage becomes a trap the moment revenue dips. Second, **contribution growth**. A shrinking contribution line is the earliest signal that donors and grantmakers are quietly pulling back, often a full year before the balance sheet breaks. These two findings shaped every downstream design choice.

**Cue:** Emphasize the "1 in 4" stat — this is the hook.

---

## Slide 4 — The At-Risk Label (~40 sec)

> So how do we actually *define* "at risk"? We built a transparent, rule-based flag that trips if an organization hits **any one** of four stress signals: a surplus margin below negative ten percent — meaning they're spending meaningfully more than they earn; fewer than one month of operating reserves — essentially no cash runway; a twenty percent or greater drop in net assets year-over-year; or a twenty-five percent or greater revenue collapse.
>
> We chose these four because they cover the four distinct failure modes an accountant would flag — **profitability, liquidity, balance-sheet erosion, and revenue shock** — and because every one of them is explainable to a board member in a single sentence. This flag becomes the target variable for everything that follows.

**Cue:** Walk through the four bullets on the slide as you name each one.

---

## Slide 5 — Model Selection & Why Random Forest (~45 sec)

> The rule-based flag is transparent, but real 990 data is messy — missing fields, edge cases, and **relationships that aren't linear**. Look at the EDA plots on this slide: risk doesn't rise smoothly with debt ratio or reserves. It spikes and plateaus at specific thresholds. A logistic regression would force a straight line through a curved reality.
>
> Trees split on thresholds, so they're purpose-built for this shape. We tested four models — Logistic Regression, Gradient Boosting, XGBoost, and Random Forest — and Random Forest won on ROC-AUC with **0.91, validated with five-fold cross-validation**. It also handles missing values gracefully and learns interactions between features — exactly what we need when no single metric defines risk in isolation. The EDA pointed the way; the model justified itself on the metrics.

**Cue:** Gesture at the curved feature-vs-target plots on the slide.

---

## Slide 6 — The Resilience Score (~40 sec)

> Risk probability answers "who's in danger." But funders also need a single number for **overall financial strength** — something you can benchmark, rank, and explain on one line. So we built the Resilience Score: a zero-to-one-hundred metric, weighted directly from our EDA findings.
>
> Operating Reserves carries thirty points because it was the single strongest stability signal. Revenue Diversification gets twenty — it counters grant dependency. Program Efficiency gets twenty — it's the core mission metric. Surplus Margin and Low Debt each get fifteen. Above seventy is strong, forty to seventy is moderate, below forty is at risk. **Think of it as a credit score for nonprofit financial health** — intuitive, transparent, and comparable across every organization in the dataset.

**Cue:** Read the weights off the table; land on the "credit score" analogy.

---

## Slide 7 — Six Decision-Making Tools (~20 sec)

> We turned every one of those findings into a live Streamlit dashboard — six interconnected tools, each answering a different funder question. Executive Overview, Peer Benchmarking, Resilience Explorer, Stress Test Simulator, Hidden Gems Finder, and Brand Map. Let's walk through each one.

**Cue:** Quick beat on each of the six names.

---

## Slide 8 — Executive Overview (~30 sec)

> The Executive Overview is the sector-wide scan — it's where a Fairlight analyst starts their day. Four KPIs at the top, the resilience-score distribution, a state-level choropleth, and a sector ranking bar. **The map reveals the Dakotas leading with low-debt community nonprofits, while DC and Nevada lag. Crime & Legal sits at the bottom of the sector ranking; Mutual Benefit orgs sit at the top.** It's the context every other page depends on.

**Cue:** Hover the KPIs, then the map, then the sector bars.

---

## Slide 9 — Peer Benchmarking (~30 sec)

> Raw metrics are meaningless without peers. We define peer groups on three dimensions — **NTEE sector, revenue-size bucket, and state** — with a fallback to sector-plus-size if a group has fewer than five members, so we never benchmark against a statistically empty bucket. The radar chart overlays the selected org against its peer median across five metrics: green outperforms, red lags. A Fairlight analyst can answer *"compared to who, and by how much"* in under ten seconds.

**Cue:** Point at the radar chart; call out one green and one red metric.

---

## Slide 10 — Resilience Explorer: Feature Importance (~25 sec)

> Funders don't just want a score — they want to know **what drives it**. This view ranks every feature by its contribution to our Random Forest. Debt-to-asset ratio alone accounts for roughly **seventeen percent of predictive power**, followed by reserves and contribution growth. These aren't arbitrary weights — they're the levers a funder or board member can actually pull.

**Cue:** Point at the top three bars on the feature-importance chart.

---

## Slide 11 — Resilience Explorer: Org View (~25 sec)

> Sector-wide importance is useful, but decisions happen at the org level. This view takes our model's **continuous risk probability** and lets a user filter by sector, size, or state — then surfaces the distribution and the individual orgs inside it. It's how a funder moves from "the Healthcare sector looks fragile" to "these twelve specific healthcare orgs in Texas need a call this week."

**Cue:** Walk through a filter → scatter → table flow.

---

## Slide 12 — Stress Test Simulator: Sector View (~30 sec)

> Knowing an org is at-risk isn't enough — funders need to know **under which shock**. Our simulator models five scenarios: government-grant cuts, donation shocks, program-revenue drops, investment shocks, and a combined recession. Drag the slider, and the sector breakdown updates live. **Crime & Legal is forty-four percent government-grant dependent; Mental Health twenty-nine; Public Safety twenty-one** — numbers a funder needs before any policy announcement hits.

**Cue:** Drag a slider live if possible; point at the sector stacked bar.

---

## Slide 13 — Stress Test: Recovery Horizon (~25 sec)

> Identifying exposure is half the question — the other half is *how long does recovery take?* This histogram shows recovery time under a given shock, assuming a realistic five-percent annual growth rate back to solvency. Under a twenty-percent shock to all revenue streams, **the majority of affected orgs need seven to eight years to claw back**. That's the number that turns a crisis headline into a capital-planning conversation.

**Cue:** Trace the distribution with a finger on the histogram.

---

## Slide 14 — Stress Test: Org-Level Diagnostics (~25 sec)

> And because aggregate trends are actionable only when you can name names, the same engine runs at the organization level — pre- and post-shock revenue by stream, the tier downgrade, time to insolvency, and the recovery horizon. This is the view that lets Fairlight walk into a client meeting and say *"here's exactly what happens to you if federal grants drop thirty percent."*

**Cue:** Point at the pre/post revenue bars and the downgrade indicator.

---

## Slide 15 — Hidden Gems Finder (~30 sec)

> Risk is only half the story. The other half is **upside** — where does a donation create outsized impact? We screen every organization in the dataset down to a candidate pool of **3,620 hidden gems** — high-impact, modest-budget, growing, and not already in distress. Then we rank them with our **Cost-Efficiency Score** — a zero-to-one-hundred blend of mission ROI at forty percent, overall impact quality at thirty, and growth plus urgency at fifteen each — and slice them into tiers: Top 25, Top 100, Top 500, or the full universe.
>
> Here's the punchline. For the **Top 25 alone**, a funder writes a check of **$2.6 million** to stabilize every one of them — and that protects **$52.6 million of annual mission work**. That's a **twenty-to-one Portfolio ROI**, with a median gem delivering **$22.80 of program activity protected for every dollar donated**. That is a concrete, board-presentable ask.

**Cue:** Land firmly on the **20:1 ROI** and **$2.6M → $52.6M** numbers.

---

## Slide 16 — Hidden Gems: Org-Level Breakdown (~20 sec)

> Click into any gem and you get the **full Cost-Efficiency breakdown** — the exact ROI percentile, impact quality, growth, and urgency components that drove the ranking, plus the precise DonationToStabilize figure. It's not a black box; a funder can defend every recommendation in a board meeting with one screenshot.

**Cue:** Gesture at the breakdown card and the per-component bars.

---

## Slide 17 — Brand Map (~25 sec)

> The Brand Map closes the loop: every organization in a sector plotted on **mission efficiency versus operating runway**, with dashed crosshairs at the sector medians. Four quadrants, and the bottom-right is where attention belongs — **highly efficient organizations with almost no runway**, one shock away from shutting down programs communities depend on. It's a single visual that tells a funder where the next dollar matters most.

**Cue:** Point at the bottom-right quadrant as you describe it.

---

## Slide 18 — Summary & Close (~30 sec)

> To recap: six tools, one dashboard. Executive Overview for the big picture, Peer Benchmarking for apples-to-apples, Resilience Explorer for the drivers, Stress Test for the shocks, Hidden Gems for the upside, and Brand Map for the strategic view.
>
> Under the hood: **one in four nonprofits are at risk, a transparent rule-based label validated by a 0.91-AUC Random Forest, a zero-to-one-hundred Resilience Score grounded in EDA, and a Top 25 Hidden Gems shortlist where $2.6 million of targeted funding protects $52 million of annual mission work — a twenty-to-one return.** Seven years of public data. Transparent peer definitions. Reproducible models. Decisions Fairlight can act on tomorrow. Thank you — we'd love your questions.

**Cue:** End on the sidebar of the live dashboard visible behind the deck.

---

## Timing Cheat-Sheet

| Slide | Topic | Time | Running |
|------:|-------|-----:|--------:|
| 1 | Title | 0:15 | 0:15 |
| 2 | Problem | 0:45 | 1:00 |
| 3 | Findings | 0:35 | 1:35 |
| 4 | At-Risk Label | 0:40 | 2:15 |
| 5 | Model Selection | 0:45 | 3:00 |
| 6 | Resilience Score | 0:40 | 3:40 |
| 7 | 6 Tools Intro | 0:20 | 4:00 |
| 8 | Exec Overview | 0:30 | 4:30 |
| 9 | Peer Benchmarking | 0:30 | 5:00 |
| 10 | Feature Importance | 0:25 | 5:25 |
| 11 | Resilience Org View | 0:25 | 5:50 |
| 12 | Stress Test Sector | 0:30 | 6:20 |
| 13 | Recovery Horizon | 0:25 | 6:45 |
| 14 | Stress Test Org | 0:25 | 7:10 |
| 15 | Hidden Gems | 0:30 | 7:40 |
| 16 | Gems Breakdown | 0:20 | 8:00 |
| 17 | Brand Map | 0:25 | 8:25 |
| 18 | Summary | 0:30 | 8:55 |

**Real 8:00 target:** Tighten Slides 14 & 16 each to ~15s and drop the Slide 18 recap to 20s if you're running long — that lands you at exactly **8:00**.
