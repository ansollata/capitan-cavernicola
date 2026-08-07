# capitan-cavernicola

Weekly **Meetings Meeting** tracker generator.

`meetings_meeting.py` reads a raw Salesforce report export (`.xls`, actually HTML)
and produces one Excel workbook per market, matching the structure of the
2026 Weekly Appt Tracker master file.

## Usage

```bash
pip install -r requirements.txt
python3 meetings_meeting.py <sf_export.xls>
python3 meetings_meeting.py <sf_export.xls> --out-dir output/
python3 meetings_meeting.py <sf_export.xls> --week 4-20-26         # override week tab
python3 meetings_meeting.py <sf_export.xls> --only-with-data       # skip empty markets
python3 meetings_meeting.py <sf_export.xls> --mapping /path/to/mapping.xlsx
```

By default the script expects the market mapping file at
`data/NEW_location_mapping.xlsx` (sheet `New Map 4.7`) and writes per-market
`.xlsx` files to `market_files/` plus a JSON run log to `logs/`.

See `WORKLOG.md` for project history, the SF export column layout, and
verified Salesforce field names.
