"""System price -> target rate, and the max rate cap [S22-S26, S24, S33].

The market-response function M(.) that turns the final reference price into
the System Price is UNKNOWN (U8) — the deck names its ingredients (demand
vs supply, elasticity) but never the formula. This module therefore:
  * accepts system_price as an input (or a caller-supplied response model),
  * implements everything documented downstream of it exactly, and
  * ships the observed calibration points a reconstruction must reproduce.
"""

from __future__ import annotations

from dataclasses import dataclass

# System Price / Final Reference Price observed in the deck, with the inputs
# visible on the same rows. S33 rows use elasticity -0.9; S24 uses -1.2.
# (forecast_sellout = Demand Forecast / Capacity; current = Current Sold / Capacity.)
OBSERVED_CALIBRATION_POINTS = [
    # (source, final_ref, system_price, multiplier, forecast_sellout, current_sellout, booking_fraction, elasticity)
    ("S33 9/16/13", 1332.91, 1410.34, 1.05809, 43 / 45, 41.25 / 45, 0.948574, -0.9),
    ("S33 9/17/13", 1349.41, 1427.79, 1.05809, 42 / 45, 40.25 / 45, 0.945395, -0.9),
    ("S33 9/18/13", 1392.00, 1527.94, 1.09766, 45.25 / 45, 42.25 / 45, 0.908463, -0.9),
    ("S33 9/19/13", 1519.91, 3155.00, 2.07578, 49.25 / 45, 46.5 / 45, 0.914680, -0.9),
    ("S33 9/20/13", 1539.27, 3200.36, 2.07914, 48.5 / 45, 45.5 / 45, 0.903518, -0.9),
    ("S24 4/5/11", 300.00, 530.00, 1.76667, 22.25 / 21, 21 / 21, 0.957975, -1.2),
]


def system_rate(system_price: float, rate_differential: float) -> float:
    """Length-specific system rate = System Price x Rate Differential.

    Verified to the penny on the three uncapped S33 rows (e.g. 1410.34 x
    0.842811 = 1188.65 = Target Rate) and stated on S24 ("System rate =
    $530 * 0.949295 = $503").
    """
    return system_price * rate_differential


@dataclass
class MaxRateResult:
    target_rate: float
    triggered: bool
    ceiling: float | None
    opt_status: str | None


def apply_max_rate(
    system_rate_value: float,
    *,
    forecast_sellout: float,
    current_sellout: float,
    max_rate_otb: float,
    avg_rate_otb: float,
    p90_rate_otb: float | None = None,
    tolerance: float,
) -> MaxRateResult:
    """The max rate cap [S22, S23].

    Max rate OTB = highest rate on the books [S22]. Max rate only LOWERS
    rates, never raises them [S22]. Tolerance is a station-wide preference
    [S25]. Two regimes, both requiring forecast sellout > 100% [S23]:

      current sellout > 95%:
          ceiling = max(max_rate_otb*(1+tol), avg_rate_otb*1.3*(1+tol))
      40% <= current sellout <= 95%:
          ceiling = max(p90_rate_otb*(1+tol), avg_rate_otb*1.3*(1+tol))

    target = min(system rate, ceiling).

    Undefined regions (as documented): current sellout < 40% with forecast
    sellout > 100% has no documented cap — returned uncapped here (see
    docs/03-optimization.md #4). Ownership of the exact 95%/40% boundaries
    is not stated; this implementation puts 95% in the 40-95% regime.
    The pool over which avg/p90 OTB rates are computed is UNKNOWN (U10) —
    they are inputs here.
    """
    if forecast_sellout <= 1.0:
        return MaxRateResult(system_rate_value, False, None, None)

    if current_sellout > 0.95:
        anchor = max_rate_otb
    elif 0.40 <= current_sellout <= 0.95:
        if p90_rate_otb is None:
            raise ValueError("regime B requires the 90th percentile rate OTB [S23]")
        anchor = p90_rate_otb
    else:
        # forecast > 100% but current sellout < 40%: no documented cap.
        return MaxRateResult(system_rate_value, False, None, None)

    ceiling = max(anchor * (1 + tolerance), avg_rate_otb * 1.3 * (1 + tolerance))
    if system_rate_value > ceiling:
        return MaxRateResult(
            ceiling, True, ceiling, "System Rate Greater Than Maximum Rate."
        )
    return MaxRateResult(system_rate_value, False, ceiling, None)
