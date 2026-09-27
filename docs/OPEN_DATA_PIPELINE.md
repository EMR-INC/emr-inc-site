# Daily open-data publication

The public source and the artwork are one build:

1. The Spotlight worker exposes `/api/open-data-snapshot`, a cached, aggregate-only rolling seven-day JSON response from the live OHPAH Research dispatch corpus.
2. Its database query selects only `dispatch_ts`, `call_type`, `unit_normalized`, `neris_type`, and `talkgroup`. Transcript, address, row ID, audio, and person-level fields are never selected or returned.
3. `.github/workflows/open_data_daily.yml` runs at 08:00 America/New_York every day and can also run manually.
4. `scripts/update_research.py` fetches and validates the endpoint, including the aggregate-only assertion and count reconciliation.
5. `data/research.json` is the machine-readable source snapshot.
6. `research.html` is the human-readable source and method record.
7. `open-data.html` is generated from the same snapshot using the approved OHPAH data-art template.
8. The workflow validates reconciliation and browser scripts, commits only the three public artifacts, and the existing Vercel Git integration deploys the commit.

## GitHub configuration

No Google credential, Supabase credential, or repository secret is required. The Supabase service-role credential stays inside the existing Spotlight Cloudflare Worker.

The workflow defaults to `https://spotlight.ohpah.app/api/open-data-snapshot`. If the worker hostname changes, set the repository Actions variable `OHPAH_OPEN_DATA_SOURCE_URL` to the replacement endpoint.

Run `Daily open-data publication` with `workflow_dispatch` after a pipeline change. A successful refresh may change only:

- `data/research.json`
- `research.html`
- `open-data.html`

## Privacy boundary

The job must never receive or commit transcript text, addresses, source-row links, row identifiers, audio URLs, or person-level records. The aggregate is a transcript-derived workload signal, not verified CAD incident data and not proof that a named unit responded.

Both endpoint and publisher fail closed when the source is unavailable, no publishable candidates are found, required output fields are missing, daily or call-type counts do not reconcile, the four-check method contract changes, or either generated page diverges from the JSON snapshot.

## Local verification

Save an aggregate endpoint response to a local file, then run:

```bash
python scripts/update_research.py --input-json snapshot.json
node scripts/validate_generated.mjs
```

The local JSON must satisfy the same aggregate-only contract as the live endpoint.

