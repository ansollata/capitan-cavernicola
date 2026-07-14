#!/usr/bin/env python3
"""Generate the proposed TTWN rate card (v0.1 DRAFT) from the ORIGINAL
`TTWN base rates` file (Updated Rates 6.1 folder).

Method: docs/05-ratecard-solution.md sections 2.2-2.3 adapted to TTWN's
native grain: Market x Affiliate x Rating (R/NR/NC) x WeekDef (M-F /
Sat-Sun) x DayPart, single rate per cell (no spot lengths in this product).
Duplicate rows on that grain are collapsed by median. Rates are floored
(kills the 472 zero/$1 rows) and grid-rounded. No audience correction in
v0.1 (rating class R/NR already encodes measured vs unmeasured); instead,
outliers vs their Rating x DayPart x WeekDef peer median are FLAGGED for
human review, never changed.

Usage: python3 generate_ttwn_card.py <TTWN.xlsx> <output.xlsx>
"""

import statistics as st
import sys
from collections import defaultdict

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

# ----------------------------- KNOBS (management decisions) -----------------
# K1. Floors by Rating, M-F; weekend floor = WEEKEND_FLOOR_FACTOR x that.
FLOOR_MF = {"R": 5, "NR": 2, "NC": 2}
WEEKEND_FLOOR_FACTOR = 0.6

# K2. Review bands vs SAME-MARKET peers (Market x Rating x DayPart x WeekDef
#     median across affiliates; flags only, minimum peer count applies).
#     National pooling was rejected: it flags every big-market affiliate.
LOW_BAND = 0.30
HIGH_BAND = 3.00
MIN_PEERS = 4

# K3. Round pricing.
def round_price(x):
    if x <= 0:
        return 0
    if x < 20:
        return max(1, round(x))
    if x < 100:
        return int(5 * round(x / 5))
    return int(10 * round(x / 10))

# K4. Non-iHeart affiliates: KEPT on the card with an iHeart? flag
#     (Ana's 2026-06-03 decision). Splitting them off is a standing option.
# -----------------------------------------------------------------------------

DP_ORDER = {"AMD": 0, "Midday": 1, "PMD": 2, "Evening": 3, "Overnight": 4}
WD_ORDER = {"M-F": 0, "Sat-Sun": 1}


def main(src, out_path):
    ws = load_workbook(src, read_only=True)["Sheet1"]
    rows = list(ws.iter_rows(values_only=True))
    hdr = {h: k for k, h in enumerate(rows[0])}

    groups = defaultdict(list)
    owner_of = {}
    for r in rows[1:]:
        key = (r[hdr["MarketName"]], r[hdr["Affiliate"]], r[hdr["Rating"]],
               r[hdr["WeekDef"]], r[hdr["DayPart"]])
        rate = r[hdr["Rate"]]
        if isinstance(rate, (int, float)):
            groups[key].append(rate)
        owner_of[key] = r[hdr["Owner"]]

    peer = defaultdict(list)
    cells = {}
    for key, rates in groups.items():
        cur = st.median(rates)
        cells[key] = cur
        if cur > 1:
            peer[(key[0], key[2], key[4], key[3])].append(cur)  # market, rating, daypart, weekdef
    peer = {k: st.median(v) for k, v in peer.items() if len(v) >= MIN_PEERS}

    out = []
    for key, cur in cells.items():
        market, aff, rating, wd, dp = key
        flags = []
        if len(groups[key]) > 1:
            flags.append(f"dup-collapsed({len(groups[key])})")
        floor = FLOOR_MF.get(rating, 2) * (1 if wd == "M-F" else WEEKEND_FLOOR_FACTOR)
        prop = cur
        if prop < floor:
            prop = floor
            flags.append("floored" + ("-was-zero" if cur == 0 else ""))
        med = peer.get((market, rating, dp, wd))
        if med and cur > 1:
            if cur < LOW_BAND * med:
                flags.append("REVIEW-low-vs-peers")
            elif cur > HIGH_BAND * med:
                flags.append("REVIEW-high-vs-peers")
        prop = round_price(prop)
        owner = owner_of[key]
        is_ih = bool(owner and "iheart" in str(owner).lower())
        out.append({
            "market": market, "aff": aff, "owner": owner, "ih": "Y" if is_ih else "N",
            "rating": rating, "wd": wd, "dp": dp, "n": len(groups[key]),
            "cur": cur, "prop": prop,
            "d": (prop - cur) / cur if cur else None,
            "flags": ";".join(flags),
        })

    out.sort(key=lambda x: (x["market"], x["aff"], x["rating"],
                            WD_ORDER.get(x["wd"], 9), DP_ORDER.get(x["dp"], 9)))

    wb = Workbook()
    hdr_font = Font(bold=True, color="FFFFFF")
    hdr_fill = PatternFill("solid", fgColor="C6002B")
    flag_fill = PatternFill("solid", fgColor="FFF2CC")

    w = wb.active
    w.title = "Proposed TTWN Card v0.1 DRAFT"
    cols = ["Market", "Affiliate", "Owner", "iHeart?", "Rating", "Days", "Daypart",
            "Obs", "Cur Rate", "PROP Rate", "Δ %", "Flags"]
    w.append(cols)
    for c in w[1]:
        c.font, c.fill = hdr_font, hdr_fill
    for o in out:
        w.append([o["market"], o["aff"], o["owner"], o["ih"], o["rating"], o["wd"],
                  o["dp"], o["n"], round(o["cur"], 2), o["prop"],
                  round(o["d"] * 100, 1) if o["d"] is not None else None, o["flags"]])
        if o["flags"]:
            w.cell(row=w.max_row, column=len(cols)).fill = flag_fill
    w.freeze_panes = "E2"
    w.auto_filter.ref = w.dimensions
    for idx, width in enumerate([22, 12, 26, 8, 7, 8, 10, 5, 9, 10, 7, 30], 1):
        w.column_dimensions[get_column_letter(idx)].width = width

    s = wb.create_sheet("Summary")
    n = len(out)
    for line in [
        ("Cells on card (after dup collapse)", n),
        ("Markets", len({o['market'] for o in out})),
        ("Affiliates", len({o['aff'] for o in out})),
        ("iHeart-owned cells", sum(1 for o in out if o['ih'] == 'Y')),
        ("Non-iHeart cells (kept + flagged, K4)", sum(1 for o in out if o['ih'] == 'N')),
        ("Cells floored (was zero/near-zero junk)",
         sum(1 for o in out if 'floored' in o['flags'])),
        ("REVIEW-low flags", sum(1 for o in out if 'REVIEW-low' in o['flags'])),
        ("REVIEW-high flags", sum(1 for o in out if 'REVIEW-high' in o['flags'])),
        ("Duplicate source rows collapsed",
         sum(o['n'] - 1 for o in out if o['n'] > 1)),
    ]:
        s.append(list(line))
    s.column_dimensions["A"].width = 50
    s["A1"].font = Font(bold=True)

    m = wb.create_sheet("Methodology & Knobs")
    for t in [
        "PROPOSED TTWN RATE CARD v0.1 - DRAFT FOR MANAGEMENT REVIEW",
        "",
        "SOURCE: original 'TTWN base rates 260601' file (Updated Rates 6.1),",
        "analyzed firsthand - NOT the media planner's transformed data.",
        "",
        "GRAIN: Market x Affiliate x Rating (R/NR/NC) x Days (M-F / Sat-Sun) x",
        "Daypart; single rate (TTWN has no spot-length dimension). Duplicate",
        "source rows on this grain collapsed by median (flagged).",
        "",
        "METHOD: baseline = median observed rate per cell; floors kill the",
        "zero/$1 rows (K1); grid rounding (K3); outliers vs SAME-MARKET peers (Market x",
        "Rating x Daypart x Days median, min 4 peers) are FLAGGED only (K2) - no",
        "automatic cuts or raises in v0.1 (no per-affiliate audience join here).",
        "",
        f"KNOBS: K1 floors M-F {FLOOR_MF} (weekend = {int(WEEKEND_FLOOR_FACTOR*100)}%);",
        f"K2 review bands {LOW_BAND}x / {HIGH_BAND}x; K3 rounding $1<20, $5<100, $10 above;",
        "K4 non-iHeart affiliates kept with iHeart?=N flag (decision standing:",
        "keep vs split card).",
        "",
        "OBSERVED STRUCTURE (for the policy discussion):",
        "- Rated ~ $24 M-F median vs Non-rated ~ $7 (about 3.4x).",
        "- Weekend ~ 0.46x weekday on rated cells.",
        "- Management may choose to make these ratios explicit policy in v1.0.",
    ]:
        m.append([t])
    m.column_dimensions["A"].width = 90

    wb.save(out_path)
    print(f"cells={n} floored={sum(1 for o in out if 'floored' in o['flags'])} "
          f"low={sum(1 for o in out if 'REVIEW-low' in o['flags'])} "
          f"high={sum(1 for o in out if 'REVIEW-high' in o['flags'])}")
    print("saved:", out_path)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
