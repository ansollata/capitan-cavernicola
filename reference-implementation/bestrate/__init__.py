"""Reference implementation of BestRate (BR5) — the documented parts.

Every formula here is sourced from the training deck
(BR_Training__New_Format.20160509.pdf, cited as S<slide>) or the transcript
(cited as T<fact>, see docs/04-source-inventory.md). Anything the sources do
not specify is marked ASSUMPTION with a pointer to the unknowns register in
docs/02-replication-spec.md §7 (U1–U20) and is exposed as configuration
rather than hard-coded silently.

Stdlib only. Run the validation suite with:
    cd reference-implementation && python3 -m unittest discover -s tests -t . -v
"""

from .curves import (
    CancellationCurve,
    booking_curve,
    pct_business_left,
    seasonality_factor,
)
from .demand import deseasonalize, exponentially_weighted_mean
from .forecast import (
    inventory_forecast,
    max_forecast_sellout,
    remaining_demand,
    round_half_up,
)
from .mrm import amr, aur, elasticity_symbol, rate_differential, relative_to_60
from .pricing import (
    OBSERVED_CALIBRATION_POINTS,
    MaxRateResult,
    apply_max_rate,
    system_rate,
)
from .overrides import (
    demand_level_override,
    rate_override_decay,
    reference_price_override,
)
from .reference_price import trim_rates, weeks_left_bucket
from .schedule import JOB_CADENCE

__all__ = [
    "CancellationCurve",
    "booking_curve",
    "pct_business_left",
    "seasonality_factor",
    "deseasonalize",
    "exponentially_weighted_mean",
    "inventory_forecast",
    "max_forecast_sellout",
    "remaining_demand",
    "round_half_up",
    "amr",
    "aur",
    "elasticity_symbol",
    "rate_differential",
    "relative_to_60",
    "OBSERVED_CALIBRATION_POINTS",
    "MaxRateResult",
    "apply_max_rate",
    "system_rate",
    "demand_level_override",
    "rate_override_decay",
    "reference_price_override",
    "trim_rates",
    "weeks_left_bucket",
    "JOB_CADENCE",
]
