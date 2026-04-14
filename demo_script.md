# Demo Video Script — Nonprofit Financial Resilience Dashboard

**Target length: 5 minutes | Speaking pace: 140 wpm (~700 words)**

---

## [0:00–0:40] Opening — The Problem & Our Approach (40 sec)

> Every year, thousands of U.S. nonprofits go dark — not because their missions failed, but because nobody saw the financial warning signs in time. Funders misallocate resources, and organizations that could have been saved miss the window for intervention.
>
> We set out to answer three questions for Fairlight Advisors using seven years of IRS Form 990 data: **Who is thriving and why? Who is at risk and what tipped them? And where can a single donation create outsized impact?**
>
> Our dataset spans nearly 400,000 filing records across 137,000 unique nonprofits, from 2018 through 2024. We chose to focus exclusively on Form 990 filers — public charities — because it gives us the most standardized, comparable operating signals at scale. We excluded 990-PF private foundations and 990-T unrelated business income filings because those represent different entity types with different accounting patterns, and mixing them in would undermine the apples-to-apples benchmarking that makes our tool reliable. With that foundation, we built a Streamlit dashboard that turns this data into an interactive decision-making tool. Let me walk you through it.

**[ACTION: Dashboard loads. Sidebar is visible with all 6 pages. Briefly mouse over the page list.]**

---

## [0:40–1:30] Executive Overview — What the Data Tells Us (50 sec)

> The Executive Overview surfaces the headline findings. Starting with the four KPIs: we analyzed nearly 400,000 records. **One in four nonprofits — 25.4% — triggers at-risk flags**, meaning they're running deep deficits, hemorrhaging revenue, or sitting on less than one month of reserves. On the brighter side, about 40% score as financially strong.
>
> Now this Resilience Score is our own composite metric built from five financial fundamentals weighted by their real-world importance: operating reserves at 30 points, revenue diversification at 20, program spending efficiency at 20, surplus margin at 15, and low debt at 15. The histogram shows the distribution — notice that roughly 12% of all nonprofits fall in the red zone below 40.
>
> The state-level map reveals a real geographic story. **South Dakota and North Dakota lead** with high average scores, while **DC and Nevada, lag behind**. This isn't random — states with smaller, community-rooted nonprofit ecosystems tend to carry less debt and maintain higher reserves.
>
> The sector bars show the extremes with **Crime & Legal ranking lowest**, and **Mutual Benefit organizations ranking highest**.

**[ACTION: Scroll through KPIs → linger on histogram → hover SD and DC on map → point at Housing & Shelter on the sector bar chart]**

---

## [1:30–2:15] Peer Benchmarking — Apples-to-Apples Comparisons (45 sec)

> Raw scores are meaningless without context, so the Peer Benchmarking page answers: *compared to who?*
>
> We define peer groups by three dimensions: NTEE sector, revenue size bucket, and state. If a group has fewer than five members, we fall back to sector-plus-size to maintain statistical validity. This ensures a rural food bank in Iowa isn't benchmarked against a billion-dollar hospital system in New York.
>
> Let me search for an organization (Iolani school). The spider chart overlays this org against its peer median on five metrics. **Green means outperforming, red means lagging.** On the right, we show the exact values with peer percentile rankings 

**[ACTION: Search for an org → show radar chart → point out a green and red metric → expand the "What do these metrics mean?" section → scroll peer table]**

---

## [2:15–3:00] Resilience Explorer & Model Development (45 sec)

> Now, the machine learning behind the scores. We trained four models — Logistic Regression, Random Forest, Gradient Boosting, and XGBoost — to classify at-risk nonprofits. Random Forest won with an AUC of .91 and five-fold cross-validation.
>
> But the real value is the feature importance chart. Debt to asset ratio **alone accounts for 17.5% of predictive power**.
>
> The interactive explorer lets you filter by sector, size, and state. 

**[ACTION: Point at feature importance chart → highlight top 3 factors → filter to Healthcare + a specific state → hover on scatter plot to show risk probability → scroll table]**

---

## [3:00–4:00] Stress Test Simulator — Scenario Planning (60 sec)

> The Stress Test Simulator is where analysis becomes scenario planning. We built five shock models that let you adjust the severity in real time.
>
> Let me start with the **Government Grant Shock**. I'll set it to 50%. The description box explains that only organizations receiving government grants are exposed The sectors hit hardest are **Crime & Legal at 44% government-grant dependency, Mental Health & Crisis at 29%, and Public Safety and Disaster Relief at 21%**. 
>
> Now watch what happens when I switch to **Combined Recession** and sync all sliders to 35%. Every revenue stream drops together — grants, government funding, program revenue, and investments. This hits more organizations because nobody is insulated. The recovery histogram below shows how long it would take for affected nonprofits to claw back to solvency at a 5% annual growth rate — you can see most cluster between 10 and 14 years. 

**[ACTION: Select "Gov Grant Shock" → drag slider to 50% → show donut chart + sector stacked bar → switch to "Combined Recession" → sync at 35% → scroll to recovery histogram → pause on the insight callout box]**

---

## [4:00–4:40] Hidden Gems Finder — Where Dollars Create Outsized Impact (40 sec)

> This page answers the third question: where should funders direct capital for maximum community return?
>
> Our Impact Efficiency Score ranks every nonprofit across five dimensions: program spending efficiency, revenue growth, program leverage community reach relative to budget, and financial sustainability. We identify **~27,000 hidden gems**: organizations in the top 20% for impact efficiency but with below-median budgets, positive growth, and a resilience score above 40.
>
> The key finding: **Most of these gems already have six-plus months of reserves**. For the few that do need stabilization, the **median donation to reach 6-month reserves is about $302,000** — a concrete, fundable number.
>
> Each card shows the exact donation-to-stabilize figure, and clicking Score Breakdown reveals exactly how the score was calculated 

**[ACTION: Show KPI cards at top → click Score Breakdown on a top gem → show the 5-component breakdown → filter to a specific state → hover on scatter plot → scroll the table]**

---

## [4:40–5:00] Brand Map & Closing (20 sec)

> The Brand Map provides one final strategic view — plotting every nonprofit on mission efficiency vs. operating runway. The dashed crosshairs mark sector medians, creating four quadrants. The bottom-right is the danger zone: highly efficient organizations with almost no runway, one shock away from shutting down programs that communities depend on.
>
> To close: this tool gives users a single platform to answer who's thriving, who's at risk, and where capital matters most — all backed by seven years of real IRS filings, transparent peer definitions, and reproducible models. Thank you.

**[ACTION: Show Brand Map → hover over bottom-right quadrant orgs → zoom back to show full view → end on sidebar visible]**