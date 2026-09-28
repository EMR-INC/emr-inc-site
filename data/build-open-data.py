#!/usr/bin/env python3
"""Build the public open-data CSV from the dispatch events table.

Takes either the Spotlight workbook (.xlsx, sheet "Dispatch Events (full)") or a
plain CSV export of the same table. Both are accepted because the workbook is
not in this repo and is not always to hand, and a build script that cannot be
re-run is a build script that stops being true.

Run with --with-location to add the raw address and coordinates. That switch is
for internal work only; the file published on the site is built without it.
"""
import argparse, csv, re, sys

# Published. Operational facts about the call. `street` is DERIVED here, not
# read from the sheet: see street() below.
PUBLIC = ["id", "dispatch_ts", "talkgroup", "call_type", "severity",
          "unit_raw", "unit_type", "unit_num", "unit_normalized",
          "status", "incident_key", "street"]

# Columns computed by this script rather than copied. The value is the source
# column each one is computed from, so the presence check below still has
# something to verify.
DERIVED = {"street": "address"}

# Added only with --with-location.
LOCATION = ["address", "geocode_lat", "geocode_lng"]

# Never published, and why.
WITHHELD = {
    "matched_user_id": "identifies an individual member; 19 people across the file",
    "audio_url":       "raw radio audio, which is the transcript by another route",
    "extracted":       "model output carrying consciousness_status, breathing_status, "
                       "patient_count, priority_symptoms and street names",
    "address":         "the house number. The street it sits on is published as "
                       "`street`; the number is not",
    "geocode_lat":     "coordinates resolve to the house number by another route",
    "geocode_lng":     "coordinates resolve to the house number by another route",
    "department_id":   "a single constant UUID; no information in it",
    "geocoded_at":     "pipeline metadata",
    "created_at":      "pipeline metadata",
    "updated_at":      "pipeline metadata",
}

# ---------------------------------------------------------------------------
# STREET DERIVATION
#
# The rule is deliberately conservative in one direction only: when it cannot
# satisfy itself that what is left is a street, it emits nothing. A blank cell
# costs a reader one row of geography. A surviving house number costs a
# household its privacy, and cannot be taken back once the file is downloaded.
# So every branch below that is unsure returns "".
#
# Three things make this harder than stripping a leading integer:
#
#   1. Ordinal street names. "3250 12th Street" must become "12th Street", not
#      "th Street". An earlier version of this file produced "th Street" for 75
#      rows and destroyed the only geography those rows carried, at no privacy
#      gain at all: the ordinal is the street's NAME, shared by everyone on it.
#      ORDINAL below is what keeps it.
#   2. Directional words. "North" and "South" are part of street names here
#      ("North Tamiami Trail") and must be kept, but "westbound Screwville
#      Road" is a direction of travel spoken on the air and is not. Only the
#      -bound forms are stripped; the bare cardinals stay.
#   3. Two leading number groups. "110 57 Artists Avenue" and "53 11 Proctor
#      Road" are transcription artifacts of a spoken address. One pass at the
#      leading number leaves a second, so HOUSE is applied until it stops
#      matching.
#
# THIS PUBLISHES THE STREET, AND THE STREET IS IDENTIFYING FOR SOME CALLS.
# Measured on the September 4 file: of 2,869 calls that reduce to a street,
# 1,130 sit on a street that appears exactly once, and roughly 990 of those
# also carry a medical nature and a second-precision timestamp. For those rows
# the combination is close to a household. Coarsening the timestamp does not
# fix it — truncating to the hour still leaves 1,987 of 2,377 street-hour pairs
# unique, because the quasi-identifier is the street, not the clock. The
# decision to publish anyway was made knowingly, on the ground that the whole
# argument of this page is that publicly funded dispatch data should be
# readable, and that a street without a number is what the agency's own
# records release. It is recorded here rather than left implicit so that
# whoever revisits it is arguing with a number and not with a feeling.
# ---------------------------------------------------------------------------
SUFFIX = {"street", "st", "avenue", "ave", "road", "rd", "drive", "dr",
          "boulevard", "blvd", "lane", "ln", "court", "ct", "circle", "cir",
          "trail", "trl", "way", "place", "pl", "terrace", "ter", "parkway",
          "pkwy", "plaza", "loop", "run", "square", "route"}

UNIT    = re.compile(r"[,#]?\s*\b(?:apt|apartment|unit|ste|suite|room|rm|"
                     r"bldg|building|fl|floor)\b.*$", re.I)
BOUND   = re.compile(r"^\s*(?:north|south|east|west)bound\s+", re.I)
HOUSE   = re.compile(r"^\s*\d+[A-Za-z]?\s*(?:-\s*\d+)?\s+")
ORDINAL = re.compile(r"^\d+(?:st|nd|rd|th)$", re.I)


def street(addr):
    """Reduce a spoken address to its street, or to "" if unsure."""
    s = (addr or "").strip()
    if not s:
        return ""
    # Apartment, unit and floor first: they are the most precise thing in the
    # string, and they sit at the end, so everything after the designator goes.
    s = UNIT.sub("", s).strip().strip(",").strip()
    s = BOUND.sub("", s).strip()
    while True:                                  # repeat: some rows carry two
        t = HOUSE.sub("", s, count=1).strip()    # leading number groups
        if t == s:
            break
        s = t
    if not s:
        return ""
    toks = s.split()
    # Must end in something that names a kind of street. This is the check that
    # rejects fragments, bare cross-street phrases and ASR noise.
    if toks[-1].strip(".,").lower() not in SUFFIX:
        return ""
    out = []
    for t in toks:
        if ORDINAL.match(t.strip(".,")):
            out.append(t)                        # the ordinal IS the name
            continue
        if re.search(r"\d", t):
            return ""                            # any other digit disqualifies
        out.append(t)
    return " ".join(out).strip().strip(",").strip()


def rows_from_xlsx(path):
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    it = wb["Dispatch Events (full)"].iter_rows(values_only=True)
    next(it)                      # provenance banner
    return list(next(it)), it


def rows_from_csv(path):
    csv.field_size_limit(10 ** 9)     # `extracted` holds long model output
    r = csv.reader(open(path, encoding="utf-8"))
    return next(r), r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src", help="the workbook (.xlsx) or a CSV export of the table")
    ap.add_argument("out")
    ap.add_argument("--with-location", action="store_true")
    a = ap.parse_args()

    cols = PUBLIC + (LOCATION if a.with_location else [])

    hdr, it = (rows_from_xlsx if a.src.endswith(".xlsx") else rows_from_csv)(a.src)
    ix = {h: i for i, h in enumerate(hdr)}

    for c in cols:
        src = DERIVED.get(c, c)
        assert src in ix, f"column missing from source: {src}"
    # Nothing withheld may reach the output. A derived column is exempt by
    # name, because `street` is computed FROM a withheld column on purpose.
    leaked = (set(cols) - set(DERIVED)) & set(WITHHELD)
    assert not leaked, f"a withheld column is in the output set: {sorted(leaked)}"
    if a.with_location:
        assert set(LOCATION) <= set(cols)   # --with-location is the only way in

    n = 0
    streets = 0
    with open(a.out, "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for row in it:
            def cell(c):
                if c == "street":
                    return street(row[ix["address"]])
                v = row[ix[c]]
                return "" if v is None else v
            vals = [cell(c) for c in cols]
            streets += 1 if vals[cols.index("street")] else 0
            w.writerow(vals)
            n += 1

    print(f"{a.out}: {n:,} rows, {len(cols)} columns")
    print(f"  street resolved on {streets:,} of {n:,} rows")
    print("  published:", ", ".join(cols))
    print("  withheld :", ", ".join(sorted(set(WITHHELD) - set(cols))))


if __name__ == "__main__":
    sys.exit(main())
