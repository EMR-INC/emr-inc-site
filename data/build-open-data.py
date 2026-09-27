#!/usr/bin/env python3
"""Build the public open-data CSV from the Spotlight workbook's
"Dispatch Events (full)" sheet.

Run with --with-location to add address and coordinates.
"""
import argparse, csv, openpyxl, sys

# Published. Operational facts about the call, carrying no location.
PUBLIC = ["id", "dispatch_ts", "talkgroup", "call_type", "severity",
          "unit_raw", "unit_type", "unit_num", "unit_normalized",
          "status", "incident_key"]

# Added only with --with-location.
LOCATION = ["address", "geocode_lat", "geocode_lng"]

# Never published, and why.
WITHHELD = {
    "matched_user_id": "identifies an individual member; 19 people across the file",
    "audio_url":       "raw radio audio, which is the transcript by another route",
    "extracted":       "model output carrying consciousness_status, breathing_status, "
                       "patient_count, priority_symptoms and street names",
    "department_id":   "a single constant UUID; no information in it",
    "geocoded_at":     "pipeline metadata",
    "created_at":      "pipeline metadata",
    "updated_at":      "pipeline metadata",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("xlsx")
    ap.add_argument("out")
    ap.add_argument("--with-location", action="store_true")
    a = ap.parse_args()

    cols = PUBLIC + (LOCATION if a.with_location else [])

    wb = openpyxl.load_workbook(a.xlsx, read_only=True, data_only=True)
    ws = wb["Dispatch Events (full)"]
    it = ws.iter_rows(values_only=True)
    next(it)                      # provenance banner
    hdr = list(next(it))
    ix = {h: i for i, h in enumerate(hdr)}

    for c in cols:
        assert c in ix, f"column missing from source: {c}"
    # Nothing withheld may reach the output.
    assert not (set(cols) & set(WITHHELD)), "a withheld column is in the output set"

    n = 0
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for row in it:
            w.writerow(["" if row[ix[c]] is None else row[ix[c]] for c in cols])
            n += 1

    print(f"{a.out}: {n:,} rows, {len(cols)} columns")
    print("  published:", ", ".join(cols))
    print("  withheld :", ", ".join(sorted(set(WITHHELD) |
                                           (set() if a.with_location else set(LOCATION)))))


if __name__ == "__main__":
    sys.exit(main())
