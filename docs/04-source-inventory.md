# Source Inventory & Traceability

Every claim in this repository traces back to one of two sources:

1. **The deck** — `BR_Training__New_Format.20160509.pdf`, "Best Rate Training", iHeartMedia,
   39 slides, file dated 2016-05-09. (Slide 31 footer still shows "Clear Channel Media +",
   a legacy branding artifact.) Cited below as **[S#]** (slide number).
2. **The transcript** — a phone conversation between "Me" (Ana) and "Them" (an executive who
   was part of the team that built the system). Cited as **[T]** with a quote or paraphrase.

Nothing else was used. Where the two sources disagree, or where a number in the deck is
internally inconsistent, it is logged in the Discrepancy Log at the bottom — not silently
resolved.

---

## Part 1 — Slide-by-slide inventory of the deck

### S1 — Title
iHeartMedia logo. Title banner: "Best Rate Training".

### S2 — BR5 overview
Diagram: three inputs feed one output.
- **Inventory forecasting** →
- **Reference prices** →
- **Market response models** →
- → **Final rate recommendation**

### S3 — Inventory forecast
Diagram (equation):
`Business on the books − Projected cancellations + Forecasted remaining demand = Forecast`

### S4 — Projecting cancellations
- Data criteria: 6 months' data (rolling); P40+ aired spots; 15s, 30s and 60s spot lengths;
  BR5 revenue types; market-specified break types.
- Calculation level: Market; Day of week; Number of days before air date.
- Example table (cancellation % by day of week × days left):

| Day of Week | 30 | 60 | 90 | 120 | 150 | 180 |
|---|---|---|---|---|---|---|
| Monday | 7% | 14% | 17% | 20% | 24% | 29% |
| Tuesday | 6% | 12% | 17% | 20% | 25% | 30% |
| Wednesday | 6% | 11% | 14% | 17% | 23% | 28% |
| Thursday | 6% | 12% | 16% | 18% | 23% | 29% |
| Friday | 6% | 11% | 15% | 17% | 22% | 27% |
| Saturday | 7% | 12% | 15% | 17% | 20% | 24% |
| Sunday | 7% | 11% | 15% | 17% | 19% | 22% |

- Footnote: "Contact James Liao to review cancellation rates for a market."
- Note: the example on S15 uses a 3% rate at **14 days** left, so the curve is stored at finer
  days-left granularity than this 30-day-step sample table.

### S5 — Forecasting remaining demand
Funnel diagram: **Average historical demand** + **Seasonality factor** + **% of business left
to be booked** → **Forecasted Remaining Demand**.

### S6 — Average historical demand
- Data criteria: 6 months' data (rolling); P40+ aired spots; 15s/30s/60s; BR5 revenue types;
  market-specified break types.
- Calculation level: Station; Day of week; Daypart.
- Example table (Wednesday AMD):

| Day of Week | Airdate | Daypart | Minutes Sold |
|---|---|---|---|
| Wednesday | 1/5/11 | AMD | 48 |
| Wednesday | 1/12/11 | AMD | 49 |
| Wednesday | 1/19/11 | AMD | 53 |
| Wednesday | 1/26/11 | AMD | 52 |
| Wednesday | 2/2/11 | AMD | 49 |
| Wednesday | 2/9/11 | AMD | 48 |
| Wednesday | 2/16/11 | AMD | 48 |
| Wednesday | 2/23/11 | AMD | 44 |

### S7 — Seasonality of demand
- Data criteria: **up to 3 years'** data, depending on data availability (rolling); P40+ aired
  spots; 15s/30s/60s; BR5 revenue types; market-specified break types.
- Calculation level: Station; Week of year; Day of week.

### S8 — Seasonality example
Table (2011 Wednesdays, whole-day minutes):

| Week of Year | Airdate | Minutes Sold | Avg Wed Minutes Sold | Seasonality Factor |
|---|---|---|---|---|
| 1 | 1/5/11 | 140 | 175 | 80% |
| 2 | 1/12/11 | 134 | 175 | 76% |
| 3 | 1/19/11 | 134 | 175 | 76% |
| 4 | 1/26/11 | 139 | 175 | 79% |
| 5 | 2/2/11 | 148 | 175 | 85% |
| 6 | 2/9/11 | 159 | 175 | 91% |
| 7 | 2/16/11 | 168 | 175 | 96% |
| 8 | 2/23/11 | 174 | 175 | 99% |
| 9 | 3/2/11 | 175 | 175 | 100% |
| 10 | 3/9/11 | 172 | 175 | 98% |

Chart: "Seasonality Factor: Wednesdays" oscillating around 100% across weeks 1–51.

### S9 — Deseasonalized demand
- Definition: "Typical demand for a given day of week & daypart after adjusting for any
  fluctuations due to the time of the year."
- Formula: `Deseasonalized Demand = Demand (Minutes Sold) / Seasonality Factor`
- Example table (Wednesday AMD):

| Airdate | Minutes Sold | Seasonality Factor | Deseasonalized Demand |
|---|---|---|---|
| 1/5/11 | 48 | 80% | 61 |
| 1/12/11 | 49 | 76% | 65 |
| 1/19/11 | 53 | 76% | 70 |
| 1/26/11 | 52 | 79% | 66 |
| 2/2/11 | 49 | 85% | 58 |
| 2/9/11 | 48 | 91% | 53 |
| 2/16/11 | 48 | 96% | 50 |
| 2/23/11 | 44 | 99% | 44 |

- Note: "6 months (26 weeks) of deseasonalized demand are averaged into one number for
  Wednesday AMD, **with recent weeks given more weight**."

### S10 — Deseasonalized demand (UI)
- Navigation: **Administration → Demand Level Override**.
- Screenshot: "Deseasonalized Demand" grid, dayparts × days of week, values in mm:ss.

| | M | Tu | W | Th | F | Sa | Su |
|---|---|---|---|---|---|---|---|
| AMD | 39:44 | 39:30 | 40:26 | 40:17 | 38:36 | 34:31 | 27:48 |
| MID | 43:33 | 43:56 | 45:36 | 45:08 | 44:20 | 54:51 | 42:13 |
| PMD | 35:33 | 34:04 | 35:43 | 27:25 | 34:32 | 32:32 | 28:10 |
| EVE | 41:55 | 35:56 | 42:54 | 43:43 | 40:53 | 35:23 | 30:09 |
| ON | 19:52 | 21:06 | 23:40 | 23:49 | 24:24 | 14:43 | 11:59 |
| 5Ato6A | 09:19 | 08:41 | 09:33 | 09:37 | 09:19 | 00:00 | 00:00 |
| 7Pto8P | 09:28 | 09:40 | 09:40 | 09:36 | 10:01 | 00:00 | 00:00 |

(Values transcribed from a screenshot; treat individual cells as approximate.)

### S11 — Booking curves
- Definition: "Historically, what % of business is on the books x days before airdate?"
- Data criteria: 2 years' data (rolling); P40+ aired spots; 15s/30s/60s; BR5 revenue types;
  market-specified break types.
- Calculation level: Station; **Month**; Day of week; Number of days before air date.

### S12 — Booking curve example
- "Wednesdays in February — booking curve based on the sum of bookings for 8 airdates
  (4 Wed in Feb 2010 + 4 Wed in Feb 2011)."

| Days Left | Minutes Booked | Cumulative Bookings | Booking Fraction |
|---|---|---|---|
| 14 | 78 | 78 | 8% |
| 13 | 78 | 156 | 15% |
| 12 | 73 | 229 | 22% |
| 11 | — | 229 | 22% |
| 10 | 2 | 230 | 22% |
| 9 | 80 | 310 | 30% |
| 8 | 138 | 448 | 44% |
| 7 | 106 | 554 | 54% |
| 6 | 244 | 798 | 78% |
| 5 | 118 | 916 | 89% |
| 4 | 2 | 918 | 89% |
| 3 | 3 | 921 | 90% |
| 2 | 29 | 949 | 93% |
| 1 | 76 | 1,025 | 100% |
| 0 | 0 | 1,026 | 100% |

(Transcribed verbatim; the three columns do not fully reconcile with each other — see
Discrepancy D8.)

### S13 — % of business left to be booked
`1 − Booking Fraction = % of Business Left` (mirrored charts).

### S14 — Putting it all together
```
Forecast = Business on the books − Projected cancellations + Forecasted remaining demand
Forecasted remaining demand = Deseasonalized demand × Seasonality factor × (1 − Booking fraction)
```
(`1 − Booking fraction` labeled "% of business left to be booked".)

### S15 — Forecasting example
"38 minutes on the books for Saturday, 4/13/13 AMD as of 3/30/13."
- Projected cancellations: 3% cancellation rate when 14 days left for Sat → **1 minute**.
- Remaining demand: 50 minutes (deseasonalized, Sat AMD) × 82% (seasonality, Week 15/Sat)
  × (1 − 90% booking fraction at 14 days left for April Sat) = 10% left → **4 minutes**.
- `38 − 1 + 4 = 41 minutes` forecast.

### S16 — Inventory forecast caps
- "Forecasts early in the booking curve are capped."
- "Prevents projected sellouts and rates from being too high when large buys are made during
  early stages of the booking curve."

| Actual Sellout | Max Forecast Sellout |
|---|---|
| 0–9% | 100% |
| 10–19% | 105% |
| 20–29% | 110% |
| 30–39% | 115% |
| 40%+ | 200% |

### S17 — Reference prices
- Data criteria: **1 year's data (rolling)**; P40+ aired spots; 15s/30s/60s; BR5 revenue
  types; market-specified break types.
- Additional filters:
  1. Include only commercial break types
  2. Exclude no charges
  3. Exclude rotators (depending on rotator preference)
  4. Exclude political and issue rates
  5. Exclude flight lengths > 98 days
  6. Exclude flights that include both weekdays and weekends
  7. Exclude Flexnet
  8. Exclude top 10% of rates
  9. Exclude bottom 10% of rates
- Calculation level: Station; Day of week; Daypart; **Number of weeks before airdate**.
- Output: "Results in **16 reference prices** for each day of week / daypart (in-week,
  1–14 weeks left and 15+ weeks left)."
- "Weighted towards more recent transactions; like the demand forecast, reference prices are
  **deseasonalized first with seasonality added back in later**."

### S18 — Reference price example
Monday AMD:

| Weeks Left | Rate |
|---|---|
| 15+ | $228 |
| 14 | $231 |
| 13 | $232 |
| 12 | $232 |
| 11 | $235 |
| 10 | $239 |
| 9 | $244 |
| 8 | $245 |
| 7 | $253 |
| 6 | $259 |
| 5 | $268 |
| 4 | $277 |
| 3 | $283 |
| 2 | $284 |
| 1 | $289 |
| In-Week | $289 |

Chart: monotonically rising curve from 15+ weeks out to in-week.

### S19 — MRM: elasticity
- Definition: "How much demand changes when rates go up or down."
- Data criteria: same filtering as reference price calculation.
- Calculation level: Station; **Weekday or weekend**; Daypart.
- UI symbols:
  - `$` (0 to −1.2) = inelastic ("demand does not decrease much in response to an increase in
    rate and vice versa")
  - `$$` (−1.2 to −1.6)
  - `$$$` (less than −1.6) = elastic ("demand decreases a lot in response to an increase in
    rate and vice versa")

### S20 — MRM: rate differentials
- Data criteria: same filtering as reference price calculation.
- Calculation level: Station; Day of week; Daypart.
- Example table:

| Day of Week | Daypart | Spot Length | AUR | AMR | Rate Differential | Relative to :60 Rate |
|---|---|---|---|---|---|---|
| Monday | AMD | 60 seconds | $232 | $232 | 95% | |
| Monday | AMD | 30 seconds | $132 | $264 | 108% | 57% |
| Monday | AMD | 15 seconds | $74 | $296 | 121% | 32% |
| | | All spot lengths | | $245 | | |

- Annotations: "Rate Differential" appears **on the reference price override screen**;
  "Relative to :60 Rate" appears **on the rate differential screen**.
- Arithmetic implied by the table (verifiable): `AMR = AUR × 60/length`;
  `Rate Differential = AMR(length) / AMR(all lengths)`; `Relative to :60 = AUR(length) / AUR(:60)`.

### S21 — MRM: rate differentials (UI)
- Navigation: **Preferences → Rate Differentials**.
- Screenshot: "Current Rate Differentials (%)" grid — rows AMD/MID/PMD/EVE/ON, columns
  Monday–Friday, each with :15 / :30 / :60 sub-columns. Callouts: the :15 and :30 cells are
  "% of :60"; the :60 cell (grayed) is "% of AMR". Legible sample values (approximate,
  from screenshot): Monday AMD 40 / 76 / 84; Monday EVE 55 / 85 / 75; Monday ON 13 / 48 / 102;
  Friday AMD 41 / 75 / 83. Weekend columns not visible in the screenshot.

### S22 — Max rate confusion
- "Max rate OTB = highest rate on the books."
- "'System rate greater than maximum rate' → max rate triggered":
  - "Forecasted demand is so high that BR5 is recommending a rate higher than anything on the
    books"; "This rate may be unsellable"; "To ensure reasonable rates, rates are capped."
- **"Max rate LOWERS rates"** / **"Max rate DOES NOT INCREASE rates"** (emphasis in original).

### S23 — Max rate methodology
Two trigger regimes, both requiring forecasted sellout > 100%:

| | Regime A | Regime B |
|---|---|---|
| Trigger | Forecasted sellout > 100% AND current sellout > 95% | Forecasted sellout > 100% AND current sellout between 40% and 95% |
| Cap (lower of) | System recommended rate; OR the **higher** of `max rate OTB × (1 + max rate tolerance)` or `avg rate OTB × 1.3 × (1 + max rate tolerance)` | System recommended rate; OR the **higher** of `90th percentile rate OTB × (1 + max rate tolerance)` or `avg rate OTB × 1.3 × (1 + max rate tolerance)` |

### S24 — Max rate example
Screenshot row (transcribed exactly):

| Air Date | Capacity | Elasticity | Booking Fraction | Original Reference Price | Adjusted Reference Price | Final Reference Price | Current Sold | Demand Forecast | System Price | Spot Length | Rate Differential | Target Rate | Opt Status | Max Rate OTB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 4/5/2011 | 21.0000 | −1.20000 | 0.957975 | 284.378 | 293.9902 | 300.00 | 21 | 22.25 | 530 | 60 | 0.949295 | 390.00 | Reference Override. System Rate Greater Than Maximum Rate. | 300 |

Bullets:
- Forecasted sellout = demand forecast / capacity → 22.25 / 21 = 106%
- Current sellout = current sold / capacity → 21 / 21 = 100%
- System rate = $530 × 0.949295 = $503
- Max rate OTB = $300; Max rate tolerance = 30%
- Rate capped at $300 × 1.3 = **$390**

### S25 — Max rate tolerance
- Navigation: **Preferences → Station Preferences**.
- "Applies to all weeks/days/dayparts/spot lengths on station."
- Screenshot text: "Max Rate Tolerance % — The % applied to the system calculated maximum rate
  to determine what the **final** maximum rate value used will be e.g. if the system calculated
  max rate is $500 and the % set is 20% then the maximum rate used will be $600." (Box shows 25%.)

### S26 — Max rate workarounds
If max rate lowers the rate too much:
1. Increase the max rate tolerance — "this will increase all weeks / days / dayparts / spot
   lengths on the station."
2. Enter hard rate overrides — "remember rates will decay over 56 days."
3. Create forecasted demand overrides to lower the forecasted sellout below 100% and prevent
   max rate from triggering — "Not ideal as forecasted sellouts are used widely for various
   corporate purposes."

### S27 — Overrides
- **Rate overrides**: ideal for highly targeted areas; time consuming to enter for extended
  periods; not flexible; requires maintenance; use sparingly.
- **Forecast overrides**: similar to rate overrides; use sparingly.
- **Reference price overrides**: "most powerful and ideal tool to adjust pricing."
- **Demand level overrides**: "useful to correct for sudden demand changes (e.g. format flip)."

### S28 — Rate overrides (UI)
- Navigation: **Rate Controls → Forecast Editor** ("Rate Editor" screenshot, week of 9/16/2013).
- Columns: current rates 60's/30's/15's; AUR 60's/30's/15's; Current Sellout %; Forecast
  Sellout %; Forecast Threshold (red/green indicator); Price Sensitivity (`$` symbols);
  Rate Overrides input boxes for 60's/30's/15's; "Reference / Demand Overrides" flag column
  ("No / No").
- Rows: Monday–Sunday per daypart (AMD expanded; MID, PMD collapsed), plus aggregate rows
  Monday-Friday, Saturday-Sunday, Monday-Sunday (override boxes N/A on aggregate rows).
- "Reset Rate Decay" button per daypart.
- Some current-rate cells carry an asterisk (e.g., Thursday `2438*`); the asterisk's meaning
  is not defined anywhere in the deck.
- Legible sample row (approximate): Monday AMD — 60's 1189, 30's 903, 15's 475, AUR 60's 1073,
  AUR 30's 892, AUR 15's 319, Current Sellout 92, Forecast Sellout 96.

### S29 — Rate decay
- "Users can override individual rates for a given airdate / daypart / spot length."
- "Overrides decay over 8 weeks (56 days) by blending with the system rate":
  - Day 1: 1/56 system rate + 55/56 override rate
  - Day 2: 2/56 system rate + 54/56 override rate
  - … Day 56: 100% system rate, override no longer in effect.
- "Rate overrides appear instantly in BR5 and **Fusion**, but do not appear in the **CPI tool**
  until the following day."
- "Buttons are available to reset the rate decay."

### S30 — Forecast overrides (UI)
- Navigation: **Rate Controls → Forecast Editor**.
- Screenshot: week selector ("Week of 9/16/2013", Current/Previous/Next Week links); left grid
  of ON/OFF toggles per daypart (AMD/MID/PMD/EVE/ON) × day (MON–SUN) plus M-F / S-S / M-S
  buttons; right table per day with columns: Last Year (% and m), Current (% and m),
  Forecast (% and m), % of Sellout (bar), Override (% and m input), Restore Base;
  Preview / Cancel / Save buttons.

### S31 — Reference price overrides (UI)
- Navigation: **Administration → Reference Price Override**.
- **Warning (red, italic in original): "typing a $ amount into a reference price override and
  choosing floating instead of fixed will add that $ amount to the reference price."**
- Form fields: Application Type (● Floating / ○ Fixed); Reference Price $ ____ − OR −
  "Enter By Percent"; Daypart dropdown (AMD shown); Days Of Week checkboxes M Tu W Th F Sa Su;
  Start Date / End Date; Air Start Date / Air End Date; [Create Overrides] button.

### S32 — Demand level overrides (UI)
- Navigation: **Administration → Demand Level Override**.
- Same form layout as S31 but the amount field is "Demand Level ____ mins − OR −
  Enter By Percent".

### S33 — Simultaneous overrides
- "Multiple overrides can exist at the same time":
  - "Reference price and demand overrides **affect** the system price — system continues to
    calculate rate, but with user adjustments."
  - "Rate overrides **replace** the system price — as rate override decays, returns to system
    price (as adjusted by reference price and demand overrides)."
- Screenshot table (transcribed exactly):

| Air Date | Capacity | Elasticity | Booking Fraction | Original Reference Price | Adjusted Reference Price | Final Reference Price | Current Sold | Demand Forecast | System Price | Spot Length | Rate Differential | Target Rate | Opt Status | Max Rate OTB |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 9/16/13 | 45 | −0.9 | 0.948574 | 1294.654 | 1332.908 | 1332.91 | 41.25 | 43 | 1410.34 | 60 | 0.842811 | 1188.65 | | 1400 |
| 9/17/13 | 45 | −0.9 | 0.945395 | 1285.382 | 1349.406 | 1349.41 | 40.25 | 42 | 1427.79 | 60 | 0.846303 | 1208.35 | | 1400 |
| 9/18/13 | 45 | −0.9 | 0.908463 | 1359.349 | 1391.998 | 1392 | 42.25 | 45.25 | 1527.94 | 60 | 0.849079 | 1297.34 | | 1950 |
| 9/19/13 | 45 | −0.9 | 0.91468 | 1435.953 | 1519.913 | 1519.91 | 46.5 | 49.25 | 3155 | 60 | 0.838511 | 2437.5 | System Rate Greater Than Maximum Rate. | 1950 |
| 9/20/13 | 45 | −0.9 | 0.903518 | 1493.644 | 1539.266 | 1539.27 | 45.5 | 48.5 | 3200.36 | 60 | 0.833514 | 2013.84 | System Rate Greater Than Maximum Rate. | 1400 |

### S34 — Revenue forecasting
- "Forecasted independently of inventory forecast."
- 4 main components: cancellation curves (**gross & net**); booking curves; seasonality
  factors; deseasonalized demand levels.
- (No further detail on revenue forecasting appears anywhere in the deck.)

### S35 — Miscellaneous questions
"How long does it take for a new station to be added to BR5?"
- Typically need around 12 months of data.
- Potentially applies to format flips as well.
- Currently unable to copy data from another station.
- Can add manual rate card to CPI tool in the interim.

### S36 — Active BR5 revenue types
**Local (14):** Local Agency-Endorsement; Local Agency-Natl Platform; Local Agency-Political;
Local Agency-Sales; Local Agency-Sales Incentive; Local Direct-Endorsement; Local Direct-Natl
Platform; Local Direct-Political; Local Direct-Sales Incentive; Local-Direct; New Bus
Local-Agency; New Bus Local-Direct; Preacher - CA mkts only; Preacher-Local Agency.

**National (10):** LOCAL ENTERPRISE CCRS; National Agency-Endorsement; National
Agency-Political; National Agency-Sales; National Direct-Political; National-Direct Sales;
National-Natl Platform; New Bus National Direct-Sales; New Bus National-Agency; Preacher-Natl
Agency.

Note (in original): "Trade revenue types are included in inventory but excluded from revenue."

### S37 — Forecast frequency

| Cancellation Curves | Booking Curves | Seasonality Factor | Deseasonalized Demand | Reference Prices | MRM (elasticity & rate differentials) |
|---|---|---|---|---|---|
| Saturdays | Nightly (except Saturdays) | Fridays | Nightly (except Saturdays) | Nightly (except Saturdays) | Monthly* |

Footnote: "* MRM has not been run since November 2010 (March 2012 update was rolled back)."

### S38 — Data criteria (summary matrix)

| | Cancellation Curves | Booking Curves | Seasonality Factor | Deseasonalized Demand | Reference Prices | MRM |
|---|---|---|---|---|---|---|
| Time frame | 6 months | 2 years | Up to 3 years | 6 months | 12 months | 12 months |
| Priority | P40+ aired (all) | | | | | |
| Spot lengths | 15s, 30s, 60s (all) | | | | | |
| Revenue types | BR5 revenue types (all) | | | | | |
| Break types | Market-specified break types (all) | | | | | |
| Other | N/A | N/A | N/A | N/A | Includes additional filters | Includes additional filters |

### S39 — Calculation levels (summary matrix)

| | Cancellation Curves | Booking Curves | Seasonality Factor | Deseasonalized Demand | Reference Prices | Elasticity | Rate Differentials |
|---|---|---|---|---|---|---|---|
| Market | ✓ | | | | | | |
| Station | | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Month | | ✓ | | | | | |
| Week of Year | | | ✓ | | | | |
| Day of Week | ✓ | ✓ | ✓ | ✓ | ✓ | | ✓ |
| Weekday/Weekend | | | | | | ✓ | |
| Daypart | | | | ✓ | ✓ | ✓ | ✓ |
| Weeks Left | | | | | ✓ | | |
| Days Left | ✓ | ✓ | | | | | |

---

## Part 2 — Transcript fact ledger

Facts stated by "Them" (the executive), quoted or closely paraphrased:

| # | Fact | Supporting quote (abridged) |
|---|---|---|
| T1 | BestRate is the pricing system for **station** (broadcast) sales; "all of the other business lines have different paradigms for pricing." | "Let's start with just station pricing. And that's really where best rate comes into play." |
| T2 | Built "2010 ish", "on the same model as airlines and hospitality pricing." | — |
| T3 | Origin: "when Bain and THC purchased Clear Channel … they brought a bunch of us from that space specifically to build a yield management practice in media." (Transcription reads "THC"; historically the Clear Channel buyers were Bain Capital and Thomas H. Lee Partners — recorded here as transcribed.) | — |
| T4 | Premise: "a minute of air time is no different than an airline seat or a hotel room. It's perishable if you don't sell it for the right price at the right time." | — |
| T5 | "Demand and supply works just like any other commodity business. Where demand is high, you can try and price up. Demand is low … you price down a bit." | — |
| T6 | Pre-BestRate, pricing was "based on whatever intelligence the market had about pricing," not expected demand (Super Bowl analogy: known sellout → price every ticket expensive). | — |
| T7 | Current leadership ("Bob") prefers flat/static pricing; "the best rate system can accommodate that flatness of rate. We just have to go and do a little bit of work, not technical work, but just like operating work to go and set up those flat rates." | — |
| T8 | Two key components: **reference price** and **reference price adjustments**. | — |
| T9 | Reference price adjustments are "predicated on a few variables, things like demand and supply as a primary, cancellations, and seasonality." High demand → adjust reference price up; low demand → down; cancellations change the demand forecast, which impacts the adjustment. | — |
| T10 | Reference price built from "a couple of years of data," weighting "recent transactions more … there's something called exponential smoothing, where you bias recency much more than all historical." | (Deck S17 says 1 year rolling — see Discrepancy Log D1.) |
| T11 | Only actual transactions are used: "everything that was actually sold, not fictitious rates, not made up rates." | — |
| T12 | Cleanup of history: "we remove those no charges, we remove the added value. We remove anything that's a super high price and we remove anything that's a super low price." | (Matches deck S17: exclude no charges, top 10%, bottom 10%.) |
| T13 | Rotators: "I want to sell Monday–Friday, 6a–7p. That has a different price point than if I just want to sell AM drive. So we clean that up as part of looking at our historical data." | (Matches deck S17: exclude rotators depending on rotator preference. Also establishes AMD = AM drive.) |
| T14 | Implementation: "It's not AI … it's basically a bunch of scripts. Database scripts that run every night, that do all of this math on their own. And spit out a price." Adjustment factors are "a little bit of mathematics … it's all math. It is no LLM." | — |
| T15 | Humans can adjust outcomes via "a front end interface." | (Deck S27–S32 shows the override UIs.) |
| T16 | The central pricing team was cut in 2015: "since we deprecated the dorm team back in 2015, 30 people to five people" (transcribed as "dorm team"; likely a transcription artifact of the team's actual name — recorded as heard). Markets typically don't make material adjustments now. | — |
| T17 | Overrides happen when "there is something big as an externality — a format flip, a big ratings jump — and the stations put their hand up and say, hey, can you help me override some of these rates?" | (Matches deck S27: demand level overrides for format flips.) |
| T18 | BestRate "pipes into a lot of our infrastructure … it feeds a bunch of optimizers that we have on media planning … it feeds Salesforce." (One system name is garbled in the transcript: "it feeds at plus".) | (Deck S29 adds Fusion and the CPI tool as downstream consumers.) |
| T19 | Recommendation if replacing: "I'm happy to change the brain … just replace it with a new algo. But let the plumbing stay intact." Do not replace "the process flow around how rates get into our system." | — |
| T20 | Scope: "it was built on station sales" — excludes DGWN inventory [as transcribed], digital, TTWN, packages, Premiere; "all of them are different… each one's going to be a bit of a convo." | — |
| T21 | Capacity: "there is no concept of infinite capacity … the upper bound is 60 minutes" per hour; "our typical clocks are 14 minutes." | — |
| T22 | Adding inventory: capacity added in response to demand keeps sellouts high and "the pricing remains somewhat inflated"; adding time **preemptively** (before demand shows) lowers forecast sellout — "I might drop my pricing a little bit. So we don't add time preemptively." The added minutes go into the denominator (supply). | — |
| T23 | Free/no-charge spots: they consume inventory ("It's six in the numerator. It's 15 in the denominator") but are stripped from price statistics, so "my target price for the future dates is not affected." They do lower the buyer's blended price. | — |
| T24 | Rationale for stripping $0 spots — the "downward spiral": if the $0 spot were blended in, a $100 target would show ~$90, and "even if a seller saw the 90 rate starting tomorrow, it would still add another no charge spot." Added value is "such a cultural problem" / "endemic" in broadcast. | — |
| T25 | Booking-curve behavior (worked narrative): system knows "typically I sell out at 85% next week"; sets target price (e.g., $100). Individual deal prices (sold at $50, $90 or $200) do **not** move the target while bookings track the curve. When bookings jump the forecast from 85% to 100% sellout, "I'm going to take the 100 from 100 to 105. Or 107. It's not going to go from 100 to 200, but it's going to start inching up." | — |
| T26 | "Every night when the algo is running and updating its future rates, it's looking at what has been sold historically." | (Matches deck S37 nightly cadence.) |
| T27 | CPM data for the top 20 markets was compiled and "sent to Dina just to do a once over" before wider sharing. | — |
| T28 | New station / format flip: needs ~12 months of data (stated in deck S35; transcript corroborates the format-flip externality process via T17). | — |

Context present in the transcript but not about BestRate mechanics (recorded so nothing is
skipped): the conversation also covered an org chart Ana prepared from Workday with Tony
Galligate's help for Rich; a reorg review across the ecosystem ("Ahmed is doing a review");
the speaker's career-growth concerns with Rich/Mike/Bob; Bob's dislike of nuance
("round vs flat world" analogy); vendor evaluations occupying the next day; media planning
appearing as "planning" under each sales team in a functional chart PDF sent the prior day;
and an agreement to cover pricing for TTWN/digital/Premiere/packages in later conversations.
These items carry no BestRate technical content beyond what is captured in T1–T28.

---

## Part 3 — Discrepancy log

| # | Discrepancy | Detail |
|---|---|---|
| D1 | Reference price data window | Transcript (T10): "a couple of years of data." Deck (S17/S38): 1 year (12 months) rolling. The deck is the authoritative training document; the transcript may be rounding loosely or describing an earlier configuration. Unresolved. |
| D2 | S9 rows 1–2 arithmetic | Row 1: 48 ÷ 80% = 60, deck shows 61. Row 2: 49 ÷ 76% = 64.47 → 64, deck shows 65. Rows 3–8 reproduce exactly from the displayed factors with half-up rounding. Explanation: the S9 factor column reuses S8's rounded **whole-day** factors for illustration, while the deseasonalized column was computed from unrounded (likely daypart-level) factors — e.g. row 1 implies a true factor of ≈78.7% (48/61). The slides are illustrative, not a consistent worked dataset. |
| D3 | S8 factor rounding | Week 2: 134/175 = 76.57% shown as 76% (rounded down); week 5: 148/175 = 84.57% shown as 85% (rounded up). Display rounding in the deck is inconsistent; underlying values are exact ratios. |
| D4 | S24 Final vs Adjusted reference price | Adjusted 293.9902 → Final 300.00. On S33 Final is simply Adjusted rounded to 2 decimals. On S24 the Opt Status includes "Reference Override", and Final is exactly 300.00 — consistent with a fixed reference price override of $300 being the final value. The deck never states the Original→Adjusted→Final pipeline explicitly. |
| D5 | Max rate tolerance values | S24 example uses 30%; S25 screenshot shows 25%; S33's capped rows are consistent with 25% (1950 × 1.25 = 2437.50 exactly). Tolerance is a per-station preference, so differing values are expected, but no single canonical value exists. |
| D6 | "Dorm team" (T16) | Almost certainly a speech-to-text artifact of the team's real name (the yield/pricing organization). Recorded as transcribed; the substantive fact is the 2015 downsizing 30 → 5. |
| D7 | "Feeds at plus" (T18) | Garbled system name in the transcript. Downstream systems confirmed by name across both sources: Fusion, CPI tool (deck S29); media-planning optimizers, Salesforce (transcript). At least one additional system name is unrecoverable from the transcript. |
| D8 | S12 columns don't reconcile | The printed "Minutes Booked" increments sum to **1,027**, not the printed cumulative total 1,026, and disagree with the printed "Cumulative Bookings" column at three rows: 229+2=231 (printed 230), 921+29=950 (printed 949), 1,025+0=1,025 (printed 1,026). Decisive evidence: the printed "Booking Fraction" column matches the increment-derived cumulative (total 1,027) with half-up rounding at **all 15 rows** — including the otherwise-unexplainable 93% at 2 days left (951/1,027 = 92.60%) — so the increments and fractions are the real data and the cumulative column carries the typos. Encoded as a test in the reference implementation. |
| D9 | Elasticity band boundaries | S19 gives "$ (0 to −1.2)", "$$ (−1.2 to −1.6)", "$$$ (less than −1.6)" — the boundary values −1.2 and −1.6 are assigned to overlapping ranges. Which band owns the exact boundary is unspecified. |
| D10 | S23/S24 "system recommended rate" vs "system price" | S24 computes "system rate" as System Price × Rate Differential ($530 × 0.949295 = $503) — i.e., the length-specific rate. The max-rate cap comparison and the Target Rate operate at this length-specific level. The deck uses "system rate", "system price", and "system recommended rate" without formal definitions; the S24/S33 numbers pin down the relationships used here. |
