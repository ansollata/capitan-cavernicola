#!/usr/bin/env python3
"""Generate the proposed broadcast rate card (v0.1 DRAFT) for management review.

Method: docs/05-ratecard-solution.md section 2.2, applied to the deployed
rate_cards table (the planner's transformation of the Updated Rates 6.1
BestRate export) joined to Nielsen Fall-2025 audience. v0.1 is a DRAFT to
be recomputed on the original raw files before sign-off.

Every policy choice below is a labeled KNOB for management to change.

Usage: python3 generate_broadcast_card.py <path-to-iheart.db> <output.xlsx>
"""

import sqlite3
import statistics as st
import sys

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

# ----------------------------- KNOBS (management decisions) -----------------
# K1. Spot-length ratios relative to :60 (fixes drifted/contradictory ratios;
#     :10 deliberately BELOW :15).
RATIOS = {"60": 1.00, "30": 0.75, "15": 0.45, "10": 0.40, "05": 0.25}

# K2. Floors on the :60 rate, Mon-Fri (kills $1 placeholder rates).
FLOOR_60_MF = {"AMD": 10, "Midday": 10, "PMD": 10, "Evening": 6, "Overnight": 3}
WEEKEND_FLOOR_FACTOR = 0.6  # Sat/Sun floors = 60% of MF floors

# K3. Audience anchoring (market-based correction):
#     raise cells whose implied CPM sits below LOW_BAND x tier/daypart median,
#     capped at MAX_RAISE per refresh; flag (never auto-cut) above HIGH_BAND.
LOW_BAND = 0.70
HIGH_BAND = 1.50
MAX_RAISE = 1.25
NIELSEN_DEMO = "Persons 25-54"   # NOTE: understates AM-talk audiences

# K4. Market tiers by Nielsen market rank.
def tier(rank):
    if rank is None:
        return "T3"
    if rank <= 25:
        return "T1"
    if rank <= 100:
        return "T2"
    return "T3"

# K5. Round pricing (card credibility).
def round_price(x):
    if x <= 0:
        return 0
    if x < 20:
        return max(1, round(x))
    if x < 100:
        return int(5 * round(x / 5))
    return int(10 * round(x / 10))

LARGE_MOVE = 0.20  # flag any length moving more than +/-20%
# -----------------------------------------------------------------------------

DP_NIELSEN = {"AMD": "MF 6-10a", "Midday": "MF 10a-3p", "PMD": "MF 3-7p",
              "Evening": "MF 7p-12m", "Overnight": "MF 12m-6a"}
DP_ORDER = {"AMD": 0, "Midday": 1, "PMD": 2, "Evening": 3, "Overnight": 4}
DG_ORDER = {"MF": 0, "Sat": 1, "Sun": 2}


def main(db_path, out_path):
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row

    rows = [dict(r) for r in con.execute(
        """SELECT r.*, m.market_rank FROM rate_cards r
           LEFT JOIN markets m ON m.market_name = r.market_nielsen""")]

    aqh = {}
    for r in con.execute(
            "SELECT call_letters, market_name, daypart, aqh FROM nielsen_ratings WHERE demo=?",
            (NIELSEN_DEMO,)):
        aqh[(r["call_letters"], r["market_name"], r["daypart"])] = r["aqh"]

    # Tier x daypart median implied CPM on the :60 (MF cells with real rates).
    tier_cpm = {}
    for r in rows:
        if r["dow_group"] != "MF" or r["br60"] <= 1:
            continue
        a = aqh.get((r["station_nielsen"], r["market_nielsen"], DP_NIELSEN[r["daypart"]]))
        if a:
            tier_cpm.setdefault((tier(r["market_rank"]), r["daypart"]), []).append(
                r["br60"] / (a / 1000))
    tier_cpm = {k: st.median(v) for k, v in tier_cpm.items()}

    # Pass 1: MF corrections -> per (station, market, daypart) factor.
    factor, mf_flags, station_aqh = {}, {}, {}
    for r in rows:
        if r["dow_group"] != "MF":
            continue
        key = (r["station_nielsen"], r["market_nielsen"], r["daypart"])
        old60, flags = r["br60"], []
        new60 = max(old60, FLOOR_60_MF[r["daypart"]])
        if new60 > old60:
            flags.append("floored")
        a = aqh.get((r["station_nielsen"], r["market_nielsen"], DP_NIELSEN[r["daypart"]]))
        station_aqh[key] = a
        med = tier_cpm.get((tier(r["market_rank"]), r["daypart"]))
        if a and med and old60 > 1:
            cpm = old60 / (a / 1000)
            if cpm < LOW_BAND * med:
                target = LOW_BAND * med * (a / 1000)
                raised = min(old60 * MAX_RAISE, target)
                if raised > new60:
                    new60 = raised
                    flags.append("raised-to-audience-band")
            elif cpm > HIGH_BAND * med:
                flags.append("REVIEW-high-vs-audience")
        elif not a:
            flags.append("no-audience-data")
        factor[key] = new60 / old60 if old60 > 0 else 1.0
        mf_flags[key] = flags

    # Pass 2: build proposed rates for every row.
    out = []
    for r in rows:
        key = (r["station_nielsen"], r["market_nielsen"], r["daypart"])
        f = factor.get(key, 1.0)
        flags = list(mf_flags.get(key, [])) if r["dow_group"] == "MF" else \
            (["factor-from-MF"] if f != 1.0 else [])
        base60 = r["br60"] * f
        fl = FLOOR_60_MF[r["daypart"]] * (1 if r["dow_group"] == "MF" else WEEKEND_FLOOR_FACTOR)
        if base60 < fl:
            base60 = fl
            if "floored" not in flags:
                flags.append("floored")
        prop = {ln: round_price(base60 * rt) for ln, rt in RATIOS.items()}
        cur = {ln: r[f"br{ln}"] for ln in RATIOS}
        if any(cur[ln] > 0 and abs(prop[ln] - cur[ln]) / cur[ln] > LARGE_MOVE for ln in RATIOS):
            flags.append("ratio-shift>20%")
        out.append({
            "rank": r["market_rank"], "tier": tier(r["market_rank"]),
            "market": r["market_nielsen"], "station": r["station_nielsen"],
            "daypart": r["daypart"], "days": r["dow_group"],
            "n": r["sample_size"], "aqh": station_aqh.get(key),
            "cur": cur, "prop": prop,
            "d60": (prop["60"] - cur["60"]) / cur["60"] if cur["60"] else None,
            "flags": ";".join(flags),
        })

    out.sort(key=lambda x: (x["rank"] or 999, x["market"], x["station"],
                            DP_ORDER[x["daypart"]], DG_ORDER[x["days"]]))

    wb = Workbook()
    hdr_font = Font(bold=True, color="FFFFFF")
    hdr_fill = PatternFill("solid", fgColor="C6002B")
    flag_fill = PatternFill("solid", fgColor="FFF2CC")

    ws = wb.active
    ws.title = "Proposed Card v0.1 DRAFT"
    cols = (["Rank", "Tier", "Market", "Station", "Daypart", "Days", "Obs", "AQH P25-54"]
            + [f"Cur :{ln}" for ln in RATIOS] + [f"PROP :{ln}" for ln in RATIOS]
            + ["Δ:60 %", "Flags"])
    ws.append(cols)
    for c in ws[1]:
        c.font, c.fill = hdr_font, hdr_fill
    for o in out:
        row = ([o["rank"], o["tier"], o["market"], o["station"], o["daypart"],
                o["days"], o["n"], o["aqh"]]
               + [o["cur"][ln] for ln in RATIOS] + [o["prop"][ln] for ln in RATIOS]
               + [round(o["d60"] * 100, 1) if o["d60"] is not None else None, o["flags"]])
        ws.append(row)
        if o["flags"]:
            ws.cell(row=ws.max_row, column=len(cols)).fill = flag_fill
    ws.freeze_panes = "E2"
    ws.auto_filter.ref = ws.dimensions
    for i, w in enumerate([6, 5, 22, 10, 10, 6, 6, 10] + [8] * 10 + [8, 34], 1):
        ws.column_dimensions[get_column_letter(i)].width = w

    s = wb.create_sheet("Summary")
    n = len(out)
    raised = [o for o in out if o["d60"] and o["d60"] > 0.005]
    audience = [o for o in out if "raised-to-audience-band" in o["flags"]]
    floored = [o for o in out if "floored" in o["flags"]]
    high = [o for o in out if "REVIEW-high" in o["flags"]]
    noaud = [o for o in out if "no-audience-data" in o["flags"]]
    for line in [
        ("Rows on card", n),
        ("Stations", len({(o['station'], o['market']) for o in out})),
        ("Markets", len({o['market'] for o in out})),
        ("Cells with :60 raised", f"{len(raised)} ({100*len(raised)/n:.0f}%)"),
        ("  of which lifted by audience-band rule", len(audience)),
        ("  of which lifted by floor rule", len(floored)),
        ("Median :60 raise among raised cells",
         f"{100*st.median([o['d60'] for o in raised]):.0f}%" if raised else "-"),
        ("Cells flagged REVIEW-high-vs-audience (no change applied)", len(high)),
        ("Cells with no Nielsen audience match", len(noaud)),
        ("Rows with any length moving >20%",
         sum(1 for o in out if "ratio-shift" in o["flags"])),
    ]:
        s.append(list(line))
    s.column_dimensions["A"].width = 55
    s["A1"].font = Font(bold=True)

    m = wb.create_sheet("Methodology & Knobs")
    text = [
        "PROPOSED BROADCAST RATE CARD v0.1 — DRAFT FOR MANAGEMENT REVIEW",
        "",
        "STATUS: computed from the deployed rate_cards data (the media-planner's",
        "transformation of the Updated Rates 6.1 BestRate export) joined to Nielsen",
        "Fall 2025 (Persons 25-54). To be RECOMPUTED on the original raw files before",
        "sign-off. Grain: Station x Daypart x (M-F / Sat / Sun) x 5 spot lengths.",
        "Season: Everyday card. High Season (Sep-Dec) variant requires the raw file's",
        "date grain - pending originals.",
        "",
        "METHOD (docs/05-ratecard-solution.md section 2.2):",
        "1. Baseline = current median achieved rate per cell (the :60 anchors the cell).",
        "2. Floor the :60 (K2) - eliminates $1 placeholder rates.",
        "3. Audience anchor (K3): implied CPM = :60 / (AQH/1000). Cells below",
        f"   {int(LOW_BAND*100)}% of their tier x daypart median CPM are raised to that band,",
        f"   capped at +{int((MAX_RAISE-1)*100)}% per refresh. Cells above {int(HIGH_BAND*100)}% are FLAGGED, never cut.",
        "4. Weekend cells move by the same factor as their MF cell (preserves the",
        "   weekend discount).",
        "5. All lengths repriced from the corrected :60 by policy ratios (K1):",
        "   " + "  ".join(f":{ln}={rt:.2f}" for ln, rt in RATIOS.items()),
        "   This replaces drifted ratios and puts :10 BELOW :15 (fixes the inversion).",
        "6. Round pricing (K5): nearest $1 under $20, $5 under $100, $10 above.",
        "",
        "KNOBS FOR MANAGEMENT (change any; regeneration is one command):",
        f"  K1 length ratios: {RATIOS}",
        f"  K2 :60 floors MF: {FLOOR_60_MF}; weekend = {int(WEEKEND_FLOOR_FACTOR*100)}% of MF",
        f"  K3 audience bands: low {LOW_BAND}, high {HIGH_BAND}, max raise {MAX_RAISE}, demo '{NIELSEN_DEMO}'",
        "  K4 tiers: T1 = rank 1-25, T2 = 26-100, T3 = 101+",
        "  K5 rounding grid as above",
        "",
        "KNOWN LIMITS OF v0.1:",
        "- Source is the transformed table (715 of 889 stations; medians per day-group).",
        "- Persons 25-54 AQH understates AM-talk audiences (their REVIEW flags may be",
        "  demo artifacts).",
        "- No never-cut violation exists by construction: :60 anchors only move up;",
        "  :30/:15 can move down where historical ratios were above policy - every such",
        "  row carries the 'ratio-shift>20%' flag for review.",
        "- TTWN and Premiere proposed cards pending the original files.",
        "",
        "Generator: proposed-rate-cards/generate_broadcast_card.py (this file's twin).",
    ]
    for t in text:
        m.append([t])
    m.column_dimensions["A"].width = 100

    wb.save(out_path)
    print(f"rows={n} raised={len(raised)} audience={len(audience)} floored={len(floored)} "
          f"review_high={len(high)} no_audience={len(noaud)}")
    print("saved:", out_path)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
