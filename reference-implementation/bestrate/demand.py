"""Deseasonalized demand [S9, S10, T10].

Deseasonalized demand = minutes sold / seasonality factor, per observation;
26 weeks of observations per (station, day-of-week, daypart) are averaged
into one number "with recent weeks given more weight" [S9]. The transcript
identifies the weighting as exponential smoothing [T10]; the smoothing
constant is UNKNOWN (U1) and therefore a parameter here.
"""

from __future__ import annotations

from collections.abc import Sequence


def deseasonalize(minutes_sold: float, seasonality_factor: float) -> float:
    """Deseasonalized demand = demand (minutes sold) / seasonality factor [S9]."""
    return minutes_sold / seasonality_factor


def exponentially_weighted_mean(values: Sequence[float], alpha: float) -> float:
    """Recency-weighted average of observations, oldest first.

    Weight of the observation with age k (0 = most recent) is
    alpha * (1 - alpha)**k, renormalized over the window.

    ASSUMPTION (U1): the sources say only "recent weeks given more weight"
    [S9] / "exponential smoothing ... bias recency much more than all
    historical" [T10]. The functional form and alpha are not specified;
    alpha is exposed so a bit-faithful clone can drop in the value found in
    the BR5 scripts.
    """
    if not values:
        raise ValueError("no observations")
    if not 0.0 < alpha <= 1.0:
        raise ValueError("alpha must be in (0, 1]")
    n = len(values)
    # values[0] is oldest -> age n-1; values[-1] is newest -> age 0.
    weights = [alpha * (1.0 - alpha) ** (n - 1 - i) for i in range(n)]
    total_w = sum(weights)
    return sum(v * w for v, w in zip(values, weights)) / total_w
