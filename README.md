# BestRate (BR5) — Analysis, Replication & Optimization

Complete reconstruction of iHeartMedia's **BestRate** station-pricing system from two source
materials: the internal training deck `BR_Training__New_Format.20160509.pdf` (39 slides,
2016-05-09) and a transcript of a conversation with one of the system's builders.

Ground rules applied throughout: every claim is traceable to a slide or a transcript quote;
gaps in the sources are marked **NOT SPECIFIED / UNKNOWN** instead of being filled in;
internal inconsistencies in the sources are logged, not silently corrected.

## Contents

| Deliverable | Location |
|---|---|
| **(a) Manual** — how BestRate works, end to end | [docs/01-bestrate-manual.md](docs/01-bestrate-manual.md) |
| **(b) Replication** — data contracts, algorithms, job schedule, unknowns register | [docs/02-replication-spec.md](docs/02-replication-spec.md) |
| **(b) Replication** — runnable reference implementation + deck-derived acceptance tests | [reference-implementation/](reference-implementation/) |
| **(c) Optimization** — 13 recommendations, each anchored to a documented limitation | [docs/03-optimization.md](docs/03-optimization.md) |
| Source traceability — slide-by-slide inventory, transcript fact ledger, discrepancy log | [docs/04-source-inventory.md](docs/04-source-inventory.md) |

## The system in one paragraph

BR5 prices broadcast radio spots the way airlines price seats. Nightly database scripts
compute, per station: an **inventory forecast** (minutes on the books − projected
cancellations + remaining demand from booking curves, seasonality and recency-weighted
demand levels), a **reference price** (cleaned, outlier-trimmed, recency-weighted achieved
rate in 16 weeks-before-airdate buckets), and **market response models** (elasticity and
per-spot-length rate differentials — frozen since November 2010). Reference price × a
demand-driven adjustment → system price; × rate differential → per-length target rate;
capped by "max rate" logic anchored to the highest/average rates already on the books.
Humans intervene through four override types with defined precedence and a 56-day decay.
Rates feed Fusion, the CPI tool, media-planning optimizers and Salesforce.

## Validation

```
cd reference-implementation
python3 -m unittest discover -s tests -t . -v
```

26 tests reproduce every numeric worked example in the deck (forecast example, booking
curve, seasonality, rate differentials, both max-rate cases, override decay), including
three places where the deck's own printed numbers are internally inconsistent (documented
as discrepancies D2/D3/D8).
