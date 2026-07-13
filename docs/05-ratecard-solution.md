# Rate Cards for Our Inventory — Current State & Proposed Solution

**Prepared for:** Ana (responding to Bob's ask, 2026-07)
**Bob's ask (verbatim):** "I want us to dig into how we build our revenue plans. Inventory × our
rates = our revenue. We have real control on inventory, but it seems that an algorithm (and not
a very good one) is telling us rates instead of us determining the rates (not CPM) we want
to/need to charge for our inventory. We had agreed we were going to stop 'best rate' and set
rates like we do in digital. Evidently that did not happen."

**Sources for this report:** the BestRate training deck and transcript (documented in
[01-bestrate-manual.md](01-bestrate-manual.md) / [04-source-inventory.md](04-source-inventory.md));
the `iheart-media-planner` repository — its `rate_cards` database (10,690 deployed static rate
rows built from the **Updated Rates 6.1** BestRate export) and its WORKLOG, which documents the
full profiling of the three 6.1 source files (broadcast 2.35M rows / TTWN 13,417 rows /
Premiere 3,412 rows). Statistics computed fresh from the database are marked **[DB]**; statistics
from the prior session's documented profiling of the raw files are marked **[WL]**. The raw 472MB
broadcast file itself is not in the repo; WL figures passed two independent subagent reviews.

---

## Part 1 — Where rates stand today

### 1.1 Bob is right on the facts

- **BestRate is still setting the rates.** The "Updated Rates 6.1" folder — the current rate
  card — is a BestRate export (daily station × daypart × spot-length rates, columns literally
  named BR60/BR30/BR15), except Premiere, which is priced via its own rate books. TTWN is also
  priced by the BestRate algorithm. (Ana, confirmed 2026-07.)
- **The algorithm's core intelligence is 16 years old.** Its market response models —
  elasticity and the spot-length differentials — have not been re-estimated since **November
  2010** (the March 2012 refresh was rolled back). Deck, slide 37.
- **It cannot be audited from its own output.** The export contains no demand, sell-through, or
  elasticity signal (its yield columns are flat or run backwards vs. price — e.g. Overnight has
  the *highest* cap_min and the *lowest* rate) [WL]. Nobody can look at the file and say why a
  rate is what it is.

### 1.2 The dirty secret: the "dynamic" system is already mostly static

- **Monday–Friday rates are identical** (×1.00 across weekdays) in the BestRate output; only
  Saturday (×0.65) and Sunday (×0.59) differ [WL]. Five of seven "dynamic" day rates are
  duplicates.
- **Seasonality is concentrated, not pervasive:** the median cell has *no* high-season lift
  (median Sep–Dec lift 1.000×); the premium lives in ~30% of cells, mostly big-market premium
  stations (e.g. Z100 AMD :30 $915 → $1,058); January is the trough (−11%) [WL].
- Only 24 of 10,690 deployed cells rest on fewer than 30 underlying observations [DB] — the
  medians are statistically stable, i.e. a static card loses very little information.

**Implication:** converting to published static cards discards far less "dynamic value" than
BestRate's complexity implies. Two cards a year (Everyday + High Season) at MF/Sat/Sun grain
reproduce almost everything the algorithm actually varies.

### 1.3 What the current rates look like

**Attribution note (corrected per Ana, 2026-07-13):** two versions of the card exist. The
**original** BestRate card (the Updated Rates 6.1 export: 889 stations / 157 markets, :60/:30/:15
only) lives on Ana's OneDrive and is profiled in the planner WORKLOG [WL]. The **planner's
derived card** (the `rate_cards` table: 715 stations / 135 markets after name-mapping, medians
per day-group, :10/:05 added by the planner's own 2026-04-17 rule) is a *transformation* of it
[DB]. Statistics below are tagged by which card they describe; planner-only artifacts are not
defects of BestRate's card and are flagged as such.

| Median :30 rate (MF) | AMD | Midday | PMD | Evening | Overnight |
|---|---|---|---|---|---|
| | $33 | $29 | $30 | $10 | $3 |

- Sensible drive-time hierarchy and a sensible market-size gradient (top-10 markets median AMD
  :30 = $155 vs $22 in markets ranked 101+).
- **But the levels are ragged where it matters:**
  - **Placeholder-grade rates are endemic in both versions:** 28% of derived-card cells price
    the :30 at ≤ $5 and 6.5% at ≤ $1 [DB]; the original card independently showed 1,118
    $1-placeholder cells and a $2.90 median Overnight :30 [WL] — the disease is BestRate's,
    not the transformation's.
  - Within a single market, the p75/p25 spread of AMD :30 rates is **2.5×** on the derived card
    (max 9.4×) [DB]; **1.6×** measured on the original card [WL] — dispersion is real in the
    original and amplified by the planner's aggregation.
  - Joined to Nielsen audience (P25-54 AQH), the implied CPM spread within the *same daypart* is
    **7× between the 10th and 90th percentile station** — and 5–8× even within the same market-size
    tier. Same tier, same daypart: WIOQ Philadelphia sells a :30 at ~$7.8 CPM while WRKO Boston
    prices at ~$1,010 CPM. (Caveat: AM talk stations' P25-54 AQH understates their older
    audiences — the extreme tail is partly a demo artifact — but the broad dispersion is real.)
- **The spot-length economics have drifted unmanaged.** Observed :30/:60 = 0.75 and
  :15/:60 = 0.43 on today's card (vs the frozen 2010 differentials of 0.57/0.32) [DB, source
  rates observed not derived]. The original card is internally consistent on its three lengths
  (only 4 monotonicity violations in 2.9M rows [WL]).
- **CORRECTED ATTRIBUTION — the :10/:05 inversion is the planner's, not BestRate's.** The
  original card carries no :10/:05 rates at all. The planner's import rule (:10 = 0.75 × :30,
  business decision 2026-04-17) prices the :10 above the observed :15 on **76% of the derived
  card** [DB]. Any :10/:05 rates quoted from the planner today are contradictory with the :15 —
  a defect to fix in the planner *and* a policy gap (nobody has set official :10/:05 pricing)
  that the new rate card must close.

### 1.4 TTWN and Premiere (the rest of "everything")

- **TTWN** [WL]: single rate per Market × Affiliate × Rated/Non-rated × Weekday/Weekend ×
  Daypart; Rated ≈ 2.5× non-rated; weekend = 0.5× weekday; median $15; 472 rows at ≤$1 or $0.
  Structural caveat: **52.4% of the affiliates on the card are non-iHeart stations** — it prices
  a network product, not just our inventory.
- **Premiere/PN** (not BestRate): 22 overlapping price books for the same Vehicle × Daypart ×
  length (17 survive after cleanup), **41% of rows were dead (all-zero)**, and the quarterly
  columns are flat — the real price signal lives in *which book you look at*. This is what
  human-set pricing without governance decays into: book sprawl instead of a card.
- **Digital** (the model Bob points to): the entire card is **three numbers** — streaming $16
  CPM, podcast market $30, podcast national $20. Simple, published, management-owned.

### 1.5 Bottom line of Part 1

The algorithm isn't "telling us rates" from live intelligence — it's replaying 2010-vintage
logic over its own transaction history, producing rates that are already 80% static, internally
contradictory across spot lengths, placeholder-cheap on a quarter of the card, and unexplainable
to the people accountable for revenue. Meanwhile the parts humans do own (Premiere) show the
opposite failure: sprawl without structure. The answer isn't "algorithm vs. no algorithm" — it's
**published cards, set by management, generated with evidence, on a governed cadence.**

---

## Part 2 — The solution: management-set rate cards, digital-style

### 2.1 Design principles (Bob's constraints, made operational)

1. **We set unit rates, not CPMs.** The card states $/spot by station, daypart, day-group and
   length. CPM is used as a *sanity check* while setting (are we mispriced vs audience?), never
   as the published rate. This is exactly Bob's "(not cpm)".
2. **Simple enough to own.** One card per business line, one grain, one refresh calendar. If a
   rate can't be explained in one sentence ("tier-2 market, AMD, :30, standard card"), it
   doesn't go on the card.
3. **Evidence-informed, human-decided.** Data proposes; the pricing owner disposes. No nightly
   repricing. No black box.
4. **Keep the plumbing, replace the brain** — the BestRate builder's own advice. Rates keep
   flowing to Fusion/CPI/Salesforce/planning through the existing paths; only the *source* of
   the numbers changes. BR5 itself supports flat rates as an operating-mode change ("operating
   work, not technical work"), and the CPI tool already supports manual rate cards.

### 2.2 The card structure (broadcast)

**Grain:** Station × 5 dayparts × {M–F, Sat, Sun} × {:60 :30 :15 :10 :05} — the grain already
proven by the deployed card (~10,700 rows; fits in one Excel tab per season). The data says this
grain is lossless: weekdays are identical in the source, and finer time slicing carries no
observed signal.

**Two seasons:** *Everyday* (Jan–Aug) and *High Season* (Sep–Dec) — because that's where the
real, observed seasonality boundary is [WL]. January promotions handled as a discount policy,
not a third card.

**How each number is set (the repeatable method):**

1. **Baseline** = median achieved BestRate rate per cell from the latest export (already built —
   this is the 6.1 static card). The baseline is where the market *has been clearing*, so the new
   card starts credible, not theoretical.
2. **Audience-anchor correction** (the "market-based" step): compute each station's implied CPM
   vs its market/tier peers using the Nielsen join (all in the database already). Cells sitting
   far below the tier band (e.g. <70% of peer-median CPM) get raised toward the band — with a
   per-refresh cap (e.g. +25%) so the card never jumps; cells far above get *flagged for review*,
   not auto-cut (never cut without a human decision). This directly attacks the 7× CPM raggedness
   and the 28%-of-card-≤$5 problem.
3. **Deliberate length ratios** — a management decision, applied uniformly: e.g. :60 = 1.00,
   :30 = 0.75, :15 = 0.45, :10 = 0.40, :05 = 0.25 of :60 (starting values taken from today's
   *observed* :30/:15 economics, with :10/:05 set BELOW :15 — fixing the 76%-inverted anomaly).
   Whatever numbers are chosen, they become policy — replacing both the frozen 2010 differentials
   and the contradictory bolt-on rule.
4. **Floors and rounding:** minimum card rate per daypart (kills the $1 placeholders — if
   inventory is worth ~nothing, that's a distribution/packaging decision, not a $1 rate), and
   round pricing ($5 increments under $100, $10 above) so the card reads like a price list, not
   an algorithm dump.
5. **Publish with a confidence column** (observation count per cell — already in the data), so
   sellers know which rates are deeply grounded vs thin.

### 2.3 TTWN and Premiere

- **TTWN:** same method, its native grain (Market × Affiliate × Rated/NR × WeekDef × Daypart).
  Two management decisions required first: (a) minimum-rate floor (there are 472 ≤$1/zero rows);
  (b) whether non-iHeart affiliates stay on the same published card or split — it's 52% of rows
  and a different economic product.
- **Premiere:** consolidation, not derivation — collapse 17 surviving price books into ONE card
  plus named discount schedules (upfront %, ethnic-programming %, voiced %). The quarters-flat
  finding says quarterly columns can go; the card becomes Vehicle × Daypart × length.
- **Digital stays as-is** — it's already the target model.

### 2.4 Governance (what makes it stick this time)

The 2015 lesson: the yield team shrank 30 → 5, and the algorithm kept running because nobody
owned an alternative. The card only replaces BestRate if it has an owner and a calendar:

| What | Who / when |
|---|---|
| Card ownership | One pricing owner (revenue management), sign-off by CRO/Bob |
| Refresh | 2×/year for levels (May → Everyday card, July → High Season card), using the refresh method above |
| Exceptions | Market managers propose; pricing owner approves; every exception has an expiry date; exception log reviewed at refresh |
| Guardrails | Sold-out relief valve: a market may request an off-cycle raise for a station/daypart demonstrably selling out; no off-cycle cuts |
| Discounting | Card is gross rate; discount authority ladder by % off card; no-charge/added-value spots tracked as a % of capacity per station (today they're invisible and inflate "demand") |
| Measurement | Quarterly: achieved rate vs card, sellout by daypart, exception count, no-charge load. This is also what finally makes the revenue plan auditable |

### 2.5 The revenue-plan tie-in (Bob's actual frame)

With a published card, the revenue plan becomes bottom-up arithmetic instead of an algorithm's
side effect:

```
Revenue plan = Σ (station × daypart × season)
               capacity minutes  ×  card rate  ×  planned sellout %  −  planned discount leakage
```

Every term is now a management lever: capacity (we control), card rate (we now control),
planned sellout (from history), discount leakage (governed by the ladder). Variance analysis
falls out for free: actual vs plan decomposes exactly into volume, rate, mix, and discount —
which today is impossible because "rate" isn't a controlled input.

### 2.6 Migration plan (no big-bang, nothing breaks)

1. **Now:** adopt the 6.1-derived static cards (already built) as the *provisional* published
   card — this alone fulfills "stop BestRate deciding daily."
2. **Refresh #1 (first cycle):** apply the method in §2.2 — audience-anchor corrections, chosen
   length ratios, floors, rounding. This is the first card that is genuinely *set* rather than
   *observed*.
3. **Plumbing:** load cards via the existing manual-rate-card path (CPI tool) / BR5 flat-rate
   operating mode, so Fusion/Salesforce/planning feeds continue untouched. BestRate's nightly
   scripts stop being the rate source; keep them running read-only for one season as a shadow
   benchmark (what would the algo have charged?) — free evidence for refresh #2.
4. **Decommission** the BestRate rate-setting role once two refresh cycles have run clean.

### 2.7 Decisions needed (the ask back to Bob/leadership)

1. Approve the model: published static cards, 2 seasons, grain as in §2.2.
2. Set the length-ratio policy (proposed: 1.00/0.75/0.45/0.40/0.25 — one meeting).
3. Set floors and the rounding rule.
4. TTWN: floor + whether non-iHeart affiliates share the card.
5. Premiere: approve book consolidation (17 → 1 card + discount schedules).
6. Name the pricing owner and approve the refresh calendar + discount ladder.

### 2.8 What this does NOT do (honest limits)

- It does not capture day-level demand surges the way a live yield system theoretically could.
  The data says that theoretical value is small today (weekdays identical, median seasonal lift
  1.0×, MRM frozen since 2010) — but the shadow benchmark in §2.6 measures what we give up
  instead of asserting it.
- The audience-anchor step inherits Nielsen's limitations (diary markets, demo choice; AM-talk
  stations need an older-demo anchor).
- TTWN's non-iHeart affiliate economics and Premiere's book consolidation need business input
  no analysis can supply.
