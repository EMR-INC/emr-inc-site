#!/usr/bin/env python3
"""Field Notes 02, brief cut. One idea, one button, one ask.

The previous build of this issue was 2,768 px of email: a seven paragraph
letter, a nine row index, a route diagram and an evidence band. That is a white
paper with a masthead. The specs that govern this are in the OHPAH design repo
and they are not ambiguous:

  brand_brain/brand_guidelines.md, tone by surface
    Email: one idea, one button, one ask.

  surfaces/README.md, campaign email
    Subject line, preheader, brand header bar, hero sized mobile first,
    one paragraph, one primary button, footer.

  docs/ux_copy.md, constraint 5
    The number is the headline whenever there is a number. Copy supports the
    figure; it does not restate it.

So: one number set large, one small figure, one paragraph, one button. The index
lives behind the button, not in the email.

Voice is taken from the Instagram plates in docs/campaigns/, which are the
register this audience already answers to. "Your body kept the record. Nobody
else did." "You logged the call. Who logged you?" Short, declarative, a turn in
it, peer to peer. Dry rather than cheerful: docs/ux_copy.md notes this audience
reads enthusiasm as a sales tell, so the humour is understated and the sentences
stay flat.

The CTA copies the proven mechanic from the campaign doc, "Comment PASSDOWN and I
will send you a sample Pass Down built on your own shift pattern." A giveaway
that is genuinely useful and specific converts better than a link to a study. We
hold all 396 Florida FDIDs, so a department's own line in this index is a real
thing to hand over.

GUARD, unchanged and non negotiable: Florida only. The source file says a count
of distinct states over the table returns 1 and that this must not be described
as a national record. assert_guard() still fails the build if it goes missing.

NOT taken from docs/campaigns/ems_world_30_day_push.md: its section 2 palette and
type. That is the retired Spotlight 1 bit system, white paper and Cinzel and EB
Garamond. brand_guidelines.md retires it explicitly. Diagrammatic modernism is
the only active visual language, so tokens come from design_system.md v3.0.
"""

from __future__ import annotations

import datetime as dt
import html
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

STOCK, INK, RED, BLUE = "#F1EBDD", "#10213B", "#D5222A", "#2363A0"
DISPLAY = "Archivo Black, Archivo, Arial, sans-serif"
BODY = "Archivo, Arial, Helvetica, sans-serif"
MONO = "Courier Prime, Courier New, monospace"

ISSUE = "02"
TOTAL_ROWS, DENOMINATOR, DROPPED = 18_251_138, 18_251_127, 11
FDIDS, FIRST, LAST, PULLED = 396, "2020", "2025", "2026-09-13"

SERIES = [
    {"code": "1", "label": "Fire",                  "n":    289_121, "pct": 1.58},
    {"code": "2", "label": "Overpressure, no fire", "n":      8_875, "pct": 0.05},
    {"code": "3", "label": "Rescue and EMS",        "n": 13_217_940, "pct": 72.42},
    {"code": "4", "label": "Hazardous condition",   "n":    272_337, "pct": 1.49},
    {"code": "5", "label": "Service call",          "n":  1_310_445, "pct": 7.18},
    {"code": "6", "label": "Good intent",           "n":  2_002_982, "pct": 10.97},
    {"code": "7", "label": "False alarm",           "n":  1_110_157, "pct": 6.08},
    {"code": "8", "label": "Severe weather",        "n":     13_861, "pct": 0.08},
    {"code": "9", "label": "Special incident",      "n":     25_409, "pct": 0.14},
]
BUILDING_FIRE = 47_286

GUARD_A, GUARD_B = "Florida only, 2020 through 2025.", "Not a national record."
GUARD = f"{GUARD_A} {GUARD_B}"

# ---------------------------------------------------------------------- copy ---
# "call", "run" and "job" are banned by the terminology table in docs/ux_copy.md.
# One word per thing, everywhere: it is an incident.

SUBJECT = "Fire is 1.58% of the job"
PREHEADER = ("A false alarm is 3.84 times more likely. Florida, six years, "
             "18,251,127 incidents.")
HOOK = "Chief, we counted every incident Florida filed for six years."
BIG = "1.58%"
BIG_UNDER = "was fire."
DEK = ("All of it. Structure, brush, car, dumpster, and the pan somebody had "
       "already smothered with a lid before you got there.")

# The one paragraph. It carries the turn, which is the only reason to send this.
PARA = ("Here is the part that stings. When you walk into budget season, the "
        "record they pull describes a rescue service: 72.42% of what your people "
        "ran was rescue and EMS. Your staffing argument describes a fire "
        "department. Both are true. Only one of them is written down.")

CTA = "Get your department's line"
CTA_MAIL = "fieldnotes@emr-inc.net"      # PLACEHOLDER, confirm before sending
CTA_UNDER = ("Reply with your FDID and we will send back your own department's "
             "line in this index. Aggregate only, and it is yours to keep.")
PS = "Next week: the 3.84 false alarms you run for every fire. Bring coffee."


def esc(s):
    return html.escape(str(s), quote=True)


def fmt(n):
    return f"{n:,}"


def derive():
    """Fail closed. Nothing is written if the source arithmetic does not hold."""
    s = sum(x["n"] for x in SERIES)
    if s != DENOMINATOR:
        sys.exit(f"series sum {s} != denominator {DENOMINATOR}")
    if DENOMINATOR + DROPPED != TOTAL_ROWS:
        sys.exit("row accounting does not reconcile")
    for x in SERIES:
        got = x["n"] / DENOMINATOR * 100
        if abs(got - x["pct"]) > 0.005:
            sys.exit(f"series {x['code']} recomputes to {got:.4f}, not {x['pct']}")
        x["exact"] = got
    fire = SERIES[0]["n"]
    alarm = next(x for x in SERIES if x["code"] == "7")["n"]
    d = {"alarm_ratio": alarm / fire, "one_in": DENOMINATOR / BUILDING_FIRE,
         "fire_pct": SERIES[0]["exact"],
         "ems_pct": next(x for x in SERIES if x["code"] == "3")["exact"]}
    if round(d["alarm_ratio"], 2) != 3.84 or round(d["one_in"]) != 386:
        sys.exit("headline claims do not reproduce")
    # Every number that appears in the copy has to come back out of the data.
    for frag, want in ((BIG, f"{d['fire_pct']:.2f}%"),
                       (PREHEADER, f"{d['alarm_ratio']:.2f} times"),
                       (PARA, f"{d['ems_pct']:.2f}%"),
                       (PS, f"{d['alarm_ratio']:.2f} false alarms")):
        if want not in frag:
            sys.exit(f"copy and data disagree: expected {want!r} in {frag!r}")
    return d


# -------------------------------------------------------------------- figure ---
# One strip. Two labels. Nothing else. It has to land in the second a thumb
# stops scrolling, which rules out an index, a legend and an axis.

FW, FH = 1200, 300
M, BAR_W = 70, 1060
BAR_Y, BAR_H = 112, 96


def figure():
    segs, x = [], float(M)
    for s in SERIES:
        w = s["exact"] / 100 * BAR_W
        segs.append({**s, "x": x, "w": w})
        x += w
    fire, ems = segs[0], segs[2]
    p = []

    def t(x, y, s, size, fam=BODY, fill=INK, w="normal", a="start", ls="0"):
        p.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" '
                 f'font-weight="{w}" fill="{fill}" text-anchor="{a}" '
                 f'letter-spacing="{ls}">{esc(s)}</text>')

    def line(x1, y1, x2, y2, sw=2):
        p.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                 f'stroke="{INK}" stroke-width="{sw}"/>')

    # Fire is 17 px of 1060. It is found by a bracket and a leader, which is
    # shape, and not by its colour: red and blue land within two points of each
    # other in grayscale, so hue carries nothing here.
    line(fire["x"], 74, fire["x"] + fire["w"], 74, 4)
    line(fire["x"] + fire["w"] / 2, 74, fire["x"] + fire["w"] / 2, BAR_Y, 4)
    line(fire["x"] + fire["w"], 74, 236, 74, 2)
    t(250, 83, f"ALL FIRE  {fire['pct']}%", 27, MONO, RED, "bold", ls="1.6")

    for s in segs:
        fill = RED if s["code"] == "1" else (BLUE if s["code"] == "3" else INK)
        p.append(f'<rect x="{s["x"]:.1f}" y="{BAR_Y}" width="{max(s["w"], 0.4):.2f}" '
                 f'height="{BAR_H}" fill="{fill}"/>')
    # Stock dividers, not colour, are what keep the segments separable in
    # grayscale. The gate below samples one.
    for s in segs[1:]:
        p.append(f'<rect x="{s["x"] - 1.5:.1f}" y="{BAR_Y}" width="3" '
                 f'height="{BAR_H}" fill="{STOCK}"/>')
    p.append(f'<rect x="{M}" y="{BAR_Y}" width="{BAR_W}" height="{BAR_H}" '
             f'fill="none" stroke="{INK}" stroke-width="3"/>')

    t(ems["x"] + ems["w"] / 2, BAR_Y + 60, f"RESCUE AND EMS  {ems['pct']}%", 31,
      MONO, STOCK, "bold", "middle", ls="2")
    # Courier Prime at 21 px plus 1.2 tracking runs about 13.8 px per glyph. A
    # caption wider than the margin is silently clipped by the viewBox rather
    # than wrapped, which is how "ACROSS 396 DEPARTM" shipped once already.
    caps = [(f"{fmt(DENOMINATOR)} INCIDENTS ACROSS {FDIDS} FLORIDA DEPARTMENTS.", INK,
             "normal"), (GUARD.upper(), RED, "bold")]
    for i, (c, col, wt) in enumerate(caps):
        if M + len(c) * 13.8 > FW - M:
            sys.exit(f"figure caption overflows and will be clipped: {c!r}")
        t(M, BAR_Y + BAR_H + 38 + i * 30, c, 21, MONO, col, wt, ls="1.2")

    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{FW}" height="{FH}" '
            f'viewBox="0 0 {FW} {FH}"><rect width="{FW}" height="{FH}" fill="{STOCK}"/>'
            f'<rect x="0" y="0" width="{FW}" height="6" fill="{INK}"/>'
            + "".join(p) + "</svg>\n"), segs


def render(svg_path, png_path, segs):
    wrap = svg_path.parent / "_r2.html"
    wrap.write_text(f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;'
                    f'background:{STOCK}}}svg{{display:block}}</style>{svg_path.read_text()}')
    subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu",
                    "--hide-scrollbars", f"--screenshot={png_path}",
                    f"--window-size={FW},{FH + 320}",
                    "--default-background-color=F1EBDD", wrap.as_uri()],
                   capture_output=True, text=True, timeout=180)
    wrap.unlink()
    if not png_path.exists():
        sys.exit("render failed")
    from PIL import Image
    im = Image.open(png_path)
    if im.size != (FW, FH):
        im.crop((0, 0, FW, FH)).save(png_path)

    g = Image.open(png_path).convert("L")
    ry = BAR_Y + BAR_H // 2
    gap = max(g.getpixel((int(segs[2]["x"]) + dx, ry)) for dx in (-1, 0, 1))
    fill = g.getpixel((int(segs[2]["x"] + 60), ry))
    if gap < 180 or fill > 120:
        sys.exit(f"mono gate 1 failed: divider {gap} vs fill {fill}")
    stem = g.getpixel((int(segs[0]["x"] + segs[0]["w"] / 2), 90))
    away = g.getpixel((int(segs[2]["x"] + 400), 90))
    if away - stem < 60:
        sys.exit(f"mono gate 2 failed: bracket {stem} vs stock {away}")
    # The guard is inside the image too, so an empty caption band means a
    # recipient with images on sees an unqualified Florida figure.
    foot = g.crop((M, FH - 70, FW - M, FH - 20))
    if min(foot.getdata()) > 200:
        sys.exit("figure caption band is empty; the guard is not visible")
    g.save(png_path.parent / "02-figure-mono.png")
    return gap, fill, stem, away


# --------------------------------------------------------------------- email ---

def email_html(d, alt):
    return f'''<!doctype html>
<html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="x-apple-disable-message-reformatting">
<title>{esc(SUBJECT)}</title>
<!--[if mso]><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml><![endif]-->
</head>
<body style="margin:0;padding:0;background-color:{STOCK};">
<div style="display:none;font-size:1px;color:{STOCK};line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">{esc(PREHEADER)}</div>

<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{STOCK}" style="background-color:{STOCK};">
<tr><td align="center" style="padding:24px 12px 36px 12px;">
<table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="width:600px;max-width:600px;">

  <tr><td style="border-top:4px solid {INK};padding:9px 0 9px 0;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>
      <td align="left" style="font-family:{DISPLAY};font-size:14px;font-weight:bold;letter-spacing:1.3px;color:{INK};">EMR INC. FIELD NOTES</td>
      <td align="right" style="font-family:{MONO};font-size:11px;font-weight:bold;letter-spacing:1.5px;color:{RED};">{esc(ISSUE)}</td>
    </tr></table>
  </td></tr>
  <tr><td style="border-top:1px solid {INK};font-size:0;line-height:0;">&nbsp;</td></tr>

  <tr><td style="padding:30px 0 0 0;">
    <p style="margin:0;font-family:{BODY};font-size:17px;line-height:26px;color:{INK};">{esc(HOOK)}</p>
  </td></tr>

  <tr><td style="padding:14px 0 0 0;">
    <p style="margin:0;font-family:{DISPLAY};font-size:84px;line-height:78px;font-weight:bold;letter-spacing:-4px;color:{RED};">{esc(BIG)}</p>
    <p style="margin:2px 0 0 0;font-family:{DISPLAY};font-size:38px;line-height:40px;font-weight:bold;letter-spacing:-1.4px;color:{INK};">{esc(BIG_UNDER)}</p>
  </td></tr>

  <tr><td style="padding:16px 0 0 0;">
    <p style="margin:0;font-family:{BODY};font-size:17px;line-height:26px;color:{INK};">{esc(DEK)}</p>
  </td></tr>

  <tr><td style="padding:24px 0 0 0;">
    <img src="02-figure.png" width="600" alt="{esc(alt)}"
         style="display:block;width:100%;max-width:600px;height:auto;border:1px solid {INK};" border="0">
  </td></tr>

  <tr><td style="padding:26px 0 0 0;">
    <p style="margin:0;font-family:{BODY};font-size:17px;line-height:26px;color:{INK};">{esc(PARA)}</p>
  </td></tr>

  <tr><td style="padding:28px 0 0 0;">
    <table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
      <td bgcolor="{INK}" style="background-color:{INK};">
        <a href="mailto:{CTA_MAIL}?subject=My%20FDID" style="display:inline-block;padding:16px 26px;
           font-family:{MONO};font-size:13px;font-weight:bold;letter-spacing:1.5px;
           text-transform:uppercase;color:{STOCK};text-decoration:none;">{esc(CTA)}</a>
      </td></tr></table>
    <p style="margin:12px 0 0 0;font-family:{BODY};font-size:14px;line-height:21px;color:{INK};">{esc(CTA_UNDER)}</p>
  </td></tr>

  <tr><td style="padding:26px 0 0 0;">
    <p style="margin:0;font-family:{BODY};font-size:15px;line-height:23px;color:{INK};">{esc(PS)}</p>
    <p style="margin:12px 0 0 0;font-family:{BODY};font-size:15px;line-height:23px;color:{INK};">EMR Inc.</p>
  </td></tr>

  <tr><td style="padding:26px 0 0 0;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-top:3px solid {INK};">
      <tr><td style="padding:12px 0 0 0;font-family:{MONO};font-size:11px;line-height:17px;color:{INK};">
        Source: NFIRS basic incident module, pulled {PULLED}. {esc(GUARD)}<br>
        {fmt(DENOMINATOR)} of {fmt(TOTAL_ROWS)} rows; {DROPPED} carry a non numeric incident type.<br>
        EMR Inc. &#183; Emergency Medical Resolutions. Individual records belong to the member.<br>
        <a href="#" style="color:{INK};text-decoration:underline;">Manage preferences</a> &#183;
        <a href="#" style="color:{INK};text-decoration:underline;">Unsubscribe</a>
      </td></tr></table>
  </td></tr>

</table>
</td></tr></table>
</body></html>
'''


def email_txt(d, alt):
    return f"""EMR INC. FIELD NOTES / {ISSUE}
{SUBJECT}

{HOOK}

  {BIG} {BIG_UNDER}

{DEK}

{GUARD} {fmt(DENOMINATOR)} incidents, {FDIDS} departments.
Fire {d['fire_pct']:.2f}%. Rescue and EMS {d['ems_pct']:.2f}%.
A building fire is 1 in {d['one_in']:.0f} incidents.

{PARA}

{CTA.upper()}: reply to this email with your FDID.
{CTA_UNDER}

{PS}

EMR Inc.

--
Source: NFIRS basic incident module, pulled {PULLED}. {GUARD}
{fmt(DENOMINATOR)} of {fmt(TOTAL_ROWS)} rows; {DROPPED} carry a non numeric incident type.
Individual records belong to the member.
Manage preferences / Unsubscribe
"""


# --------------------------------------------------------------------- gates ---

def assert_guard(**docs):
    for name, text in docs.items():
        low = text.lower()
        for needle in ("florida only", "not a national record"):
            if needle not in low:
                sys.exit(f"GUARD MISSING from {name}: {needle!r}. Nothing is written.")


FORBIDDEN = [(r"@import", "Gmail strips @import"),
             (r"::(before|after)", "Gmail drops pseudo elements"),
             (r"display\s*:\s*(flex|grid)", "Outlook ignores flex and grid"),
             (r"var\(--", "Outlook ignores custom properties"),
             (r"\d(vh|vw)\b", "viewport units are unreliable in mail"),
             (r"clamp\(", "clamp() is unreliable in mail"),
             (r"position\s*:\s*(absolute|fixed|sticky)", "positioning is unreliable"),
             (r"<style", "a style block is stripped by several clients")]

# docs/ux_copy.md and brand_guidelines.md. A banned word in a send to the whole
# CRM list is not a thing to catch in review.
BANNED = ["wellness", "hero", "heroes", "brave", "revolutionary", "seamless",
          "empower", "game changer", "cutting edge", "unlock", "compliance tool",
          "wearable", "injury risk index", "thin red line", "diagnose",
          "predict cancer", "users", "our community"]


def assert_voice(*texts):
    blob = " ".join(texts)
    low = blob.lower()
    for w in BANNED:
        if re.search(rf"\b{re.escape(w)}\b", low):
            sys.exit(f"BANNED WORD in copy: {w!r}. See brand_guidelines.md.")
    # "No hyphens and no em dashes", docs/ux_copy.md constraint 1. Checked on the
    # prose only, since CSS and URLs legitimately carry hyphens.
    prose = " ".join([SUBJECT, PREHEADER, HOOK, BIG_UNDER, DEK, PARA, CTA,
                      CTA_UNDER, PS, GUARD])
    for ch in ("—", "–"):
        if ch in prose:
            sys.exit("em dash or en dash in prose; use a colon or restructure")
    if re.search(r"[a-z]-[a-z]", prose, re.I):
        sys.exit(f"hyphen in prose: {prose}")
    if "!" in prose:
        sys.exit("exclamation mark in prose; this audience reads it as a sales tell")


def assert_email_safe(h):
    bad = [why for pat, why in FORBIDDEN if re.search(pat, h, re.I)]
    if bad:
        sys.exit("email.html breaks in real clients:\n  " + "\n  ".join(bad))
    n = len(h.encode())
    if n > 102_400:
        sys.exit(f"email.html is {n:,} bytes; Gmail clips above 102,400")
    return n


def main():
    d = derive()
    svg, segs = figure()
    alt = (f"Fire is {d['fire_pct']:.2f}% of every incident Florida filed from "
           f"{FIRST} to {LAST}, and rescue and EMS is {d['ems_pct']:.2f}%. "
           f"{GUARD} {fmt(DENOMINATOR)} incidents across {FDIDS} departments, "
           f"drawn at true proportion in NFIRS code order. A building fire is one "
           f"in {d['one_in']:.0f} incidents and a false alarm is "
           f"{d['alarm_ratio']:.2f} times more likely than any fire at all.")

    (ROOT / "02-figure.svg").write_text(svg)
    gap, fill, stem, away = render(ROOT / "02-figure.svg", ROOT / "02-figure.png", segs)

    eh, et = email_html(d, alt), email_txt(d, alt)
    assert_guard(figure_svg=svg, email_html=eh, email_txt=et, alt=alt)
    assert_voice(SUBJECT, PREHEADER, HOOK, DEK, PARA, CTA, CTA_UNDER, PS)
    nbytes = assert_email_safe(eh)

    (ROOT / "02-email.html").write_text(eh)
    (ROOT / "02-email.txt").write_text(et)

    words = len(" ".join([HOOK, DEK, PARA, CTA_UNDER, PS]).split())
    for n in ("02-figure.svg", "02-figure.png", "02-figure-mono.png",
              "02-email.html", "02-email.txt"):
        print(f"  {n:22s} {(ROOT / n).stat().st_size:>8,} bytes")
    print(f"\n  subject:  {SUBJECT}")
    print(f"  body copy: {words} words, one paragraph, one button, one ask")
    print(f"  mono gate 1 divider {gap} vs fill {fill}")
    print(f"  mono gate 2 bracket {stem} vs stock {away}")
    print(f"  voice gate: {len(BANNED)} banned terms, no hyphen, no em dash, no '!'")
    print(f"  email.html {nbytes:,} bytes")
    print(f"  guard in figure, html, txt and alt text")


if __name__ == "__main__":
    main()
