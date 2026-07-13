"""Acceptance tests: every numeric worked example in the training deck.

Each test cites its slide. Where the deck's own displayed numbers are
internally inconsistent (catalogued as D2/D3/D8 in docs/04-source-inventory.md),
the test asserts the arithmetic and documents the deck's displayed value in a
comment instead of forcing a match.
"""

import unittest

from bestrate.curves import (
    S4_EXAMPLE_CANCELLATION_TABLE,
    booking_curve,
    pct_business_left,
    seasonality_factor,
)
from bestrate.demand import deseasonalize, exponentially_weighted_mean
from bestrate.forecast import (
    inventory_forecast,
    max_forecast_sellout,
    remaining_demand,
    round_half_up,
)
from bestrate.mrm import amr, elasticity_symbol, rate_differential, relative_to_60
from bestrate.overrides import (
    rate_override_decay,
    reference_price_override,
)
from bestrate.pricing import apply_max_rate, system_rate
from bestrate.reference_price import (
    S18_EXAMPLE_REFERENCE_PRICES,
    IN_WEEK,
    FIFTEEN_PLUS,
    trim_rates,
    weeks_left_bucket,
)


class TestS4Cancellations(unittest.TestCase):
    def test_table_lookup(self):
        t = S4_EXAMPLE_CANCELLATION_TABLE
        self.assertEqual(t.rate("Monday", 30), 0.07)
        self.assertEqual(t.rate("Tuesday", 180), 0.30)
        self.assertEqual(t.rate("Sunday", 150), 0.19)
        self.assertEqual(t.rate("Wednesday", 90), 0.14)

    def test_finer_granularity_requires_interpolation_or_denser_curve(self):
        # S15 uses 3% at 14 days left — below the S4 table's 30-day floor.
        with self.assertRaises(KeyError):
            S4_EXAMPLE_CANCELLATION_TABLE.rate("Saturday", 14)


class TestS8S9Seasonality(unittest.TestCase):
    # S8: 2011 Wednesdays, average 175 minutes.
    S8_ROWS = [  # (week, minutes sold, deck-displayed factor %)
        (1, 140, 80), (2, 134, 76), (3, 134, 76), (4, 139, 79), (5, 148, 85),
        (6, 159, 91), (7, 168, 96), (8, 174, 99), (9, 175, 100), (10, 172, 98),
    ]

    def test_seasonality_factors(self):
        for _, sold, displayed_pct in self.S8_ROWS:
            factor = seasonality_factor(sold, 175)
            # The deck's display rounding is inconsistent (D3): week 2 shows
            # 76% for 76.57 while week 5 shows 85% for 84.57. Assert the
            # exact ratio is within 1 point of the displayed value.
            self.assertAlmostEqual(factor * 100, displayed_pct, delta=1.0)
        self.assertEqual(seasonality_factor(140, 175), 0.80)   # week 1 exactly
        self.assertEqual(seasonality_factor(175, 175), 1.00)   # week 9 exactly

    def test_deseasonalized_demand(self):
        # S9: Wednesday AMD, deseasonalized = sold / factor.
        # Rows 3-8 reproduce from the displayed factors with half-up rounding.
        rows = [  # (sold, displayed factor, deck deseasonalized)
            (53, 0.76, 70), (52, 0.79, 66), (49, 0.85, 58),
            (48, 0.91, 53), (48, 0.96, 50), (44, 0.99, 44),
        ]
        for sold, factor, expected in rows:
            self.assertEqual(round_half_up(deseasonalize(sold, factor)), expected)
        # Deck inconsistencies (D2): row 1 shows 61 but 48/0.80 = 60; row 2
        # shows 65 but 49/0.76 = 64.47 -> 64. The S9 factor column reuses
        # S8's rounded whole-day factors while the deseasonalized column was
        # evidently computed from unrounded daypart-level factors.
        self.assertEqual(round_half_up(deseasonalize(48, 0.80)), 60)  # deck: 61
        self.assertEqual(round_half_up(deseasonalize(49, 0.76)), 64)  # deck: 65

    def test_recency_weighting_biases_recent(self):
        # S9: "recent weeks given more weight"; T10: exponential smoothing.
        vals = [61, 65, 70, 66, 58, 53, 50, 44]  # oldest -> newest
        ewm = exponentially_weighted_mean(vals, alpha=0.3)
        simple = sum(vals) / len(vals)
        self.assertLess(ewm, simple)  # recent values are lower here


class TestS12BookingCurve(unittest.TestCase):
    # S12: Wednesdays in February. All three columns as printed in the deck
    # ("—" at days-left 11 read as 0).
    BOOKED = {14: 78, 13: 78, 12: 73, 11: 0, 10: 2, 9: 80, 8: 138, 7: 106,
              6: 244, 5: 118, 4: 2, 3: 3, 2: 29, 1: 76, 0: 0}
    DECK_CUMULATIVE = {14: 78, 13: 156, 12: 229, 11: 229, 10: 230, 9: 310,
                       8: 448, 7: 554, 6: 798, 5: 916, 4: 918, 3: 921,
                       2: 949, 1: 1025, 0: 1026}
    DECK_FRACTION_PCT = {14: 8, 13: 15, 12: 22, 11: 22, 10: 22, 9: 30, 8: 44,
                         7: 54, 6: 78, 5: 89, 4: 89, 3: 90, 2: 93, 1: 100, 0: 100}

    def test_fractions_from_printed_increments(self):
        # The printed Minutes Booked column sums to 1,027 and reproduces the
        # printed Booking Fraction column EXACTLY (all 15 rows, half-up
        # rounding) — including the 93% at 2 days left (951/1027 = 92.60%).
        curve = booking_curve(self.BOOKED)
        self.assertEqual(sum(self.BOOKED.values()), 1027)
        for dl, pct in self.DECK_FRACTION_PCT.items():
            self.assertEqual(round_half_up(curve[dl] * 100), pct)

    def test_deck_cumulative_column_has_typos(self):
        # D8: the printed Cumulative Bookings column's row-to-row steps
        # disagree with the printed Minutes Booked increments at exactly
        # three rows: days-left 10 (step 230-229=1 vs booked 2), 2 (step
        # 949-921=28 vs booked 29) and 0 (step 1026-1025=1 vs booked 0).
        # The fraction column proves the increments are the real data and
        # the cumulative column carries the typos.
        days = sorted(self.BOOKED, reverse=True)
        mismatches = []
        prev_cum = 0
        for dl in days:
            step = self.DECK_CUMULATIVE[dl] - prev_cum
            if step != self.BOOKED[dl]:
                mismatches.append(dl)
            prev_cum = self.DECK_CUMULATIVE[dl]
        self.assertEqual(mismatches, [10, 2, 0])

    def test_pct_business_left(self):
        # S13: 1 - booking fraction.
        self.assertAlmostEqual(pct_business_left(0.90), 0.10)


class TestS15ForecastExample(unittest.TestCase):
    def test_full_example(self):
        # 38 min OTB for Sat 4/13/13 AMD as of 3/30/13 (14 days out).
        otb = 38
        cancel_rate = 0.03            # 3% when 14 days left for Sat
        deseason = 50                 # minutes for Sat AMD
        season = 0.82                 # week 15 / Sat
        booking_fraction = 0.90       # 90% OTB at 14 days for April Sat

        rem = remaining_demand(deseason, season, booking_fraction)
        self.assertAlmostEqual(rem, 4.1, places=9)          # deck: "4 minutes"
        self.assertEqual(round_half_up(rem), 4)

        cancellations = otb * cancel_rate
        self.assertAlmostEqual(cancellations, 1.14, places=9)  # deck: "1 minute"
        self.assertEqual(round_half_up(cancellations), 1)

        # Deck arithmetic uses the whole-minute display values: 38 - 1 + 4 = 41.
        self.assertEqual(otb - round_half_up(cancellations) + round_half_up(rem), 41)
        # Unrounded: 38 - 1.14 + 4.1 = 40.96; rounding stage is UNKNOWN (U14).
        self.assertAlmostEqual(
            inventory_forecast(otb, cancel_rate, rem), 40.96, places=9
        )


class TestS16ForecastCaps(unittest.TestCase):
    def test_bands(self):
        self.assertEqual(max_forecast_sellout(0.00), 1.00)
        self.assertEqual(max_forecast_sellout(0.05), 1.00)
        self.assertEqual(max_forecast_sellout(0.10), 1.05)
        self.assertEqual(max_forecast_sellout(0.15), 1.05)
        self.assertEqual(max_forecast_sellout(0.25), 1.10)
        self.assertEqual(max_forecast_sellout(0.35), 1.15)
        self.assertEqual(max_forecast_sellout(0.40), 2.00)
        self.assertEqual(max_forecast_sellout(0.95), 2.00)


class TestS17S18ReferencePrices(unittest.TestCase):
    def test_sixteen_buckets(self):
        self.assertEqual(len(S18_EXAMPLE_REFERENCE_PRICES), 16)  # S17
        self.assertEqual(weeks_left_bucket(0), IN_WEEK)
        self.assertEqual(weeks_left_bucket(1), 1)
        self.assertEqual(weeks_left_bucket(14), 14)
        self.assertEqual(weeks_left_bucket(15), FIFTEEN_PLUS)
        self.assertEqual(weeks_left_bucket(40), FIFTEEN_PLUS)

    def test_prices_rise_toward_airdate(self):
        # S18: $228 at 15+ weeks -> $289 in-week, monotonically non-decreasing.
        order = [FIFTEEN_PLUS, *range(14, 0, -1), IN_WEEK]
        prices = [S18_EXAMPLE_REFERENCE_PRICES[b] for b in order]
        self.assertEqual(prices[0], 228)
        self.assertEqual(prices[-1], 289)
        self.assertEqual(prices, sorted(prices))

    def test_trim_10_10(self):
        # S17: exclude top 10% and bottom 10% of rates.
        rates = list(range(1, 21))  # 20 observations
        trimmed = trim_rates(rates)
        self.assertEqual(trimmed, list(range(3, 19)))  # 2 dropped each end


class TestS19Elasticity(unittest.TestCase):
    def test_symbols(self):
        self.assertEqual(elasticity_symbol(-0.9), "$")     # S33's stations
        self.assertEqual(elasticity_symbol(-1.3), "$$")
        self.assertEqual(elasticity_symbol(-1.7), "$$$")
        # Boundary handling per D9 (deck ambiguous): stronger band wins.
        self.assertEqual(elasticity_symbol(-1.2), "$$")
        self.assertEqual(elasticity_symbol(-1.6), "$$$")


class TestS20RateDifferentials(unittest.TestCase):
    def test_amr_from_aur(self):
        self.assertEqual(amr(232, 60), 232)
        self.assertEqual(amr(132, 30), 264)
        self.assertEqual(amr(74, 15), 296)

    def test_differentials_vs_all_lengths_amr(self):
        # All-lengths AMR = $245 [S20]; percentages as displayed.
        self.assertEqual(round_half_up(rate_differential(232, 245) * 100), 95)
        self.assertEqual(round_half_up(rate_differential(264, 245) * 100), 108)
        self.assertEqual(round_half_up(rate_differential(296, 245) * 100), 121)

    def test_relative_to_60(self):
        self.assertEqual(round_half_up(relative_to_60(132, 232) * 100), 57)
        self.assertEqual(round_half_up(relative_to_60(74, 232) * 100), 32)


class TestS24MaxRateExample(unittest.TestCase):
    def test_worked_example(self):
        # Forecasted sellout 22.25/21 = 106%; current sellout 21/21 = 100%.
        sr = system_rate(530, 0.949295)
        self.assertEqual(round_half_up(sr), 503)  # deck: "$503"

        result = apply_max_rate(
            sr,
            forecast_sellout=22.25 / 21,
            current_sellout=21 / 21,
            max_rate_otb=300,
            # avg rate OTB is not shown on S24; any value with
            # avg*1.3*1.3 < 390 leaves the max-OTB branch binding.
            avg_rate_otb=200,
            tolerance=0.30,
        )
        self.assertTrue(result.triggered)
        self.assertEqual(result.target_rate, 390.0)  # deck: $300 x 1.3 = $390
        self.assertEqual(result.opt_status, "System Rate Greater Than Maximum Rate.")


class TestS33SimultaneousOverridesGrid(unittest.TestCase):
    # (final_ref, system_price, rate_diff, deck_target, max_rate_otb)
    UNCAPPED_ROWS = [
        (1332.91, 1410.34, 0.842811, 1188.65, 1400),
        (1349.41, 1427.79, 0.846303, 1208.35, 1400),
        (1392.00, 1527.94, 0.849079, 1297.34, 1950),
    ]

    def test_target_rate_is_system_price_times_differential(self):
        for _, sys_price, diff, deck_target, _ in self.UNCAPPED_ROWS:
            # Within 2 cents (the grid displays already-rounded inputs).
            self.assertAlmostEqual(system_rate(sys_price, diff), deck_target, delta=0.02)

    def test_uncapped_rows_do_not_trigger(self):
        # 9/16: forecast 43/45 = 95.6% <= 100% -> no cap.
        r = apply_max_rate(
            system_rate(1410.34, 0.842811),
            forecast_sellout=43 / 45,
            current_sellout=41.25 / 45,
            max_rate_otb=1400,
            avg_rate_otb=1239.2862,
            tolerance=0.25,
        )
        self.assertFalse(r.triggered)

    def test_capped_row_9_19(self):
        # Forecast 49.25/45 = 109.4% > 100%; current 46.5/45 = 103.3% > 95%.
        # Deck target 2437.5 = 1950 x 1.25 exactly => tolerance 25% (derived,
        # consistent with the S25 screenshot showing 25%).
        sr = system_rate(3155, 0.838511)  # 2645.50 uncapped
        r = apply_max_rate(
            sr,
            forecast_sellout=49.25 / 45,
            current_sellout=46.5 / 45,
            max_rate_otb=1950,
            avg_rate_otb=1239.2862,  # derived from the 9/20 row (see below)
            tolerance=0.25,
        )
        self.assertTrue(r.triggered)
        self.assertAlmostEqual(r.target_rate, 2437.5, places=4)

    def test_capped_row_9_20(self):
        # Forecast 48.5/45 = 107.8% > 100%; current 45.5/45 = 101.1% > 95%.
        # Deck target 2013.84 > max_rate_otb branch (1400 x 1.25 = 1750), so
        # the avg-OTB branch bound: avg x 1.3 x 1.25 = 2013.84
        # => avg rate OTB = 1239.286 (derived; not shown on the slide).
        sr = system_rate(3200.36, 0.833514)  # 2667.56 uncapped
        r = apply_max_rate(
            sr,
            forecast_sellout=48.5 / 45,
            current_sellout=45.5 / 45,
            max_rate_otb=1400,
            avg_rate_otb=1239.2862,
            tolerance=0.25,
        )
        self.assertTrue(r.triggered)
        self.assertAlmostEqual(r.target_rate, 2013.84, delta=0.01)


class TestS29RateDecay(unittest.TestCase):
    def test_decay_schedule(self):
        ovr, sys = 200.0, 100.0
        self.assertAlmostEqual(
            rate_override_decay(ovr, sys, 1), (1 / 56) * sys + (55 / 56) * ovr
        )
        self.assertAlmostEqual(
            rate_override_decay(ovr, sys, 2), (2 / 56) * sys + (54 / 56) * ovr
        )
        self.assertAlmostEqual(rate_override_decay(ovr, sys, 28), 150.0)  # halfway
        self.assertEqual(rate_override_decay(ovr, sys, 56), sys)  # fully decayed
        self.assertEqual(rate_override_decay(ovr, sys, 90), sys)  # stays decayed


class TestS31ReferencePriceOverride(unittest.TestCase):
    def test_floating_dollar_adds(self):
        # The S31 warning: floating + $ ADDS to the reference price.
        self.assertEqual(
            reference_price_override(250, application_type="floating", amount=50), 300
        )

    def test_fixed_dollar_replaces(self):
        # S24: adjusted 293.9902 -> final 300.00 under "Reference Override".
        self.assertEqual(
            reference_price_override(293.9902, application_type="fixed", amount=300.0),
            300.0,
        )

    def test_percent_mode_is_undocumented(self):
        with self.assertRaises(NotImplementedError):
            reference_price_override(250, application_type="floating", percent=0.10)


if __name__ == "__main__":
    unittest.main()
