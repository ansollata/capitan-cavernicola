# BestRate (BR5) — Optimization Opportunities

Scope note: sections (a) and (b) of this project report only what the sources say. This
document is the requested exception — it contains recommendations. To keep the line clean,
every item states its **documented basis** (deck [S#] / transcript [T#], as catalogued in
[04-source-inventory.md](04-source-inventory.md)) before the proposal. No claims are made
about current (2026) system state beyond what the 2016 deck and the transcript establish;
where a proposal depends on an assumption, the assumption is labeled.

Priority key: 🔴 correctness/decay of the existing system · 🟠 methodology upgrades ·
🟡 operational/architectural.

---

## 🔴 1. The market response model is frozen in November 2010

**Basis:** MRM (elasticity and rate differentials) is nominally monthly but "has not been run
since November 2010 (March 2012 update was rolled back)" [S37]. Elasticity is one of the
three pillars of the rate recommendation [S2, S19]; rate differentials directly scale every
per-length rate [S24, S33].

**Problem:** every price the system emitted after 2010 used demand-sensitivity and
length-premium estimates from a pre-2011 market. The one refresh attempt (March 2012) was
rolled back, and the deck records no retry — meaning there was no safe mechanism to update a
core model.

**Proposal:**
1. Re-estimate elasticity and differentials on current data (the pipelines already exist per
   [S37]; they are dormant, not absent).
2. Build the missing safety mechanism that caused the 2012 rollback to be terminal: shadow
   runs (new MRM prices computed but not published), station-level A/B or staggered-market
   rollout, automatic revert thresholds on sellout/revenue deltas.
3. Add drift monitoring so "model last refreshed" is a dashboard fact, not deck trivia.

## 🔴 2. Replace the undocumented "brain" only after pinning it down — then simplify it

**Basis:** the reference-price→system-price adjustment function is documented nowhere
[manual §6.2]; its observed behavior at five S33 calibration points shows identical
multipliers (1.05809) for different sellouts (95.6% vs 93.3%) and a discontinuous jump
(≈1.10 → ≈2.08) once forecast sellout crosses 100% [S33]. The builder himself endorses
replacing the algorithm while keeping the plumbing [T19].

**Problem:** (i) nobody can currently audit why a rate is what it is; (ii) the observed jump
at 100% forecast sellout produces cliff-edge pricing — a fraction of a minute of extra
forecast demand can double the recommended rate, which is exactly what the max-rate machinery
then has to claw back [S22–S24]; (iii) banded multipliers create plateau-then-jump dynamics
rather than the smooth "inching up" the philosophy calls for [T25].

**Proposal:** extract M(·) from the nightly scripts (unknowns register U8), publish it, then
replace it with a continuous, monotone-in-sellout response curve with elasticity as an
explicit parameter — eliminating the cliff at 100% and most max-rate triggers at the source.

## 🔴 3. Max rate anchors tomorrow's price to yesterday's book — a self-limiting feedback loop

**Basis:** when demand is strongest (forecast sellout > 100%), the rate is capped by
statistics of what is already on the books — max rate OTB, 90th percentile OTB, average OTB
× 1.3, each with tolerance [S22–S24]. "Max rate LOWERS rates" [S22]. The deck's own
workarounds (raise station-wide tolerance; hard overrides that decay; distort the demand
forecast) are all blunt [S26], and the third pollutes corporate reporting [S26].

**Problem:** the cap makes the achievable ceiling a function of past selling behavior. A
station whose sellers historically underpriced can never be recommended a market-correct
rate in high demand; the cap re-bases on the depressed book each cycle. Meanwhile the only
clean relief valve (tolerance) is station-global — one knob for all weeks/days/dayparts/
lengths [S25].

**Proposal:**
1. Make tolerance settable per daypart/day-of-week (removes the main reason people reach for
   forecast-distorting workarounds).
2. Re-anchor the ceiling: blend OTB statistics with the reference price path (e.g., cap
   relative to the in-week reference price) so the ceiling reflects cleaned market value,
   not just legacy deals.
3. Log every max-rate trigger; a daypart that triggers chronically is evidence the reference
   price or response curve is mis-calibrated, not that demand is "too high."

## 🔴 4. Fix the trigger gap below 40% current sellout

**Basis:** the two documented max-rate regimes cover current sellout > 95% and 40–95%
[S23]. Nothing is documented for forecast sellout > 100% with current sellout < 40% (early
huge forecast, thin book). The forecast caps [S16] limit forecast sellout to 100% only below
10% actual sellout; between 10% and 40% actual sellout, forecast sellout up to 105–115% is
reachable while neither max-rate regime applies.

**Problem:** either the behavior is undefined (uncapped spikes) or it exists but is
undocumented — both are defects; the training material cannot say what the system does.

**Proposal:** close unknowns U8/U17, then either document the below-40% behavior or define it
(the natural completion is the regime-B formula with the 90th-percentile anchor).

## 🟠 5. Modernize the statistical estimators (keep the architecture)

**Basis:** current estimators, per the deck: recency-weighted averages with hard top/bottom
10% trims [S17, S9]; seasonality as simple ratios per week-of-year [S8]; cancellation rates
at market × dow × days-left [S4]; booking curves pooled by month × dow from 2 years [S11,
S12]; step-function forecast caps [S16].

**Problems & proposals**, component by component (architecture — the decomposition into
curves, seasonality, demand levels, reference prices — is sound and retained):

| Component | Documented limitation | Upgrade |
|---|---|---|
| Reference price trims | Fixed 10%/10% trim discards a fifth of clean data and still admits drift between the trims [S17] | Robust estimators (winsorized/quantile-weighted mean); trim fractions as tunable config per station volume |
| Seasonality | Week-of-year ratios misalign moving events (Easter, Super Bowl week shifts, election cycles) [S7, S8 structure] | Event-aligned calendar features alongside week-of-year; multi-year weighting (closes U4 with something better than the unknown) |
| Cancellation curves | Market-level only [S39]; day-of-week × days-left cells from 6 months of data are thin | Hierarchical shrinkage: station-level estimates pooled toward market; smooth across days-left instead of step lookup |
| Booking curves | Month × dow pooling ignores year-over-year drift; sparse cells visible in the deck's own example ("—" at 11 days) [S12] | Monotone smoothing of the cumulative curve; blend adjacent months; explicit uncertainty bands feeding the cap logic |
| Forecast caps | Five-band step function [S16] creates discontinuities at band edges | Replace with a continuous cap curve; keep the intent (distrust early forecasts) |
| Demand smoothing | Undocumented alpha [U1]; 26-week window fixed [S9] | Documented, backtested smoothing constant; window sensitivity testing |

All of these are drop-in replacements inside jobs J1–J5 of the replication spec — the brain
swap the builder endorsed [T19].

## 🟠 6. Backtesting and forecast-accuracy measurement as first-class infrastructure

**Basis:** the deck documents no accuracy measurement of any kind — no error metrics for the
inventory forecast, no revenue lift attribution for pricing. The 2012 MRM rollback [S37] and
the "forecasted sellouts are used widely for various corporate purposes" caveat [S26] both
show decisions being made without a measurement harness.

**Proposal:** nightly forecast snapshots vs realized minutes (WAPE/bias by horizon, station,
daypart); reference-price vs achieved-rate tracking; a replay harness so any proposed change
(new MRM, new smoothing constant, flat-rate mode) is backtested on history before touching
production. This is also the acceptance gate for any brain replacement (spec §6 extends
naturally from worked-example tests to full replay).

## 🟠 7. Separate the pricing forecast from the reporting forecast

**Basis:** demand/forecast overrides entered to manipulate *pricing* flow straight into
corporate reporting, and the deck explicitly warns people off the workaround for that reason
[S26].

**Problem:** one artifact serves two masters; pricing hygiene and reporting integrity are
coupled, so users must choose between a bad rate and bad corporate data.

**Proposal:** dual-track forecasts — raw model forecast (reporting) and adjusted forecast
(pricing), with override provenance recorded. Removes the documented conflict at zero
modeling cost.

## 🟠 8. Cold start: pool across stations instead of waiting 12 months

**Basis:** a new station needs ~12 months of data; a format flip potentially resets it;
"currently unable to copy data from another station"; interim is a manual rate card in the
CPI tool [S35]. Format flips are also the canonical externality that forces manual override
work [T17, S27].

**Proposal:** hierarchical priors — initialize a new/flipped station from similar stations
(same format cluster, market size), then let its own data take over as it accumulates. This
converts a 12-month blind spot (at exactly the moment pricing matters most) into a
weeks-long calibration period, and gives format flips a principled reset instead of ad-hoc
demand overrides.

## 🟠 9. Instrument the no-charge economy instead of only hiding it

**Basis:** $0/added-value spots are "a cultural problem … endemic" [T24, corroborated by
"Me" in the transcript]; they are excluded from price statistics (correctly, per the
downward-spiral argument [T24]) but consume inventory and thus raise sellout and recommended
rates [T23]; buyers' blended prices fall while list rates rise.

**Problem:** the current design is defensible but blind: no documented metric tracks how much
inventory is given away, and the freebies actively *inflate* the demand signal (they count as
sold minutes) — free spots make the paid rate go up.

**Proposal:**
1. Report no-charge load (minutes and % of capacity) and effective blended rate per station/
   daypart alongside the reference price, so the CPM-review exercise the transcript describes
   [T27] is standing reporting, not a one-off pull.
2. Decide explicitly whether no-charge minutes should count toward sellout for *pricing*
   (status quo: yes [T23]). If they remain in, document it as policy; if a discount factor is
   applied, backtest it (see #6). Either way it becomes a controlled lever instead of a side
   effect.

## 🟡 10. Overrides: audit, expiry, and safer UX

**Basis:** four override types with sharp edges: floating-$ **adds** to the reference price
(a red-letter warning in the deck [S31]); rate overrides decay linearly over 56 days,
invisibly to anyone not watching [S29]; overrides propagate to CPI on a one-day lag [S29];
five people now oversee what thirty used to [T16].

**Proposal:** override ledger (who/when/why, expiry, current decay state) with scheduled
review; replace the floating/fixed radio-button trap with explicit "Add $X / Set to $X /
Scale by X%" verbs; surface decay progress in the Rate Editor (the asterisk [S28] is not an
interface); alert when an override expires or when a decayed override has silently returned
a rate to system control.

## 🟡 11. Re-platform the nightly scripts without changing the math (first)

**Basis:** the whole system is "a bunch of database scripts that run every night" [T14],
various UI artifacts are undocumented ([S28] asterisks, threshold dots), and knowledge
concentration is thin post-2015 [T16].

**Proposal:** port scripts to a versioned, tested pipeline **bit-identically first** (the
validation harness in the replication spec is the regression suite), then refactor. Never
combine re-platforming with methodology changes — the 2012 rollback [S37] is the cautionary
precedent for unseparated changes. This also mechanically closes the unknowns register
(U1–U20) as each script is read and encoded.

## 🟡 12. If the strategic decision is flat/static rates, generate the flat rates from BR5

**Basis:** leadership pressure toward flat pricing exists [T7]; the system "can accommodate
that flatness of rate. We just have to go and do a little bit of work, not technical work"
[T7]; the builder recommends keeping the plumbing regardless [T19]; the deck shows demand-
based gradients are real (advance-purchase curve $228→$289 [S18], seasonal swings 76–100%
[S8]).

**Proposal (the operationalization the transcript keeps circling):** publish a **static rate
card generated periodically from BR5's own statistics** — e.g., quarterly snapshots of the
reference-price surface, flattened across the weeks-left axis, with bounded drift between
snapshots. Buyers/sellers get the stability Bob wants ("it doesn't need to change every
day"); the company keeps the demand signal and can quantify, from the same system, exactly
what revenue the flattening gives up (via #6's replay harness). This uses the flat-rate
operating mode that already exists rather than ripping out plumbing — precisely the
"change the brain, keep the pipes" path both the builder [T19] and the static-rate sponsors
can accept.

## 🟡 13. Close the scope gap deliberately, not accidentally

**Basis:** BestRate covers station spot sales only [T1, T20]; TTWN, digital, Premiere,
packages each price differently and were deferred to later conversations [T20]; there is no
unified product catalog with pricing across lines (the transcript's product-catalog question
got "it was built on station sales").

**Proposal:** whatever replaces or extends the brain should expose reference-price +
adjustment as a *service* with the station feed as its first client, so additional inventory
types can be added as data contracts rather than new systems. (This is an extension of the
builder's plumbing principle [T19], not a contradiction of it.)

---

## Sequencing (dependency-ordered, not a mandate)

1. **Pin down the unknowns** (U1–U20) by reading the nightly scripts → unlocks everything.
2. **Stand up measurement** (#6) → prerequisite for safely changing anything.
3. **Re-platform bit-identically** (#11) → makes the system changeable.
4. **Refresh MRM with guardrails** (#1) and **smooth the response curve / fix max rate**
   (#2, #3, #4) → largest pricing-quality wins inside the current architecture.
5. **Estimator upgrades and cold-start pooling** (#5, #8) → incremental accuracy.
6. **Policy layers** (#7, #9, #10) → operational hygiene.
7. **Strategic mode decision** (#12, #13) → static vs dynamic becomes a measured choice, not
   a philosophical one.
