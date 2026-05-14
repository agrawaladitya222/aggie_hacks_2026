# Judge Q&A Prep — Likely Questions & Answers

Anticipated questions by slide, mapped to the Aggie Hacks judging rubric
(Business Insights 40% / Data Analysis 20% / Solution Development 20% / Storytelling 20%).

---

## Slide 1 — Title

**Q1. Why the framing "decisions Fairlight can act on tomorrow"? What's the actual user workflow?**
A Fairlight analyst lands on the Executive Overview each morning to scan sector health, uses Peer Benchmarking when a client asks "how am I doing vs. similar orgs," runs the Stress Test before any policy-change client call, and pulls Hidden Gems when a donor asks "where should my next $500K go?" Every page answers one repeatable analyst question, so it replaces hours of spreadsheet work with a single click.

**Q2. Why the name RAV?**
It's just our initials — Rishabh, Aditya, Viraj — we kept it simple so the project name doesn't distract from the work.

---

## Slide 2 — The Problem

**Q1. Why only 990 filers? Why not 990-PF or 990-T?**
990-PF filers are private foundations — they *give* money, they don't operate programs, so their financial dynamics (investment income, required 5% payouts) are fundamentally different. 990-T captures unrelated business income, which is a supplementary return, not a full financial picture. Mixing them in would break apples-to-apples benchmarking, which is the central promise of the tool. Restricting to 990 public charities gives us 400K+ clean, comparable records.

**Q2. How big is the coverage gap — aren't many small nonprofits filing 990-N postcards instead?**
Yes. Orgs under $50K in gross receipts file 990-N, which has almost no financial detail. We explicitly scope to 990-filers ($50K+), which is the population Fairlight's clients actually work with. We flag this scope limitation openly in the dashboard.

---

## Slide 3 — Important Findings

**Q1. Is 25.4% high or low? What's the comparable benchmark?**
Academic literature (Urban Institute, Nonprofit Finance Fund) typically cites 30-40% of nonprofits running on less than one month of reserves in any given year. Our 25.4% uses a *composite* flag (four triggers), so it's actually a more conservative count — and it's consistent with the sector narrative that roughly a third of nonprofits are chronically fragile.

**Q2. Why debt ratio as a top predictor — nonprofits aren't supposed to carry much debt?**
Exactly the point. Most nonprofits run lean balance sheets, so *any* meaningful leverage is a strong outlier signal. Orgs with elevated debt-to-asset ratios lose the flexibility to absorb a funding shock, and our model picks that up as the single most predictive feature (~17.5% importance).

---

## Slide 4 — The At-Risk Label

**Q1. Why an OR-rule instead of requiring multiple triggers (AND-rule)?**
Nonprofits rarely fail from one slow decline across every metric — they fail from a single acute stressor. A 30% revenue collapse is a crisis even if reserves look fine; a zero-reserve org is in trouble even if margin is flat. An OR-rule captures distinct failure modes; an AND-rule would hide them. We validated this against the Resilience Score distribution — the flag cleanly separates the red zone.

**Q2. Where did the specific thresholds (-10%, 1 month, -20%, -25%) come from?**
They come from our EDA and nonprofit-finance literature. Under -10% surplus margin is the point where one-time write-offs can't explain the deficit. One month of reserves is the Nonprofit Finance Fund's standard "critical" threshold. 20% net-asset drop and 25% revenue drop are one standard deviation worse than the median YoY change in the dataset — statistically significant deterioration.

---

## Slide 5 — Model Selection & Why Random Forest

**Q1. If the rule-based label already works, why train a model at all?**
Two reasons. First, the rule is binary — at-risk or not. Real decisions need a *continuous* probability so a funder can rank a portfolio of 500 orgs from most to least vulnerable. Second, real 990 data has missing fields and edge cases where the rule under-triggers; Random Forest handles missingness and learns interactions the rule can't capture. The rule is the target; the model is the ranker.

**Q2. What did the four models actually score, and why Random Forest over XGBoost?**
All four beat 0.85 AUC, which means the underlying features are strong. Random Forest edged out XGBoost slightly (0.91 vs ~0.90) on ROC-AUC with 5-fold CV, and it's easier to explain to a non-technical audience with feature-importance bars. Given that explainability is a hard requirement for Fairlight's client conversations, we picked the more interpretable winner.

**Q3. Isn't there a risk of label leakage since the features generate the target?**
Fair concern. The AtRisk label uses four specific cutoffs on four specific ratios; the model uses a broader feature set (15+ features including NTEE sector dummies, org age, log revenue/assets, growth rates) — so it's learning *generalizable patterns* that predict the label, not just re-deriving it. That's why the feature-importance chart shows debt ratio and asset growth as top drivers, not the four label-defining ratios themselves.

---

## Slide 6 — The Resilience Score

**Q1. Why weight reserves at 30 and not 20 or 40? Isn't that arbitrary?**
Not arbitrary — anchored to EDA. Operating Reserve Months had the strongest univariate separation between at-risk and healthy orgs (largest AUC of any single feature). Revenue Diversification and Program Efficiency were second-tier. We set the weights proportional to the relative predictive strength from our bivariate analysis, then sanity-checked that the resulting distribution matched the 25% at-risk baseline.

**Q2. Why not just use the model's risk probability — why invent a second metric?**
They answer different questions. Risk probability is a *classifier output* — "how likely is this org to trigger distress flags this year?" Resilience Score is a *composite quality metric* — "how financially strong is this org overall?" A well-funded org can have low risk probability but mediocre resilience if it's entirely grant-dependent. Funders need both: the probability for triage, the score for benchmarking and long-term strategy.

---

## Slide 7 — Six Decision-Making Tools

**Q1. Isn't six pages too many for one dashboard?**
Each page maps to a distinct analyst question that Fairlight's team already answers manually today. We deliberately didn't collapse them into one mega-page because the mental model — "pick the question, get the view" — is how analysts actually think. The sidebar keeps navigation to one click.

---

## Slide 8 — Executive Overview

**Q1. The state map shows SD/ND at the top and DC/NV at the bottom — is this a population artifact?**
Partly, but not entirely. Small-state nonprofits are community-funded, carry less debt, and have fewer large-hospital-system outliers dragging the mean down. We verified the signal isn't a small-n artifact by checking that these states have 200+ orgs each. DC/NV lag because DC has a high concentration of advocacy orgs with grant dependency >60% and NV has a thinner nonprofit ecosystem — both structural, not statistical.

**Q2. What about year-over-year trends — does the Executive Overview show how the sector is changing?**
The score we display is based on the most recent filing per org. We intentionally kept the headline view a *snapshot* to keep it readable, but the full dataset covers 2018-2024 and the underlying pipeline supports a time-series view — a natural next iteration.

---

## Slide 9 — Peer Benchmarking

**Q1. How did you define "peer" — and what happens when a bucket is too small?**
Peers are defined on three axes: NTEE major sector, revenue-size bucket (five tiers from <$250K to >$50M), and state. If the resulting bucket has fewer than five orgs, we fall back to sector-plus-size (dropping geography). If that's still <5, we fall back to sector alone. This keeps every comparison statistically grounded without hiding small-state orgs behind a "no peers" message.

**Q2. Why median and not mean for the peer baseline?**
Nonprofit financials are extremely right-skewed — a handful of massive orgs would drag the mean up and make every small org look like an underperformer. Median gives the true "middle peer" reference a board member would intuitively expect.

---

## Slide 10 — Resilience Explorer: Feature Importance

**Q1. Debt ratio is 17.5% of importance — but you also said nonprofits rarely carry debt. Reconciling?**
Exactly the tension that makes it predictive. Because most nonprofits carry near-zero debt, the minority that *do* carry meaningful leverage are unusual — and in our data, unusually fragile. Low variance on most of the distribution plus a long right tail of leveraged orgs is exactly the pattern trees exploit best.

**Q2. Are the top features correlated with each other? How do you handle multicollinearity?**
Random Forest is relatively robust to multicollinearity compared to linear models — it just splits on whichever correlated feature gives the cleanest split. We did check correlations (see `outputs/eda/03_model_justification/fig3_feature_correlation.png`) and removed redundant features like total-revenue-levels where log-revenue already captured the signal.

---

## Slide 11 — Resilience Explorer: Org View

**Q1. An analyst clicks an org and gets a risk probability of 0.72 — how should they interpret that?**
As a relative ranking, not an absolute probability of collapse. An org at 0.72 is in the riskiest ~20% of its peer group. The dashboard shows the peer distribution alongside, so 0.72 reads as "notably worse than similar orgs" — which is the actionable framing, not "72% chance of failure."

---

## Slide 12 — Stress Test Simulator: Sector View

**Q1. Are the shock magnitudes realistic?**
They're calibrated against historical precedent. A 20% government-grant cut matches the 2013 sequestration impact on nonprofit grants; a 35% combined shock approximates the worst quarters of 2008-2009 and 2020. Users can go beyond historical precedent (up to 100%), which is useful for stress-testing tail scenarios Fairlight's clients worry about — major federal funding rescissions, for example.

**Q2. Doesn't the shock ignore that orgs adapt — cut costs, raise emergency donations?**
Yes, intentionally. This is a *stress test*, not a forecast. The point is to expose unmitigated exposure — which is what a risk officer wants to see first. A separate "adaptation" layer is feasible as a next iteration but would dilute the stress signal.

---

## Slide 13 — Stress Test: Recovery Horizon

**Q1. Why 5% annual growth as the recovery assumption?**
5% is the median multi-year real revenue growth rate in our dataset for healthy (non-at-risk) nonprofits. It's a realistic "back to normal" rate — not aggressive, not pessimistic. Users can adjust this assumption in the code; we keep one default visible to keep the story clean.

**Q2. 7-8 years to recover from a 20% shock seems long. Is that right?**
It's right because recovery is *compound* — you have to grow back the lost revenue *and* rebuild depleted reserves to pre-shock levels. At 5% growth from a 20%-down base, the math gives you roughly 7-8 years to catch up. That long tail is precisely the insight — a single shock creates a decade of fragility, which is why proactive intervention matters.

---

## Slide 14 — Stress Test: Org-Level Diagnostics

**Q1. How is "time to insolvency" computed?**
Post-shock monthly burn divided into post-shock net assets — literally "how many months until the org runs out of cash if the shock is sustained and nothing changes." It's a deliberately simple, defensible calculation; a board member can recompute it on a napkin.

---

## Slide 15 — Hidden Gems Finder

**Q1. You said 3,620 hidden gems — how did you get to that number, and why is it the right size?**
It's the candidate pool after four filters: Impact Efficiency above the 80th percentile, revenue below the median (so we surface small-but-mighty orgs, not sector giants), positive revenue growth (so we're not rewarding decline), and a Resilience Score above 40 (so we're not recommending already-fragile orgs). 3,620 is the opportunity space; the Top 25 / 100 / 500 tiers turn it into a shortlist a funder can actually act on.

**Q2. Walk us through the Cost-Efficiency Score — why those four components and those weights?**
Forty percent mission ROI — because the funder's core question is "how much program activity does every dollar I donate protect?" Thirty percent overall impact quality (the Impact Efficiency Score) — rewarding orgs that are efficient *and* growing *and* reaching the community *and* financially sustainable, not just one of those. Fifteen percent revenue growth — momentum. Fifteen percent funding urgency — orgs with lower reserves get a higher weight because the marginal dollar matters more there. Weights are tuned so the Top 25 always concentrates in the high-ROI, high-urgency quadrant.

**Q3. Why does Cost-Efficiency exist on top of Impact Efficiency — isn't that double-counting?**
They answer different questions. Impact Efficiency answers *"is this a well-run, high-impact organization?"* Cost-Efficiency answers *"per dollar of stabilization funding, how much mission work does my dollar protect?"* An org can be a five-star operator (high Impact Efficiency) but if it already has ten months of reserves, your funding dollar doesn't move the needle. Cost-Efficiency blends quality with marginal impact of a donation — that's what funders actually decide on.

**Q4. The Top 25 ROI is 20-to-1 — that sounds too good to be true.**
It's honest and defensible. Each gem's "ROI" is *annual* program activity protected per dollar of one-time stabilization funding — and nonprofits deliver program work year after year. A $100K one-time grant that prevents an org delivering $2M of programs per year from collapsing is literally a 20-to-1 return in Year 1 alone. We also exclude orgs needing under $25K of stabilization (they'd show absurd 400-to-1 ratios from tiny denominators) so the published ROI isn't inflated by edge cases.

**Q5. DonationToStabilize — what exactly is it computing?**
It's the dollar amount needed to bring the org's operating reserves up to 6 months of expenses — the Nonprofit Finance Fund's standard "safe" threshold. Months needed times monthly burn. If the org already has 6+ months of reserves, DonationToStabilize is $0 and it's labeled "Already Stable" (excluded from the funding tiers).

---

## Slide 16 — Hidden Gems: Org Breakdown

**Q1. What if a judge clicks a specific gem and disagrees it's high-impact?**
Every Cost-Efficiency Score is decomposed into its four components — ROI percentile, Impact Efficiency, growth, urgency — right there on the breakdown card. If a user disagrees with our 40/30/15/15 weighting, they can see exactly which component drove the ranking and mentally re-weight. The tool supports judgment; it doesn't replace it.

**Q2. The three gems on the slide span wildly different sizes ($30K to $426K donation needs). Is the ranking biased toward small orgs?**
It's biased toward *efficient* orgs at every size. Hawaiian Canoe Racing needs only $30K but protects $25 of program activity per dollar; Overflow Health needs $426K but protects $12.9 — both made the Top 3 because their ROI justifies the ask at their respective scales. We deliberately don't collapse to one size bucket because real donor portfolios span small and mid-size gifts.

---

## Slide 17 — Brand Map

**Q1. Why efficiency × runway specifically — why not a different two axes?**
Because those two axes capture the two questions a strategic funder asks: "does this org deliver on its mission?" (efficiency) and "will it still be around next year?" (runway). Plotting both simultaneously turns a 1D "is it good?" question into a 2D "is it both good *and* durable?" question — and the bottom-right quadrant (efficient but fragile) is the single most actionable cohort in the entire dataset.

---

## Slide 18 — Summary

**Q1. What's the biggest limitation we should know about?**
Two honest ones. First, 990 data is filed annually and often lagged 12-18 months — so we're looking at a rear-view mirror, not real-time. Second, our AtRisk label is current-state, not forward-looking — it identifies orgs in distress *now*, not orgs that will enter distress next year. Both are solvable with time-lagged modeling, which is the natural next iteration.

**Q2. If Fairlight wanted to deploy this tomorrow, what would it take?**
The entire stack is reproducible — a single `run_all.py` rebuilds the pipeline from raw IRS data to a live Streamlit app. Productionizing means scheduling the 990 refresh (IRS publishes quarterly), hosting the Streamlit instance, and layering client authentication. Realistically, a two-week engineering sprint to get it into Fairlight's client workflow.

**Q3. What makes this different from existing tools like GuideStar or ProPublica Nonprofit Explorer?**
Those tools are great for *looking up* a single nonprofit. Ours is built for *comparison, ranking, and scenario planning* across 130K orgs at once — with transparent peer definitions, a predictive model, and a stress-test simulator none of the existing tools offer. It's the difference between a dictionary and a decision engine.

---

## Cross-Cutting Questions (likely asked regardless of slide)

**Q. How are you handling the "business storytelling" criterion — what's the one sentence you want us to remember?**
*"One in four nonprofits are quietly in distress, and we built the tool that tells Fairlight which ones, why, and what it costs to save them."*

**Q. What's the monetary impact?**
Two angles. First, operational: if a Fairlight analyst saves one hour per client engagement on spreadsheet work, and Fairlight runs 100+ engagements a year, that's 100+ reclaimed billable hours. Second — and bigger — allocation quality. Our Top 25 Hidden Gems shortlist shows **$2.6M of targeted funding protects $52.6M of annual mission work — a 20-to-1 portfolio return**. That's the difference between a misallocated $500K grant and a $500K grant that keeps five high-impact orgs alive. Our tool is designed to surface exactly that delta.

**Q. How did you split the work across the team?**
Rishabh owned the Streamlit app, the Hidden Gems logic, and the Stress Test simulator. Aditya led the data pipeline and the resilience model. Viraj led EDA, peer-group design, and the storytelling layer. All three of us pair-reviewed every component.

**Q. If you had another week, what would you build next?**
Time-lagged prediction — using 2018-2022 data to predict 2023-2024 AtRisk status, so the model moves from current-state classification to true forward-looking early warning. The feature pipeline already supports it; we'd need a proper train/holdout by year and a drift check.
