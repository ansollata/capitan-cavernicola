"""Override semantics [S27-S33]."""

from __future__ import annotations


def reference_price_override(
    base_reference_price: float,
    *,
    application_type: str,  # "floating" | "fixed"
    amount: float | None = None,
    percent: float | None = None,
) -> float:
    """Reference price override [S31].

    Documented semantics:
      floating + $ amount  ->  ADDS the amount to the reference price
        (the deck's red-letter warning: "typing a $ amount ... and choosing
        floating instead of fixed will add that $ amount")
      fixed + $ amount     ->  replaces the reference price
        (S24: adjusted 293.9902 -> final 300.00 under "Reference Override")

    Percent mode exists in the UI ("Enter By Percent") but its math is
    UNKNOWN (U9); it is deliberately not implemented rather than guessed.
    """
    if (amount is None) == (percent is None):
        raise ValueError("provide exactly one of amount / percent")
    if percent is not None:
        raise NotImplementedError(
            "Percent-mode reference price override semantics are not "
            "documented in the source materials (unknowns register U9)."
        )
    if application_type == "floating":
        return base_reference_price + amount
    if application_type == "fixed":
        return amount
    raise ValueError("application_type must be 'floating' or 'fixed'")


def demand_level_override(
    base_demand_minutes: float,
    *,
    application_type: str,  # "floating" | "fixed"
    minutes: float | None = None,
    percent: float | None = None,
) -> float:
    """Demand level override [S32, S10].

    The form mirrors the reference price override (Floating/Fixed; amount in
    minutes or by percent). ASSUMPTION: floating/fixed behave as they do for
    reference prices (add vs replace) — the deck shows the identical form but
    states the add-vs-replace warning only for reference prices. Percent mode
    is UNKNOWN (U9) and not implemented.
    """
    if (minutes is None) == (percent is None):
        raise ValueError("provide exactly one of minutes / percent")
    if percent is not None:
        raise NotImplementedError(
            "Percent-mode demand override semantics are not documented (U9)."
        )
    if application_type == "floating":
        return base_demand_minutes + minutes
    if application_type == "fixed":
        return minutes
    raise ValueError("application_type must be 'floating' or 'fixed'")


def rate_override_decay(
    override_rate: float, system_rate: float, day_number: int
) -> float:
    """Rate override decay over 8 weeks (56 days) [S29].

    Day 1: 1/56 system + 55/56 override
    Day 2: 2/56 system + 54/56 override
    ...
    Day 56: 100% system, override no longer in effect.

    The system rate an override decays back to is the system price as
    adjusted by any reference price and demand overrides [S33]. "Reset Rate
    Decay" restarts day_number at 1 [S28, S29]. Day-0 behavior (the moment
    of entry) is not enumerated by the deck; the deck's sequence starts at
    day 1.
    """
    if day_number < 1:
        raise ValueError("the documented decay sequence starts at day 1")
    n = min(day_number, 56)
    return (n / 56.0) * system_rate + ((56 - n) / 56.0) * override_rate
