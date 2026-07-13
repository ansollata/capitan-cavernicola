"""Market response models: elasticity [S19] and rate differentials [S20, S21].

Production note: MRM had not been re-run since November 2010 as of the deck
date; a March 2012 refresh was rolled back [S37].
"""

from __future__ import annotations

from collections.abc import Sequence


def elasticity_symbol(e: float) -> str:
    """UI banding of elasticity [S19].

    $   (0 to -1.2)  = inelastic
    $$  (-1.2 to -1.6)
    $$$ (less than -1.6) = elastic

    The deck assigns -1.2 and -1.6 to overlapping ranges (D9); this
    implementation gives the boundary to the stronger band:
    $ for e > -1.2, $$ for -1.6 < e <= -1.2, $$$ for e <= -1.6.
    """
    if e > 0:
        raise ValueError("elasticity is non-positive in BR5's convention")
    if e > -1.2:
        return "$"
    if e > -1.6:
        return "$$"
    return "$$$"


def aur(spot_rates: Sequence[float]) -> float:
    """Average unit rate: average rate per spot of one length [S20].

    ASSUMPTION (U7): simple mean; the deck does not state the weighting.
    """
    if not spot_rates:
        raise ValueError("no spots")
    return sum(spot_rates) / len(spot_rates)


def amr(aur_value: float, spot_length_seconds: int) -> float:
    """Average minute rate = AUR x 60/length [S20].

    Verified against S20: :60 $232->$232, :30 $132->$264, :15 $74->$296.
    """
    return aur_value * (60.0 / spot_length_seconds)


def rate_differential(amr_length: float, amr_all_lengths: float) -> float:
    """Length AMR / all-lengths AMR [S20] — the multiplier shown on the
    reference price override screen and in the rate grid's Rate Differential
    column [S24, S33]. How the all-lengths AMR is aggregated is UNKNOWN (U7).
    """
    return amr_length / amr_all_lengths


def relative_to_60(aur_length: float, aur_60: float) -> float:
    """Length AUR / :60 AUR [S20] — shown on the rate differential screen
    (Preferences -> Rate Differentials) [S21]."""
    return aur_length / aur_60
