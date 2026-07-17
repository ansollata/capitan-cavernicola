# PROJECT HANDOFF — BestRate Replacement / Rate-Card Project

**Written:** 2026-07-14, by the Claude session that produced everything below.
**Purpose:** complete state transfer. A new Claude session (any account) with access to this
repository should be able to continue the project from this document alone, without the
original conversation.

---

## 1. The mission

Ana (as.llanotamayo@gmail.com / anasofiallanotamayo@iheartmedia.com, revenue org at
iHeartMedia) is answering an ask from Bob (senior leadership). Bob's ask, verbatim:

> "I want us to dig into how we build our revenue plans. Inventory × our rates = our revenue.
> We have real control on inventory, but it seems that an algorithm (and not a very good one)
> is telling us rates instead of us determining the rates (not cpm) we want to/need to charge
> for our inventory. We had agreed we were going to stop 'best rate' and set rates like we do
> in digital. Evidently that did not happen."

Confirmed facts: **BestRate (BR5)** — the 2010 yield-management system — still sets rates for
**broadcast stations AND TTWN** today. Only **Premiere (PN)** is human-priced (via 22
overlapping "price books"), and **digital** is the target model (a 3-number CPM card:
streaming $16, podcast market $30, podcast national $20 — Ana said to disregard digital).

**The deliverable:** management-set, published static rate cards for all inventory
("set rates like we do in digital"), with the method, governance, and migration plan —
plus the evidence base (how BestRate works, what current rates look like).

## 2. Where everything lives

### Repo `ansollata/capitan-cavernicola`, branch `claude/bestrate-pricing-analysis-spqk1i`

| Path | What it is |
|---|---|
| `docs/01-bestrate-manual.md` | Complete operating manual of BestRate/BR5, from the 2016 training deck + builder interview. Every claim cited [S# slide / T# transcript]. |
| `docs/02-replication-spec.md` | How to rebuild BR5: data contracts, per-job algorithms, batch schedule, validation harness, and a **20-item unknowns register** (U1–U20) of things only BR5's nightly SQL scripts can answer. |
| `docs/03-optimization.md` | 13 optimization findings/recommendations, each anchored to a documented limitation, dependency-ordered. |
| `docs/04-source-inventory.md` | Slide-by-slide inventory of the deck, transcript fact ledger (T1–T28), discrepancy log (D1–D10, incl. arithmetic errors in the deck itself). |
| `docs/05-ratecard-solution.md` | **The answer to Bob**: current-state analysis (Part 1) + the replacement design (Part 2): card structure, rate-setting method, governance, revenue-plan tie-in, migration. Contains an attribution-correction section (original vs transformed data). |
| `reference-implementation/` | Stdlib-Python implementation of every documented BR5 formula; 26 unit tests reproduce every worked example in the deck (all pass: `cd reference-implementation && python3 -m unittest discover -s tests -t . -v`). |
| `proposed-rate-cards/Broadcast_Proposed_Rate_Card_v0.1_DRAFT.xlsx` | 10,690 rows, current vs proposed, flags. **Built on the planner's TRANSFORMED table** (see §4) — recompute on originals pending. |
| `proposed-rate-cards/TTWN_Proposed_Rate_Card_v0.1_DRAFT.xlsx` | 13,095 cells. **Built firsthand from the ORIGINAL file** — final-grade v0.1. |
| `proposed-rate-cards/PN_Proposed_Rate_Card_v0.1_DRAFT.xlsx` | 536-cell base card + 16 discount schedules. **Firsthand from the ORIGINAL file** — final-grade v0.1. |
| `proposed-rate-cards/iHeart_Proposed_Rate_Cards_v0.1_ALL_PIPELINE.xlsx` | All three cards + pipeline tab in one workbook. |
| `proposed-rate-cards/generate_*.py` | Generators. Change a knob, re-run, card regenerates in seconds. Broadcast generator needs the planner DB (`iheart-media-planner/backend/data/iheart.db`); TTWN/PN generators need the original xlsx files. |
| `HANDOFF.md` | This document. |

Git state notes: PR #1 for this branch was opened by an accidental click and **closed**
(reopenable). Two stray branches (`claude/add-claude-documentation-*`, `claude/claude-md-docs-*`)
contain only auto-generated CLAUDE.md files from accidental sessions — ignorable/deletable.
A published review artifact (sample rows of all three cards) exists at
https://claude.ai/code/artifact/1b499c48-1083-4e68-9208-c1c6ec0a7188 (private to Ana's
original account; regenerate from the workbooks if needed — script pattern in conversation,
data all in the repo).

### Repo `ansollata/iheart-media-planner` (reference only — do not modify)

Ana's separate media-planner project (built by local Claude sessions on her Mac). Relevant
contents: `backend/data/iheart.db` (SQLite: `rate_cards` 10,690 rows — the TRANSFORMED
rates; `nielsen_ratings` 319,820 rows Fall-2025; `markets`/`stations`; `digital_rate_cards`),
`backend/scripts/import_data.py` (documents the transformation incl. the 2026-04-17 derived
:10/:05 ratio rules), and `WORKLOG.md` (invaluable: full profiling of the original rate files
by the prior local session, two subagent verifications).

### Source data files ("Updated Rates 6.1" — all dated June 1, 2026)

| File | Where it is | Fidelity status |
|---|---|---|
| `broadcastrates.txt` (472MB; forward BestRate rates for airdates 6/2/2026–12/31/2027; 2,354,555 rows; 889 stations/157 markets) | Ana's Mac + personal OneDrive + **work OneDrive** (`.../Documents/DESKTOP`-level folder "Updated Rates 6.1", as `broadcastrates.zip`, 99MB) | **Never analyzed firsthand by the cloud session** (too big for every channel). Profiled by the prior local session (WORKLOG). |
| `TTWN base rates 260601[1].xlsx` (13,417 rows) | Same locations; was also attached in the original chat | **Analyzed firsthand** — findings and card final-grade. |
| `PN Rate Cards.xlsx` (3,412 rows) | Same locations; was also attached in the original chat | **Analyzed firsthand** — findings and card final-grade. |

Predecessor: `rates.txt` (February 2026 pull) — superseded by 6.1, historical interest only.

## 3. What we know about BestRate (compressed; full detail in docs/01–04)

- Built ~2010 on airline/hotel yield management by hires from that industry post-buyout.
  Nightly database scripts — no AI. Reference price (cleaned, recency-weighted achieved
  rates, 16 weeks-out buckets) × demand-driven adjustment → system price × spot-length
  differential → rate. Max-rate logic caps peaks against rates already on the books.
- **Its market response models (elasticity, length differentials) have not been re-estimated
  since November 2010.** A March 2012 refresh was rolled back.
- The exact reference-price→system-price function is documented nowhere; 6 numeric
  calibration points extracted from the deck (docs/01 §6.2). The 2016 deck itself contains
  internal arithmetic errors (logged in docs/04).
- Yield team cut from ~30 to ~5 in 2015; markets rarely override. The builder's advice if
  replacing: **keep the plumbing (Fusion, CPI tool, Salesforce, planning optimizers), swap
  the brain.** BR5 can run flat rates as an operating-mode change; the CPI tool supports
  manual rate cards.

## 4. Current-state findings (evidence for Bob; full detail docs/05 Part 1)

Attribution matters — two data versions exist:
**[ORIG]** = original 6.1 files (firsthand for TTWN/PN; via WORKLOG for broadcast).
**[DB]** = planner's transformed table (medians per MF/Sat/Sun group, 715/889 stations
mapped, :10/:05 added by the planner's own rule).

- The "dynamic" system is mostly static: **Mon–Fri rates identical**; only Sat (~×0.65) and
  Sun (~×0.59) differ [ORIG]. Median cell has **no seasonal lift**; the Sep–Dec premium lives
  in ~30% of cells (premium stations; Nov peak; Jan trough) [ORIG].
- Junk pricing: 1,118 $1-placeholder cells [ORIG]; 28% of [DB] cells ≤$5 for a :30.
- Price-vs-audience dispersion: implied CPM (Nielsen P25-54) spreads ~7× p90/p10 within the
  same daypart, 5–8× within market-size tiers [DB; direction confirmed at 1.6× p75/p25 in
  ORIG]. Caveat: P25-54 understates AM-talk audiences (e.g., WRKO Boston's extreme CPM is
  partly demo artifact).
- Length economics drifted unmanaged: observed :30/:60 ≈ 0.75 vs the frozen 2010
  differential 0.57. **The ":10 priced above :15 on 76% of rows" defect is the PLANNER'S
  import rule, not BestRate's** — original card has no :10/:05 at all (only 4 monotonicity
  violations in 2.9M rows). Corrected in docs/05.
- TTWN [ORIG, firsthand]: Rated ≈ $24 M-F median vs Non-rated $7 (~3.4×); weekend ≈ 0.46×;
  472 zero/$1 rows; **52.4% of affiliate rows are non-iHeart stations** (Cumulus, Audacy…).
- Premiere [ORIG, firsthand]: 22 books, 1,413 dead rows (41%); quarters flat; TARGET books
  are clean hidden discount schedules (1Q ≈ 87%, Upfront ≈ 86%, 2Q ≈ 80% of base); Label
  = exactly 120%; AA ≈ 130%; Voiced books inconsistent (100–280% row to row).
- BestRate's export contains no demand/sell-through signal — cannot be audited or optimized
  from its own output [ORIG].

## 5. The proposed solution (full detail docs/05 Part 2)

Published static cards, set by management, regenerated from data on a governed calendar:

- **Broadcast:** Station × 5 dayparts × {M-F, Sat, Sun} × {:60 :30 :15 :10 :05}; two
  seasons/yr (Everyday Jan–Aug, High Season Sep–Dec — the observed seasonality boundary).
  Method: median-achieved baseline → floors (kill $1 rates) → audience-band correction
  (raise if CPM < 70% of tier×daypart peers, cap +25%/refresh, NEVER auto-cut; flag > 150%)
  → policy length ratios (1.00/.75/.45/.40/.25 — puts :10 below :15) → round pricing
  ($1<$20, $5<$100, $10 above). Weekend cells move by their weekday factor.
- **TTWN:** native grain, dup-collapse, floors (R $5 / NR $2, weekend 60%), within-market
  outlier flags only, iHeart?/non-iHeart flag on every row.
- **Premiere:** ONE base card + named discount schedules (% of base); dead rows dropped;
  quarter columns dropped (flat).
- **Governance:** one pricing owner; 2 refreshes/yr; exception log with expiry; discount
  ladder; quarterly achieved-vs-card, sellout, exception count, no-charge load.
- **Revenue plan tie-in (Bob's frame):** plan = Σ capacity × card rate × planned sellout −
  discount leakage; every term becomes a management lever; variance decomposes into
  volume/rate/mix/discount.
- **Migration:** adopt 6.1-derived static cards as provisional card now (this alone = "stop
  BestRate deciding daily") → first governed refresh applies the method → cards flow through
  existing plumbing (CPI manual-rate-card path / BR5 flat mode) → BestRate runs read-only
  one season as a shadow benchmark → decommission after two clean cycles.

## 6. Open items (in order)

1. **Broadcast recompute on the ORIGINAL file + High Season companion card.** Needs
   `broadcastrates.txt` (in `broadcastrates.zip`, 99MB, Ana's work OneDrive → "Updated Rates
   6.1" folder). Cloud sessions couldn't get it (see §7). A local session on Ana's Mac reads
   it directly at `~/Library/CloudStorage/OneDrive-.../…/Updated Rates 6.1/`. Method: mirror
   `generate_broadcast_card.py` but source medians from the raw file per season
   (Jan–Aug / Sep–Dec), then update docs/05 §1.3 numbers to [ORIG].
2. **Management knob decisions** (docs/05 §2.7): approve the model; length-ratio policy;
   floors + rounding; TTWN non-iHeart split-or-keep; Premiere book consolidation (which
   schedules survive; normalize Voiced); name the pricing owner + refresh calendar +
   discount ladder.
3. **v1.0 cards** after decisions: re-run generators with chosen knobs on original data.
4. Optional evidence work: read BR5's nightly SQL scripts to close the unknowns register
   (U1–U20, docs/02 §7) — mainly to defend "we understand what we're replacing."

## 7. Access lessons (read before repeating our mistakes)

- **Cloud sessions cannot see Ana's Mac or personal OneDrive.** Her local folders were only
  ever readable by LOCAL Claude Code sessions on her Mac (OneDrive syncs to local disk).
- The **work Microsoft 365 connector** can find and read her work OneDrive files BUT
  truncates content at ~100k chars of flattened text — fine for small/simple files (that's
  how the Cannes pipeline file was read in full), useless for big spreadsheets.
- The cloud sandbox **network policy blocked OneDrive domains** (1drv.ms etc.); Ana added
  custom allowed domains, but that applies to NEW sessions only. Direct share-link downloads
  may work in a fresh session in the same environment.
- **What worked best: attaching files to the chat** (TTWN + PN xlsx came through perfectly)
  and reading committed repo data.
- **Session transfer across Claude accounts does NOT carry conversations.** This document +
  the repo IS the transfer. (Same-account continuation could use teleport; cross-account
  cannot.)
- Do not commit named-seller sales data (e.g., the unrelated Cannes pipeline detour) to the
  repo; rate cards and analysis are fine.

## 8. First actions for the next session

1. Clone `ansollata/capitan-cavernicola`, check out `claude/bestrate-pricing-analysis-spqk1i`,
   read `docs/05-ratecard-solution.md` first, then this file's §6.
2. If running LOCALLY on Ana's Mac (recommended): open item #1 is immediately unblocked —
   the Updated Rates 6.1 folder is on local disk.
3. If running in the cloud: add repo `ansollata/iheart-media-planner` (read-only reference),
   and have Ana attach or share the broadcast zip per §7.
4. Verify the reference implementation still passes:
   `cd reference-implementation && python3 -m unittest discover -s tests -t . -v` (26 tests).
