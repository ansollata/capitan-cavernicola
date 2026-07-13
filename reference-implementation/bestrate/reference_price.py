"""Reference prices [S17, S18, T10-T13].

A reference price is the cleaned, recency-weighted price actually achieved,
computed nightly per station x day-of-week x daypart x weeks-left bucket
from 12 months rolling data [S17] (transcript says "a couple of years" —
discrepancy D1).
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from typing import Any

from .demand import exponentially_weighted_mean

# The 16 weeks-left buckets: in-week, 1..14, 15+ [S17].
IN_WEEK = "in-week"
FIFTEEN_PLUS = "15+"
WEEKS_LEFT_BUCKETS: list[Any] = [IN_WEEK, *range(1, 15), FIFTEEN_PLUS]


def weeks_left_bucket(weeks_left: int) -> Any:
    """Map integer weeks-before-airdate to one of the 16 buckets [S17].

    ASSUMPTION (U13): the sources do not define where "in-week" ends and
    "1 week left" begins; weeks_left == 0 is treated as in-week here.
    """
    if weeks_left < 0:
        raise ValueError("weeks_left cannot be negative")
    if weeks_left == 0:
        return IN_WEEK
    if weeks_left >= 15:
        return FIFTEEN_PLUS
    return weeks_left


def passes_reference_price_filters(
    spot: dict,
    *,
    market_break_types: set[str],
    exclude_rotators: bool = True,
) -> bool:
    """The S17 filter stack on top of the universal criteria [S17, S38, S36].

    Universal: P40+ aired, 15/30/60s, BR5 revenue types, market break types.
    Additional: commercial breaks only; no no-charges; no rotators (subject
    to the per-station rotator preference, semantics UNKNOWN); no political/
    issue rates; no flights > 98 days; no weekday+weekend flights; no Flexnet.
    Top/bottom 10% trims are applied afterwards on the surviving rates
    (see trim_rates; order of operations UNKNOWN, U5).
    """
    return (
        spot["priority"] >= 40  # P40+ (priority scale itself NOT SPECIFIED)
        and spot["aired"]
        and spot["spot_length"] in (15, 30, 60)
        and spot["is_br5_revenue_type"]
        and spot["break_type"] in market_break_types
        and spot["is_commercial_break"]
        and not spot["no_charge"]
        and not (exclude_rotators and spot["is_rotator"])
        and not spot["is_political_or_issue"]
        and not spot["flight_length_days"] > 98
        and not (spot["flight_has_weekdays"] and spot["flight_has_weekend"])
        and not spot["is_flexnet"]
    )


def trim_rates(rates: Sequence[float], lower: float = 0.10, upper: float = 0.10) -> list[float]:
    """Exclude top 10% and bottom 10% of rates [S17].

    ASSUMPTION (U5): the deck does not define the percentile method; this
    drops floor(n*lower) observations from the bottom and floor(n*upper)
    from the top of the sorted sample.
    """
    s = sorted(rates)
    n = len(s)
    lo = math.floor(n * lower)
    hi = n - math.floor(n * upper)
    return s[lo:hi]


def reference_price(
    rates_oldest_first: Sequence[float],
    *,
    alpha: float,
    deseasonalize_fn=None,
    reseasonalize_fn=None,
) -> float:
    """Recency-weighted reference price for one bucket [S17, T10].

    "Weighted towards more recent transactions; like the demand forecast,
    reference prices are deseasonalized first with seasonality added back in
    later" [S17]. The deseasonalize/re-seasonalize mechanics for PRICES are
    UNKNOWN (U2) — hooks are provided; identity by default. The smoothing
    constant is UNKNOWN (U1) — pass alpha explicitly.
    """
    values: Iterable[float] = rates_oldest_first
    if deseasonalize_fn is not None:
        values = [deseasonalize_fn(v) for v in values]
    price = exponentially_weighted_mean(list(values), alpha)
    if reseasonalize_fn is not None:
        price = reseasonalize_fn(price)
    return price


# S18 example, verbatim: Monday AMD reference prices by weeks left.
S18_EXAMPLE_REFERENCE_PRICES: dict[Any, int] = {
    FIFTEEN_PLUS: 228, 14: 231, 13: 232, 12: 232, 11: 235, 10: 239, 9: 244,
    8: 245, 7: 253, 6: 259, 5: 268, 4: 277, 3: 283, 2: 284, 1: 289,
    IN_WEEK: 289,
}
