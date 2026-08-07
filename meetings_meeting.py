#!/usr/bin/env python3
"""
meetings_meeting.py — weekly Meetings Meeting tracker generator.

Reads a raw Salesforce report export and produces one Excel workbook per
market, matching the structure of 2026_Weekly_Appt_Tracker_Master_4_6.xlsx.

The SF export is filename `.xls` but actually HTML — the file from Salesforce
Lightning is an HTML <table> that Excel will open. pandas.read_html parses it.

Per-market workbook structure:
  Tab 1: Summary         KPI dashboard (10 rows), one column per week + "2026 Avg"
  Tab 2: Mgr In Person   Manager × Week grid (headers only until a roster is wired)
  Tabs 3+: M-D-YY        Weekly tabs with A-K data + M/N cumulative sidebar

Usage:
  python3 meetings_meeting.py <sf_export.xls>
  python3 meetings_meeting.py <sf_export.xls> --out-dir output/
  python3 meetings_meeting.py <sf_export.xls> --week 4-20-26
  python3 meetings_meeting.py <sf_export.xls> --mapping data/NEW_location_mapping.xlsx
  python3 meetings_meeting.py <sf_export.xls> --only-with-data

Defaults:
  --out-dir  ./market_files/
  --mapping  data/NEW_location_mapping.xlsx
  --week     inferred from the Date column (Monday inside the Sun-Sat week)

Dependencies:
  pandas, openpyxl, lxml (or html5lib)
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from datetime import date, datetime, timedelta, time as dtime
from pathlib import Path
from typing import Optional

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.worksheet import Worksheet


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# Output columns on every weekly tab, in order (A..K).
WEEKLY_HEADERS = [
    'Mgr', 'AE', 'Account', 'Date', 'Due Time',
    'Event Purpose', 'Type', 'Method', 'Amount', 'Division', 'Market',
]

# Map SF export column name → output header.
INPUT_TO_OUTPUT = {
    'Assigned To: Full Name':             'AE',
    'Account: Account Name':              'Account',
    'Date':                               'Date',
    'Due Time':                           'Due Time',
    'Event Purpose':                      'Event Purpose',
    'Type':                               'Type',
    'Meeting Method':                     'Method',
    'Amount Discussed':                   'Amount',
    'Assigned To: Market Division':       'Division',
    'Assigned To: Home Operating Market': 'Market',
}

# Manual market crosswalk. For combo/re-branded markets, SF's concatenated
# name doesn't follow the pattern of "strip punctuation from official name",
# so these need explicit overrides.
MANUAL_CROSSWALK = {
    'AshlandOH':     'Ashland+Mansfield, OH',
    'BayAreaCA':     'San Francisco, CA',
    'CedarRapidsIA': 'Cedar Rapids+Iowa City, IA',
    'FortMyersFL':   'Fort Myers+Naples, FL',
    'ModestoCA':     'Modesto+Stockton, CA',
    'NewYorkNY':     'New York City, NY',
    'PanamaCityFL':  'Panama City+Tallahassee, FL',
    'PuntaGordaFL':  'Fort Myers+Naples, FL',
    'RoanokeVA':     'Roanoke+Lynchburg, VA',
    'SarasotaFL':    'Sarasota+Bradenton, FL',
    'TallahasseeFL': 'Panama City+Tallahassee, FL',
}

# Summary tab: (row_label, metric_key). Rows are written 2..8 in this order.
SUMMARY_METRICS = [
    ('Total $ Pitched ',                              'total_pitched'),
    ('Average $ Pitched (Total $/# Ask Meetings)',    'avg_pitched'),
    ('Number of First Time Meetings',                 'first_time'),
    ('Number of Ask Meetings ',                       'ask_meetings'),
    ('Number of Total Meetings ',                     'total_meetings'),
    ('Number of In Person Meetings',                  'in_person'),
    ('% of In Person Meetings',                       'pct_in_person'),
]

SUMMARY_TAB = 'Summary'
MGR_IN_PERSON_TAB = 'Mgr In Person'

HEADER_FONT = Font(bold=True)
HEADER_FILL = PatternFill('solid', fgColor='E8E8E8')

DATE_FMT = '[$-F800]dddd, mmmm dd, yyyy'
TIME_FMT = 'h:mm AM/PM'
MONEY_FMT = '_("$"* #,##0_);_("$"* (#,##0);_("$"* "-"??_);_(@_)'
PCT_FMT = '0.0%'
INT_FMT = '#,##0'


# ═══════════════════════════════════════════════════════════════════════════════
# CSV READER — parse SF HTML-as-xls
# ═══════════════════════════════════════════════════════════════════════════════

def _parse_date(s) -> Optional[date]:
    """Parse 'M/D/YYYY' → datetime.date."""
    if pd.isna(s) or not s:
        return None
    return datetime.strptime(str(s).strip(), '%m/%d/%Y').date()


def _parse_due_time(s) -> Optional[dtime]:
    """Parse 'M/D/YYYY H:MM AM/PM' → datetime.time (drops the date part)."""
    if pd.isna(s) or not s:
        return None
    return datetime.strptime(str(s).strip(), '%m/%d/%Y %I:%M %p').time()


def _clean(v):
    return None if pd.isna(v) else v


def load_sf_export(path: Path) -> pd.DataFrame:
    """
    Load the SF export file and return a DataFrame in A-K output form.

    Drops `# of FTMs`, renames columns to the spreadsheet headers,
    inserts a blank `Mgr` column at position 0, type-coerces dates/times/amounts.
    """
    if not path.exists():
        raise FileNotFoundError(f"SF export not found: {path}")

    tables = pd.read_html(str(path))
    if not tables:
        raise ValueError(f"No <table> found in {path}")
    df = tables[0]

    missing = [c for c in INPUT_TO_OUTPUT if c not in df.columns]
    if missing:
        raise ValueError(
            f"SF export is missing expected columns: {missing}\n"
            f"Columns found: {list(df.columns)}"
        )

    if '# of FTMs' in df.columns:
        df = df.drop(columns=['# of FTMs'])

    df = df.rename(columns=INPUT_TO_OUTPUT)

    df['Date'] = df['Date'].apply(_parse_date)
    df['Due Time'] = df['Due Time'].apply(_parse_due_time)
    df['Amount'] = df['Amount'].apply(lambda v: None if pd.isna(v) else float(v))
    for col in ('AE', 'Account', 'Event Purpose', 'Type', 'Method', 'Division', 'Market'):
        df[col] = df[col].apply(_clean)

    df.insert(0, 'Mgr', None)
    return df[WEEKLY_HEADERS]


def summarize_export(df: pd.DataFrame) -> dict:
    return {
        'rows': len(df),
        'distinct_markets': int(df['Market'].nunique()),
        'distinct_divisions': int(df['Division'].nunique()),
        'date_range': (df['Date'].min(), df['Date'].max()) if len(df) else (None, None),
        'amount_total': float(df['Amount'].sum(skipna=True)),
        'amount_nonnull': int(df['Amount'].notna().sum()),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MARKET CROSSWALK + SPLIT
# ═══════════════════════════════════════════════════════════════════════════════

def _sf_key(official_name: str) -> str:
    """Derive the SF-style concatenated key from an official 'Market Short' name."""
    return (
        str(official_name)
        .replace(', ', '')
        .replace(' ', '')
        .replace('+', '')
        .replace('/', '')
    )


def build_crosswalk(mapping_path: Path) -> dict[str, str]:
    """
    Return {SF short name → official market name}, built from the mapping file
    plus the 11 manual overrides. Manual entries win on collisions.
    """
    df = pd.read_excel(mapping_path, sheet_name='New Map 4.7')
    auto: dict[str, str] = {}
    for name in df['Market Short'].dropna().astype(str):
        auto[_sf_key(name)] = name
    auto.update(MANUAL_CROSSWALK)
    return auto


def resolve_market(sf_name: Optional[str], crosswalk: dict[str, str]) -> Optional[str]:
    if sf_name is None:
        return None
    return crosswalk.get(sf_name, sf_name)


def split_by_market(df: pd.DataFrame, crosswalk: dict[str, str]) -> dict[str, pd.DataFrame]:
    """
    Group rows by resolved (official) market name. Multiple SF keys that map
    to the same official market (e.g. PanamaCityFL + TallahasseeFL) are combined.
    """
    resolved = df['Market'].apply(lambda m: resolve_market(m, crosswalk))
    groups: dict[str, pd.DataFrame] = {}
    for name, sub in df.assign(_official=resolved).groupby('_official', dropna=False):
        groups[str(name)] = sub.drop(columns=['_official']).reset_index(drop=True)
    return groups


def load_all_official_markets(mapping_path: Path) -> list[str]:
    """All 162 official market names from the mapping file."""
    df = pd.read_excel(mapping_path, sheet_name='New Map 4.7')
    return sorted(df['Market Short'].dropna().astype(str).unique())


# ═══════════════════════════════════════════════════════════════════════════════
# WEEK-TAB NAME HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def week_tab_name(monday: date) -> str:
    """Format a Monday date as 'M-D-YY' with no zero padding."""
    return f"{monday.month}-{monday.day}-{monday.year % 100}"


def parse_week_tab_name(name: str) -> Optional[date]:
    """Parse 'M-D-YY' back to a date. Returns None if not a valid weekly tab name."""
    try:
        m, d, y = name.split('-')
        return date(2000 + int(y), int(m), int(d))
    except (ValueError, AttributeError):
        return None


def is_weekly_tab(name: str) -> bool:
    return parse_week_tab_name(name) is not None


def infer_week_tab(df: pd.DataFrame) -> str:
    """
    Guess the week tab name from the data's earliest date.

    The SF report covers a Sunday–Saturday week. Tabs are named after the
    Monday *inside* that week (verified: tab '4-13-26' contains 4/12 Sun – 4/18 Sat).

    Algorithm:
      - If the earliest date is Sunday → Monday is earliest + 1
      - Otherwise → Monday is the most recent Monday at or before earliest
    """
    dates = df['Date'].dropna()
    if dates.empty:
        raise ValueError("No dates in export — can't infer week label")
    first = min(dates)
    if first.weekday() == 6:  # Sunday (Python: Mon=0..Sun=6)
        monday = first + timedelta(days=1)
    else:
        monday = first - timedelta(days=first.weekday())
    return week_tab_name(monday)


# ═══════════════════════════════════════════════════════════════════════════════
# WEEKLY METRICS (for Summary tab and M/N sidebar)
# ═══════════════════════════════════════════════════════════════════════════════

def _is_ask(purpose: Optional[str]) -> bool:
    return bool(purpose) and 'Ask' in purpose


def _is_first_time(purpose: Optional[str]) -> bool:
    return purpose == 'First Time Meeting (CNA)'


def _is_in_person(method: Optional[str]) -> bool:
    return method == 'In-Person Meeting'


def compute_week_metrics(df: pd.DataFrame) -> dict:
    """
    Compute Summary-tab KPIs for one week of meetings. Definitions:

      Total $ Pitched     SUM of ALL Amount values (verified against master: $44.25M
                          for 4/6 week, matches the raw data — NOT filtered by purpose)
      # Ask Meetings      COUNT where Event Purpose contains 'Ask'
      # Total Meetings    COUNT rows
      Avg $ Pitched       Total $ Pitched / # Ask Meetings
      Total Developed $   Always None — source unclear, had #REF! errors in master
      # In-Person         COUNT where Method == 'In-Person Meeting'
      % In-Person         # In-Person / # Total
      # First Time - IP   COUNT where Purpose == 'First Time Meeting (CNA)' AND Method == 'In-Person Meeting'
      # First Time        COUNT where Purpose == 'First Time Meeting (CNA)'
      % First Time - IP   # First Time-IP / # First Time
    """
    n = len(df)
    total_pitched = float(df['Amount'].sum(skipna=True)) if n else 0.0
    ask_meetings = int(df['Event Purpose'].apply(_is_ask).sum()) if n else 0
    in_person = int(df['Method'].apply(_is_in_person).sum()) if n else 0
    first_time = int(df['Event Purpose'].apply(_is_first_time).sum()) if n else 0
    ft_in_person = int(
        (df['Event Purpose'].apply(_is_first_time) & df['Method'].apply(_is_in_person)).sum()
    ) if n else 0

    return {
        'total_pitched':    total_pitched,
        'ask_meetings':     ask_meetings,
        'total_meetings':   n,
        'avg_pitched':      (total_pitched / ask_meetings) if ask_meetings else 0.0,
        'total_developed':  None,
        'in_person':        in_person,
        'pct_in_person':    (in_person / n) if n else 0.0,
        'ft_in_person':     ft_in_person,
        'first_time':       first_time,
        'pct_ft_in_person': (ft_in_person / first_time) if first_time else 0.0,
    }


def week_pitched_total(df: pd.DataFrame) -> float:
    """SUM of all Amount values for the week — used in the M/N sidebar."""
    return float(df['Amount'].sum(skipna=True)) if len(df) else 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# WORKBOOK HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def open_or_create(path: Path) -> Workbook:
    """Open an existing workbook or create a new one with a Summary tab stub."""
    if path.exists():
        wb = load_workbook(path)
        # Strip the legacy "Mgr In Person" tab if present — no longer produced.
        if MGR_IN_PERSON_TAB in wb.sheetnames:
            del wb[MGR_IN_PERSON_TAB]
        return wb
    wb = Workbook()
    wb.active.title = SUMMARY_TAB
    return wb


def _style_header(cell) -> None:
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(horizontal='center')


def _weekly_tab_headers(ws: Worksheet) -> None:
    for col_idx, header in enumerate(WEEKLY_HEADERS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = HEADER_FONT
        cell.fill = HEADER_FILL


def _set_weekly_widths(ws: Worksheet) -> None:
    widths = {
        'A': 18.5, 'B': 22, 'C': 32, 'D': 25, 'E': 11,
        'F': 26, 'G': 14, 'H': 20, 'I': 14, 'J': 30, 'K': 18,
        'L': 3, 'M': 14, 'N': 14,
    }
    for col, w in widths.items():
        ws.column_dimensions[col].width = w


def _write_weekly_data(ws: Worksheet, df: pd.DataFrame) -> None:
    # Clear any existing A-K content (for idempotent re-runs)
    if ws.max_row > 1:
        for r in range(2, ws.max_row + 1):
            for c in range(1, 12):  # A..K
                ws.cell(row=r, column=c, value=None)

    # Sort by Date (Mon→Fri) then Due Time (8a→6p) so Monday 8am is at top
    if len(df) > 0:
        df = df.copy()
        df['_sort_date'] = pd.to_datetime(df['Date'].apply(
            lambda d: d.isoformat() if d else '9999-12-31'))
        df['_sort_time'] = df['Due Time'].apply(
            lambda t: t.hour * 60 + t.minute if t else 9999)
        df = df.sort_values(['_sort_date', '_sort_time'], ascending=True)
        df = df.drop(columns=['_sort_date', '_sort_time']).reset_index(drop=True)

    for row_idx, (_, row) in enumerate(df.iterrows(), start=2):
        for col_idx, header in enumerate(WEEKLY_HEADERS, start=1):
            value = row[header]
            if pd.isna(value):
                value = None
            cell = ws.cell(row=row_idx, column=col_idx, value=value)
            if header == 'Date' and value is not None:
                cell.number_format = DATE_FMT
            elif header == 'Due Time' and value is not None:
                cell.number_format = TIME_FMT
            elif header == 'Amount' and value is not None:
                cell.number_format = MONEY_FMT


def _write_sidebar(ws: Worksheet, current_tab: str, current_monday: date) -> None:
    """
    Columns M+N: simple two-row sidebar showing the current week's total pitched.
    Row 2: headers ("Week " | "Pitched")
    Row 3: current week date | =SUM('<tab>'!I:I)
    """
    for r in range(1, ws.max_row + 1):
        ws.cell(row=r, column=13, value=None)
        ws.cell(row=r, column=14, value=None)

    _style_header(ws.cell(row=2, column=13, value='Week '))
    _style_header(ws.cell(row=2, column=14, value='Pitched'))

    date_cell = ws.cell(row=3, column=13, value=current_monday)
    date_cell.number_format = 'm/d/yyyy'
    val_cell = ws.cell(row=3, column=14,
                       value=f"=SUM('{current_tab}'!I:I)")
    val_cell.number_format = MONEY_FMT


def upsert_weekly_tab(wb: Workbook, tab_name: str, df: pd.DataFrame) -> Worksheet:
    """Create or overwrite a weekly tab's A-K content. Sidebar is done separately."""
    if tab_name in wb.sheetnames:
        ws = wb[tab_name]
    else:
        ws = wb.create_sheet(tab_name)
    _weekly_tab_headers(ws)
    _write_weekly_data(ws, df)
    _set_weekly_widths(ws)
    return ws


def _read_weekly_tab_as_df(ws: Worksheet) -> pd.DataFrame:
    rows = []
    for row in ws.iter_rows(min_row=2, max_col=11, values_only=True):
        if all(v is None for v in row):
            continue
        rows.append(row)
    return pd.DataFrame(rows, columns=WEEKLY_HEADERS)


def get_weekly_tabs_sorted(wb: Workbook) -> list[tuple[str, date]]:
    """Return [(tab_name, monday_date), ...] sorted oldest → newest."""
    found = [(name, parse_week_tab_name(name)) for name in wb.sheetnames]
    return sorted([(n, d) for n, d in found if d is not None], key=lambda t: t[1])


def write_sidebar_on_new_tab(wb: Workbook, new_tab_name: str) -> None:
    """
    Write the M/N sidebar on the current weekly tab showing only this week's
    total pitched amount.
    """
    monday = parse_week_tab_name(new_tab_name)
    _write_sidebar(wb[new_tab_name], new_tab_name, monday)


def _apply_metric_format(cell, metric_key: str) -> None:
    if metric_key in ('total_pitched', 'avg_pitched'):
        cell.number_format = MONEY_FMT
    elif metric_key in ('pct_in_person',):
        cell.number_format = PCT_FMT
    else:
        cell.number_format = INT_FMT


def _summary_formula(metric_key: str, tab_name: str, col_letter: str, row: int) -> Optional[str]:
    """
    Build a live Excel formula for a given Summary metric that references
    the corresponding week's tab. `col_letter`/`row` are this cell's own
    position — used for within-Summary references (e.g., % rows dividing
    another metric row in the same column).

    Weekly tab columns (row 1 is header, data starts at row 2):
      B=AE, F=Event Purpose, H=Method, I=Amount
    """
    t = tab_name
    # Row positions: 2=total_pitched, 3=avg_pitched, 4=first_time,
    #                5=ask_meetings, 6=total_meetings, 7=in_person, 8=pct_in_person
    if metric_key == 'total_pitched':
        return f"=SUM('{t}'!I:I)"
    if metric_key == 'avg_pitched':
        return f"=IFERROR({col_letter}2/{col_letter}5,0)"
    if metric_key == 'first_time':
        return f"=COUNTIF('{t}'!F:F,\"First Time Meeting (CNA)\")"
    if metric_key == 'ask_meetings':
        return f"=COUNTIF('{t}'!F:F,\"*Ask*\")"
    if metric_key == 'total_meetings':
        return f"=COUNTA('{t}'!B:B)-1"
    if metric_key == 'in_person':
        return f"=COUNTIF('{t}'!H:H,\"In-Person Meeting\")"
    if metric_key == 'pct_in_person':
        return f"=IFERROR({col_letter}7/{col_letter}6,0)"
    return None


def rebuild_summary(wb: Workbook) -> None:
    """Rebuild the Summary tab. Every metric is a live formula — no hard codes."""
    ws = wb[SUMMARY_TAB]
    ws.delete_rows(1, ws.max_row + 1)

    weekly = get_weekly_tabs_sorted(wb)

    # Row 1: A blank, B '2026 Avg', then one col per week (oldest → newest)
    ws.cell(row=1, column=1, value=None)
    _style_header(ws.cell(row=1, column=2, value='2026 Avg'))
    for col_idx, (_, monday) in enumerate(weekly, start=3):
        h = ws.cell(row=1, column=col_idx, value=monday)
        h.number_format = 'm/d/yyyy'
        _style_header(h)

    first_week_col = 3
    last_week_col = first_week_col + len(weekly) - 1

    # Rows 2..11: metric rows
    for row_offset, (label, metric_key) in enumerate(SUMMARY_METRICS):
        r = 2 + row_offset
        label_cell = ws.cell(row=r, column=1, value=label)
        label_cell.font = HEADER_FONT

        # One cell per week with a live formula referencing that week's tab
        for col_idx, (tab_name, _) in enumerate(weekly, start=first_week_col):
            col_letter = get_column_letter(col_idx)
            formula = _summary_formula(metric_key, tab_name, col_letter, r)
            cell = ws.cell(row=r, column=col_idx, value=formula)
            _apply_metric_format(cell, metric_key)

        # 2026 Avg column (B): average across all week columns on this row
        if weekly:
            first_letter = get_column_letter(first_week_col)
            last_letter = get_column_letter(last_week_col)
            avg_formula = f"=IFERROR(AVERAGE({first_letter}{r}:{last_letter}{r}),0)"
            avg_cell = ws.cell(row=r, column=2, value=avg_formula)
        else:
            avg_cell = ws.cell(row=r, column=2, value=None)
        _apply_metric_format(avg_cell, metric_key)

    ws.column_dimensions['A'].width = 42
    ws.column_dimensions['B'].width = 14
    for col_idx in range(first_week_col, first_week_col + max(len(weekly), 1)):
        ws.column_dimensions[get_column_letter(col_idx)].width = 14


def rebuild_mgr_in_person(wb: Workbook, roster: Optional[dict] = None) -> None:
    """
    Rebuild the Mgr In Person tab.

    `roster` (optional): {manager_name: {monday_date: count}}. If None, the
    tab is written with headers only. The Mgr column in weekly tabs is
    intentionally blank per the master tracker, and the SF export has no
    manager data — so without an external roster this tab stays empty.
    """
    ws = wb[MGR_IN_PERSON_TAB]
    ws.delete_rows(1, ws.max_row + 1)

    weekly = get_weekly_tabs_sorted(wb)

    ws.cell(row=1, column=1, value='Manager').font = HEADER_FONT
    _style_header(ws.cell(row=1, column=2, value='2026 Avg'))
    for col_idx, (_, monday) in enumerate(weekly, start=3):
        h = ws.cell(row=1, column=col_idx, value=monday)
        h.number_format = 'm/d/yyyy'
        _style_header(h)

    if roster:
        for r_offset, mgr in enumerate(sorted(roster.keys()), start=2):
            ws.cell(row=r_offset, column=1, value=mgr).font = HEADER_FONT
            counts = []
            for col_idx, (_, monday) in enumerate(weekly, start=3):
                c = roster[mgr].get(monday, 0)
                ws.cell(row=r_offset, column=col_idx, value=c).number_format = INT_FMT
                counts.append(c)
            avg = (sum(counts) / len(counts)) if counts else 0
            ws.cell(row=r_offset, column=2, value=avg).number_format = '0.0'

    ws.column_dimensions['A'].width = 26
    ws.column_dimensions['B'].width = 12
    for col_idx in range(3, 3 + len(weekly)):
        ws.column_dimensions[get_column_letter(col_idx)].width = 12


def reorder_tabs(wb: Workbook) -> None:
    """Tabs in order: Summary, weekly tabs (newest first)."""
    weekly_sorted = sorted(
        [(name, parse_week_tab_name(name)) for name in wb.sheetnames if is_weekly_tab(name)],
        key=lambda t: t[1],
        reverse=True,
    )
    desired = [SUMMARY_TAB] + [name for name, _ in weekly_sorted]
    by_name = {s.title: s for s in wb._sheets}
    wb._sheets = [by_name[n] for n in desired if n in by_name]
    for s in by_name.values():
        if s not in wb._sheets:
            wb._sheets.append(s)


def update_market_workbook(path: Path, week_tab: str, week_df: pd.DataFrame) -> None:
    """
    Full update for one market workbook.

    Produces exactly 2 tabs:
      1. Summary — KPI dashboard with formulas referencing the weekly tab
      2. <week_tab> — this week's data sorted by Date + Due Time, with M/N sidebar

    All prior weekly tabs are removed so the file stays clean.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    wb = open_or_create(path)

    # Remove ALL prior weekly tabs (keep only Summary)
    for name in list(wb.sheetnames):
        if is_weekly_tab(name) and name != week_tab:
            del wb[name]

    upsert_weekly_tab(wb, week_tab, week_df)
    write_sidebar_on_new_tab(wb, week_tab)
    rebuild_summary(wb)
    reorder_tabs(wb)
    wb.save(path)


# ═══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════════════

def safe_filename(market_name: str) -> str:
    """'Fort Myers+Naples, FL' → 'Fort_Myers_Naples__FL' (filesystem-safe)."""
    return re.sub(r'[^\w\-_. ]', '_', market_name).replace(' ', '_')


def empty_week_df() -> pd.DataFrame:
    return pd.DataFrame(columns=WEEKLY_HEADERS)


def run(
    sf_export: Path,
    out_dir: Path,
    mapping_path: Path,
    week_tab: Optional[str] = None,
    all_markets: bool = True,
) -> dict:
    """Load the export, split by market, and update one workbook per market."""
    log = logging.getLogger('meetings_meeting')

    log.info("Loading SF export: %s", sf_export)
    df = load_sf_export(sf_export)
    stats = summarize_export(df)
    log.info("Export: %s rows, %s markets, %s divisions, $%s total",
             stats['rows'], stats['distinct_markets'], stats['distinct_divisions'],
             f"{stats['amount_total']:,.0f}")

    if week_tab is None:
        week_tab = infer_week_tab(df)
    if parse_week_tab_name(week_tab) is None:
        raise ValueError(f"Invalid week tab name: {week_tab!r} (expected 'M-D-YY')")
    log.info("Week tab: %s", week_tab)

    crosswalk = build_crosswalk(mapping_path)
    groups = split_by_market(df, crosswalk)
    log.info("Split into %d market groups with data", len(groups))

    # Flag any SF markets not in the crosswalk (shouldn't happen, but loud if it does)
    sf_markets_in_data = set(df['Market'].dropna().unique())
    unresolved = sorted(m for m in sf_markets_in_data if m not in crosswalk)
    if unresolved:
        log.warning("%d SF market names not in crosswalk: %s", len(unresolved), unresolved)

    if all_markets:
        markets_to_update = load_all_official_markets(mapping_path)
    else:
        markets_to_update = sorted(groups.keys())
    log.info("Will update %d market workbooks", len(markets_to_update))

    out_dir.mkdir(parents=True, exist_ok=True)
    written, empty, failed = 0, 0, []
    for market in markets_to_update:
        week_df = groups.get(market, empty_week_df())
        if len(week_df) == 0:
            empty += 1
        out_path = out_dir / f"{safe_filename(market)}.xlsx"
        try:
            update_market_workbook(out_path, week_tab, week_df)
            written += 1
        except Exception as e:
            log.exception("Failed on %s", market)
            failed.append((market, str(e)))

    return {
        'sf_export': str(sf_export),
        'mapping': str(mapping_path),
        'out_dir': str(out_dir),
        'week_tab': week_tab,
        'input_rows': stats['rows'],
        'input_sf_markets': stats['distinct_markets'],
        'markets_with_data': len(groups),
        'official_markets_total': len(markets_to_update),
        'workbooks_written': written,
        'workbooks_empty_week': empty,
        'unresolved_sf_markets': unresolved,
        'failed': failed,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate per-market Meetings Meeting workbooks from a raw SF report export.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument('sf_export', help="Path to the SF report export (.xls, actually HTML)")
    p.add_argument('--out-dir', default='market_files',
                   help="Directory to write per-market .xlsx files")
    p.add_argument('--mapping', default='data/NEW_location_mapping.xlsx',
                   help="Market mapping file (sheet 'New Map 4.7')")
    p.add_argument('--week', default=None,
                   help="Week tab name 'M-D-YY'. Default: inferred from the data")
    p.add_argument('--only-with-data', action='store_true',
                   help="Only write workbooks for markets with meetings this week "
                        "(skip zero-meeting markets)")
    p.add_argument('--quiet', '-q', action='store_true', help="Suppress INFO logs")
    return p


def main() -> int:
    args = _parser().parse_args()
    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format='%(asctime)s %(levelname)-7s %(message)s',
    )

    result = run(
        sf_export=Path(args.sf_export),
        out_dir=Path(args.out_dir),
        mapping_path=Path(args.mapping),
        week_tab=args.week,
        all_markets=not args.only_with_data,
    )

    print("\n── Run Summary ────────────────────────────────────")
    for k, v in result.items():
        if k == 'failed':
            print(f"  {k}: {len(v)}" + ("" if not v else f" — {v[:3]}"))
        elif k == 'unresolved_sf_markets':
            print(f"  {k}: {len(v)}" + ("" if not v else f" — {v}"))
        else:
            print(f"  {k}: {v}")

    # Persist a JSON run log alongside the output
    log_dir = Path(args.out_dir).parent / 'logs'
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / f"run_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    with open(log_path, 'w') as f:
        out = {**result, 'failed': [list(t) for t in result['failed']]}
        json.dump(out, f, indent=2, default=str)
    print(f"\nRun log: {log_path}")

    return 1 if result['failed'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
