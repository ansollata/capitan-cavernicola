"""Inventory forecast [S3, S14, S15] and forecast caps [S16]."""

from __future__ import annotations

import math


def round_half_up(x: float) -> int:
    """Round half away from zero, as the deck's displayed values require
    (e.g. S12: 78/1026 = 7.60% -> 8%). Python's built-in round() is
    banker's rounding and does not reproduce the deck."""
    return int(math.floor(x + 0.5))


def remaining_demand(
    deseasonalized_demand: float,
    seasonality_factor: float,
    booking_fraction: float,
) -> float:
    """Forecasted remaining demand [S5, S14].

    = deseasonalized demand x seasonality factor x (1 - booking fraction),
    the last term being "% of business left to be booked" [S13].
    """
    return deseasonalized_demand * seasonality_factor * (1.0 - booking_fraction)


def inventory_forecast(
    business_on_the_books: float,
    cancellation_rate: float,
    forecasted_remaining_demand: float,
) -> float:
    """Forecast = OTB - projected cancellations + remaining demand [S3, S14].

    Projected cancellations = OTB x cancellation rate, per the S15 example
    (38 min x 3% ~= 1 minute). OTB includes no-charge spots [T23].
    """
    projected_cancellations = business_on_the_books * cancellation_rate
    return business_on_the_books - projected_cancellations + forecasted_remaining_demand


# S16: actual sellout band -> maximum forecast sellout. Bands are printed as
# integer percent ranges ("0-9%", "10-19%", ...); treatment of fractional
# sellouts inside the gaps (e.g. 9.5%) is UNKNOWN — implemented here as
# half-open decimal bands [0,.10), [.10,.20), [.20,.30), [.30,.40), [.40,inf).
FORECAST_CAP_BANDS: list[tuple[float, float, float]] = [
    (0.00, 0.10, 1.00),
    (0.10, 0.20, 1.05),
    (0.20, 0.30, 1.10),
    (0.30, 0.40, 1.15),
    (0.40, math.inf, 2.00),
]


def max_forecast_sellout(actual_sellout: float) -> float:
    """Cap on forecast sellout as a function of actual sellout [S16].

    "Prevents projected sellouts and rates from being too high when large
    buys are made during early stages of the booking curve."
    """
    if actual_sellout < 0:
        raise ValueError("sellout cannot be negative")
    for lo, hi, cap in FORECAST_CAP_BANDS:
        if lo <= actual_sellout < hi:
            return cap
    raise AssertionError("unreachable")


def capped_forecast_sellout(
    forecast_minutes: float, sold_minutes: float, capacity_minutes: float
) -> float:
    """Forecast sellout = forecast / capacity [S24], capped per S16.

    Whether BR5 stores the cap on the sellout ratio or on forecast minutes is
    display-equivalent; UNKNOWN which representation is used internally.
    """
    actual = sold_minutes / capacity_minutes
    return min(forecast_minutes / capacity_minutes, max_forecast_sellout(actual))
