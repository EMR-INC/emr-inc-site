# Daily open-data publication

The public source and the artwork are one build:

1. `.github/workflows/open_data_daily.yml` runs at 08:00 America/New_York every day and can also run manually.
2. `scripts/update_research.py` exports the private `OHPAH - Raw Radio Traffic` workbook through a read-only Google service account.
3. Raw rows remain in memory only. Rows flagged for possible PHI are excluded. The script publishes aggregate counts and time bins only.
4. `data/research.json` is the machine-readable source snapshot.
5. `research.html` is the human-readable source and method record.
6. `open-data.html` is generated from the same snapshot using the approved OHPAH data-art template.
7. The workflow validates reconciliation and browser scripts, commits only the three public artifacts, and the existing Vercel Git integration deploys the commit.

## One-time GitHub configuration

Create a Google Cloud service account with read-only Drive API access. Share only the `OHPAH - Raw Radio Traffic` spreadsheet with that service account as Viewer.

Add the complete service-account JSON document as the repository Actions secret `GOOGLE_SERVICE_ACCOUNT_JSON`. Do not commit the credential.

Optionally set the repository Actions variable `OHPAH_CALL_SHEET_ID`. If omitted, the publisher uses the reviewed workbook ID already recorded in the script.

Run `Daily open-data publication` once with `workflow_dispatch`. Confirm that the commit changes only:

- `data/research.json`
- `research.html`
- `open-data.html`

## Privacy boundary

The job must never commit workbook exports, transcript text, addresses, source-row links, or person-level records. The aggregate is a transcript-derived workload signal, not verified CAD incident data and not proof that a named unit responded.

The generator fails closed when no publishable candidates are found, the source columns change, the daily counts do not reconcile, the four-check method contract changes, or either generated page diverges from the JSON snapshot.

## Local verification

Export the workbook to an untracked temporary `.xlsx`, then run:

```sh
python -m pip install google-auth requests openpyxl
python scripts/update_research.py --input-xlsx /path/to/export.xlsx
node scripts/validate_generated.mjs
```

Never add the workbook export to Git.
