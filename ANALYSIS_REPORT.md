# IPL Data Analysis Report (2008–2023)

**Indian Premier League | 16 Seasons | 1,024 Matches**

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Dataset Summary](#2-dataset-summary)
3. [Toss & Strategy Metrics](#3-toss--strategy-metrics)
4. [Team Dominance & Resilience](#4-team-dominance--resilience)
5. [Venue & Ground Conditions](#5-venue--ground-conditions)
6. [Squad Dependency & Star Power](#6-squad-dependency--star-power)
7. [Temporal & Historical Trends](#7-temporal--historical-trends)
8. [Additional Insights](#8-additional-insights)
9. [Key Takeaways](#9-key-takeaways)
10. [How to Run the Analysis](#10-how-to-run-the-analysis)

---

## 1. Project Overview

This report presents a comprehensive data analysis of the Indian Premier League (IPL) from its inaugural season in 2008 through 2023. The analysis goes beyond simple win-loss records and introduces **10 custom analytical metrics** designed to measure strategic effectiveness, clutch performance, venue conditions, player impact, and momentum patterns.

### Charts & Outputs

| File | Description |
|------|-------------|
| `output/ipl_dashboard.html` | Interactive 5-tab Plotly dashboard (open in browser) |
| `output/tdy_grouped_bar.png` | Toss Decision Yield per team |
| `output/tac_scatter.png` | Toss Advantage Coefficient scatter |
| `output/mwdi_box.png` | Margin-Weighted Dominance box plot |
| `output/cmri_diverging.png` | Close-Match Resilience diverging bar |
| `output/vbs_horizontal_bar.png` | Venue Bias Score ranked bar |
| `output/fdr_radar.png` | Fortress Dominance Ratio radar chart |
| `output/pom_treemap.png` | Player of Match Concentration treemap |
| `output/bmpi_dot.png` | Big-Match Performance Index dot plot |
| `output/dmc_facetgrid.png` | Dynamic Momentum Coefficient facet grid |
| `output/tce_donut.png` | Title Conversion Efficiency donut chart |
| `output/h2h_heatmap.png` | Head-to-Head win matrix heatmap |
| `output/era_chase_bat_bar.png` | Batting first vs chasing across eras |
| `output/season_win_trend.png` | Season-by-season team win rate trends |
| `output/venue_toss_heatmap.png` | Venue × Toss Decision interaction |
| `output/super_over_bar.png` | Super Over results by team |
| `output/pom_wordcloud.png` | Player of Match frequency word cloud |

---

## 2. Dataset Summary

| Attribute | Value |
|-----------|-------|
| Total matches | **1,024** |
| Seasons covered | **2008 – 2023 (16 seasons)** |
| Unique teams | **18** (including defunct franchises) |
| Unique venues | **56** |
| League stage matches | **972** |
| Playoff matches | **52** |
| Matches won by wickets | **542 (52.9%)** |
| Matches won by runs | **468 (45.7%)** |
| Super Over (tie) matches | **14 (1.4%)** |
| Average winning margin | **30.1 runs** / **6.2 wickets** |
| Biggest win (runs) | **146 runs** |
| Biggest win (wickets) | **10 wickets** |

> **Data cleaning applied:** The `Player_of_Match` column contained list-style formatting (e.g., `['AB de Villiers']`) which was stripped to plain names before analysis.

---

## 3. Toss & Strategy Metrics

### 3.1 Toss Decision Yield (TDY)
**Chart:** `tdy_grouped_bar.png` — Grouped bar chart showing win rate after winning the toss and choosing to bat or field, per team.

**What it measures:** Does winning the toss and choosing a specific strategy (bat first vs. chase) actually translate into wins?

#### Key Findings

| Metric | Value |
|--------|-------|
| Overall toss winner win rate | **51.1%** |
| Win rate when choosing to bat (after toss win) | **45.7%** |
| Win rate when choosing to field (after toss win) | **54.1%** |
| Overall chase win rate (across all matches) | **54.2%** |

- **Chasing is the dominant strategy** across all 16 seasons. Teams that win the toss and choose to field win at a rate of 54.1%, compared to just 45.7% for those who choose to bat.
- The toss itself only provides a marginal edge (51.1% win rate) — the advantage comes entirely from the **decision to chase**, not from winning the toss per se.
- Teams like Chennai Super Kings and Mumbai Indians have historically leveraged the toss-and-chase combination more effectively than others.

---

### 3.2 Toss Advantage Coefficient (TAC)
**Chart:** `tac_scatter.png` — Scatter plot comparing win rate when toss is won vs. lost. Teams above the diagonal benefit more from winning the toss; teams circled in red have TAC > 1.5 (extreme toss dependency).

**Formula:** `TAC = Win% when toss won / Win% when toss lost`

**Interpretation:**
- TAC = 1.0 → Toss has no impact on performance
- TAC > 1.5 → Team is extremely toss-dependent
- TAC < 1.0 → Team performs *better* when they lose the toss (rare)

#### Key Finding
Most established franchises (CSK, MI, KKR) cluster near the diagonal — indicating their win rates are driven by squad quality, not toss luck. Teams with fewer resources and shorter IPL histories show higher TAC values, suggesting they rely more on favorable conditions.

---

## 4. Team Dominance & Resilience

### 4.1 All-Time Team Win Rates

| Team | Wins | Matches | Win Rate |
|------|------|---------|----------|
| **Gujarat Titans** | 23 | 33 | **69.7%** |
| **Chennai Super Kings** | 131 | 224 | **58.5%** |
| **Lucknow Super Giants** | 17 | 30 | **56.7%** |
| **Mumbai Indians** | 140 | 247 | **56.7%** |
| **Delhi Capitals** | 41 | 77 | **53.2%** |
| **Kolkata Knight Riders** | 120 | 237 | **50.6%** |
| **Rajasthan Royals** | 103 | 206 | **50.0%** |
| Royal Challengers Bangalore | 116 | 240 | 48.3% |
| Sunrisers Hyderabad | 79 | 166 | 47.6% |
| Kings XI Punjab | 88 | 190 | 46.3% |
| Pune Warriors | 12 | 46 | 26.1% |

> Note: Gujarat Titans' 69.7% rate is over only 33 matches (2022–23). CSK and MI's rates are the most statistically significant given their 224 and 247 matches respectively.

---

### 4.2 Margin-Weighted Dominance Index (MWDI)
**Chart:** `mwdi_box.png` — Box and whisker plot showing the distribution of normalized win margins per team. A high median means the team wins by dominant margins consistently; a wide box indicates inconsistency.

**What it measures:** Clinical nature of victories — does the team win convincingly or just scrape through?

**Normalization:** Run-based and wicket-based margins are normalized separately to a [0, 1] scale within their respective groups before comparison.

#### Key Findings
- **Chennai Super Kings** consistently shows a high median normalized margin, indicating they don't just win — they win comfortably.
- **Royal Challengers Bangalore** shows a wide interquartile range: highly inconsistent, capable of both dominant wins and narrow victories.
- The average IPL match is won by **30.1 runs** or **6.2 wickets**, suggesting most wins are decisive rather than razor-thin.

---

### 4.3 Close-Match Resilience Index (CMRI)
**Chart:** `cmri_diverging.png` — Diverging bar chart. Teams to the right of the centerline win a higher-than-average proportion of close matches; teams to the left underperform in clutch situations.

**Definition of a "close match":**
- Win by ≤ 10 runs, OR
- Win by ≤ 3 wickets, OR
- Match decided by Super Over (tie)

**Formula:** `CMRI = Close Wins / Total Close Games played`

| Team | Close Wins | Close Games | CMRI |
|------|-----------|-------------|------|
| **Punjab Kings** | 5 | 7 | **71.4%** |
| **Rajasthan Royals** | 23 | 34 | **67.6%** |
| **Delhi Capitals** | 8 | 13 | **61.5%** |
| **Gujarat Lions** | 3 | 5 | **60.0%** |
| **Lucknow Super Giants** | 6 | 10 | **60.0%** |
| Royal Challengers Bangalore | 20 | 34 | 58.8% |
| Chennai Super Kings | 15 | 34 | 44.1% |
| Kolkata Knight Riders | 18 | 45 | 40.0% |
| **Delhi Daredevils** | 9 | 28 | **32.1%** *(worst)* |

> Total close matches across 1,024 games: **169** (16.5% of all matches)

**Key Finding:** Rajasthan Royals are the standout clutch team with 23 close-match wins — the most of any team. Despite their moderate overall win rate (50.0%), they punch above their weight in pressure situations.

---

## 5. Venue & Ground Conditions

### 5.1 Venue Bias Score (VBS)
**Chart:** `vbs_horizontal_bar.png` — Horizontal ranked bar chart. Green bars = chasing-friendly venues (VBS > 0.55); red bars = defending-friendly (VBS < 0.45); orange = neutral.

**Formula:** `VBS = Chases won / Total matches at venue`

| Venue | VBS | Bias | Matches |
|-------|-----|------|---------|
| Punjab CA IS Bindra Stadium | **0.60** | Chase | 10 |
| Maharashtra CA Stadium | **0.59** | Chase | 22 |
| M Chinnaswamy Stadium | ~0.50 | Neutral | — |
| **Subrata Roy Sahara Stadium** | **0.00** | Defend | 16 |
| **MA Chidambaram Stadium, Chepauk** | **0.08** | Defend | 48 |
| Dubai International Cricket Stadium | 0.24 | Defend | 46 |
| Wankhede Stadium | 0.36 | Defend | 73 |
| Feroz Shah Kotla | 0.32 | Defend | 60 |

**Key Findings:**
- **Chepauk (Chennai)** is the most defend-friendly major venue in the IPL — batting first teams win **92% of the time** at Chepauk. This is likely driven by a slow, turning pitch that makes chasing difficult.
- **Wankhede (Mumbai)** also favors batting first despite being a high-scoring ground — the dew factor doesn't seem to overcome the pitch and conditions.
- Only **2 of 56 venues** clearly favor chasing (VBS > 0.55), suggesting defending is generally advantageous when conditions are controlled, and the overall chasing edge comes from the toss winner's strategy choice.

---

### 5.2 Fortress Dominance Ratio (FDR)
**Chart:** `fdr_radar.png` — Radar (spider) chart comparing Home Win Rate vs. Away Win Rate for the top 8 franchises.

**Formula:** `FDR = Home Win% / Away Win%`  
Note: Home match defined as Team1's city ground in league stage only (playoffs excluded as neutral venues).

**Key Findings:**
- **Chennai Super Kings** display the most pronounced home advantage — their home record at Chepauk significantly outpaces their away performance.
- **Kolkata Knight Riders** at Eden Gardens similarly show a strong home fortress effect.
- Teams like **Royal Challengers Bangalore** have a smaller FDR, suggesting their performance is more consistent regardless of venue.

---

## 6. Squad Dependency & Star Power

### 6.1 Player of Match (POM) Concentration Index
**Chart:** `pom_treemap.png` — Treemap where tile size = total POM awards won by the team, and tile color = concentration index (green = collective effort, red = star-dependent).

**Method:** Modified Herfindahl-Hirschman Index (HHI):  
`Concentration = 1 − Σ(player_share²)`  
High value (→ 1.0) = awards distributed widely across many players = collective team effort  
Low value (→ 0.0) = dominated by one or two players

**Key Findings:**
- Teams with lower concentration scores (more star-dependent) are typically those built around a single match-winner (e.g., CSK era with MS Dhoni, or RCB with ABD/Kohli).
- More balanced concentration scores indicate deep squads where multiple players can step up on any given day.

---

### 6.2 Player of Match Leaders

| Rank | Player | Total POM Awards |
|------|--------|-----------------|
| 1 | **AB de Villiers** | **25** |
| 2 | **CH Gayle** | **22** |
| 3 | **RG Sharma (Rohit)** | **19** |
| 4 | **DA Warner** | **18** |
| 5 | **MS Dhoni** | **17** |
| 6 | **SR Watson** | **16** |
| 7 | **V Kohli** | **16** |
| 8 | **YK Pathan** | **16** |
| 9 | **KA Pollard** | **14** |
| 10 | **RA Jadeja** | **14** |

> AB de Villiers leads all-time with 25 POM awards — averaging a match-winning performance every 9.6 matches he played.

---

### 6.3 Big-Match Performance Index (BMPI)
**Chart:** `bmpi_dot.png` — Dot plot where x = total POM wins, y = playoff POM wins, dot size and color = BMPI ratio. Players in the top-right with large dots are the true "big game" performers.

**Formula:** `BMPI = Playoff POM wins / Total POM wins`

**Top Playoff Performers (by Playoff POM wins):**

| Player | Playoff POMs | Total POMs | BMPI |
|--------|-------------|------------|------|
| KA Pollard | 3 | 14 | 0.21 |
| F du Plessis | 3 | — | — |
| SR Watson | 2 | 16 | 0.13 |
| MK Pandey | 2 | — | — |
| A Kumble | 2 | — | — |

**Key Finding:** Kieron Pollard's playoff POM rate (3 out of 14 total) is particularly impressive — he performs at his best when the stakes are highest.

---

## 7. Temporal & Historical Trends

### 7.1 Dynamic Momentum Coefficient (DMC)
**Chart:** `dmc_facetgrid.png` — Seaborn FacetGrid with one panel per team. Each line shows rolling 3-match win rate across the season, colored by year, showing how teams build and lose momentum.

**Key Findings:**
- **Chennai Super Kings** typically show consistent momentum: their win rate rarely drops below 40% for extended stretches in any season.
- **Royal Challengers Bangalore** exhibit high volatility — dramatic momentum swings within seasons, which aligns with their history of strong starts followed by collapse (or vice versa).
- Most teams peak in the mid-season and tend to either consolidate (playoff qualifiers) or decline (bottom-half teams) as the season progresses.

---

### 7.2 Title Conversion Efficiency (TCE)
**Chart:** `tce_donut.png` — Concentric donut chart where the outer ring shows finals reached and the inner ring shows finals won.

**Formula:** `TCE = Finals Won / Finals Reached`

| Team | Finals Won | Finals Reached | TCE |
|------|-----------|----------------|-----|
| **Mumbai Indians** | **5** | **6** | **83%** ← Best |
| **Kolkata Knight Riders** | 2 | 3 | 67% |
| **Chennai Super Kings** | 5 | 10 | 50% |
| Rajasthan Royals | 1 | 2 | 50% |
| Sunrisers Hyderabad | 1 | 2 | 50% |
| Gujarat Titans | 1 | 2 | 50% |
| Deccan Chargers | 1 | 1 | 100% |

**Key Findings:**
- **Mumbai Indians** are the most clinically efficient title-winning team: 5 championships from just 6 final appearances (83% TCE). When they make the final, they almost always win.
- **Chennai Super Kings** have the most final appearances (10) but a lower conversion rate (50%), highlighting their consistency in reaching the biggest stage even if not always winning it.
- **Royal Challengers Bangalore** — despite 240 matches and a competitive record — have never won the IPL title, making them the most high-profile example of playoff underperformance.

---

## 8. Additional Insights

### 8.1 Head-to-Head Top Rivalries

| Rivalry | Wins (Team A) | Wins (Team B) | Total Matches |
|---------|--------------|--------------|---------------|
| Mumbai Indians vs Royal Challengers | 18 | 14 | 32 |
| Mumbai Indians vs Delhi Capitals | 18 | 15 | 33 |
| **Mumbai Indians vs Kolkata Knight Riders** | **23** | **9** | **32** |
| Kolkata Knight Riders vs Punjab Kings | 21 | 11 | 32 |
| Royal Challengers vs Delhi Capitals | 18 | 11 | 30 |

**Key Finding:** Mumbai Indians dominate their H2H record against Kolkata Knight Riders (23–9 in 32 matches), a rivalry between two of the most successful franchises in the league.

---

### 8.2 Era Analysis — Batting First vs. Chasing

| Era | Matches | Bat First Wins | Chase Wins |
|-----|---------|---------------|------------|
| Era 1 (2008–13) | 398 | **46.2%** | 53.8% |
| Era 2 (2014–18) | 298 | **43.6%** | 56.4% |
| Era 3 (2019–23) | 328 | **47.3%** | 52.7% |

**Key Findings:**
- Chasing has been dominant in every era, but **Era 2 (2014–18)** showed the strongest chasing advantage (56.4%), possibly due to more batsman-friendly pitches and improved T20 chasing techniques during that period.
- **Era 3 (2019–23)** shows a slight reversion — teams batting first recovered slightly, possibly due to UAE venues (2021 season) where dew was less of a factor, making conditions more equal.

---

### 8.3 Super Over Analysis

**14 matches** (1.4% of all IPL games) were decided by Super Over between 2008–2023.

**Notable patterns:**
- **2021** had 5 Super Overs in a single season — the highest ever, likely influenced by highly competitive conditions during the UAE leg.
- **Delhi Capitals** appeared in 4 Super Overs (2019 × 1, 2021 × 2), winning 3 — the best Super Over record.
- **Mumbai Indians** appeared in 3 Super Overs, winning 2.
- **Kings XI Punjab** appeared in 3, winning 2.

---

### 8.4 Venue-Toss Decision Interaction

**Chart:** `venue_toss_heatmap.png` — Heatmap showing win rate of toss winner when they choose "bat" vs. "field" at each venue.

**Key Findings:**
- At **Chepauk (MA Chidambaram Stadium)**, toss winners who choose to bat win at an unusually high rate — reinforcing that this is a pitch where batting first is the correct strategy regardless of conditions.
- At most **UAE venues** (Dubai, Sharjah, Abu Dhabi), fielding first after winning the toss is clearly the right call, as dew makes chasing easier in the second half.
- The **Eden Gardens (Kolkata)** shows a more balanced profile, making toss decisions there less clear-cut.

---

## 9. Key Takeaways

| # | Finding | Evidence |
|---|---------|----------|
| 1 | **Chasing wins** — fielding first is the better toss strategy overall | 54.2% chase win rate vs. 45.8% for batting first |
| 2 | **Chepauk is a batters' fortress** — almost impossible to chase at | VBS = 0.08 (batting first wins 92% of the time) |
| 3 | **Mumbai Indians are the most efficient champions** | 83% TCE — 5 titles from 6 finals |
| 4 | **Rajasthan Royals are the best clutch team** | 67.6% CMRI — best among teams with 30+ close games |
| 5 | **AB de Villiers is the greatest match-winner** in IPL history | 25 POM awards — most all-time |
| 6 | **CSK are the most consistent franchise** | 58.5% win rate over 224 matches; most finals appearances (10) |
| 7 | **RCB are the most star-dependent and least consistent** | High volatility in DMC; highest POM concentration; 0 titles |
| 8 | **Toss matters less than strategy** | Toss winner wins only 51.1% of matches — barely above chance |
| 9 | **Era 2 (2014–18) was the golden era of chasing** | 56.4% chase win rate — highest of the three eras |
| 10 | **2021 was the year of drama** — 5 Super Overs in one season | More Super Overs than any other single season |

---

## 10. How to Run the Analysis

### Prerequisites

```bash
pip install pandas matplotlib seaborn plotly squarify wordcloud
```

### Run the Analysis

```bash
python workflows/ipl_analysis.py
```

This generates all 16 charts + the interactive HTML dashboard in the `output/` folder. Expected runtime: ~60–90 seconds.

### View the Dashboard

Open `output/ipl_dashboard.html` in any modern browser (Chrome, Firefox, Edge). An internet connection is required to load the Plotly library from CDN.

### Project Structure

```
IPL Analysis/
├── CLAUDE.md                          # Analysis specifications
├── ANALYSIS_REPORT.md                 # This report
├── Dataset/
│   └── IPL_Dataset(2008 - 2023).csv   # Source data (1,024 matches)
├── workflows/
│   └── ipl_analysis.py                # Full analysis script
└── output/
    ├── ipl_dashboard.html             # Interactive dashboard
    └── *.png                          # 16 individual charts
```

---

*Analysis performed using Python (pandas, matplotlib, seaborn, plotly, squarify, wordcloud). Data source: IPL matches 2008–2023.*
