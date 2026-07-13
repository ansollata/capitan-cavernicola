# BestRate (BR5) — Operating & Methodology Manual

**Sources.** This manual is compiled exclusively from (1) the iHeartMedia internal training
deck "Best Rate Training" (`BR_Training__New_Format.20160509.pdf`, 39 slides, dated
2016-05-09) and (2) a transcript of a conversation with an executive who helped build the
system. Citations: **[S#]** = slide number, **[T#]** = transcript fact number as catalogued in
[docs/04-source-inventory.md](04-source-inventory.md). Anything the sources do not specify is
explicitly marked **NOT SPECIFIED** rather than filled in. Discrepancies between sources are
flagged inline and catalogued in the Discrepancy Log of the source inventory.

---

## 1. What BestRate is

BestRate (current version "BR5") is iHeartMedia's yield-management pricing system for
**broadcast station spot sales** — and only that business line. All other business lines
(TTWN, digital, Premiere, packages, network) have different pricing paradigms [T1, T20].

- Built circa 2010, explicitly modeled on airline and hospitality revenue management, by
  practitioners hired from that industry after the Bain / Thomas H. Lee ("THC" in the
  transcript) buyout of Clear Channel, to establish a yield-management practice in media
  [T2, T3].
- Core premise: a minute of airtime is perishable inventory, like an airline seat or hotel
  room — unsold time at airdate is lost forever, so it should be priced to expected demand
  [T4, T5]. Before BestRate, stations priced off market intelligence rather than expected
  demand [T6].
- It is **not** AI. It is a set of database scripts that run nightly, compute statistics, and
  emit a recommended rate; all adjustments are deterministic math [T14, T26].
- Humans interact with it through a web front end (override screens); since the central
  pricing/yield team was cut from ~30 people to ~5 in 2015, markets rarely make material
  manual adjustments except after large externalities (format flips, big ratings swings)
  [T15, T16, T17].

### 1.1 Conceptual model

Two concepts anchor the whole system [T8, T9]:

1. **Reference price** — a cleaned, recency-weighted statistical summary of what the station
   *actually sold* comparable inventory for (no-charge spots, added value, outliers, rotators,
   political rates etc. stripped out) [T10–T13, S17].
2. **Reference price adjustments** — a multiplier applied to the reference price driven by
   forecast demand vs. supply (with cancellations and seasonality folded into the demand
   forecast) [T9]. High expected sellout ⇒ adjust up; low ⇒ adjust down.

### 1.2 The three computational components [S2]

```
Inventory forecasting ─┐
Reference prices ──────┼──►  Final rate recommendation
Market response models ┘
```

| Component | What it produces |
|---|---|
| Inventory forecasting (§3) | Forecast of minutes that will ultimately be sold per station/airdate/daypart → forecast sellout % |
| Reference prices (§4) | Baseline price per station/day-of-week/daypart/weeks-before-airdate |
| Market response models (§5) | Elasticity per station/weekday-weekend/daypart, and rate differentials across spot lengths |

---

## 2. Data foundation

### 2.1 Universal data criteria (applied to every calculation) [S4, S6, S7, S11, S17, S38]

- **P40+ aired spots** — only spots at priority 40 or above that actually aired. (The deck
  does not define the priority scale itself — NOT SPECIFIED.)
- **Spot lengths 15s, 30s, 60s** only.
- **BR5 revenue types** only (full list in Appendix B) [S36].
- **Market-specified break types** only (each market designates which break types count —
  the per-market lists are NOT SPECIFIED in the deck).
- Trade revenue types are included in **inventory** but excluded from **revenue** [S36].

### 2.2 Look-back windows per calculation [S38]

| Calculation | Time frame (rolling) |
|---|---|
| Cancellation curves | 6 months |
| Booking curves | 2 years |
| Seasonality factor | up to 3 years (data permitting) |
| Deseasonalized demand | 6 months |
| Reference prices | 12 months |
| MRM (elasticity & rate differentials) | 12 months |

### 2.3 Calculation levels (granularity) per component [S39]

| Dimension | Cancellation | Booking | Seasonality | Deseason. demand | Reference prices | Elasticity | Rate differentials |
|---|---|---|---|---|---|---|---|
| Market | ✓ | | | | | | |
| Station | | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Month | | ✓ | | | | | |
| Week of year | | | ✓ | | | | |
| Day of week | ✓ | ✓ | ✓ | ✓ | ✓ | | ✓ |
| Weekday/Weekend | | | | | | ✓ | |
| Daypart | | | | ✓ | ✓ | ✓ | ✓ |
| Weeks left | | | | | ✓ | | |
| Days left | ✓ | ✓ | | | | | |

Note the asymmetries: cancellations are the only **market-level** statistic; booking curves
are the only **month-level** statistic; reference prices are the only statistic bucketed by
**weeks left**.

### 2.4 Batch cadence [S37, T14, T26]

Everything runs as nightly database scripts:

| Job | When it runs |
|---|---|
| Booking curves | Nightly (except Saturdays) |
| Deseasonalized demand | Nightly (except Saturdays) |
| Reference prices | Nightly (except Saturdays) |
| Cancellation curves | Saturdays |
| Seasonality factor | Fridays |
| MRM (elasticity & rate differentials) | Monthly* |

\* **MRM has not actually been run since November 2010; a March 2012 refresh was rolled
back** [S37 footnote]. As of the deck date (May 2016), elasticities and rate differentials in
production were 5½ years stale.

### 2.5 Dayparts

Daypart codes appearing in the system: **AMD** (AM drive — expansion confirmed by transcript
[T13]), **MID**, **PMD**, **EVE**, **ON**, plus **5Ato6A** and **7Pto8P** [S10]. The deck does
not define the clock boundaries of these dayparts — NOT SPECIFIED (MID/PMD/EVE/ON expansions
are conventional radio usage, not stated in the sources).

### 2.6 Capacity

- Capacity is finite: hard upper bound 60 minutes/hour; typical commercial clocks ~14
  minutes/hour [T21].
- Capacity is the denominator of every sellout calculation; sold minutes (including $0
  no-charge spots) are the numerator [T22, T23, S24].
- Operating practice: capacity is added **in response to** observed demand, never
  preemptively — preemptive additions depress forecast sellout and would push recommended
  rates down [T22].
- Capacity appears per airdate at fractional-minute precision in the rate grid (e.g.,
  21.0000, 45) [S24, S33]. Where capacity values are sourced from (clock templates, traffic
  system) is NOT SPECIFIED.

---

## 3. Inventory forecasting

### 3.1 Master formula [S3, S14]

```
Forecast = Business on the books
         − Projected cancellations
         + Forecasted remaining demand

Forecasted remaining demand = Deseasonalized demand
                            × Seasonality factor
                            × (1 − Booking fraction)      ← "% of business left to be booked"
```

Everything is denominated in **minutes** per station / airdate / daypart.

### 3.2 Projected cancellations [S4]

- Historical cancellation rates computed at **market × day-of-week × days-before-airdate**
  level from 6 months of rolling data.
- Applied as: `projected cancellations = business on the books × cancellation rate(dow, days_left)`
  (application form shown in the S15 worked example: 38 min × 3% ≈ 1 min).
- Example curve values (one market) — cancellation % by day-of-week × days left:

| Day | 30 | 60 | 90 | 120 | 150 | 180 |
|---|---|---|---|---|---|---|
| Mon | 7% | 14% | 17% | 20% | 24% | 29% |
| Tue | 6% | 12% | 17% | 20% | 25% | 30% |
| Wed | 6% | 11% | 14% | 17% | 23% | 28% |
| Thu | 6% | 12% | 16% | 18% | 23% | 29% |
| Fri | 6% | 11% | 15% | 17% | 22% | 27% |
| Sat | 7% | 12% | 15% | 17% | 20% | 24% |
| Sun | 7% | 11% | 15% | 17% | 19% | 22% |

  The S15 example uses 3% at 14 days left, so the stored curve is finer-grained than this
  30-day-step display. The interpolation/step behavior between tabulated points is NOT
  SPECIFIED.
- The pattern: the further out the airdate, the more of the currently-booked business will
  cancel before air (up to ~30% at 180 days).
- Escalation path for reviewing a market's cancellation rates existed ("Contact James Liao")
  [S4].

### 3.3 Average historical demand [S6]

- Minutes sold per **station × day-of-week × daypart**, 6 months rolling, filtered per §2.1.
- Raw observations are per airdate (e.g., every Wednesday AMD's minutes sold).

### 3.4 Seasonality factor [S7, S8]

- Computed per **station × week-of-year × day-of-week** from up to 3 years of data.
- `Seasonality factor(week, dow) = minutes sold that week-dow ÷ average minutes sold for that dow`
  (implied by the S8 example: 140 ÷ 175 = 80%).
- Example: Wednesdays start the year at ~76–80% of average and reach 100% by early March.
  Factors fluctuate around 100% across the year.

### 3.5 Deseasonalized demand [S9, S10]

- `Deseasonalized demand = minutes sold ÷ seasonality factor` per observation.
- The last 26 weeks of deseasonalized observations for each (station, day-of-week, daypart)
  are **averaged into a single number, with recent weeks weighted more** [S9]. The transcript
  identifies the weighting technique as **exponential smoothing** ("you bias recency much more
  than all historical") [T10]. The exact decay constant / weight schedule is NOT SPECIFIED.
- The result is the system's standing estimate of "typical demand" per station/dow/daypart,
  viewable (and overridable) at *Administration → Demand Level Override*, displayed in mm:ss
  per daypart × day-of-week [S10].

### 3.6 Booking curves [S11, S12, S13]

- Question answered: "historically, what % of business is on the books x days before
  airdate?" [S11]
- Computed per **station × month × day-of-week × days-before-airdate**, 2 years rolling.
- Construction (from the S12 example): pool all airdates of that day-of-week in that month
  across the window (e.g., 8 February Wednesdays = 4 in 2010 + 4 in 2011), sum minutes booked
  by days-left, cumulate, and divide by the final total:
  `booking fraction(d) = cumulative minutes booked through d days left ÷ total minutes at day 0`.
- `% of business left to be booked = 1 − booking fraction` [S13].
- Example curve: 8% on the books at 14 days out → 22% at 12–10 days → 54% at 7 days → 89% at
  5 days → 100% at 1 day [S12].

### 3.7 Worked example (reproduced from S15)

38 minutes on the books for Saturday 4/13/13 AMD, observed on 3/30/13 (14 days out):

```
Projected cancellations = 38 × 3% (Sat, 14 days left)               ≈ 1 minute
Remaining demand        = 50 (deseason. Sat AMD) × 82% (wk15 Sat)
                          × (1 − 90% booked at 14 days, April Sat)  ≈ 4 minutes
Forecast                = 38 − 1 + 4                                = 41 minutes
```

### 3.8 Inventory forecast caps [S16]

To stop early large buys from spiking projected sellout (and therefore rates), the forecast
is capped as a function of **actual** sellout:

| Actual sellout | Max forecast sellout |
|---|---|
| 0–9% | 100% |
| 10–19% | 105% |
| 20–29% | 110% |
| 30–39% | 115% |
| 40%+ | 200% |

### 3.9 Behavioral properties (from the transcript)

- The forecast — not any individual deal's price — is what moves rates. If bookings track the
  historical booking curve, the target price stays put regardless of whether individual spots
  sold at $50, $90 or $200. When cumulative bookings run ahead of the curve (e.g., forecast
  sellout jumps from 85% to 100%), the target inches up ($100 → $105–107, not $200) [T25].
- $0 / no-charge spots consume inventory (numerator of sellout) and therefore push sellout —
  and rates — **up**, while being excluded from all price statistics (see §4). They never pull
  the reference price down. This is deliberate, to avoid a "downward spiral" where blended-down
  targets get another no-charge spot layered on top by sellers [T23, T24].
- Added capacity enters the denominator immediately. Demand-following additions keep sellout
  high (rates stay inflated); preemptive additions crater forecast sellout (rates would drop) —
  hence the no-preemptive-adds practice [T22].

---

## 4. Reference prices

### 4.1 Definition and construction [S17, T10–T13]

A reference price is the cleaned, recency-weighted price actually achieved for comparable
inventory, computed **nightly** per **station × day-of-week × daypart × weeks-before-airdate**
from 12 months of rolling data (transcript says "a couple of years" — see Discrepancy D1).

Filters, in addition to the universal criteria of §2.1:

1. Include only commercial break types
2. Exclude no charges
3. Exclude rotators (subject to a per-station/market "rotator preference" setting)
4. Exclude political and issue rates
5. Exclude flight lengths > 98 days
6. Exclude flights that include both weekdays and weekends
7. Exclude Flexnet (NOT SPECIFIED what Flexnet is — recorded as named)
8. Exclude top 10% of rates
9. Exclude bottom 10% of rates

The surviving transactions are **weighted toward recency** (exponential smoothing per the
transcript [T10]; exact weights NOT SPECIFIED) and — like the demand forecast — are
**deseasonalized first, with seasonality added back in later** [S17]. The precise mechanics of
the deseasonalize/re-seasonalize round trip for prices are NOT SPECIFIED.

### 4.2 Output shape [S17, S18]

**16 reference prices** per (station, day-of-week, daypart): one for each of *in-week*,
*1–14 weeks left*, and *15+ weeks left*. Reference prices **rise as the airdate approaches**.
Example (Monday AMD): $228 at 15+ weeks → $268 at 5 weeks → $289 at 1 week and in-week [S18].

This is the airline-style advance-purchase gradient: book early, pay less.

### 4.3 Reference price lifecycle in the rate grid [S24, S33, D4]

The rate grid shows three reference price columns per airdate:

- **Original Reference Price** — the nightly statistical output.
- **Adjusted Reference Price** — original after floating reference-price/demand overrides are
  applied ("system continues to calculate rate, but with user adjustments" [S33]).
- **Final Reference Price** — the value actually priced from. Observed to equal the adjusted
  value (rounded to 2 decimals) normally [S33], or the fixed override value when a fixed
  reference price override is in effect (S24: adjusted 293.9902 → final 300.00 with Opt
  Status "Reference Override"). The deck never states this pipeline explicitly — inferred
  from the two screenshots and flagged as inference (D4).

---

## 5. Market response models (MRM)

### 5.1 Elasticity [S19]

- Definition: how much demand changes when rates go up or down.
- Same data filtering as reference prices; computed per **station × weekday-or-weekend ×
  daypart**; refreshed monthly in theory (stale since Nov 2010 in practice [S37]).
- Values are negative (demand falls as price rises). UI banding:
  - `$` — 0 to −1.2: inelastic
  - `$$` — −1.2 to −1.6
  - `$$$` — below −1.6: elastic
  (Boundary ownership at exactly −1.2/−1.6 is NOT SPECIFIED — D9.)
- Elasticity appears as a column in the rate grid (−1.2 in S24; −0.9 in S33) and as the
  "Price Sensitivity" `$` symbols in the Rate Editor [S28].
- **How elasticity numerically enters the rate calculation is NOT SPECIFIED anywhere in the
  sources.** See §6.2.

### 5.2 Rate differentials [S20, S21]

Purpose: translate a single price level into per-spot-length rates.

- Same filtering as reference prices; per **station × day-of-week × daypart**; monthly cadence
  (also stale since Nov 2010).
- Definitions (verifiable from the S20 table):
  - **AUR** — average unit rate per spot of a given length.
  - **AMR** — average minute rate: `AUR × (60 ÷ length)`. (60s: $232 → $232; 30s: $132 →
    $264; 15s: $74 → $296.)
  - **All-lengths AMR** — $245 in the example (aggregation weighting NOT SPECIFIED).
  - **Rate differential** = length AMR ÷ all-lengths AMR (95% / 108% / 121%) — shown on the
    reference price override screen.
  - **Relative to :60 rate** = length AUR ÷ :60 AUR (57% for :30, 32% for :15) — shown on the
    rate differential screen.
- Managed at *Preferences → Rate Differentials*: a grid per daypart × weekday where :15 and
  :30 are expressed as % of :60, and :60 is expressed as % of AMR [S21].
- Note the economics embedded in the example: a :30 costs 57% of a :60 and a :15 costs 32% —
  shorter units carry a per-minute premium (AMR 108% and 121% of the all-lengths average).

---

## 6. From forecast to rate

### 6.1 What is documented

The rate grid [S24, S33] exposes the chain per airdate × daypart × spot length:

```
Final Reference Price ──(market response adjustment)──► System Price (all-lengths level)
System Price × Rate Differential ──────────────────────► length-specific system rate
                                                          = Target Rate (unless max rate caps it)
```

Verified numerically from S33 (all three uncapped rows): Target Rate = System Price × Rate
Differential to the penny (1410.34 × 0.842811 = 1188.65, etc.). S24's bullet does the same
multiplication and calls the product the "system rate" ($530 × 0.949295 = $503).

### 6.2 What is NOT specified — the adjustment function

The functional form mapping {final reference price, forecast sellout, current sellout,
booking fraction, elasticity, days/weeks left} → System Price is **not documented in either
source**. This is the single largest gap for replication. What the sources give us:

- Directionality and damping: adjustments follow demand vs. supply; movements are gradual
  ("inching up", 100 → 105–107 on a 15-point sellout jump) [T25, T9].
- Five calibration points from S33 (System Price ÷ Final Reference Price, elasticity −0.9):

| Airdate | Forecast sellout | Booking fraction | Multiplier |
|---|---|---|---|
| 9/16/13 | 43 ÷ 45 = 95.6% | 0.948574 | 1.05809 |
| 9/17/13 | 42 ÷ 45 = 93.3% | 0.945395 | 1.05809 |
| 9/18/13 | 45.25 ÷ 45 = 100.6% | 0.908463 | 1.09766 |
| 9/19/13 | 49.25 ÷ 45 = 109.4% | 0.914680 | 2.07578 |
| 9/20/13 | 48.5 ÷ 45 = 107.8% | 0.903518 | 2.07914 |

  Observations (facts about the numbers, not claims about the algorithm): two different
  sellouts (95.6%, 93.3%) produced *identical* multipliers to 5 decimal places, suggesting
  banded rather than continuous adjustment; the multiplier roughly doubles once forecast
  sellout exceeds ~100%; the multiplier is not monotone in forecast sellout alone (9/19 vs
  9/20), so other inputs participate.
- One more calibration point from S24 (elasticity −1.2): final reference 300 → system price
  530, multiplier 1.7667, at forecast sellout 106% / current sellout 100%.

Recovering the exact function requires reading the BR5 database scripts (see the replication
spec, §7 unknowns register).

### 6.3 Max rate (the rate ceiling) [S22–S26]

Definitions:
- **Max rate OTB** = highest rate currently on the books [S22].
- "System rate greater than maximum rate" in Opt Status ⇒ max rate triggered: forecast demand
  is so high that BR5's recommended rate exceeds anything on the books, which may be
  unsellable, so the rate is capped [S22].
- **Max rate only ever LOWERS rates; it never increases them** [S22, emphasis in original].

Trigger and cap logic [S23] — both regimes require forecasted sellout > 100%:

| Current sellout | Cap = the LOWER of |
|---|---|
| > 95% | system recommended rate **vs** max( max rate OTB × (1+tol), avg rate OTB × 1.3 × (1+tol) ) |
| 40%–95% | system recommended rate **vs** max( 90th-percentile rate OTB × (1+tol), avg rate OTB × 1.3 × (1+tol) ) |

where *tol* = **max rate tolerance**, a station-wide preference (*Preferences → Station
Preferences*) applying to all weeks/days/dayparts/spot lengths [S25]. UI help text: system
max $500 with 20% tolerance ⇒ $600 used.

Worked example [S24]: forecast sellout 22.25/21 = 106%, current sellout 21/21 = 100% ⇒
regime A. System rate $530 × 0.949295 = $503. Max rate OTB $300, tolerance 30% ⇒ cap
$300 × 1.3 = **$390** = Target Rate.

Scope of "avg rate OTB" / "90th percentile rate OTB" (which pool of booked spots they are
computed over) is NOT SPECIFIED.

Workarounds when the cap bites too hard [S26]:
1. Raise the station's max rate tolerance (affects the entire station).
2. Hard rate overrides (subject to 56-day decay, §7.3).
3. Demand/forecast overrides to force forecast sellout below 100% — discouraged because
   forecasted sellouts feed corporate reporting.

---

## 7. Overrides (the human control surface)

Four override types [S27], in the deck's own ranking:

| Type | Where | Verdict in deck |
|---|---|---|
| Reference price override | Administration → Reference Price Override | "Most powerful and ideal tool to adjust pricing" |
| Demand level override | Administration → Demand Level Override | For sudden demand changes (e.g., format flip) |
| Rate override | Rate Controls → Forecast Editor (Rate Editor) | Targeted; time-consuming; inflexible; needs maintenance; use sparingly |
| Forecast override | Rate Controls → Forecast Editor | Like rate overrides; use sparingly |

### 7.1 Reference price overrides [S31]

- Form: Application Type **Floating / Fixed**; amount in $ or by percent; daypart; days of
  week; Start/End date (override validity window) and Air Start/Air End date (airdates
  affected).
- **Warning (verbatim from deck): "typing a $ amount into a reference price override and
  choosing floating instead of fixed will ADD that $ amount to the reference price."**
  Floating-$ = additive; Fixed-$ = replaces. (Floating-percent semantics beyond this are NOT
  SPECIFIED.)
- Effect: modifies the reference price feeding the calculation; the system keeps calculating
  around it [S33].

### 7.2 Demand level overrides [S10, S32]

- Same form structure; amount in **minutes** or by percent; adjusts the deseasonalized demand
  level per daypart/day.
- Use case: step-change demand events such as format flips [S27, T17].
- Also affects the system price indirectly (through the forecast), while the system continues
  to calculate [S33].

### 7.3 Rate overrides and rate decay [S28, S29]

- Entered per **airdate × daypart × spot length** in the Rate Editor; aggregate rows
  (M-F, S-S, M-S) do not accept overrides (N/A).
- A rate override **replaces** the system price [S33].
- **Decay**: overrides blend back to the system rate linearly over 8 weeks (56 days):
  day *n* = (n/56) × system rate + ((56−n)/56) × override rate; at day 56 the override is
  gone [S29]. "Reset Rate Decay" buttons restart the clock [S28, S29].
- As the override decays, the rate returns to the system price *as adjusted by any reference
  price and demand overrides* [S33].
- Propagation: rate overrides appear **instantly in BR5 and Fusion**, but in the **CPI tool
  only the following day** [S29].

### 7.4 Forecast overrides [S30]

- In the Forecast Editor: per week, toggle dayparts × days on/off; per day, view Last Year /
  Current / Forecast (% and minutes) and enter an Override (% and minutes); Restore Base
  undoes; Preview/Save.
- Overriding the forecast changes forecast sellout, and is the (discouraged) lever for
  defeating max rate [S26].

### 7.5 Simultaneous overrides [S33]

All override types can coexist. Composition semantics:
- Reference price + demand overrides **feed** the calculation (Original → Adjusted → Final
  reference price; forecast reflects demand override).
- Rate overrides **bypass** the calculation, then decay back to it.
- Opt Status strings observed: "Reference Override", "System Rate Greater Than Maximum Rate"
  (comma-combined when both apply) [S24, S33].

---

## 8. Downstream integration ("the plumbing")

Named consumers of BestRate rates:
- **Fusion** — receives rate overrides instantly [S29]. (What Fusion is, is NOT SPECIFIED in
  the sources.)
- **CPI tool** — receives overrides on a next-day cycle [S29]; also where a manual rate card
  can be maintained for stations too new for BR5 [S35].
- **Media planning optimizers** — "it feeds a bunch of optimizers that we have on media
  planning" [T18].
- **Salesforce** [T18].
- At least one more system whose name is garbled in the transcript ("it feeds at plus…") — 
  unrecoverable [T18/D7].

Architectural guidance from the system's builder: if the pricing algorithm is ever replaced,
**swap the brain, keep the plumbing** — preserve the data flows into Fusion/CPI/optimizers/
Salesforce and the process flow around how rates enter the systems; only substitute the
algorithm that generates the numbers [T19]. The system can also be operated in **flat/static
rate card mode** purely through operating work (setting flat rates via the override
machinery) with no technical changes [T7].

---

## 9. Revenue forecasting [S34]

A separate output, forecast **independently** of the inventory forecast, from 4 components:
1. Cancellation curves (**gross & net** — the gross/net distinction is only mentioned here,
   NOT SPECIFIED further)
2. Booking curves
3. Seasonality factors
4. Deseasonalized demand levels

Forecasted sellouts are "used widely for various corporate purposes" [S26] — i.e., BR5's
forecasts serve reporting functions beyond pricing.

---

## 10. Station onboarding & lifecycle [S35]

- New station in BR5: needs **~12 months of data** before the models can run.
- A **format flip** potentially resets the clock the same way (and in practice triggers the
  demand-level override process [T17]).
- No capability to seed/copy data from another station.
- Interim: manual rate card in the CPI tool.

---

## 11. Glossary

| Term | Meaning | Source |
|---|---|---|
| AMD / MID / PMD / EVE / ON | Dayparts; AMD = AM drive | S10, T13 |
| AMR | Average minute rate = AUR × 60/length | S20 |
| AUR | Average unit rate (per spot) | S20 |
| Booking curve / fraction | % of final business on books at d days out | S11–S13 |
| BR5 | Current BestRate version | S2 |
| Business on the books (OTB) | Minutes currently sold for a future airdate | S3 |
| CPI tool | Downstream rate/pricing tool; next-day sync; hosts manual rate cards | S29, S35 |
| Deseasonalized demand | Minutes sold ÷ seasonality factor, recency-weighted average | S9 |
| Elasticity | % demand change per % rate change; $/$$/$$$ bands | S19 |
| Flexnet | Excluded transaction category (undefined in sources) | S17 |
| Fusion | Downstream system; instant rate sync | S29 |
| Max rate OTB | Highest rate on the books | S22 |
| Max rate tolerance | Station-wide % headroom over the computed max rate | S25 |
| MRM | Market response model (elasticity + rate differentials) | S19–S21 |
| Opt Status | Rate-grid status message (e.g., max rate triggered, reference override) | S24, S33 |
| P40+ | Spot priority filter for all calculations | S4 etc. |
| Rate differential | Length AMR ÷ all-lengths AMR | S20 |
| Reference price | Cleaned recency-weighted achieved price, 16 buckets by weeks-left | S17–S18 |
| Rotator | Broad-rotation buy (e.g., M–F 6a–7p) vs specific daypart | T13, S17 |
| Sellout | Sold (or forecast) minutes ÷ capacity minutes | S24 |
| System price | All-lengths price level after market-response adjustment | S24, S33 |
| Target rate | Length-specific recommended rate = system price × rate differential, post max-rate cap | S24, S33 |
| TTWN | Separate business line, not priced by BestRate | T20 |

---

## 12. Known gaps in this manual (inherited from the sources)

Compiled here so no reader mistakes silence for completeness. Full register in the
[replication spec §7](02-replication-spec.md):

1. The market-response function (reference price → system price) — undocumented (§6.2).
2. Exponential smoothing weights for demand and reference prices — undocumented.
3. Price deseasonalization / re-seasonalization mechanics — undocumented.
4. Daypart clock boundaries; P40 priority scale; per-market break types; Flexnet definition;
   rotator-preference values — undocumented.
5. "Avg rate OTB" / "90th-percentile rate OTB" computation scope for max rate — undocumented.
6. Revenue forecasting mechanics beyond its four named components; gross vs net cancellation
   curves — undocumented.
7. Rate Editor asterisks; "Forecast Threshold" red/green indicator semantics — undocumented.
8. Rounding rules throughout (the deck itself rounds inconsistently — D2, D3, D8).
9. In-week bucket behavior (how "in-week" pricing is selected vs the 1-week bucket, given
   both show $289 in the example) — undocumented.
10. Whether/how the inventory-forecast caps (S16) interact with the max-rate triggers —
    undocumented.
