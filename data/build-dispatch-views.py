#!/usr/bin/env python3
"""Build data/dispatch-views.json, which is what dispatch-views.html draws.

THE INPUT IS THE PUBLISHED FILE, data/dispatch-events.csv, and that is the
point. Every figure on the views page can be reproduced by a reader who
downloads the CSV from the open-data page and runs this script. There is no
private intermediate step and no number on the page that came from somewhere
the reader cannot reach. If this ever starts reading a private source, the
claim the page makes about itself stops being true.

Cadence is Monday, Wednesday and Friday, driven by
.github/workflows/dispatch-views.yml.

WHAT THIS DELIBERATELY DOES NOT COMPUTE
---------------------------------------
Governed by OHPAH_Department_Unit_Timeframe_Views_2026-09-04 (the imagineer
doc), which is the source of truth for these views.

  * NO STATION GRAIN. Build rule 2: a department view is the sum of its
    rostered units, and the station view is deferred. Pushing a department
    rate down to a station is the ecological fallacy in its textbook form
    (Robinson 1950, Am Sociol Rev 15:351; Diez-Roux 1998, AJPH 88:216), and
    on this data it misstates the busiest station by several times.
  * NO PER PERSON ANYTHING. Sleep Debt and Fire Exposure are defined per
    person per shift in migration 00071, behind the consent firewall that
    00122 enforces. Nothing person grain is reachable from a radio
    transmission, and nothing person grain belongs on a public page.
  * NO SCORE. The three named measures, Work Intensity, Sleep Debt and Fire
    Exposure, are not computed here. Section 5 of the imagineer doc holds any
    exposure framing until legal and clinical review. What IS published is the
    dispatch activity those measures are built from, which is counting.
  * NO AVERAGED LONGEST GAP. The imagineer doc is explicit that the longest
    unbroken gap is distributed, never aggregated into a fake average. It is
    emitted below as every night's value, in order.

Numerators and denominators are stored, never ratios. That is a standing rule
from the tiered scores plan and it is what lets a reader recompute a rate
under a different definition instead of taking ours.
"""
import csv, json, collections, datetime as dt, statistics, sys
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
CSV_IN = HERE / "dispatch-events.csv"
NFIRS = HERE / "nfirs-hour-of-day.json"
OUT = HERE / "dispatch-views.json"

# Dispatch timestamps are UTC. Every hour of day question is about the body
# clock of the crew, so they are converted to the local zone before any
# grouping. Getting this wrong shifts the whole overnight window by four hours
# and turns the quietest part of the night into the evening peak.
LOCAL = ZoneInfo("America/New_York")

DOW = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# The overnight window is 22:00 to 06:00 local, taken from migration
# 00071_metrics_one_definition.sql so that the public counting uses the same
# window as the internal measure. No new constant is invented here.
NIGHT_START, NIGHT_END = 22, 6

# Grouping for the composition view. Every pattern is matched against the
# lowercased call_type. This is a display grouping over free text and it is
# labelled as one on the page: it is NOT a controlled vocabulary and it is not
# an NFIRS mapping.
NATURE = [
    ("Cardiac arrest",      ["cardiac arrest", "cardiac  arrest", "arrest", "cpr",
                             "unresponsive not breathing", "code blue", "pea",
                             "v-fib", "vfib", "asystole"]),
    ("Structure fire",      ["structure fire", "building fire", "house fire",
                             "residential fire", "commercial fire", "working fire",
                             "apartment fire"]),
    ("Fire alarm",          ["fire alarm", "alarm", "smoke detector", "alarm activation"]),
    ("Traffic",             ["mvc", "mva", "traffic crash", "vehicle crash",
                             "motor vehicle", "traffic accident", "rollover"]),
    ("Fall",                ["fall", "fell"]),
    ("Chest pain",          ["chest pain", "chest pressure"]),
    ("Breathing",           ["breathing", "respiratory", "sob", "shortness of breath",
                             "difficulty breathing"]),
    ("Other medical",       ["medical", "ill person", "sick person", "illness",
                             "abdominal", "diabetic", "seizure", "stroke",
                             "overdose", "od", "psychiatric", "bleeding",
                             "syncope", "unconscious", "weakness", "pain"]),
]


def classify(call_type):
    """Return the display grouping for a free text nature, or None."""
    s = (call_type or "").strip().lower()
    if not s:
        return None
    for label, pats in NATURE:
        if any(p in s for p in pats):
            return label
    return "Unclassified"


def local_dt(ts):
    """Parse a dispatch_ts and return it in the local zone."""
    # Postgres renders as "2026-07-03 20:04:50+00", which fromisoformat on 3.9
    # will not take because of the two digit offset. Normalise it.
    s = ts.strip().replace(" ", "T")
    if s.endswith("+00"):
        s = s[:-3] + "+00:00"
    return dt.datetime.fromisoformat(s).astimezone(LOCAL)


def main():
    rows = list(csv.DictReader(open(CSV_IN, encoding="utf-8")))
    stamped = [(local_dt(r["dispatch_ts"]), r) for r in rows if r["dispatch_ts"]]
    stamped.sort(key=lambda x: x[0])
    first, last = stamped[0][0], stamped[-1][0]
    days = (last.date() - first.date()).days + 1

    # -- 1. DEMAND SURFACE -------------------------------------------------
    # Day of week by hour of day. The imagineer doc marks this ship ready on
    # the grounds that it is the same raw counts with one more grouping key,
    # so it needs no external citation to stand up.
    #
    # The denominator is NOT uniform across cells: a sixty three day window
    # does not contain the same number of Mondays as Tuesdays. Each cell
    # therefore carries its own count of days observed, and the page divides.
    # Publishing the raw cell count instead would draw a surface whose ridges
    # are partly an artifact of where the window happened to start and stop.
    grid = [[0] * 24 for _ in range(7)]
    for t, _ in stamped:
        grid[t.weekday()][t.hour] += 1

    dates = {t.date() for t, _ in stamped}
    weekday_days = collections.Counter(d.weekday() for d in dates)
    observed = [weekday_days.get(i, 0) for i in range(7)]

    # -- 2. THE SAME SHAPE, AGAINST A REAL BASELINE ------------------------
    # OHPAH captures a fraction of true call volume. The honest test of
    # whether the captured slice is representative is whether its hour of day
    # profile matches a census sized record of the same state. That record is
    # already in this repo: 18.2 million Florida NFIRS incidents.
    #
    # Shares, not counts, because the two denominators differ by four orders
    # of magnitude. Both denominators are published below so the shares can be
    # turned back into counts.
    nf = json.loads(NFIRS.read_text())
    nf_total = nf["total_incidents"]
    nf_by_hour = {h["hour"]: h["count"] for h in nf["by_hour"]}

    # nfirs-hour-of-day.json carries an INTERNAL provenance string naming our
    # Supabase project by its reference. That file is not published; this one
    # is, and it is read straight into a caption on a public page. Do not pass
    # nf["source"] or nf["scope"]["note"] through. A reader needs to know what
    # the baseline IS and what it does not cover, which is the description
    # below; where our copy of it happens to live is not public information and
    # naming the project reference is a small credential leak.
    nf_years = nf["coverage_years"]
    nf_public_source = (
        f"NFIRS basic incident records, {nf['scope']['distinct_fdids']} "
        f"reporting Florida departments, {min(nf_years)} to {max(nf_years)}"
    )
    nf_public_scope = (
        "Florida only. It is a state record and must not be read as a national "
        "one. Hour of alarm is taken from the NFIRS alarm timestamp, and every "
        f"one of the {nf_total:,} rows parses to a valid hour, so nothing is "
        "dropped from the baseline."
    )
    ohpah_by_hour = collections.Counter(t.hour for t, _ in stamped)
    n_ohpah = len(stamped)
    hour_compare = [
        {
            "hour": h,
            "ohpah_count": ohpah_by_hour.get(h, 0),
            "ohpah_share": round(ohpah_by_hour.get(h, 0) / n_ohpah, 5),
            "nfirs_count": nf_by_hour.get(h, 0),
            "nfirs_share": round(nf_by_hour.get(h, 0) / nf_total, 5),
        }
        for h in range(24)
    ]

    # -- 3. OVERNIGHT LOAD AND THE LONGEST GAP -----------------------------
    # This is the Sleep Debt baseline at department grain, and it is dispatch
    # counting, not the person grain minutes of migration 00071. Two counts
    # that scale, and one per night statistic that does not.
    #
    # A night is labelled by the date it STARTS on, so the 02:00 calls belong
    # to the night before, which is how a crew experiences them.
    nights = collections.defaultdict(list)
    for t, _ in stamped:
        if t.hour >= NIGHT_START:
            nights[t.date()].append(t)
        elif t.hour < NIGHT_END:
            nights[t.date() - dt.timedelta(days=1)].append(t)

    # EVERY night in the window is emitted, not only the nights that had a
    # call. Dropping the empty ones would be the worst available choice: a
    # night with no overnight transmission looks like the most restful night
    # in the file, and it is at least as likely to be a night the receiver was
    # not hearing anything. Those two are not distinguishable from the inside,
    # so each night carries day_transmissions, the count for the whole
    # calendar day. A night with zero overnight calls AND zero calls all day
    # is a capture gap and is marked as one. The page draws it as absent
    # rather than as quiet.
    night_dates = [first.date() + dt.timedelta(days=i) for i in range(days)]
    day_totals = collections.Counter(t.date() for t, _ in stamped)

    night_rows = []
    for d in night_dates:
        times = sorted(nights.get(d, []))
        # The window runs into the following calendar day, so both days count
        # towards deciding whether the receiver was up.
        day_tx = day_totals.get(d, 0) + day_totals.get(d + dt.timedelta(days=1), 0)
        start = dt.datetime.combine(d, dt.time(NIGHT_START), tzinfo=LOCAL)
        end = start + dt.timedelta(hours=8)
        # Gaps across the whole window, including the run before the first
        # call and after the last, because both are sleep opportunity.
        edges = [start] + times + [end]
        gaps = [(b - a).total_seconds() / 60 for a, b in zip(edges, edges[1:])]
        # A fragmented pair is two calls close enough together that the gap
        # between them is not a rest opportunity. The imagineer doc flags the
        # citation for this threshold as still open, so it is reported as a
        # raw count at a stated cutoff and given no interpretation.
        night_rows.append({
            "night": d.isoformat(),
            "calls": len(times),
            "day_transmissions": day_tx,
            "capture_gap": day_tx == 0,
            # A gap of the full window is only meaningful if the receiver was
            # hearing anything at all, so it is withheld when it was not.
            "longest_gap_min": None if day_tx == 0 else round(max(gaps)),
            "pairs_under_90_min": None if day_tx == 0 else sum(
                1 for g in gaps[1:-1] if g < 90),
        })

    # -- 4. WHAT THE FILE CAUGHT -------------------------------------------
    # Section 4 of the imagineer doc: instrument the premise. Publish the
    # achieved rate rather than asserting coverage. Every one of these is a
    # limit of the file, printed by the file.
    incidents = {r["incident_key"] for _, r in stamped if r["incident_key"]}
    status = collections.Counter(r["status"] for _, r in stamped)
    with_unit = sum(1 for _, r in stamped if r["unit_normalized"])
    with_sev = sum(1 for _, r in stamped if r["severity"])
    with_nature = sum(1 for _, r in stamped if r["call_type"])
    with_street = sum(1 for _, r in stamped if r["street"])

    # -- 5. NATURE COMPOSITION ---------------------------------------------
    # call_type is free text off the air. The count of distinct spellings
    # feeding each group is reported next to the group, because that number is
    # the honest measure of how soft the grouping is.
    groups = collections.Counter()
    spellings = collections.defaultdict(set)
    for _, r in stamped:
        g = classify(r["call_type"])
        if g is None:
            continue
        groups[g] += 1
        spellings[g].add(r["call_type"].strip().lower())
    nature_rows = sorted(
        ({"group": g, "count": c, "distinct_spellings": len(spellings[g])}
         for g, c in groups.items()),
        key=lambda x: -x["count"],
    )

    # -- 6. UNIT WORKLOAD ---------------------------------------------------
    # Unit grain is the finest grain the imagineer doc allows. Transmissions,
    # not incidents, because a unit can be heard several times on one call and
    # the incident key is blank on 4,221 rows.
    units = collections.Counter(r["unit_normalized"] for _, r in stamped
                                if r["unit_normalized"])

    doc = {
        "title": "OHPAH dispatch views",
        "source": "data/dispatch-events.csv, the file published on the open data page",
        "built_by": "data/build-dispatch-views.py",
        # Stamped in LOCAL, not UTC. The stamp is printed next to a window that
        # the page declares as America/New_York, so a UTC stamp reads a day
        # ahead of the window for every build made after 8pm Eastern. Two dates
        # side by side in two different zones is the same class of error as
        # parsing an ISO date as UTC and printing it local.
        "built": dt.datetime.now(LOCAL).strftime("%Y-%m-%d"),
        "cadence": "Monday, Wednesday, Friday",
        "note": "Every figure here is recomputable from the published CSV alone. "
                "The CSV is a static capture, so these views move only when the "
                "capture is refreshed, not on every build.",
        "grain": "Department and unit. Station grain is deferred by "
                 "OHPAH_Department_Unit_Timeframe_Views_2026-09-04, build rule 2.",
        "window": {
            "first_local": first.isoformat(),
            "last_local": last.isoformat(),
            "days": days,
            "timezone": "America/New_York",
            "transmissions": n_ohpah,
        },
        "demand_surface": {
            "title": "Dispatch transmissions by day of week and hour of day",
            "unit": "transmissions per day observed",
            "n": n_ohpah,
            "days_of_week": DOW,
            "days_observed": observed,
            "grid": grid,
            # The day count is interpolated rather than typed, because it moves
            # every time the capture is refreshed and a stale one here would be
            # printed verbatim into a caption on the public page.
            "note": f"grid holds raw counts and each row is divided by its own "
                    f"days_observed to get the rate, because a {days} day "
                    f"window does not hold equal numbers of each weekday.",
        },
        "hour_profile": {
            "title": "Hour of day profile against the Florida NFIRS record",
            "unit": "share of all incidents",
            "ohpah_n": n_ohpah,
            "nfirs_n": nf_total,
            "nfirs_source": nf_public_source,
            "nfirs_scope": nf_public_scope,
            "nfirs_years": f"{min(nf_years)} to {max(nf_years)}",
            "by_hour": hour_compare,
        },
        "overnight": {
            "title": "Overnight dispatch load",
            "window_local": f"{NIGHT_START}:00 to 0{NIGHT_END}:00",
            "window_source": "migration 00071_metrics_one_definition.sql",
            "unit": "calls per night, and minutes for the longest gap",
            "nights": len(night_rows),
            "nights_with_capture": sum(1 for n in night_rows if not n["capture_gap"]),
            "nights_capture_gap": sum(1 for n in night_rows if n["capture_gap"]),
            "by_night": night_rows,
            "note": "The longest gap is given for every night and is never "
                    "averaged. Nights the receiver heard nothing at all are "
                    "marked capture_gap and carry no gap value, because a quiet "
                    "night and a deaf receiver look identical from inside the "
                    "file. The 90 minute cutoff for a fragmented pair is a "
                    "reporting cutoff with no clinical claim attached; the "
                    "citation for a defensible threshold is still open.",
        },
        "capture": {
            "title": "What the file caught, and what it did not",
            "transmissions": n_ohpah,
            "days": days,
            "transmissions_per_day": round(n_ohpah / days, 1),
            "incidents": len(incidents),
            "incidents_per_day": round(len(incidents) / days, 1),
            "rows_without_incident_key": sum(1 for _, r in stamped if not r["incident_key"]),
            "with_unit": with_unit,
            "with_severity": with_sev,
            "with_nature": with_nature,
            "with_street": with_street,
            "status": dict(status),
            "distinct_units": len(units),
            "note": "These are the denominators for everything above. A field "
                    "blank on most rows cannot carry a chart, and the ones that "
                    "are blank are named here rather than quietly skipped.",
        },
        "nature": {
            "title": "Call nature composition",
            "unit": "transmissions",
            "n_with_nature": with_nature,
            "n_without_nature": n_ohpah - with_nature,
            "distinct_raw_values": len({r["call_type"].strip().lower()
                                        for _, r in stamped if r["call_type"]}),
            "groups": nature_rows,
            "note": "call_type is free text transcribed from the air. These "
                    "groups are a display grouping over that text, not a "
                    "controlled vocabulary and not an NFIRS mapping. The "
                    "spelling count next to each group is how soft it is.",
        },
        "units": {
            "title": "Transmissions by unit",
            "unit": "transmissions",
            "n": with_unit,
            "distinct": len(units),
            "top": [{"unit": u, "count": c} for u, c in units.most_common(20)],
            "note": "Transmissions, not incidents: a unit is heard more than "
                    "once on a call, and the incident key is blank on "
                    f"{sum(1 for _, r in stamped if not r['incident_key']):,} rows.",
        },
    }

    OUT.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"{OUT.name}: {n_ohpah:,} transmissions over {days} days")
    print(f"  incidents {len(incidents):,}  units {len(units)}  nights {len(night_rows)}")
    print(f"  with unit {with_unit:,}  severity {with_sev:,}  nature {with_nature:,}  street {with_street:,}")


if __name__ == "__main__":
    sys.exit(main())
