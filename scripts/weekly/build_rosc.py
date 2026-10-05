#!/usr/bin/env python3
"""Field Notes, cardiac arrest and radio documented ROSC.

Same chassis as build.py. Different subject, different geometry, same evidence
rules and the same two part structure: the letter argues it, the figure proves it.

THE ONE THING THIS FILE EXISTS TO PROTECT. 3.3% is the share of cardiac arrest
incidents where ROSC language reached the radio record. It is NOT a survival
rate. The published study on open-data.html says so in its own type, and this
newsletter goes to firefighters and medics who will do the arithmetic in their
head before they finish the first paragraph. The guard appears in the claim, in
the letter's second beat, in the figure, in the plain text part and in the alt
text. assert_guard() fails the build if it goes missing from any of them.

Source data is the published study, assets/cardiac-arrest-rosc-diagrammatic-modernism.svg,
already live on emr-inc.net/open-data.html. The two ROSC days are read from the
ring positions in that file rather than assumed.
"""

from __future__ import annotations

import datetime as dt
import html
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

STOCK, INK, RED, BLUE, GREEN = "#F1EBDD", "#10213B", "#D5222A", "#2363A0", "#287443"
DISPLAY = "Archivo Black, Archivo, Arial, sans-serif"
BODY = "Archivo, Arial, Helvetica, sans-serif"
MONO = "Courier Prime, Courier New, monospace"

ISSUE = "PROTOTYPE"
WINDOW_LABEL = "September 20 to 26, 2026"

# From the published study. Counts sum to 61; ROSC rings sit on Sep 20 and Sep 26.
DAYS = [
    {"date": "Sep 20", "n": 8,  "rosc": 1},
    {"date": "Sep 21", "n": 7,  "rosc": 0},
    {"date": "Sep 22", "n": 6,  "rosc": 0},
    {"date": "Sep 23", "n": 12, "rosc": 0},
    {"date": "Sep 24", "n": 7,  "rosc": 0},
    {"date": "Sep 25", "n": 16, "rosc": 0},
    {"date": "Sep 26", "n": 5,  "rosc": 1},
]

GUARD = "This is not a clinical survival rate."

LETTER = [
    "Sixty one times in seven days, a cardiac arrest went out over the air.",

    "Twice, somebody said the words on the radio. Return of spontaneous circulation. "
    "Two.",

    "Before you do the arithmetic: that is not a survival rate. We do not know what "
    "happened on the other fifty nine. Neither does the record. That is the entire "
    "reason for this letter.",

    "ROSC gets called in the back of the rig, on a different channel, on a phone to "
    "the receiving facility, or nowhere at all, because the crew is busy doing the "
    "thing rather than narrating it. None of that is a failure of the crew. All of "
    "it is a hole in the only record an outsider can actually obtain.",

    "So three point three percent is not an outcome. It is the share of cardiac "
    "arrests where the outcome survived into the written record at all.",

    "That is the number worth being angry about. Not because of what your people did. "
    "Because of what the file kept.",
]
LETTER_SIGN = "EMR Inc."
LETTER_KICKER = "Two marks carry a ring. Fifty nine carry no outcome either way."


def esc(s):
    return html.escape(str(s), quote=False)


# ------------------------------------------------------------------- derive ---

def derive():
    total = sum(d["n"] for d in DAYS)
    rosc = sum(d["rosc"] for d in DAYS)
    assert total == 61, f"incident total moved: {total}"
    assert rosc == 2, f"ROSC total moved: {rosc}"
    for d in DAYS:
        assert d["rosc"] <= d["n"], f"more ROSC than incidents on {d['date']}"
    ratio = rosc / total * 100
    assert 3.2 < ratio < 3.4, f"ratio no longer matches the published 3.3%: {ratio:.2f}"
    return total, rosc, ratio


# ------------------------------------------------------------------- figure ---

W, H = 1200, 1060
M = 48
COL_W = (W - 2 * M) / len(DAYS)
R, PITCH = 9, 26          # mark radius and vertical pitch
RING_R = 16               # ROSC ring, separated from the dot by a halo of stock
BASE = 700                # marks stack upward from here


def marks():
    """One mark per deduplicated incident. The ROSC mark is the same dot inside a
    ring, separated by a gap of stock. The gap is what makes it survive grayscale:
    green and blue are nearly the same luminance, so a coloured ring touching the
    dot would disappear. The halo is a shape difference, not a colour difference."""
    p = []
    for i, d in enumerate(DAYS):
        cx = M + i * COL_W + COL_W / 2
        for k in range(d["n"]):
            cy = BASE - k * PITCH - R - 4
            # the ROSC mark is the topmost of its day, so the ring is never buried
            is_rosc = d["rosc"] and k == d["n"] - 1
            if is_rosc:
                p.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{RING_R}" fill="none" '
                         f'stroke="{GREEN}" stroke-width="3.5"/>')
            p.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{R}" fill="{BLUE}"/>')
        p.append(f'<text x="{cx:.1f}" y="{BASE + 34}" text-anchor="middle" '
                 f'font-family="{MONO}" font-size="14" font-weight="700" fill="{INK}">{d["date"]}</text>')
        p.append(f'<text x="{cx:.1f}" y="{BASE + 58}" text-anchor="middle" '
                 f'font-family="{MONO}" font-size="19" font-weight="700" fill="{INK}">{d["n"]}</text>')
    p.append(f'<line x1="{M}" y1="{BASE + 6}" x2="{W - M}" y2="{BASE + 6}" stroke="{INK}" stroke-width="2"/>')
    return "\n".join(p)


def figure(total, rosc, ratio):
    claim_1 = "SIXTY ONE ARRESTS."
    claim_2 = "TWO WROTE IT DOWN."
    sub = f"{GUARD} It is how often the outcome reached the record."

    fig = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}"
     viewBox="0 0 {W} {H}" role="img"
     aria-label="{esc(claim_1 + ' ' + claim_2 + ' ' + sub)}">
  <rect width="{W}" height="{H}" fill="{STOCK}"/>

  <text x="{M}" y="104" font-family="{DISPLAY}" font-size="54" font-weight="900"
        letter-spacing="-2.4" fill="{INK}">{esc(claim_1)}</text>
  <text x="{M}" y="158" font-family="{DISPLAY}" font-size="54" font-weight="900"
        letter-spacing="-2.4" fill="{INK}">{esc(claim_2)}</text>
  <text x="{M}" y="196" font-family="{BODY}" font-size="19" fill="{INK}">{esc(sub)}</text>
  <line x1="{M}" y1="218" x2="{W - M}" y2="218" stroke="{INK}" stroke-width="1"/>

  <text x="{M}" y="248" font-family="{MONO}" font-size="13" font-weight="700"
        letter-spacing="1.6" fill="{INK}">CARDIAC ARREST INCIDENTS ON THE MONITORED TALKGROUPS</text>

{marks()}

  <line x1="{M}" y1="790" x2="{W - M}" y2="790" stroke="{INK}" stroke-width="2"/>

  <text x="{M}" y="836" font-family="{DISPLAY}" font-size="40" font-weight="900"
        letter-spacing="-1.6" fill="{INK}">{total}</text>
  <text x="{M}" y="860" font-family="{MONO}" font-size="12" font-weight="700"
        letter-spacing="1.4" fill="{INK}">DEDUPLICATED INCIDENTS</text>

  <text x="{M + 300}" y="836" font-family="{DISPLAY}" font-size="40" font-weight="900"
        letter-spacing="-1.6" fill="{GREEN}">{rosc}</text>
  <text x="{M + 300}" y="860" font-family="{MONO}" font-size="12" font-weight="700"
        letter-spacing="1.4" fill="{INK}">ROSC STATED ON RADIO</text>

  <text x="{M + 600}" y="836" font-family="{DISPLAY}" font-size="40" font-weight="900"
        letter-spacing="-1.6" fill="{INK}">{ratio:.1f}%</text>
  <text x="{M + 600}" y="860" font-family="{MONO}" font-size="12" font-weight="700"
        letter-spacing="1.4" fill="{INK}">RADIO DOCUMENT RATIO</text>

  <text x="{M + 880}" y="836" font-family="{MONO}" font-size="13" font-weight="700"
        letter-spacing="1.2" fill="{RED}">NOT A CLINICAL</text>
  <text x="{M + 880}" y="856" font-family="{MONO}" font-size="13" font-weight="700"
        letter-spacing="1.2" fill="{RED}">SURVIVAL RATE</text>

  <circle cx="{M + 9}" cy="{905}" r="{R}" fill="{BLUE}"/>
  <text x="{M + 42}" y="910" font-family="{MONO}" font-size="13" fill="{INK}">One mark is one deduplicated cardiac arrest incident</text>
  <circle cx="{M + 9}" cy="{937}" r="{RING_R}" fill="none" stroke="{GREEN}" stroke-width="3.5"/>
  <circle cx="{M + 9}" cy="{937}" r="{R}" fill="{BLUE}"/>
  <text x="{M + 42}" y="942" font-family="{MONO}" font-size="13" fill="{INK}">Ring, ROSC language captured on the radio. Absence is not an outcome.</text>

  <text x="{M}" y="990" font-family="{MONO}" font-size="12" fill="{INK}">PERIOD {esc(WINDOW_LABEL)}, capture ends Sep 26 at 11:58 ET &#183; UNIT deduplicated incident, grouped by time, channel and context</text>
  <text x="{M}" y="1010" font-family="{MONO}" font-size="12" fill="{INK}">DENOMINATOR 61 incidents in this window &#183; Tactical traffic may be incomplete and missing traffic is not zero</text>
  <text x="{M}" y="1030" font-family="{MONO}" font-size="12" fill="{INK}">SOURCE OHPAH raw emergency dispatch transcripts, published study on emr-inc.net/open-data.html</text>
  <text x="{W - M}" y="1030" text-anchor="end" font-family="{MONO}" font-size="12"
        font-weight="700" fill="{RED}">{esc(ISSUE)}</text>
</svg>
'''
    return fig, claim_1 + " " + claim_2, sub


def render(svg_path, png_path):
    wrap = svg_path.parent / "_r.html"
    wrap.write_text(f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;'
                    f'background:{STOCK}}}svg{{display:block}}</style>{svg_path.read_text()}')
    subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu",
                    "--hide-scrollbars", f"--screenshot={png_path}",
                    f"--window-size={W},{H + 320}",
                    "--default-background-color=F1EBDD", wrap.as_uri()],
                   capture_output=True, text=True, timeout=180)
    wrap.unlink()
    if not png_path.exists():
        sys.exit("render failed")

    from PIL import Image
    im = Image.open(png_path)
    if im.size != (W, H):
        im.crop((0, 0, W, H)).save(png_path)

    # Monochrome gate. Green and blue sit at almost the same luminance, so the ring
    # has to read as a SHAPE. Sample a pixel on the ring of the Sep 20 ROSC mark and
    # the same offset from a plain mark on Sep 21; if they match, the ring vanished.
    g = Image.open(png_path).convert("L")

    def at(day_i, k, dy):
        cx = M + day_i * COL_W + COL_W / 2
        cy = BASE - k * PITCH - R - 4
        return g.getpixel((int(cx), int(cy + dy)))

    on_ring = at(0, DAYS[0]["n"] - 1, RING_R)      # Sep 20, topmost mark, on the ring
    no_ring = at(1, DAYS[1]["n"] - 1, RING_R)      # Sep 21, same offset, stock
    if no_ring - on_ring < 60:
        sys.exit(f"monochrome gate failed: ring {on_ring} vs background {no_ring}; "
                 f"the ROSC mark is not distinguishable without colour")
    g.save(png_path.parent / "rosc-figure-mono.png")
    Image.open(png_path).crop((0, 206, W, H)).save(png_path.parent / "rosc-figure-email.png")
    return on_ring, no_ring


# -------------------------------------------------------------------- email ---

def strip_html():
    """Seven days as marks. Two carry a ring. Built from table cells so Outlook
    keeps it, and it previews the figure's own vocabulary under the letter."""
    tds = []
    for d in DAYS:
        if d["rosc"]:
            tds.append(f'<td width="56" height="16" bgcolor="{GREEN}" style="width:56px;'
                       f'height:16px;background-color:{GREEN};font-size:0;line-height:0;">&nbsp;</td>')
        else:
            tds.append(f'<td width="56" height="16" bgcolor="{BLUE}" style="width:56px;'
                       f'height:16px;background-color:{BLUE};font-size:0;line-height:0;">&nbsp;</td>')
        tds.append('<td width="8" style="width:8px;font-size:0;line-height:0;">&nbsp;</td>')
    return ('<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
            + "".join(tds[:-1]) + "</tr></table>")


def email_html(claim, sub, total, rosc, ratio, alt):
    pre = f"{claim} {GUARD}"
    paras = "".join(
        f'<p style="margin:0 0 14px 0;font-family:{BODY};font-size:18px;line-height:27px;'
        f'color:{INK};">{esc(t)}</p>' for t in LETTER)

    def label(t):
        return (f'<td style="padding:0 0 6px 0;font-family:{MONO};font-size:11px;'
                f'line-height:16px;font-weight:bold;letter-spacing:1.5px;'
                f'text-transform:uppercase;color:{RED}">{esc(t)}</td>')

    ev = [("Source", "OHPAH raw emergency dispatch transcripts. Published study on emr-inc.net/open-data.html"),
          ("Period", f"{WINDOW_LABEL}. Capture ends Sep 26 at 11:58 ET."),
          ("Unit", "One deduplicated incident, grouped by time, channel and context"),
          ("Denominator", "61 incidents in this window"),
          ("Measure", "Share of incidents with ROSC language on the radio. Not an outcome."),
          ("Status", "Saved snapshot. Tactical traffic may be incomplete."),
          ("Updated", dt.date.today().isoformat())]
    rows = "".join(
        f'<tr><td width="112" valign="top" style="padding:3px 12px 3px 0;font-family:{MONO};'
        f'font-size:11px;line-height:17px;font-weight:bold;letter-spacing:1px;'
        f'text-transform:uppercase;color:{INK}">{esc(k)}</td>'
        f'<td valign="top" style="padding:3px 0;font-family:{MONO};font-size:11px;'
        f'line-height:17px;color:{INK}">{esc(v)}</td></tr>' for k, v in ev)

    return f'''<!doctype html>
<html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="x-apple-disable-message-reformatting">
<title>EMR Inc. Field Notes</title>
<!--[if mso]><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml><![endif]-->
</head>
<body style="margin:0;padding:0;background-color:{STOCK};">
<div style="display:none;font-size:1px;color:{STOCK};line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">{esc(pre)}</div>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{STOCK}" style="background-color:{STOCK};">
<tr><td align="center" style="padding:24px 12px 40px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px;max-width:600px;">

  <tr><td style="border-top:4px solid {INK};padding:10px 0 10px 0;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
      <td align="left" style="font-family:{DISPLAY};font-size:16px;font-weight:bold;letter-spacing:1.3px;color:{INK};">EMR INC. FIELD NOTES</td>
      <td align="right" style="font-family:{MONO};font-size:11px;font-weight:bold;letter-spacing:1.5px;color:{RED};">{esc(ISSUE)}</td>
    </tr></table>
  </td></tr>
  <tr><td style="border-top:1px solid {INK};font-size:0;line-height:0;">&nbsp;</td></tr>

  <tr><td style="padding:34px 0 0 0;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>{label("01 / dear chief")}</tr></table>
    <h1 style="margin:6px 0 0 0;font-family:{DISPLAY};font-size:72px;line-height:62px;font-weight:bold;letter-spacing:-3.5px;text-transform:uppercase;color:{INK};">DEAR<br>CHIEF.</h1>
  </td></tr>

  <tr><td style="padding:26px 0 0 0;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
      <tr><td style="border-left:3px solid {INK};padding:2px 0 2px 20px;">{paras}</td></tr>
    </table>
  </td></tr>

  <tr><td style="padding:22px 0 0 20px;">
    <p style="margin:0;font-family:{BODY};font-size:15px;line-height:23px;color:{INK};">
      <strong>Sincerely,</strong><br>{esc(LETTER_SIGN)}</p>
  </td></tr>

  <tr><td style="padding:30px 0 0 0;">
    {strip_html()}
    <p style="margin:10px 0 0 0;font-family:{MONO};font-size:11px;line-height:16px;letter-spacing:1.2px;text-transform:uppercase;color:{INK};">
      Seven days &#183; {total} incidents &#183; {rosc} with ROSC on the radio &#183; {esc(LETTER_KICKER)}
    </p>
  </td></tr>

  <tr><td style="padding:34px 0 0 0;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>{label("02 / the week on the air")}</tr></table>
    <h2 style="margin:4px 0 0 0;font-family:{DISPLAY};font-size:32px;line-height:34px;font-weight:bold;letter-spacing:-1px;text-transform:uppercase;color:{INK};">{esc(claim)}</h2>
    <p style="margin:10px 0 0 0;font-family:{BODY};font-size:16px;line-height:24px;color:{INK};"><strong>{esc(GUARD)}</strong> It is how often the outcome reached the record.</p>
  </td></tr>

  <tr><td style="padding:18px 0 0 0;">
    <a href="https://emr-inc.net/open-data.html" style="text-decoration:none;">
      <img src="rosc-figure-email.png" width="600" alt="{esc(alt)}"
           style="display:block;width:100%;max-width:600px;height:auto;border:1px solid {INK};" border="0">
    </a>
  </td></tr>

  <tr><td style="padding:30px 0 0 0;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>{label("03 / how to read it")}</tr></table>
    <p style="margin:0;font-family:{BODY};font-size:15px;line-height:23px;color:{INK};">
      One mark is one deduplicated cardiac arrest incident on the monitored talkgroups, grouped by
      time, channel and context. A ring means the words were said on the radio. {rosc} of {total}
      carried a ring, which is {ratio:.1f}%.
    </p>
    <p style="margin:12px 0 0 0;font-family:{BODY};font-size:15px;line-height:23px;color:{INK};">
      <strong>What this cannot say.</strong> {esc(GUARD)} It says nothing about what happened to any
      patient, and an absent ring is not a death. Tactical traffic may be incomplete and missing
      traffic is not zero. No department is named and nothing here describes an individual member.
    </p>
  </td></tr>

  <tr><td style="padding:26px 0 0 0;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-top:2px solid {INK};">
      <tr><td style="padding:12px 0 0 0;">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">{rows}</table>
      </td></tr>
    </table>
  </td></tr>

  <tr><td style="padding:30px 0 0 0;">
    <table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
      <td bgcolor="{INK}" style="background-color:{INK};">
        <a href="https://emr-inc.net/open-data.html" style="display:inline-block;padding:16px 24px;
           font-family:{MONO};font-size:12px;font-weight:bold;letter-spacing:1.5px;
           text-transform:uppercase;color:{STOCK};text-decoration:none;">Open the full study</a>
      </td></tr></table>
  </td></tr>

  <tr><td style="padding:30px 0 0 0;">
    <p style="margin:0;font-family:{BODY};font-size:15px;line-height:23px;color:{INK};">
      <strong>What should next week count?</strong> Reply with a question and we will answer it with a figure.</p>
  </td></tr>

  <tr><td style="padding:28px 0 0 0;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-top:4px solid {INK};">
      <tr><td style="padding:14px 0 0 0;font-family:{MONO};font-size:11px;line-height:17px;color:{INK};">
        EMR Inc. &#183; Emergency Medical Resolutions<br>
        Individual records belong to the member. Union and department views use aggregates.<br>
        <a href="#" style="color:{INK};text-decoration:underline;">Manage preferences</a> &#183;
        <a href="#" style="color:{INK};text-decoration:underline;">Unsubscribe</a>
      </td></tr></table>
  </td></tr>

</table>
</td></tr></table>
</body></html>
'''


def email_txt(claim, total, rosc, ratio):
    body = "\n\n".join(textwrap.fill(t, 72) for t in LETTER)
    strip = "  ".join(("(o)" if d["rosc"] else " o ") for d in DAYS)
    daily = "  ".join(f"{d['date'][4:]}:{d['n']}" for d in DAYS)
    return f"""EMR INC. FIELD NOTES / {ISSUE}

01 / DEAR CHIEF.

{body}

Sincerely,
{LETTER_SIGN}

  {strip}
  SEVEN DAYS / {total} INCIDENTS / {rosc} WITH ROSC ON THE RADIO
  {LETTER_KICKER}

02 / THE WEEK ON THE AIR

{claim}
{GUARD} It is how often the outcome reached the record.

  Daily incidents   {daily}
  Total             {total} deduplicated incidents
  ROSC on radio     {rosc}
  Radio document    {ratio:.1f}%

03 / HOW TO READ IT
One mark is one deduplicated cardiac arrest incident on the monitored
talkgroups, grouped by time, channel and context. A ring means the words were
said on the radio. {rosc} of {total} carried a ring.

WHAT THIS CANNOT SAY
{GUARD} It says nothing about what happened to any patient, and an absent ring
is not a death. Tactical traffic may be incomplete and missing traffic is not
zero. No department is named and nothing here describes an individual member.

EVIDENCE
Source       OHPAH raw emergency dispatch transcripts
Period       {WINDOW_LABEL}. Capture ends Sep 26 at 11:58 ET.
Unit         One deduplicated incident
Denominator  {total} incidents in this window
Measure      Share with ROSC language on the radio. Not an outcome.
Status       Saved snapshot. Tactical traffic may be incomplete.
Updated      {dt.date.today().isoformat()}

Open the full study: https://emr-inc.net/open-data.html

--
EMR Inc. Individual records belong to the member.
Manage preferences / Unsubscribe
"""


def assert_guard(**docs):
    """The guard must survive into every artifact a reader can reach."""
    for name, text in docs.items():
        if "not a clinical survival rate" not in text.lower():
            sys.exit(f"GUARD MISSING from {name}: the survival rate disclaimer is "
                     f"not present. Nothing is written.")


def main():
    total, rosc, ratio = derive()
    svg, claim, sub = figure(total, rosc, ratio)
    alt = (f"{claim} {GUARD} {total} deduplicated cardiac arrest incidents over seven days, "
           f"{rosc} with ROSC language captured on the radio, which is {ratio:.1f}%. "
           f"An absent ring is not an outcome.")

    (ROOT / "rosc-figure.svg").write_text(svg)
    on_ring, no_ring = render(ROOT / "rosc-figure.svg", ROOT / "rosc-figure.png")

    eh = email_html(claim, sub, total, rosc, ratio, alt)
    et = email_txt(claim, total, rosc, ratio)
    assert_guard(svg=svg, email_html=eh, email_txt=et, alt=alt)

    (ROOT / "rosc-email.html").write_text(eh)
    (ROOT / "rosc-email.txt").write_text(et)

    for n in ("rosc-figure.svg", "rosc-figure.png", "rosc-figure-email.png",
              "rosc-figure-mono.png", "rosc-email.html", "rosc-email.txt"):
        print(f"  {n:24s} {(ROOT / n).stat().st_size:>8,} bytes")
    print(f"\n  claim: {claim}")
    print(f"  {total} incidents, {rosc} ROSC, {ratio:.2f}%")
    print(f"  monochrome gate: ring {on_ring} vs background {no_ring} (need >=60 apart)")
    print(f"  guard present in svg, email.html, email.txt and alt text")


if __name__ == "__main__":
    main()
