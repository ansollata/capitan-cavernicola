# BestRate (BR5) Reference Implementation

A stdlib-only Python implementation of every **documented** part of BestRate, with the
deck's worked examples as its acceptance-test suite. Companion to
[docs/02-replication-spec.md](../docs/02-replication-spec.md); source citations (S# slides,
T# transcript facts, U# unknowns, D# discrepancies) resolve via
[docs/04-source-inventory.md](../docs/04-source-inventory.md).

## Layout

| Module | Implements | Slides |
|---|---|---|
| `bestrate/curves.py` | Cancellation curves, booking curves, seasonality factors | S4, S7–S8, S11–S13 |
| `bestrate/demand.py` | Deseasonalization, recency-weighted averaging | S9, T10 |
| `bestrate/forecast.py` | Inventory forecast, forecast caps, half-up rounding | S3, S14–S16 |
| `bestrate/reference_price.py` | Filter stack, 10/10 trims, 16 weeks-left buckets | S17–S18 |
| `bestrate/mrm.py` | Elasticity banding, AUR/AMR, rate differentials | S19–S21 |
| `bestrate/pricing.py` | System rate, max-rate cap, observed calibration points | S22–S24, S33 |
| `bestrate/overrides.py` | Reference/demand/rate overrides, 56-day decay | S27–S33 |
| `bestrate/schedule.py` | Job cadence, BR5 revenue type lists | S36–S37 |

## What is deliberately NOT implemented

The market-response function (final reference price → system price) is undocumented in the
source materials (unknowns register **U8**). `bestrate/pricing.py` ships the six observed
calibration points any reconstruction must reproduce, and takes `system_price` as an input.
Percent-mode overrides (U9) raise `NotImplementedError` instead of guessing. All other
assumptions are labeled `ASSUMPTION (U#)` in docstrings and exposed as parameters.

## Running the validation suite

```
cd reference-implementation
python3 -m unittest discover -s tests -t . -v
```

Every test cites the slide it reproduces. Three tests intentionally encode the deck's own
internal inconsistencies (D2, D3, D8 — display-rounding artifacts) by asserting the correct
arithmetic and noting the deck's displayed value in a comment.
