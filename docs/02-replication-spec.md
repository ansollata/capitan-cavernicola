# BestRate (BR5) — Replication Specification

Purpose: everything needed to rebuild BestRate's behavior — data contracts, algorithms in
pseudocode, job schedule, output interfaces — separated ruthlessly into **DOCUMENTED**
(sourced from the deck [S#] / transcript [T#]) and **UNKNOWN** (must be recovered from the
BR5 database scripts or the production database before a bit-faithful clone is possible).
A runnable reference implementation of the documented parts, with tests reproducing every
numeric example in the deck, lives in [`reference-implementation/`](../reference-implementation/).

Fidelity levels this spec supports:
- **Level 1 — behavioral clone**: same structure, same formulas where documented, sensible
  configurable stand-ins for the unknowns. Achievable from this repo alone.
- **Level 2 — bit-faithful clone**: reproduces BR5's exact numbers. Requires closing the
  §7 unknowns register against the BR5 SQL scripts.

---

## 1. Input data contract

### 1.1 Spot transaction record (the single source table)

Every calculation consumes aired/booked spot-level records. Minimum schema implied by the
documented filters and grains:

| Field | Used by / because |
|---|---|
| market_id, station_id | calc levels [S39] |
| airdate, air daypart | all grains |
| spot_length ∈ {15, 30, 60} | universal filter [S38] |
| priority (for P40+ test) | universal filter [S38] |
| revenue_type | BR5 revenue types filter [S36] |
| break_type | market-specified break types; commercial-break filter [S17] |
| rate ($, per spot) | reference prices, MRM, max rate |
| no_charge flag | reference price exclusion [S17]; inventory inclusion [T23] |
| booked_date (order timestamp) | booking curves (days-left) [S11] |
| cancelled flag + cancel date | cancellation curves [S4] |
| aired flag | "P40+ **aired**" [S38] |
| flight start/end dates | flight-length > 98 days and weekday+weekend exclusions [S17] |
| rotator flag / rotation width | rotator exclusion [S17, T13] |
| political / issue flag | exclusion [S17] |
| Flexnet flag | exclusion [S17] |
| trade flag | in inventory, out of revenue [S36] |

### 1.2 Capacity

Minutes of sellable time per station × airdate × daypart, fractional precision [S24, S33].
Source system: UNKNOWN (§7-U12). Hard bound 60 min/hour; typical clock ~14 min [T21].

### 1.3 Configuration (per market/station)

| Setting | Documented? |
|---|---|
| Market break-type list | Exists [S4 etc.]; values UNKNOWN per market |
| Rotator preference | Exists [S17]; semantics UNKNOWN |
| Max rate tolerance % (station-wide) | Documented [S25] |
| Rate differential grid (:15/:30 as % of :60; :60 as % of AMR) | Documented [S21] |
| BR5 revenue type list | Documented, full list [S36] |
| Daypart definitions (AMD, MID, PMD, EVE, ON, 5Ato6A, 7Pto8P) | Codes documented [S10]; clock boundaries UNKNOWN |

---

## 2. Batch job schedule [S37]

| # | Job | Cadence | Grain of output |
|---|---|---|---|
| J1 | Cancellation curves | Saturdays | market × dow × days_left → % |
| J2 | Booking curves | Nightly except Sat | station × month × dow × days_left → fraction |
| J3 | Seasonality factors | Fridays | station × week_of_year × dow → factor |
| J4 | Deseasonalized demand | Nightly except Sat | station × dow × daypart → minutes |
| J5 | Reference prices | Nightly except Sat | station × dow × daypart × weeks_left(16) → $ |
| J6 | MRM: elasticity | Monthly (dormant since Nov 2010) | station × weekday/weekend × daypart → e |
| J7 | MRM: rate differentials | Monthly (dormant since Nov 2010) | station × dow × daypart × length → % |
| J8 | Rate generation (nightly repricing of all future airdates) | Nightly [T26] | station × airdate × daypart × length → target rate |

Execution order within a night is UNKNOWN; the dependency graph requires
J1–J7 outputs before J8.

---

## 3. Algorithms

Notation: `dow` day of week; `dl` days before airdate; `wl` weeks before airdate.

### J1 — Cancellation curves [S4] — DOCUMENTED (grain, window, filters); estimator UNKNOWN

```
input:  spots, 6 months rolling, universal filters (P40+ aired, lengths, revenue types, break types)
group:  market × dow × dl
output: cancel_rate(market, dow, dl)
```
The deck shows the output table (percent by dow × dl) but not the estimator (e.g., cancelled
minutes ÷ booked minutes at dl). Days-left granularity is finer than the 30-day display step
(3% at dl=14 in S15). Estimator formula and any smoothing across dl: UNKNOWN (§7-U3).

### J2 — Booking curves [S11, S12] — DOCUMENTED

```
input:  spots, 2 years rolling, universal filters
group:  station × month × dow
for each group:
    pool all airdates of that dow in that month across the window
    booked_minutes[dl] = Σ minutes booked exactly dl days before air
    cum[dl]  = Σ booked_minutes[d] for d ≥ dl        # cumulate toward airdate
    total    = cum[0]
    booking_fraction[dl] = cum[dl] / total
pct_business_left[dl] = 1 − booking_fraction[dl]      # [S13]
```

### J3 — Seasonality factors [S7, S8] — DOCUMENTED (formula implied by example)

```
input:  spots, up to 3 years rolling, universal filters
group:  station × week_of_year × dow
factor(station, woy, dow) = minutes_sold(that woy, dow) / mean(minutes_sold over all weeks, that dow)
```
Multi-year averaging across the up-to-3 years (simple vs weighted): UNKNOWN (§7-U4).

### J4 — Deseasonalized demand [S9] — DOCUMENTED except weights

```
input:  spots, 6 months (26 weeks) rolling, universal filters
group:  station × dow × daypart
per observation (airdate):
    deseasonalized[i] = minutes_sold[i] / factor(station, woy(airdate_i), dow)
output: recency-weighted average of the 26 deseasonalized observations
        ("recent weeks given more weight" [S9]; exponential smoothing [T10])
```
Weight schedule / smoothing constant: UNKNOWN (§7-U1). The reference implementation exposes
`alpha` as configuration.

### J5 — Reference prices [S17] — DOCUMENTED except weights & deseasonalization mechanics

```
input:  spots, 12 months rolling, universal filters
filter: only commercial break types
        AND NOT no_charge
        AND NOT rotator (per rotator preference)
        AND NOT political/issue
        AND NOT flight_length > 98 days
        AND NOT (flight covers weekdays AND weekend)
        AND NOT flexnet
group:  station × dow × daypart × weeks_left_bucket
        weeks_left_bucket ∈ {in-week, 1, 2, …, 14, 15+}   # 16 buckets
per group:
        drop top 10% and bottom 10% of rates              # trim AFTER other filters (order UNKNOWN §7-U5)
        deseasonalize rates, recency-weighted average, re-seasonalize   # mechanics UNKNOWN §7-U2
output: reference_price(station, dow, daypart, wl_bucket)
```

### J6 — Elasticity [S19] — grain & banding DOCUMENTED; estimator UNKNOWN

```
input:  same filtered set as J5
group:  station × weekday/weekend × daypart
output: elasticity e < 0
UI band: $ if e ∈ (−1.2, 0]; $$ if e ∈ (−1.6, −1.2]; $$$ if e ≤ −1.6
         (boundary ownership ambiguous in deck — D9; reference impl uses half-open as shown)
```
Estimation method (regression of demand on rate, functional form, identification): UNKNOWN
(§7-U6). Note: production values are frozen at Nov 2010 estimates [S37].

### J7 — Rate differentials [S20] — DOCUMENTED

```
input:  same filtered set as J5
group:  station × dow × daypart
AUR(len)  = mean rate per spot of that length          # weighting UNKNOWN §7-U7
AMR(len)  = AUR(len) × 60/len
AMR(all)  = all-lengths average minute rate            # aggregation weights UNKNOWN §7-U7
rate_differential(len)  = AMR(len) / AMR(all)          # shown on reference price override screen
relative_to_60(len)     = AUR(len) / AUR(60)           # shown on rate differential screen
```

### J8 — Nightly rate generation — partially DOCUMENTED

Per station × future airdate × daypart:

```
# 1. Inventory forecast [S3, S14]
otb        = minutes currently on the books (INCLUDING no-charge spots [T23])
cxl        = otb × cancel_rate(market, dow, dl)                      # [S4, S15]
remaining  = deseason_demand(station,dow,daypart)
             × factor(station, woy(airdate), dow)
             × (1 − booking_fraction(station, month, dow, dl))       # [S14]
forecast   = otb − cxl + remaining

# 2. Forecast cap [S16]
actual_sellout   = otb / capacity
cap according to band: 0–9%→100%, 10–19%→105%, 20–29%→110%, 30–39%→115%, 40%+→200%
forecast_sellout = min(forecast / capacity, cap(actual_sellout))
      # whether the cap applies to sellout or to forecast minutes first: display-equivalent;
      # exact stored representation UNKNOWN

# 3. Reference price [S17, S24, S33]
ref = reference_price(station, dow, daypart, wl_bucket(airdate))
ref = apply_floating_reference_overrides(ref)          # ADDS $ amount [S31] → "Adjusted"
ref = apply_fixed_reference_override_if_any(ref)       # replaces → "Final"

# 4. Market response adjustment — FUNCTIONAL FORM UNKNOWN (§7-U8)
system_price = ref × M(forecast_sellout, current_sellout, booking_fraction,
                       elasticity, dl/wl, …)
      # M's observed values: see calibration table in manual §6.2

# 5. Spot-length rate [S24, S33 — verified arithmetic]
system_rate(len) = system_price × rate_differential(len)

# 6. Max rate cap [S23, S24]
if forecast_sellout > 100%:
    if current_sellout > 95%:
        ceiling = max( max_rate_otb × (1+tol), avg_rate_otb × 1.3 × (1+tol) )
    elif 40% ≤ current_sellout ≤ 95%:
        ceiling = max( p90_rate_otb × (1+tol), avg_rate_otb × 1.3 × (1+tol) )
    target_rate = min(system_rate, ceiling)
    if system_rate > ceiling: opt_status += "System Rate Greater Than Maximum Rate."
else:
    target_rate = system_rate

# 7. Rate overrides [S29, S33]
if rate_override exists for (airdate, daypart, len):
    n = days since override entered (1-based)
    target_rate = (n/56) × target_rate + ((56−n)/56) × override_rate   # n ≥ 56 → pure system
```

### Override semantics summary [S27–S33]

| Override | Mechanism | Entry grain | Persistence |
|---|---|---|---|
| Reference price (floating $) | ADDS $ to reference price | daypart × dow set × date ranges | start/end dates |
| Reference price (fixed $) | replaces reference price | same | start/end dates |
| Reference price (percent) | by percent (exact math UNKNOWN §7-U9) | same | start/end dates |
| Demand level (mins or %) | adjusts deseasonalized demand | daypart × dow set × date ranges | start/end dates |
| Forecast override | replaces forecast (% and minutes) | week × day × daypart toggles | until restored |
| Rate override | replaces target rate, linear 56-day decay to system | airdate × daypart × length | 56 days, resettable |

Propagation: BR5 & Fusion instant; CPI tool next day [S29].

---

## 4. Output interfaces

1. **Rate grid** (per station × airdate × daypart × length): Air Date, Capacity, Elasticity,
   Booking Fraction, Original/Adjusted/Final Reference Price, Current Sold, Demand Forecast,
   System Price, Spot Length, Rate Differential, Target Rate, Opt Status, Max Rate OTB
   [S24, S33]. This is the canonical output contract a replacement "brain" must fill [T19].
2. **Rate Editor view**: current rates and AURs per length, current/forecast sellout %,
   forecast threshold indicator, price sensitivity symbol, override entry [S28].
3. **Feeds**: Fusion (instant), CPI tool (next-day), media-planning optimizers, Salesforce
   [S29, T18]. Payload formats UNKNOWN (§7-U11).
4. **Forecast sellouts** consumed by corporate reporting [S26].

---

## 5. Operational rules that must be preserved in any clone

1. $0/no-charge spots count in inventory (sellout numerator) but never in price statistics
   [T23, T24, S17].
2. Trade revenue counts in inventory, not revenue [S36].
3. Max rate can only lower, never raise, a rate [S22].
4. Nightly refresh of all future rates [T26, S37].
5. New station / format flip: ~12 months of data before models activate; manual rate card in
   CPI tool in the interim; no cross-station data copying exists [S35].
6. Forecast overrides leak into corporate reporting — a clone that separates pricing
   forecasts from reported forecasts changes downstream behavior [S26].
7. Flat/static rate operation is an operating-mode choice, not a code change [T7].

---

## 6. Validation harness

The deck contains enough worked numbers to acceptance-test a clone. All are implemented as
tests in `reference-implementation/tests/`:

| Test | Source | Expectation |
|---|---|---|
| Cancellation table lookup | S4 | table reproduced |
| Seasonality factors | S8 | 140/175 = 80% etc. |
| Deseasonalized demand | S9 | 49/76% = 65 etc. (row 1 deck-inconsistent, D2) |
| Booking fractions | S12 | printed increments (total 1,027) reproduce all 15 printed fractions; printed cumulative column shown to carry typos (D8) |
| Full forecast | S15 | 38 − 1 + 4 = 41 minutes |
| Forecast caps | S16 | band table |
| AUR/AMR/differentials | S20 | 95% / 108% / 121%; 57% / 32% |
| Elasticity banding | S19 | $, $$, $$$ |
| Max rate regime A | S24 | min($503, $300×1.3) = $390 |
| Target rate arithmetic | S33 | System Price × Rate Differential to the penny (3 rows) |
| Max rate on S33 rows | S33 | 9/19: 1950 × 1.25 = 2437.50 exactly (tol 25%); 9/20: 2013.84 consistent with avg-OTB branch (derived avg ≈ 1239.29) |
| Rate decay | S29 | day-1/2/56 blends |

---

## 7. UNKNOWNS REGISTER — what must be pulled from the BR5 scripts for a bit-faithful clone

| ID | Unknown | Where it bites |
|---|---|---|
| U1 | Exponential smoothing constant / weight schedule for deseasonalized demand [S9, T10] | J4 |
| U2 | Price deseasonalization & re-seasonalization mechanics for reference prices [S17] | J5 |
| U3 | Cancellation-rate estimator (numerator/denominator, dl granularity, interpolation) [S4] | J1 |
| U4 | Multi-year averaging inside seasonality factors [S7] | J3 |
| U5 | Order of operations for top/bottom-10% trims vs other filters; percentile definition [S17] | J5 |
| U6 | Elasticity estimation method [S19] | J6 |
| U7 | AUR/AMR aggregation weights, incl. all-lengths AMR [S20] | J7 |
| U8 | **The market-response function M(·) mapping reference price + forecast to system price** — the biggest gap; only 6 calibration points exist (manual §6.2) | J8 |
| U9 | Percent-mode override semantics (reference price & demand) [S31, S32] | overrides |
| U10 | "avg rate OTB" and "90th percentile rate OTB" computation scope for max rate [S23] | J8 |
| U11 | Feed formats/protocols to Fusion, CPI, optimizers, Salesforce [S29, T18] | integration |
| U12 | Capacity source-of-truth and its update path [S24] | J8 |
| U13 | In-week vs 1-week bucket selection logic [S17, S18] | J5/J8 |
| U14 | Rounding rules at each stage (deck itself is inconsistent — D2/D3/D8) | all |
| U15 | Rate Editor asterisk and Forecast Threshold indicator semantics [S28] | UI |
| U16 | Revenue forecasting computation (gross vs net cancellation curves, assembly) [S34] | J-rev |
| U17 | Interaction (if any) between S16 forecast caps and S23 max-rate triggers | J8 |
| U18 | Whether reference-price window is 12 months [S17] or ~2 years [T10] (D1) | J5 |
| U19 | Booking-curve handling of sparse cells (the "—" at dl=11 in S12) and of dl > 14 days | J2 |
| U20 | Time conventions: week-of-year definition, in-week boundary day, timezone per market | all |

**How to close them:** the transcript establishes that the entire logic lives in nightly
database scripts [T14]. The register above is the checklist for reading those scripts; each
closed unknown converts a config stub in the reference implementation into a fixed rule.

---

## 8. Migration guidance encoded in the sources

If replicating in order to *replace* BR5 (per its builder [T19]):
- Keep: the output contract (§4), the feeds, the override UIs' semantics, the process flow of
  how rates reach Fusion/CPI/Salesforce/optimizers.
- Swap: jobs J1–J8 ("the brain").
- The flat-rate mode [T7] means a replacement can be de-risked by first running the new brain
  in "static output" mode and layering dynamics back in.
