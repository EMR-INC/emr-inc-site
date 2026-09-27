#!/usr/bin/env python3
"""Build the public EMR research snapshot and data-art page from call traffic.

The source workbook contains PHI-adjacent raw transcripts. This program keeps
that material in memory only and writes aggregate counts. It never serializes a
transcript, address, source row, or person-level record.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import tempfile
from collections import Counter
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SHEET_ID = "1ZqyTT9tFZqq61FrRbdS8MFXjmmycv3sa9xgvgfgP3GU"
TIME_ZONE = ZoneInfo("America/New_York")
WINDOW = dt.timedelta(days=7)
DEDUP_SECONDS = 180

UNIT_RE = re.compile(
    r"\b(rescue|engine|truck|ladder|squad|medic|ambulance|battalion|chief|hazmat|tanker|marine|air)\s*[- ]?(\d{1,3}[a-z]?)\b",
    re.I,
)

TYPE_RULES: list[tuple[str, re.Pattern[str]]] = [
    ("FIRE", re.compile(r"\b(structure fire|working fire|fire alarm|smoke|brush fire|vehicle fire|outside fire|commercial fire|residential fire)\b", re.I)),
    ("MVC", re.compile(r"\b(mvc|mva|motor vehicle|vehicle accident|traffic crash|rollover|extrication|pedestrian struck)\b", re.I)),
    ("MEDICAL", re.compile(r"\b(medical|ill person|chest pain|difficulty breathing|unconscious|seizure|fall|overdose|cardiac|stroke|hemorrhage|injury|sick person|trauma)\b", re.I)),
]


def clean(value: object) -> str:
    return "" if value is None else str(value).strip()


def parse_time(value: object) -> dt.datetime | None:
    if isinstance(value, dt.datetime):
        parsed = value
    else:
        raw = clean(value)
        if not raw:
            return None
        parsed = None
        for form in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
            try:
                parsed = dt.datetime.strptime(raw, form)
                break
            except ValueError:
                continue
        if parsed is None:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=TIME_ZONE)
    return parsed.astimezone(TIME_ZONE)


def phi_flagged(value: object) -> bool:
    raw = clean(value).lower()
    return raw not in {"", "0", "false", "no", "n", "none"}


def classify(call_type: str, transcript: str) -> str:
    combined = f"{call_type} {transcript}"
    for label, pattern in TYPE_RULES:
        if pattern.search(combined):
            return label
    return "OTHER"


def primary_unit(unit: str, transcript: str) -> str | None:
    match = UNIT_RE.search(f"{unit} {transcript}")
    if not match:
        return None
    return f"{match.group(1).upper()} {match.group(2).upper()}"


def normalized_signature(unit: str, call_type: str, address: str, transcript: str) -> str:
    # The hash is used only while deduplicating in memory; it is never published.
    detail = address or re.sub(r"\s+", " ", transcript.lower())[:180]
    raw = "|".join((unit, call_type, detail)).encode("utf-8", "ignore")
    return hashlib.sha256(raw).hexdigest()


def iter_workbook_rows(path: Path) -> Iterable[dict[str, object]]:
    from openpyxl import load_workbook

    workbook = load_workbook(path, read_only=True, data_only=True)
    for sheet in workbook.worksheets:
        if not re.fullmatch(r"[A-Z][a-z]{2} \d{4}", sheet.title):
            continue
        headers = [clean(value) for value in next(sheet.iter_rows(min_row=2, max_row=2, values_only=True))]
        index = {name: position for position, name in enumerate(headers) if name}
        required = {"Time (ET)", "Channel", "PHI?", "Call type", "Address", "Unit", "Transcript"}
        if not required.issubset(index):
            continue
        for values in sheet.iter_rows(min_row=3, values_only=True):
            yield {name: values[position] if position < len(values) else None for name, position in index.items()}


def download_workbook() -> Path:
    secret = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if not secret:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON is required for a live refresh")

    try:
        info = json.loads(secret)
    except json.JSONDecodeError as exc:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON") from exc

    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2.service_account import Credentials

    credentials = Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/drive.readonly"],
    )
    session = AuthorizedSession(credentials)
    sheet_id = os.environ.get("OHPAH_CALL_SHEET_ID", DEFAULT_SHEET_ID)
    response = session.get(
        f"https://www.googleapis.com/drive/v3/files/{sheet_id}/export",
        params={"mimeType": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
        timeout=120,
    )
    response.raise_for_status()
    handle = tempfile.NamedTemporaryFile(prefix="ohpah-call-source-", suffix=".xlsx", delete=False)
    handle.write(response.content)
    handle.close()
    return Path(handle.name)


def aggregate(rows: Iterable[dict[str, object]]) -> dict:
    parsed: list[dict[str, object]] = []
    phi_times: list[dt.datetime] = []

    for row in rows:
        when = parse_time(row.get("Time (ET)"))
        if when is None:
            continue
        if phi_flagged(row.get("PHI?")):
            phi_times.append(when)
            continue

        channel = clean(row.get("Channel"))
        call_type_raw = clean(row.get("Call type"))
        transcript = clean(row.get("Transcript"))
        unit = primary_unit(clean(row.get("Unit")), transcript)
        broad_type = classify(call_type_raw, transcript)

        channel_lc = channel.lower()
        source_ok = "station alerting" in channel_lc or "dispatch" in channel_lc
        if not source_ok or unit is None or broad_type == "OTHER":
            continue

        parsed.append({
            "time": when,
            "type": broad_type,
            "unit": unit,
            "signature": normalized_signature(unit, broad_type, clean(row.get("Address")), transcript),
        })

    if not parsed:
        raise ValueError("No publishable alert candidates were found; refusing to replace the current snapshot")

    latest = max(item["time"] for item in parsed)
    start = latest - WINDOW
    excluded_phi = sum(1 for when in phi_times if start <= when <= latest)
    in_window = [item for item in parsed if start <= item["time"] <= latest]
    in_window.sort(key=lambda item: item["time"])

    deduped: list[dict[str, object]] = []
    recent: dict[str, dt.datetime] = {}
    for item in in_window:
        signature = str(item["signature"])
        previous = recent.get(signature)
        if previous and (item["time"] - previous).total_seconds() <= DEDUP_SECONDS:
            continue
        recent[signature] = item["time"]
        deduped.append(item)

    if not deduped:
        raise ValueError("The seven-day window contains no publishable candidates")

    daily_counts = Counter(item["time"].date() for item in deduped)
    type_counts = Counter(str(item["type"]) for item in deduped)
    night_count = sum(1 for item in deduped if item["time"].hour >= 22 or item["time"].hour < 6)

    dates: list[dt.date] = []
    cursor = start.date()
    while cursor <= latest.date():
        dates.append(cursor)
        cursor += dt.timedelta(days=1)

    total = len(deduped)
    generated = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    snapshot = {
        "schema_version": 1,
        "edition": "rolling seven days",
        "generated_at_utc": generated.isoformat().replace("+00:00", "Z"),
        "source": {
            "title": "OHPAH - Raw Radio Traffic",
            "kind": "read-only Google Sheet",
            "published_fields": "aggregate counts only",
        },
        "window": {
            "start_et": start.isoformat(timespec="seconds"),
            "end_et": latest.isoformat(timespec="seconds"),
            "hours": 168,
        },
        "metrics": {
            "total_alert_candidates": total,
            "mean_per_24_hours": round(total / 7, 1),
            "night_share_pct": round(night_count / total * 100, 1),
        },
        "daily": [
            {"date": day.isoformat(), "label": day.strftime("%b %-d"), "count": daily_counts.get(day, 0)}
            for day in dates
        ],
        "call_types": [
            {"label": label, "count": count}
            for label, count in sorted(type_counts.items(), key=lambda pair: (-pair[1], pair[0]))
        ],
        "quality": {
            "phi_flagged_rows_excluded": excluded_phi,
            "dedupe_window_seconds": DEDUP_SECONDS,
            "candidate_definition": "Dispatch-channel rows with a recognized apparatus identifier and broad emergency type.",
        },
        "method": [
            {"label": "Source workbook", "text": "Read-only rows from the OHPAH Raw Radio Traffic workbook. The public artifact contains aggregates only; transcripts, addresses, and source rows are never written to this repository."},
            {"label": "Candidate rule", "text": "A row counts only when it comes from a station-alerting or dispatch channel and contains both a recognized apparatus identifier and a broad emergency type."},
            {"label": "Privacy boundary", "text": "Rows flagged for possible PHI are excluded before analysis. The committed snapshot contains counts and time bins only."},
            {"label": "Publish check", "text": "The job fails closed when the source schema changes, no candidates are found, required output fields are missing, or generated HTML does not contain the same snapshot."},
        ],
        "limitations": [
            "Florida radio systems represented in the source workbook only.",
            "Transcript-derived alert candidates are not verified CAD incidents or confirmed unit responses.",
            "Repeated transmissions are grouped conservatively within a three-minute window.",
            "No transcript, address, source-row link, or person-level record is published.",
        ],
    }
    return snapshot


def render_research(snapshot: dict) -> str:
    daily_rows = "".join(
        f"<tr><th scope='row'>{html.escape(day['label'])}</th><td>{day['count']}</td></tr>"
        for day in snapshot["daily"]
    )
    type_rows = "".join(
        f"<tr><th scope='row'>{html.escape(item['label'].title())}</th><td>{item['count']}</td></tr>"
        for item in snapshot["call_types"]
    )
    methods = "".join(
        f"<article><p>{index:02d}</p><h2>{html.escape(item['label'])}</h2><p>{html.escape(item['text'])}</p></article>"
        for index, item in enumerate(snapshot["method"], 1)
    )
    limits = "".join(f"<li>{html.escape(item)}</li>" for item in snapshot["limitations"])
    metrics = snapshot["metrics"]
    return f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Research · Daily Call Record · EMR Inc.</title><meta name='description' content='Daily aggregate call-traffic research used by the EMR Inc. open-data artwork.'><link rel='canonical' href='https://emr-inc.net/research'><style>
:root{{--stock:#F1EBDD;--ink:#10213B;--red:#D5222A;--blue:#2363A0;--green:#287443;--yellow:#E5C500}}*{{box-sizing:border-box}}body{{margin:0;background:var(--stock);color:var(--ink);font:16px/1.6 'Courier New',monospace}}a{{color:inherit}}header,main,footer{{padding:clamp(24px,5vw,72px)}}header{{border-bottom:2px solid var(--ink)}}h1{{font:900 clamp(56px,12vw,190px)/.82 'Arial Black',Arial,sans-serif;letter-spacing:-.065em;margin:.2em 0;text-transform:uppercase}}.lede{{max-width:70ch}}.metrics{{display:grid;grid-template-columns:repeat(3,1fr);background:var(--ink);color:var(--stock)}}.metric{{padding:32px;border-right:1px solid var(--stock)}}.metric strong{{display:block;font:900 clamp(36px,6vw,78px)/1 'Arial Black',Arial,sans-serif}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:40px;margin:64px 0}}table{{width:100%;border-collapse:collapse}}th,td{{padding:12px;border-bottom:1px solid var(--ink);text-align:left}}td{{text-align:right;font-weight:bold}}.method{{display:grid;grid-template-columns:repeat(2,1fr);gap:24px}}article{{border:2px solid var(--ink);padding:24px}}article h2{{font:900 30px/1 'Arial Black',Arial,sans-serif;text-transform:uppercase}}footer{{border-top:2px solid var(--ink)}}@media(max-width:760px){{.metrics,.grid,.method{{grid-template-columns:1fr}}.metric{{border-bottom:1px solid var(--stock)}}}}
</style></head><body><header><p>OHPAH research file · refreshed daily</p><h1>The call<br>record.</h1><p class='lede'>This is the public source document for the open-data artwork. It contains aggregate counts only. Raw transcripts, addresses, row links, and person-level records remain outside the public site.</p></header><section class='metrics'><div class='metric'><span>Alert candidates</span><strong>{metrics['total_alert_candidates']}</strong></div><div class='metric'><span>Mean per 24 hours</span><strong>{metrics['mean_per_24_hours']:.1f}</strong></div><div class='metric'><span>Night share</span><strong>{metrics['night_share_pct']:.1f}%</strong></div></section><main><p><a href='open-data.html'>Open the interactive data artwork →</a></p><p><strong>Window:</strong> {html.escape(snapshot['window']['start_et'])} through {html.escape(snapshot['window']['end_et'])}. <strong>Generated:</strong> {html.escape(snapshot['generated_at_utc'])}.</p><div class='grid'><section><h2>Daily field</h2><table><tbody>{daily_rows}</tbody></table></section><section><h2>Broad call types</h2><table><tbody>{type_rows}</tbody></table></section></div><section class='method'>{methods}</section><section><h2>Limits</h2><ul>{limits}</ul></section></main><footer>EMR Inc. · aggregate public research · source snapshot <a href='data/research.json'>JSON</a></footer></body></html>"""


def validate(snapshot: dict, open_data: str, research: str) -> None:
    required = {"schema_version", "generated_at_utc", "window", "metrics", "daily", "method", "limitations"}
    missing = required - snapshot.keys()
    if missing:
        raise ValueError(f"Snapshot missing required keys: {sorted(missing)}")
    if len(snapshot["method"]) != 4:
        raise ValueError("The approved method object requires exactly four checks")
    if not snapshot["daily"]:
        raise ValueError("Daily series is empty")
    total = snapshot["metrics"]["total_alert_candidates"]
    if total != sum(day["count"] for day in snapshot["daily"]):
        raise ValueError("Daily counts do not reconcile to total_alert_candidates")
    payload = json.dumps(snapshot, separators=(",", ":")).replace("</", "<\\/")
    if payload not in open_data:
        raise ValueError("Open-data page does not embed the generated snapshot")
    for token in (str(total), snapshot["generated_at_utc"], "aggregate counts only"):
        if token not in research:
            raise ValueError(f"Research page failed content check for {token!r}")


def write_outputs(snapshot: dict, template_path: Path) -> None:
    payload_pretty = json.dumps(snapshot, indent=2) + "\n"
    payload_compact = json.dumps(snapshot, separators=(",", ":")).replace("</", "<\\/")
    template = template_path.read_text(encoding="utf-8")
    if template.count("__RESEARCH_DATA_JSON__") != 1:
        raise ValueError("Open-data template must contain exactly one __RESEARCH_DATA_JSON__ placeholder")
    max_day = max((day["count"] for day in snapshot["daily"]), default=1)
    daily_bars = "".join(
        "<div class='day-column'>"
        f"<div class='day-bar' style='height:{max(4, day['count'] / max_day * 100):.2f}%'></div>"
        f"<strong class='day-count'>{day['count']}</strong>"
        f"<span class='day-label'>{html.escape(day['label'])}</span>"
        "</div>"
        for day in snapshot["daily"]
    )
    daily_aria = "; ".join(f"{day['label']}: {day['count']}" for day in snapshot["daily"])
    replacements = {
        "__RESEARCH_DATA_JSON__": payload_compact,
        "__EDITION_LABEL__": html.escape(snapshot["edition"]),
        "__TOTAL_VALUE__": f"{snapshot['metrics']['total_alert_candidates']:,}",
        "__MEAN_VALUE__": f"{snapshot['metrics']['mean_per_24_hours']:.1f}",
        "__NIGHT_VALUE__": f"{snapshot['metrics']['night_share_pct']:.1f}%",
        "__WINDOW_COPY__": "Each column is one calendar date touched by the rolling seven-day window. Height is the count of transcript-derived alert candidates.",
        "__DAILY_ARIA__": html.escape(daily_aria, quote=True),
        "__DAILY_BARS__": daily_bars,
        "__REFRESH_NOTE__": html.escape(f"Window {snapshot['window']['start_et']} through {snapshot['window']['end_et']}. Refreshed {snapshot['generated_at_utc']}."),
    }
    open_data = template
    for marker, value in replacements.items():
        if marker not in open_data:
            raise ValueError(f"Open-data template marker is missing: {marker}")
        open_data = open_data.replace(marker, value)
    research = render_research(snapshot)
    validate(snapshot, open_data, research)

    (ROOT / "data").mkdir(exist_ok=True)
    (ROOT / "data" / "research.json").write_text(payload_pretty, encoding="utf-8")
    (ROOT / "research.html").write_text(research, encoding="utf-8")
    (ROOT / "open-data.html").write_text(open_data, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-xlsx", type=Path, help="Use a local workbook export instead of Google Drive")
    parser.add_argument("--template", type=Path, default=ROOT / "templates" / "open-data.html")
    args = parser.parse_args()

    workbook = args.input_xlsx or download_workbook()
    temporary = args.input_xlsx is None
    try:
        snapshot = aggregate(iter_workbook_rows(workbook))
        write_outputs(snapshot, args.template)
    finally:
        if temporary:
            workbook.unlink(missing_ok=True)
    print("Built data/research.json, research.html, and open-data.html")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"open-data refresh failed: {exc}", file=sys.stderr)
        raise
