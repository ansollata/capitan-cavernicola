# Meetings Meeting Automation — WORKLOG
# Last updated: 2026-04-15

## STATUS
**Single-file script `meetings_meeting.py` ready.** User pivoted from the
multi-module src/ layout to one consolidated script for Cowork invocation.
No Google Sheets, no SF API — just CSV in, per-market Excel files out.

Last verified run: 2026-04-15 20:33
- 747 input rows, 107 markets with data, 162 workbooks written, 0 failures
- Week tab name: `4-20-26` (correct — Monday inside the Sun–Sat week of 4/19–4/25)
- Idempotent: 2nd run produces same output (no duplicate rows, no sidebar accumulation)
- Invocation: `python3 meetings_meeting.py data/sample_sf_export.xls`

Spot-checks passed (retained from earlier modular pipeline, same outputs):
- NYC (largest): 78 rows, $1,131,150 pitched
- Memphis: 5 rows, $17,400
- Panama City+Tallahassee (combo): 8 rows — confirms combo-market merging
- Fort Myers+Naples (combo): 3 rows
- Akron (empty week): tab exists, A-K blank, sidebar shows $0, Summary shows 0s

## NEXT STEPS
1. User tests `python3 meetings_meeting.py <path-to-export.xls>` via Cowork
2. Spot-check a few generated market files against what's currently done manually
3. (Optional) Wire up a manager roster to populate Mgr In Person tab
4. (Optional) Schedule it — cron/launchd/GitHub Actions/etc.

## SF EXPORT COLUMN LAYOUT (authoritative)
Source: `report1776290426866.xls` (NEXT_WEEK, 747 rows)

| # | SF Export Column | → Output Col | Output Header | Notes |
|---|---|---|---|---|
| — | (none) | A | Mgr | **blank** — add empty column |
| 1 | `Assigned To: Full Name` | B | AE | |
| 2 | `Account: Account Name` | C | Account | 119/747 null (16%) |
| 3 | `Date` | D | Date | string "M/D/YYYY" → parse to date |
| 4 | `Due Time` | E | Due Time | string "M/D/YYYY H:MM AM/PM" → extract time |
| 5 | `Event Purpose` | F | Event Purpose | 105/747 null. Already in LABEL form ("First Time Meeting (CNA)") — no translation needed |
| 6 | `Type` | G | Type | no nulls |
| 7 | `Meeting Method` | H | Method | no nulls in this export; spec says nulls possible |
| 8 | `Amount Discussed` | I | Amount | 480/747 null (mostly non-Ask) |
| 9 | `# of FTMs` | — | — | **DROP** — computed (0/1), not in output |
| 10 | `Assigned To: Market Division` | J | Division | |
| 11 | `Assigned To: Home Operating Market` | K | Market | |

SF export data profile:
- Sort: Division → Market → AE (grouped by report). Master tracker is chronological — we may re-sort or preserve export order (TBD from user preference).
- No grand total row, no grouping subheaders, no empty separator rows
- 11 divisions, 107 distinct markets, $12.38M total Amount
- Date range: 4/19–4/25 (Sun–Sat, 7 days)

## SPEC CORRECTIONS (from cached Event.json / User.json schemas)
Spec says `Meeting_Method__c` on Event — **this field does not exist**.
Real field: `Event_Type__c` (picklist, label "Event Type").
Picklist values: `Client Recap`, `In-Person Meeting`, `Phone Call`, `Video Call` — matches spec values exactly.

Spec says Event Purpose picklist value `'First Time Meeting (CNA)'` — **that's the report LABEL**.
Real API value: `First Time CNA`.
Full picklist: `Ask - New`, `Ask - Returning`, `Customer Service`, `First Time CNA`, `Other`.

The MWM script at ~/mwm_pull.py already uses `Event_Type__c` and `'First Time CNA'` — consistent with cached schema. The instructions file has stale/wrong names.

## VERIFIED CUSTOM FIELDS
**Event:**
- `Event_Purpose__c` (picklist) ✓
- `Event_Type__c` (picklist) ← replaces the spec's `Meeting_Method__c`
- `Amount_Discussed__c` (currency) ✓
  - Note: also exists as `Amount_Discussed_Text_Field__c` (string) and `Amount_Discussed_Formula__c` (formula). Use the __c currency field.

**User:**
- `Market_Division__c` (string) ✓
- `Home_Operating_Market__c` (string) ✓
- `Market_Region__c` (string, label "Market Area") — not needed for this report but worth knowing
- `ProfileId` (reference → Profile)
- `ManagerId` (reference → User)

## PRIOR WORK DISCOVERED
- `~/sf_schemas/` — all 12 object schemas pulled (Mar 25–26)
- `~/sf_schemas/Event.json` — 164 fields
- `~/sf_schemas/User.json` — 270 fields
- `~/sf_schemas/_field_values.json` — cached field values
- `~/mwm_pull.py` — working prod SF auth (client_credentials flow), uses Event_Type__c and First Time CNA
- `~/Reporting Bernie/MWM_SESSION_WORKLOG.md` — detailed MWM project history
- `~/sf_schemas/CLAUDE.md` — knowledge dump (noted to have some errors per MWM session log)

Auth: prod `ihm.my.salesforce.com`, client_credentials flow, Run-As Jennifer Mueller, API v62.0.

## CORRECTED TEST SOQL (LIMIT 10)
```sql
SELECT
    Owner.Name,
    Owner.Manager.Name,
    Owner.Market_Division__c,
    Owner.Home_Operating_Market__c,
    Owner.Profile.Name,
    Account.Name,
    ActivityDate,
    ActivityDateTime,
    Event_Purpose__c,
    Type,
    Event_Type__c,
    Amount_Discussed__c
FROM Event
WHERE
    ActivityDate = NEXT_WEEK
    AND Event_Type__c IN ('Client Recap', 'In-Person Meeting', 'Phone Call', 'Video Call')
    AND Owner.Market_Division__c != null
    AND Owner.Home_Operating_Market__c != null
    AND Owner.Profile.Name LIKE '%local ae%'
LIMIT 10
```

## KNOWN ISSUES
1. Spec had wrong field name (`Meeting_Method__c`) — corrected to `Event_Type__c`
2. Spec had wrong picklist value (`First Time Meeting (CNA)`) — corrected to `First Time CNA`
3. NEXT_WEEK on ActivityDate — `= NEXT_WEEK` (range literal), not `>=`. Spec gets this right.
4. Role filter ("iHM Local - Sales" hierarchy) not in SOQL — deferred to Phase 2. Profile.Name LIKE '%local ae%' is a reasonable proxy filter per the spec.

## ARTIFACTS (current state)
```
meetings_meeting.py     SINGLE-FILE script — the deliverable
requirements.txt        pandas, openpyxl, lxml
data/
  NEW_location_mapping.xlsx   162-market mapping (used by --mapping)
  sample_sf_export.xls        reference SF export (747 rows, NEXT_WEEK)
config/
  market_crosswalk.json       side artifact from earlier modular build; not used by the script
logs/
  run_YYYY-MM-DD_HHMMSS.json  run summary written by every invocation
market_files/           output dir — 162 per-market xlsx files (created at runtime)
WORKLOG.md
```

## USAGE
```
pip install -r requirements.txt
python3 meetings_meeting.py <sf_export.xls>
python3 meetings_meeting.py <sf_export.xls> --out-dir output/
python3 meetings_meeting.py <sf_export.xls> --week 4-20-26         # override week tab
python3 meetings_meeting.py <sf_export.xls> --only-with-data       # skip empty markets
python3 meetings_meeting.py <sf_export.xls> --mapping /path/to/mapping.xlsx
```

## LESSONS LEARNED
- Always verify custom field names against cached schema before trusting a spec doc.
- Picklist API values often differ from report labels (e.g., "First Time CNA" vs "First Time Meeting (CNA)").
- Prior project artifacts (~/sf_schemas/, ~/mwm_pull.py) saved a full round of discovery — always check for prior work.
- SF Lightning report exports are HTML-as-xls: `pd.read_html(path)[0]` is the right parser.
- For Sun–Sat weeks, the Monday-inside-the-week logic is: if date is Sunday, +1 day; otherwise, subtract weekday() from date. The naive `first - weekday()` gives the Monday of the *previous* week when the first date is Sunday.
- The master tracker's Mgr In Person tab is stale 2024 data and is not actively maintained. Without an AE→Manager roster, this tab can only have structure, not data.
- Report specs written by humans get small-but-critical facts wrong (field names, picklist values, filter semantics, sort order). The source of truth is the actual exported report file — build on that, not on the spec prose.

## BUSINESS DECISIONS LOG

### 1. Mgr column source — RESOLVED (intentionally blank)
**Finding**: Column A "Mgr" is intentionally blank in the master tracker, confirmed by
inspecting 2026 Weekly Appt Tracker Master 4.6.xlsx:
- Tab "4-6-26": 3,685/3,685 rows have column A null
- Tab "4-13-26": 578/578 rows have column A null
Manager data lives in the separate "Mgr In Person" tab, not inline with each meeting.

**Why**: User confirmed it's intentional. The spec's `Owner.Manager.Name` → Mgr mapping
is a misread — the template has "Mgr" as a header but no data is ever written to it.

**How to apply**: Drop `Owner.Manager.Name` from the SOQL entirely. In the row output,
column A is blank, B=AE name. Saves a User join and simplifies the query.
