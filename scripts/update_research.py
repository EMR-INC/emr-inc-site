#!/usr/bin/env python3
"""Build the public EMR research snapshot and data-art page.

The source is an aggregate-only JSON endpoint. This publisher rejects row-level
fields and writes the same verified snapshot into JSON and both public pages.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE_URL = "https://spotlight.ohpah.app/api/open-data-snapshot"
FORBIDDEN_KEYS = {"transcript", "address", "audio_url", "id", "source_row", "person"}


def load_snapshot(path: Path | None) -> dict:
    if path is not None:
        return json.loads(path.read_text(encoding="utf-8"))

    url = os.environ.get("OHPAH_OPEN_DATA_SOURCE_URL", DEFAULT_SOURCE_URL)
    request = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": "emr-inc-open-data-publisher/1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        if response.status != 200:
            raise RuntimeError(f"aggregate source returned HTTP {response.status}")
        return json.load(response)


def validate_source(snapshot: dict) -> None:
    required = {"schema_version", "edition", "generated_at_utc", "source", "window", "metrics", "daily", "call_types", "quality", "method", "limitations"}
    missing = required - snapshot.keys()
    if missing:
        raise ValueError(f"Snapshot missing required keys: {sorted(missing)}")
    if snapshot.get("schema_version") != 1:
        raise ValueError("Unsupported snapshot schema version")
    if snapshot.get("source", {}).get("published_fields") != "aggregate counts only":
        raise ValueError("Source did not assert the aggregate-only privacy boundary")
    if len(snapshot.get("method", [])) != 4:
        raise ValueError("The approved method object requires exactly four checks")
    if not snapshot.get("daily"):
        raise ValueError("Daily series is empty")

    total = snapshot["metrics"].get("total_alert_candidates")
    if not isinstance(total, int) or total <= 0:
        raise ValueError("total_alert_candidates must be a positive integer")
    if total != sum(day.get("count", 0) for day in snapshot["daily"]):
        raise ValueError("Daily counts do not reconcile to total_alert_candidates")
    if total != sum(item.get("count", 0) for item in snapshot["call_types"]):
        raise ValueError("Call-type counts do not reconcile to total_alert_candidates")

    def walk(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                if key.lower() in FORBIDDEN_KEYS:
                    raise ValueError(f"Forbidden row-level field reached public snapshot: {key}")
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(snapshot)


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
    parser.add_argument("--input-json", type=Path, help="Use a local aggregate snapshot instead of the live endpoint")
    parser.add_argument("--template", type=Path, default=ROOT / "templates" / "open-data.html")
    args = parser.parse_args()

    snapshot = load_snapshot(args.input_json)
    validate_source(snapshot)
    write_outputs(snapshot, args.template)
    print("Built data/research.json, research.html, and open-data.html")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"open-data refresh failed: {exc}", file=sys.stderr)
        raise
