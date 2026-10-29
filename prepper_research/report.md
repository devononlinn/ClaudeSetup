# YouTube prepper niche — growth check, 2026-10-28

## Verdict: **Growing** (confidence: **medium**)

Measured on home-preparedness videos only (English, keyword-classified; see note). The raw search results are about half off-topic.

| # | Number | Last 90 days | Same 90 days, 2025 | Type |
|---|---|---|---|---|
| 1 | Core-prep videos with >50K views | **225** | 129 (**+74%**) | measured |
| 2 | Median views per core-prep video | **78,030** | 33,224 (**2.35×**) | measured |
| 3 | Median-views growth on grid and emergency queries ("power grid failure" / "emergency preparedness" / "grid down") | **9.0× / 6.1× / 4.2×** | 1.0× baseline | measured |

The age bias works against the result: year-ago videos have had about 12 more months to collect views and still lose on counts and medians. The previous quarter (2026-05-01→07-29, about 3 months older) shows the same jump: 152 → 225 videos over 50K, median 37,159 → 78,030 (measured).

**Why the confidence is only medium:**
- **The growth is news-driven.** The core-prep sample for the last 90 days has 42 titles tied to three events (counted from titles; the events themselves not independently checked):
  - US national emergency over power-grid parts (videos from 2026-08-27)
  - UK government stockpiling guidance (2026-08-26 → 10-27; BBC video at 1.45M views)
  - Pentagon grid / "doomsday" planning (2026-10-26 → 10-28)

  News spikes fade. Google Trends would have shown whether search interest is a trend or a spike, but it was blocked (step 8 below).
- **Total views don't confirm it:**
  - Year-ago core videos: 195.7M total. Last 90 days: 89.9M (measured).
  - Without each window's top 5: 80.9M vs 63.5M (measured).
  - The age bias explains most of this gap but can't be measured exactly with this API, which reports lifetime views only.
- **Broad queries fell year on year:**
  - "prepper": 0.53× median
  - "prepping": 0.32× median
  - "go bag": 0.37× median
  - "food storage prepping": 0.47× median

  All measured, but these rest on only 9–23 relevant videos per query. The growth is in specific topics (grid, emergency, earthquake, 72-hour kits), not the generic label.
- **This is a sample, not the whole niche:** the top 50 by views per query (16 queries), as YouTube's search returns them.

**Room for a new faceless channel: yes (measured counts, estimated faceless split).**
- 12 channels created in the last 12 months had a core-prep video over 100K views in the last 90 days. That counts the 8-channel first-aid-kit seller network as one.
- By manual guess, 8 of the 12 are faceless. The other 4 are 2 on-camera and 2 unclear.
- 29% of last-90 core videos (100/340) beat 5× their channel's subscriber count.
- Those 340 videos come from 238 channels. In 12 of 15 subtopics, the top channel holds ≤40% of the views.

**Steps incomplete:** Step 8 (Google Trends) was skipped. The environment's network policy blocks trends.google.com (proxy returned 403; error saved in `cache/trends_error.txt`). `trends.py` is included and runs unchanged where that host is reachable. All other steps are complete, including the optional third window.

**Quota:** 4,870 units (48 search.list = 4,800; 41 videos.list; 29 channels.list), measured from `cache/quota_ledger.json`. Reruns cost 0.

## Method notes (read before the tables)

- **Search:** per query and window, `order=viewCount`, `maxResults=50`, `regionCode=US`, `relevanceLanguage=en`, `type=video`.
- **Shorts:** duration ≤180 s or "#short" in the title or description.
- **Views are lifetime views** at collection time (2026-10-28/29). Older windows have had more time to accrue, so last-90 numbers are understated against both comparison windows.
- **Relevance filter (`classify.py`):** each video is labelled *core prep*, *wilderness/bushcraft* or *off-topic*, plus a non-English flag.
  - Off-topic examples: meal prep, Avengers: Doomsday, fashion "go-to bags".
  - A hand audit of 80 random videos puts precision at about 90% (estimated).
  - Bushcraft/log-cabin Shorts are excluded because they're a different audience. They are 74% of all views returned in the last 90 days, mostly copies of the same "Building Wooden Log Cabin in Forest" Shorts across dozens of channels (measured).
- **Themes:** first matching keyword rule wins, one theme per video (estimated grouping).
- **"Faceless":** judged from titles and descriptions only; no video was watched. Every label is a guess.

## Tables

### 0. What the searches actually return (share of unique videos, all 16 queries) — measured; categories are keyword-classified (≈90% precision on an 80-video hand audit — estimated)

| Window | Unique videos | Core prep (English) | Wilderness/bushcraft | Off-topic | Non-English | Bushcraft share of views |
|---|---|---|---|---|---|---|
| yoy90 | 649 | 48% | 18% | 31% | 12% | 55% |
| prev90 | 698 | 48% | 14% | 34% | 15% | 67% |
| last90 | 702 | 48% | 18% | 31% | 14% | 74% |

**All tables below use core-prep English videos only** unless stated.

### 4a. Window totals (unique core-prep videos across all 16 queries) — measured

| Window | Unique videos | >50K views | Median views | Total views | Median views/day | Shorts share | Distinct channels | Top-5 videos' share of total views |
|---|---|---|---|---|---|---|---|---|
| yoy90 (2025-07-30→10-28) | 325 | 129 | 33,224 | 195,705,398 | 79 | 45% | 245 | 56% |
| prev90 (2026-05-01→07-29) | 350 | 152 | 37,159 | 76,914,887 | 262 | 32% | 267 | 43% |
| last90 (2026-07-30→10-28) | 340 | 225 | 78,030 | 89,904,829 | 1,613 | 31% | 238 | 29% |

### 4b. Per query: core-prep videos inside each top-50 result set — measured (YoY = last90 median ÷ yoy90 median)

| Query | >50K (yoy/prev/last) | Median views (yoy/prev/last) | YoY median | Shorts share | Distinct channels | Core-prep videos of 50 (yoy/prev/last) |
|---|---|---|---|---|---|---|
| prepper | 11 / 21 / 10 | 2,151,642 / 463,114 / 1,138,784 | 0.53× | 36% / 29% / 30% | 10 / 15 / 9 | 11 / 21 / 10 |
| prepping | 4 / 11 / 12 | 1,980,718 / 710,566 / 758,242 | 0.38× | 50% / 36% / 25% | 4 / 11 / 11 | 4 / 11 / 12 |
| doomsday prep | 20 / 6 / 18 | 76,096 / 19,835 / 114,940 | 1.51× | 50% / 58% / 40% | 25 / 22 / 20 | 34 / 24 / 20 |
| power grid failure | 8 / 16 / 34 | 10,366 / 32,552 / 93,666 | 9.04× | 28% / 18% / 14% | 30 / 35 / 34 | 32 / 38 / 44 |
| grid down | 11 / 13 / 37 | 34,815 / 19,687 / 145,935 | 4.19× | 26% / 8% / 8% | 24 / 31 / 30 | 27 / 39 / 40 |
| emergency preparedness | 9 / 9 / 31 | 20,838 / 4,424 / 127,493 | 6.12× | 61% / 47% / 16% | 37 / 32 / 24 | 38 / 36 / 31 |
| bug out bag | 32 / 14 / 34 | 85,718 / 50,066 / 98,408 | 1.15× | 21% / 7% / 53% | 31 / 23 / 30 | 38 / 28 / 38 |
| go bag | 5 / 3 / 9 | 421,452 / 305,170 / 155,655 | 0.37× | 40% / 0% / 22% | 5 / 3 / 8 | 5 / 3 / 9 |
| 72 hour kit | 10 / 7 / 16 | 30,290 / 19,709 / 58,764 | 1.94× | 41% / 16% / 40% | 27 / 21 / 28 | 32 / 25 / 30 |
| food storage prepping | 11 / 25 / 23 | 544,945 / 95,780 / 254,704 | 0.47× | 27% / 3% / 9% | 9 / 23 / 20 | 11 / 32 / 23 |
| garage prepper | 2 / 1 / 0 | 24,214 / 480 / 300 | 0.01× | 33% / 67% / 23% | 6 / 6 / 13 | 6 / 6 / 13 |
| earthquake preparedness | 9 / 5 / 13 | 25,361 / 45,120 / 86,027 | 3.39× | 70% / 56% / 50% | 27 / 17 / 16 | 30 / 18 / 18 |
| hurricane prep | 19 / 6 / 15 | 35,827 / 1,518 / 36,016 | 1.01× | 63% / 51% / 57% | 37 / 37 / 32 | 41 / 43 / 40 |
| wildfire evacuation | 13 / 37 / 35 | 35,348 / 113,678 / 66,740 | 1.89× | 51% / 42% / 40% | 24 / 27 / 30 | 43 / 38 / 47 |
| EMP prep | 3 / 0 / 2 | 1,023 / 268 / 124 | 0.12× | 23% / 17% / 13% | 22 / 20 / 26 | 26 / 23 / 31 |
| off grid survival | 1 / 0 / 0 | 2,415,218 / 0 / 0 | 0.00× | 0% / 0% / 0% | 1 / 0 / 0 | 1 / 0 / 0 |

Queries where last-90 median beats year-ago median: **9/16**; where last-90 >50K count beats year-ago: **10/16** (measured).

### 5. New entrants — channels created on/after 2025-10-28 with a >100K-view core-prep video in the last 90 days

Qualifying channels found: **12** (measured). Ranked by summed views of their videos in our last-90 sample. The 'First aid kit…' channels (same name, one shared WhatsApp contact) and are merged into one row (subs/uploads summed). Faceless/on-camera is judged from titles + descriptions only — a guess.

| # | Channel | Subs | Created | Uploads | Best video | Views | Short? | Faceless? (guess) |
|---|---|---|---|---|---|---|---|---|
| 1 | First aid kit factory (network of 8 channels) | 19,112 | 2025-12-12 | 1010 | [#firstaidkit #healthy #emegencykit #bugoutbag #prepper](https://www.youtube.com/watch?v=-3klw2hPbmI) | 4,050,271 | Y | faceless: product B-roll Shorts from one seller (manual guess) |
| 2 | TACTIXLAB | 7,380 | 2026-07-21 | 75 | [Firearms Expert Reveals 5 Must Have Survival Items](https://www.youtube.com/watch?v=bBtFD1pl8aA) | 4,420,971 | Y | faceless: re-cut clips of military podcasts (manual guess) |
| 3 | Galactic Highway | 91,400 | 2026-06-18 | 34 | [Bunker Survival 1 Year](https://www.youtube.com/watch?v=RmyjNoz2pw4) | 2,191,920 | N | faceless: animated scenarios (manual guess) |
| 4 | Sadik_lifestyle2.0 | 20,900 | 2025-12-24 | 218 | [🇯🇵Would you try Japan’s earthquake simulator? 😱#japan #earthquake #sho](https://www.youtube.com/watch?v=KD4Iv_8b2e0) | 1,317,863 | Y | faceless: facts + voice-over (manual guess) |
| 5 | Be Prepared UK | 8,500 | 2026-09-11 | 37 | [UK Government Says Prepare: But What Aren't They Telling Us?](https://www.youtube.com/watch?v=LCRFQuk3hME) | 337,851 | N | unclear (manual guess) |
| 6 | The Sensei's Home | 7,060 | 2026-06-15 | 57 | [If The Grid Fails Tomorrow, Every Japanese Home Already Has These 7 Th](https://www.youtube.com/watch?v=7mZa4nlB1jg) | 368,099 | N | faceless: narrated listicles (manual guess, low confidence) |
| 7 | One More Day | 5,810 | 2026-10-08 | 29 | [Doomsday: 7 Days To Prepare Before Everything Collapses](https://www.youtube.com/watch?v=JEFq2fJVW3w) | 465,873 | N | faceless: animated survival story (manual guess) |
| 8 | DoomPrep | 12,200 | 2025-11-30 | 116 | [The 10 UK Locations The Government Has Already Written Off In A Grid C](https://www.youtube.com/watch?v=orl3qGAe3rI) | 222,548 | N | faceless: narrated document breakdowns (manual guess) |
| 9 | Bunker Bob | 3,380 | 2026-08-19 | 20 | [The Secret Survival Kit Hobby Lobby Still Sells to Anyone (No Permit R](https://www.youtube.com/watch?v=90FxBZ0scIA) | 409,640 | N | unclear: 'Bob' mascot/persona (manual guess) |
| 10 | Christy Ladd / HelloVestavia | 559 | 2026-03-21 | 58 | [Hurricane prep part 3](https://www.youtube.com/watch?v=yEWQldakOI8) | 232,072 | Y | on-camera: lifestyle creator (manual guess) |
| 11 | Grid Atlas | 846 | 2026-10-16 | 6 | [If the US Power Grid Failed, These States Go Dark First (All 50 Ranked](https://www.youtube.com/watch?v=dF2jbfYirlU) | 307,097 | N | faceless: data/ranking explainer (manual guess) |
| 12 | She Prepares | 51,900 | 2026-02-20 | 65 | [I Found The Best Forever Foods To Stockpile At Sam’s Club](https://www.youtube.com/watch?v=nSP8vMn1ijQ) | 127,277 | N | on-camera: personal vlog (manual guess) |

### 6. Outliers — last-90 core-prep videos with views > 5× channel subscribers

Outliers: **100** of 340 last-90 videos (29%), measured. Top 20 ranked by views (ranking by raw ratio is dominated by <100-sub channels).

| # | Title | Views | Subs | Ratio | Short? | Theme |
|---|---|---|---|---|---|---|
| 1 | [Keeping my kids safe during a hurricane 🌪️❤️ #hurricane #florida #safetytip](https://www.youtube.com/watch?v=9Bwe8JsAPQQ) | 10,042,945 | 44,600 | 225× | Y | specific disasters |
| 2 | [The first thing I do when I receive a hurricane warning🌪️ #shorts #hurrican](https://www.youtube.com/watch?v=wwNaw8D2p7M) | 4,685,776 | 349,000 | 13× | Y | specific disasters |
| 3 | [Firearms Expert Reveals 5 Must Have Survival Items](https://www.youtube.com/watch?v=bBtFD1pl8aA) | 4,420,971 | 7,380 | 599× | Y | what to buy / stockpile lists |
| 4 | [#firstaidkit #healthy #emegencykit #bugoutbag #prepper](https://www.youtube.com/watch?v=-3klw2hPbmI) | 4,050,271 | 1,140 | 3553× | Y | bug-out / go-bag / kits |
| 5 | [#healthy #firstaidkit#bugoutbag #emegencykit #prepper](https://www.youtube.com/watch?v=ymp82EqyU0M) | 3,204,752 | 4,240 | 756× | Y | bug-out / go-bag / kits |
| 6 | [Bunker Survival 1 Year](https://www.youtube.com/watch?v=RmyjNoz2pw4) | 2,191,920 | 91,400 | 24× | N | scenario / fiction |
| 7 | [Surviving Power Outages / Storm Prep / EcoFlow Home Backup Solutions / Delt](https://www.youtube.com/watch?v=3jPucpWphR0) | 1,692,229 | 309,000 | 5× | N | grid / power |
| 8 | [The Problem With America’s Power Grid ft. Underwhelming Podcast](https://www.youtube.com/watch?v=BiaQXxu7wrM) | 1,618,661 | 199,000 | 8× | Y | grid / power |
| 9 | [You Only Need These 6 Canned Foods to Survive Hard Times!](https://www.youtube.com/watch?v=BiWZG7D5Xfs) | 1,325,695 | 36,000 | 37× | N | food storage |
| 10 | [🇯🇵Would you try Japan’s earthquake simulator? 😱#japan #earthquake #shorts](https://www.youtube.com/watch?v=KD4Iv_8b2e0) | 1,317,863 | 20,900 | 63× | Y | specific disasters |
| 11 | [Everything We Know About the New Madrid Fault - And What We Got Wrong](https://www.youtube.com/watch?v=y93guHU5HPU) | 1,120,333 | 80,800 | 14× | N | specific disasters |
| 12 | [Bunker Survival 1 Year (Part 2)](https://www.youtube.com/watch?v=L_BJJVPGysg) | 1,085,645 | 91,400 | 12× | N | scenario / fiction |
| 13 | [PREPPING for the OIL CRISIS](https://www.youtube.com/watch?v=GgLnzNMZ0sc) | 1,026,409 | 29,900 | 34× | Y | government / news-driven |
| 14 | [#firstaidkit #healthy #emergencykit #bugoutbag#prepper](https://www.youtube.com/watch?v=BUcrgnxSceU) | 910,397 | 1,010 | 901× | Y | bug-out / go-bag / kits |
| 15 | [11 Dollar Tree Heating Items That'll Be WORTH GOLD in a Winter Blackout](https://www.youtube.com/watch?v=H1qCDI9DJmY) | 884,587 | 42,500 | 21× | N | what to buy / stockpile lists |
| 16 | [#firstaidkit  #healthy #emegencykit #bugoutbag #prepper](https://www.youtube.com/watch?v=vQrLzmlGHwk) | 855,384 | 4,580 | 187× | Y | bug-out / go-bag / kits |
| 17 | [#firstaidkit  #healthy #emegencykit #bugoutbag #prepper](https://www.youtube.com/watch?v=8rAYuh4UE9I) | 814,627 | 4,580 | 178× | Y | bug-out / go-bag / kits |
| 18 | [13 Must-Have Survival Tools To STOCKPILE Before Anyone Else Does Tools](https://www.youtube.com/watch?v=qf4-xtbaSfo) | 762,202 | 36,000 | 21× | N | what to buy / stockpile lists |
| 19 | [9 Foods Quietly Disappearing From Shelves (Preppers Are Buying Them FAST)](https://www.youtube.com/watch?v=BIEM2o_Fg4Y) | 567,204 | 5,300 | 107× | N | what to buy / stockpile lists |
| 20 | [15 Walmart Items Smart Preppers Are Quietly Buying Before October (All Unde](https://www.youtube.com/watch?v=r27PgmGTB84) | 552,560 | 32,700 | 17× | N | what to buy / stockpile lists |

### 7. Topic clusters — outlier + new-entrant videos, last 90 days (themes are keyword-assigned, one theme per video, first match wins)

| Theme | Outlier+new videos | Their views | Channels | Shorts share | All last-90 videos in theme | Outlier rate | Median views/subs | Channels ≥100K subs in theme | Top video |
|---|---|---|---|---|---|---|---|---|---|
| specific disasters | 15 | 18,148,814 | 13 | 67% | 94 | 16% | 0.28× | 41 | [Keeping my kids safe during a hurricane 🌪️❤️ #hurricane](https://www.youtube.com/watch?v=9Bwe8JsAPQQ) |
| bug-out / go-bag / kits | 22 | 11,759,012 | 12 | 91% | 35 | 63% | 10.29× | 10 | [#firstaidkit #healthy #emegencykit #bugoutbag #prepper](https://www.youtube.com/watch?v=-3klw2hPbmI) |
| what to buy / stockpile lists | 21 | 9,674,574 | 17 | 5% | 55 | 36% | 1.08× | 15 | [Firearms Expert Reveals 5 Must Have Survival Items](https://www.youtube.com/watch?v=bBtFD1pl8aA) |
| grid / power | 18 | 5,459,093 | 16 | 22% | 75 | 21% | 0.38× | 25 | [Surviving Power Outages / Storm Prep / EcoFlow Home Bac](https://www.youtube.com/watch?v=3jPucpWphR0) |
| scenario / fiction | 7 | 4,174,616 | 6 | 0% | 16 | 44% | 1.02× | 4 | [Bunker Survival 1 Year](https://www.youtube.com/watch?v=RmyjNoz2pw4) |
| government / news-driven | 11 | 2,204,597 | 8 | 9% | 17 | 59% | 7.38× | 4 | [PREPPING for the OIL CRISIS](https://www.youtube.com/watch?v=GgLnzNMZ0sc) |
| food storage | 2 | 1,774,168 | 2 | 50% | 7 | 29% | 1.70× | 2 | [You Only Need These 6 Canned Foods to Survive Hard Time](https://www.youtube.com/watch?v=BiWZG7D5Xfs) |
| other / unclassified | 6 | 676,976 | 6 | 50% | 28 | 21% | 0.33× | 15 | [British Prepping Is Different: What You ACTUALLY Need t](https://www.youtube.com/watch?v=hLLQc-1HvHM) |
| bunkers / off-grid / homestead | 2 | 107,963 | 2 | 50% | 10 | 20% | 0.46× | 4 | [20 Survival Essentials: What I Carry Every Time!](https://www.youtube.com/watch?v=pBvCwfIH3OI) |

### 9a. Gap inputs per subtopic — last 90 days, core-prep videos in each query's top 50 — measured

| Subtopic (query) | Core videos | Median views | YoY median | Outlier rate (>5× subs) | Channels ≥100K subs | Top channel's view share | New-entrant channels | Shorts share |
|---|---|---|---|---|---|---|---|---|
| prepper | 10 | 1,138,784 | 0.53× | 70% | 3 | 24% | 3 | 30% |
| prepping | 12 | 758,242 | 0.38× | 50% | 6 | 33% | 1 | 25% |
| doomsday prep | 20 | 114,940 | 1.51× | 40% | 10 | 24% | 2 | 40% |
| power grid failure | 44 | 93,666 | 9.04× | 30% | 16 | 19% | 3 | 14% |
| grid down | 40 | 145,935 | 4.19× | 18% | 19 | 15% | 4 | 8% |
| emergency preparedness | 31 | 127,493 | 6.12× | 29% | 16 | 24% | 3 | 16% |
| bug out bag | 38 | 98,408 | 1.15× | 55% | 10 | 29% | 8 | 53% |
| go bag | 9 | 155,655 | 0.37× | 22% | 5 | 33% | 1 | 22% |
| 72 hour kit | 30 | 58,764 | 1.94× | 43% | 10 | 40% | 9 | 40% |
| food storage prepping | 23 | 254,704 | 0.47× | 43% | 8 | 16% | 1 | 9% |
| garage prepper | 13 | 300 | 0.01× | 23% | 1 | 78% | 0 | 23% |
| earthquake preparedness | 18 | 86,027 | 3.39× | 39% | 5 | 30% | 2 | 50% |
| hurricane prep | 40 | 36,016 | 1.01× | 20% | 20 | 52% | 1 | 57% |
| wildfire evacuation | 47 | 66,740 | 1.89× | 6% | 23 | 17% | 0 | 40% |
| EMP prep | 31 | 124 | 0.12× | 23% | 2 | 52% | 0 | 13% |

## 5 gaps a new faceless channel could own

Chosen from tables 7 and 9a: high outlier rate, few channels ≥100K subs, a faceless format already working. All figures are measured from the last-90 core sample unless marked.

1. **72-hour kit / bug-out bag builds as product B-roll Shorts.**
   - "72 hour kit": median 1.94× year on year; 43% outliers; only 10 channels ≥100K subs; 9 new-entrant channels in its top 50, the most of any subtopic.
   - "bug out bag": 55% outliers; 8 new entrants.
   - Proof it works without a face: the first-aid-kit seller network (19K subs combined, no narration) got Shorts to 4.05M and 3.20M views.
   - Open angle (estimated): a US, non-seller channel doing kit builds by budget, household size and region.
2. **Plain-English decoders of official prep guidance (US).**
   - Government/news theme: 59% outliers, median 7.4× views/subs, only 4 channels ≥100K subs.
   - The UK version is already being taken. Be Prepared UK (created 2026-09-11, 8.5K subs) reached 338K; DoomPrep (12.2K subs) reached 223K.
   - No faceless US channel turned up doing the same for FEMA/Ready.gov lists, grid emergency declarations or Pentagon grid plans (estimated: absence from this sample).
   - Risk: depends on the news cycle.
3. **Animated survival scenarios ("7 days before collapse", "1 year in a bunker").**
   - Scenario theme: 44% outliers, 0% Shorts (long-form), only 4 channels ≥100K subs.
   - One More Day (created 2026-10-08, 5.8K subs, 29 uploads) reached 466K.
   - Galactic Highway (created 2026-06-18) is at 91.4K subs, with 2.19M on "Bunker Survival 1 Year".
   - Weak spot in the field (estimated): most scenarios are fiction-first. One that ends with a real checklist ties the story to practical prep.
4. **US earthquake / fault-line preparedness (New Madrid, Cascadia, California).**
   - "earthquake preparedness": median 86,027 (3.39× year on year); 39% outliers; only 5 channels ≥100K subs; 50% Shorts.
   - "Everything We Know About the New Madrid Fault" got 1.12M views on 80.8K subs (14×).
   - Unlike hurricane prep, where one channel holds 52% of views, no single channel owns this.
5. **Store-specific budget stockpile lists (Dollar Tree / Walmart / Sam's / Hobby Lobby), seasonal.**
   - Lists theme: 55 videos, 36% outliers, 5% Shorts.
   - Outliers: "11 Dollar Tree Heating Items… Winter Blackout" 885K on 42.5K subs (21×); "9 Foods Quietly Disappearing From Shelves" 567K on 5.3K (107×); "15 Walmart Items…" 553K on 32.7K (17×).
   - Bunker Bob (created 2026-08-19, 3.4K subs) reached 410K with a Hobby Lobby angle.
   - Winter-blackout lists can be published November–February (estimated timing).

**Avoid:**
- **"garage prepper":** median 300 views; 13 relevant videos in its top 50; 0 over 50K.
- **"EMP prep":** median 124 views; median 0.12× year on year.

There's almost no search demand for either (both measured).

## Files

- `collect.py`: API pulls with caching and a quota guard.
- `classify.py`: relevance filter.
- `analyze.py`: all tables and CSVs.
- `trends.py`: Google Trends pull (blocked here).
- `videos.csv`: 2,051 unique videos with category, English flag, Shorts flag, views/subs ratio and views/day.
- `new_channels.csv`: step 5.
- `cache/`: every raw API response plus the quota ledger.
