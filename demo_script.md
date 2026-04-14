# Demo Video Script — Nonprofit Financial Resilience Dashboard
**Target length: \~5 minutes | Speaking pace: \~140 wpm (~700 words)**

---

## [0:00–0:40] Opening — The Problem & Our Approach (40 sec)

> Every year, thousands of U.S. nonprofits go dark — not because their missions failed, but because nobody saw the financial warning signs in time. Funders misallocate resources, and organizations that could have been saved miss the window for intervention.
>
> We set out to answer three questions for Fairlight Advisors using seven years of IRS Form 990 data: **Who is thriving and why? Who is at risk and what tipped them? And where can a single donation create outsized impact?**
>
> Our dataset spans nearly 400,000 filing records across 137,000 unique nonprofits, all 50 states plus territories, and 25 NTEE sectors, from 2018 through 2024. An important scoping decision: we focused exclusively on Form 990 filers — public charities — because it gives us the most standardized, comparable operating signals at scale. We excluded 990-PF private foundations and 990-T unrelated business income filings because those represent different entity types with different accounting patterns, and mixing them in would undermine the apples-to-apples benchmarking that makes our tool reliable. With that foundation, we built a Streamlit dashboard that turns this data into an interactive decision-making tool. Let me walk you through it.

**[ACTION: Dashboard loads. Sidebar is visible with all 6 pages. Briefly mouse over the page list.]**

---

## [0:40–1:30] Executive Overview — What the Data Tells Us (50 sec)

> The Executive Overview surfaces the headline findings. Starting with the four KPIs: we analyzed nearly 400,000 records. **One in four nonprofits — 25.4% — triggers at-risk flags**, meaning they're running deep deficits, hemorrhaging revenue, or sitting on less than one month of reserves. On the brighter side, about 40% score as financially strong.
>
> Now this Resilience Score is our own composite metric built from five financial fundamentals weighted by their real-world importance: operating reserves at 30 points, revenue diversification at 20, program spending efficiency at 20, surplus margin at 15, and low debt at 15. The histogram shows the distribution — notice that roughly 12% of all nonprofits fall in the red zone below 40.
>
> The state-level map reveals a real geographic story. **South Dakota, North Dakota, and Iowa consistently lead** with average scores near 70, while **DC, Nevada, and New York lag behind**, scoring around 59 to 61. This isn't random — states with smaller, community-rooted nonprofit ecosystems tend to carry less debt and maintain higher reserves.
>
> The sector bars confirm what you'd expect: **Mental Health & Crisis and Crime & Legal rank lowest**, both averaging below 60, while **Mutual Benefit organizations lead at 75**. But here's the non-obvious finding — Housing & Shelter has the highest at-risk rate at 36%, even higher than sectors that score lower overall. That means Housing nonprofits tend to be polarized: some are quite strong, but more of them hit critical financial distress than any other sector.

**[ACTION: Scroll through KPIs → linger on histogram → hover SD and DC on map → point at Housing & Shelter on the sector bar chart]**

---

## [1:30–2:15] Peer Benchmarking — Apples-to-Apples Comparisons (45 sec)

> Raw scores are meaningless without context, so the Peer Benchmarking page answers: *compared to who?*
>
> We define peer groups by three dimensions: NTEE sector, revenue size bucket, and state. If a group has fewer than five members, we fall back to sector-plus-size to maintain statistical validity. This ensures a rural food bank in Iowa isn't benchmarked against a billion-dollar hospital system in New York.
>
> Let me search for an organization. The radar chart overlays this org against its peer median on five metrics. **Green means outperforming, red means lagging.** On the right, we show the exact values with peer percentile rankings — so you can see at a glance that this org is, say, in the top 15% for program spending but the bottom 30% for reserves.
>
> The key insight for Fairlight here is the **Z-score flagging system**. Any metric more than 1.5 standard deviations from the peer mean gets flagged as "Above Peer Norm" or "Below Peer Norm" — turning a wall of financial data into three actionable categories: fine, watch, and act.

**[ACTION: Search for an org → show radar chart → point out a green and red metric → expand the "What do these metrics mean?" section → scroll peer table]**

---

## [2:15–3:00] Resilience Explorer & Model Development (45 sec)

> Now, the machine learning behind the scores. We trained four models — Logistic Regression, Random Forest, Gradient Boosting, and XGBoost — to classify at-risk nonprofits. Random Forest won with an AUC of 0.9999 and five-fold cross-validation, far ahead of Logistic Regression's 0.91.
>
> But the real value is the feature importance chart. **Surplus margin alone accounts for 31.6% of predictive power**, followed by revenue growth at 17.9% and operating reserve months at 17.8%. These three factors drive nearly 70% of the model. What's notable is what *doesn't* matter as much: organization age, employee count, and even program expense ratio each contribute less than 1%. That challenges the common assumption that older or larger nonprofits are inherently safer.
>
> The interactive explorer lets you filter by sector, size, and state. Every row in the table includes both the rule-based resilience score *and* the model's risk probability, so a funder can cross-check both signals. **About 29% of all nonprofits are running deficits, and nearly 1 in 10 are both in deficit and have less than three months of reserves** — these are the organizations on the edge.

**[ACTION: Point at feature importance chart → highlight top 3 factors → filter to Healthcare + a specific state → hover on scatter plot to show risk probability → scroll table]**

---

## [3:00–4:00] Stress Test Simulator — Scenario Planning (60 sec)

> The Stress Test Simulator is where analysis becomes scenario planning. We built five shock models that let you adjust the severity in real time.
>
> Let me start with the **Government Grant Shock**. I'll set it to 50%. The description box explains that only organizations receiving government grants are exposed — this is why a large government cut can paradoxically show *fewer* at-risk nonprofits than a broad recession. The sectors hit hardest are **Crime & Legal at 39% government-grant dependency, Mental Health & Crisis at 31%, and Housing & Shelter at 21%**. Notice how the stacked bar on the right turns these sectors red.
>
> Now watch what happens when I switch to **Combined Recession** and sync all sliders to 35%. Every revenue stream drops together — grants, government funding, program revenue, and investments. This hits more organizations because nobody is insulated. The recovery histogram below shows how long it would take for affected nonprofits to claw back to solvency at a 5% annual growth rate — you can see most cluster between 3 and 8 years. That's a planning horizon Fairlight can use when advising clients about long-term grant commitments.
>
> The critical threshold we found: **once grant dependency exceeds 80% and reserves drop below 3 months, organizations almost universally fall to critical status under any shock scenario.** That's 36% of nonprofits that are grant-heavy, and 19% with under 3 months of reserves — the overlap is where intervention is most urgent.

**[ACTION: Select "Gov Grant Shock" → drag slider to 50% → show donut chart + sector stacked bar → switch to "Combined Recession" → sync at 35% → scroll to recovery histogram → pause on the insight callout box]**

---

## [4:00–4:40] Hidden Gems Finder — Where Dollars Create Outsized Impact (40 sec)

> This page answers the third question: where should funders direct capital for maximum community return?
>
> Our Impact Efficiency Score ranks every nonprofit across five dimensions: program spending efficiency, revenue growth, program leverage — how much mission output per donor dollar — community reach relative to budget, and financial sustainability. We identify **27,208 hidden gems**: organizations in the top 20% for impact efficiency but with below-median budgets, positive growth, and a resilience score above 40.
>
> The key finding: **81% of these gems already have six-plus months of reserves** — they're efficient *and* stable, just small. They don't need rescuing; they need fuel. For the 19% that do need stabilization, the **median donation to reach 6-month reserves is about $302,000** — a concrete, fundable number.
>
> The top sectors for hidden gems are **Human Services with over 6,000 gems and Education with 5,700**. California, Texas, and New York lead by state. Each card shows the exact donation-to-stabilize figure, and clicking Score Breakdown reveals exactly how the score was calculated — full transparency for due diligence.

**[ACTION: Show KPI cards at top → click Score Breakdown on a top gem → show the 5-component breakdown → filter to a specific state → hover on scatter plot → scroll the table]**

---

## [4:40–5:00] Brand Map & Closing (20 sec)

> The Brand Map provides one final strategic view — plotting every nonprofit on mission efficiency vs. operating runway. The dashed crosshairs mark sector medians, creating four quadrants. The bottom-right is the danger zone: highly efficient organizations with almost no runway, one shock away from shutting down programs that communities depend on.
>
> To close: this tool gives Fairlight a single platform to answer who's thriving, who's at risk, and where capital matters most — all backed by seven years of real IRS filings, transparent peer definitions, and reproducible models. Thank you.

**[ACTION: Show Brand Map → hover over bottom-right quadrant orgs → zoom back to show full view → end on sidebar visible]**
