"""Cancellation curves, booking curves, seasonality factors.

Sources: S4 (cancellations), S7–S8 (seasonality), S11–S13 (booking curves).
"""

from __future__ import annotations


class CancellationCurve:
    """Cancellation rates at market x day-of-week x days-before-airdate [S4].

    Built from 6 months' rolling data (P40+ aired spots, 15/30/60s, BR5
    revenue types, market-specified break types) [S4, S38]. The estimator
    that produces the rates is UNKNOWN (U3); this class only represents and
    looks up an already-computed curve, as the deck does.

    The S4 sample table is tabulated at 30-day steps, but the S15 worked
    example uses a rate at 14 days left, so production curves are stored at
    finer days-left granularity. When an exact days-left point is absent,
    lookup optionally interpolates linearly between the nearest tabulated
    points (ASSUMPTION: interpolation behavior is UNKNOWN, U3).
    """

    def __init__(self, rates: dict[str, dict[int, float]]):
        # rates[day_of_week][days_left] = cancellation rate (0..1)
        self._rates = {
            dow: dict(sorted(by_dl.items())) for dow, by_dl in rates.items()
        }

    def rate(self, day_of_week: str, days_left: int, interpolate: bool = False) -> float:
        by_dl = self._rates[day_of_week]
        if days_left in by_dl:
            return by_dl[days_left]
        if not interpolate:
            raise KeyError(
                f"No tabulated rate for {day_of_week} at {days_left} days left; "
                "production granularity is finer than the S4 sample (U3)."
            )
        points = list(by_dl.items())
        lo = max((p for p in points if p[0] < days_left), default=None)
        hi = min((p for p in points if p[0] > days_left), default=None)
        if lo is None:
            return hi[1]
        if hi is None:
            return lo[1]
        span = hi[0] - lo[0]
        w = (days_left - lo[0]) / span
        return lo[1] + w * (hi[1] - lo[1])


# The S4 example table, verbatim (one market; percentages as fractions).
S4_EXAMPLE_CANCELLATION_TABLE = CancellationCurve(
    {
        "Monday": {30: 0.07, 60: 0.14, 90: 0.17, 120: 0.20, 150: 0.24, 180: 0.29},
        "Tuesday": {30: 0.06, 60: 0.12, 90: 0.17, 120: 0.20, 150: 0.25, 180: 0.30},
        "Wednesday": {30: 0.06, 60: 0.11, 90: 0.14, 120: 0.17, 150: 0.23, 180: 0.28},
        "Thursday": {30: 0.06, 60: 0.12, 90: 0.16, 120: 0.18, 150: 0.23, 180: 0.29},
        "Friday": {30: 0.06, 60: 0.11, 90: 0.15, 120: 0.17, 150: 0.22, 180: 0.27},
        "Saturday": {30: 0.07, 60: 0.12, 90: 0.15, 120: 0.17, 150: 0.20, 180: 0.24},
        "Sunday": {30: 0.07, 60: 0.11, 90: 0.15, 120: 0.17, 150: 0.19, 180: 0.22},
    }
)


def booking_curve(minutes_booked_by_days_left: dict[int, float]) -> dict[int, float]:
    """Booking fraction by days-before-airdate [S11, S12].

    Input: minutes booked exactly d days before air (pooled across all
    airdates of one station x month x day-of-week group, 2 years rolling).
    Output: booking_fraction[d] = cumulative minutes booked through d days
    left / total minutes at day 0. Larger d = earlier in time, so the
    cumulative sum runs from the largest d down to each d.
    """
    days = sorted(minutes_booked_by_days_left, reverse=True)
    total = sum(minutes_booked_by_days_left.values())
    if total == 0:
        raise ValueError("no bookings in group")
    out: dict[int, float] = {}
    cum = 0.0
    for d in days:
        cum += minutes_booked_by_days_left[d]
        out[d] = cum / total
    return out


def pct_business_left(booking_fraction: float) -> float:
    """1 - booking fraction = % of business left to be booked [S13]."""
    return 1.0 - booking_fraction


def seasonality_factor(minutes_sold: float, average_minutes_sold: float) -> float:
    """Seasonality factor at station x week-of-year x day-of-week [S7, S8].

    Implied by the S8 example: 140 sold vs 175 average Wednesday -> 80%.
    How observations from up to 3 years are averaged into `average_minutes_sold`
    is UNKNOWN (U4).
    """
    return minutes_sold / average_minutes_sold
