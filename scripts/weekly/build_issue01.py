#!/usr/bin/env python3
"""Field Notes, issue 01. Three sections.

Structure set by the client:

  01  Dear Chief     a new letter every issue. Biting, ironic, thought provoking.
                     It is its own provocation, not a wrapper for the data.
  02  The number     one figure set large, with the data art.
  03  The update     product or business news.

Reuses build_02.py for the data layer: the same fail closed derive(), the same
figure, the same monochrome gates, the same scope guard. Only the email changes.

GUARD, unchanged: Florida only. data/nfirs-incident-composition.json states that a
count of distinct states over the table returns 1 and that this must never be
described as a national record. assert_guard() fails the build if either half of
that goes missing from any artifact a reader can reach.

Section 03 is reported from the client's own account of EMS World Expo, 28
September 2026. Four takeaways, given verbatim: mental health came up first;
people want it automatic; departments are tech forward but occupational health
blind; and one veteran asked why he would want to know. Nothing here is invented
except the phrase "one of the old heads", which characterises a person the client
described but did not name. Flag it for confirmation before send.

Mental health is written as a listening item and explicitly NOT in the beta,
because brand_guidelines.md allows a roadmap subject only when it is labelled
one, and docs/ux_copy.md forbids any clinical claim anywhere, tooltips included.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import figure_v2  # noqa: E402
from build_02 import (  # noqa: E402
    BANNED, DENOMINATOR, DISPLAY, DROPPED, FDIDS, FORBIDDEN, GUARD, INK, MONO,
    PULLED, RED, STOCK, TOTAL_ROWS, assert_guard, derive, esc, figure, fmt, render,
)

ROOT = Path(__file__).resolve().parent
BODY = "Archivo, Arial, Helvetica, sans-serif"
ISSUE = "01"

SUBJECT = "Your engine has a better file than your firefighters"
PREHEADER = ("Fire is 1.58% of the job. Plus what we heard at EMS World, and the beta "
             "is open to look at.")

# ------------------------------------------------------- 01 / dear chief ---
# The irony is structural and verifiable: apparatus maintenance records are
# mandated and kept for the life of the rig. There is no equivalent for the
# person. That gap is the company's entire founding thesis, argued here without
# naming the product once.
LETTER = [
    "Your engine has a file.",

    "Every pump test since the day it was delivered. Every oil change. Every "
    "length of hose that failed a pressure test, and the date it got replaced. "
    "If that truck ever hurts somebody, you can reconstruct its whole life in an "
    "afternoon.",

    "Your people have a hire date and an emergency contact.",

    "Nobody sat down and decided that. It just settled that way. The truck costs "
    "nine hundred thousand dollars, so somebody wrote a rule. The person costs "
    "nothing to replace, because there is always another list.",

    "The apparatus is better documented than the firefighter. That is not a "
    "scandal. It is a choice your service makes every morning by not making it.",
]
LETTER_SIGN = "EMR Inc."

# ---------------------------------------------------------- 02 / the number ---
BIG, BIG_UNDER = "1.58%", "was fire."
DEK = ("All of it. Structure, brush, car, dumpster, and the pan somebody had "
       "already smothered with a lid before you got there.")
TURN = ("Here is the part that stings. When you walk into budget season, the "
        "record they pull describes a rescue service: 72.42% of what your people "
        "ran was rescue and EMS. Your staffing argument describes a fire "
        "department. Both are true. Only one of them is written down.")

# ---------------------------------------------------------- 03 / the update ---
UPDATE_LEDE = ("We just got back from EMS World Expo. Four things came up at the "
               "booth more than anything else.")
UPDATE = [
    ("Mental health.", "We did not expect it to be the first question, and it was, "
     "over and over. Sleep, call load, the back half of a 24. It is not in the "
     "beta. It is on the list now."),
    ("Automatic or do not bother.", "Nobody wants another form. Agreed: exposure "
     "comes off dispatch data, not off you remembering to log it."),
    ("Tech forward, occupational health blind.", "Plenty of departments showed us "
     "real technology. Almost none of it was pointed at what the job does to the "
     "people doing it."),
    ("And the one we keep thinking about.", "One of the old heads looked at a "
     "filled in record and asked, why would I want to know that?"),
]
UPDATE_CLOSE = ("Fair question. Maybe you would not. The file is not really for "
                "you. It is for whoever goes looking in 2041 and finds out nobody "
                "wrote it down.")

# An earlier note here said a cid: reference "did not resolve in Gmail". That was
# wrong, and worth recording as wrong. Those were sends through the Gmail API,
# whose sanitizer deletes the whole <img> element. Nothing was left for the cid
# to resolve to. MailApp does not sanitize, so cid works there as it does
# everywhere else. GitHub raw really is unusable, for a different reason: it
# sends "content-security-policy: default-src 'none'; sandbox", so Gmail's image
# proxy refuses it.
#
# The figure travels INSIDE the message as an inline attachment, not as a link
# to a hosted file. Two reasons, both learned the hard way.
#
# One, a hosted url has to actually be published. assets/ pushed to main does not
# reach emr-inc.net: the site deploys only from the open_data_daily workflow,
# which fires on a schedule or on pushes touching three unrelated paths. The
# figure sat on main, unpublished and 404ing, while the email pointed at it.
#
# Two, even a working url is blocked by default in Gmail and Outlook for a large
# share of recipients, so the figure would silently vanish for people we never
# hear from. An inline image carries no tracking risk and is shown without asking.
#
# The sender attaches the png as cid:figure. See issueFiles_() in Code.gs.
FIGURE_CID = "figure"

# The masthead image, optional. Same cid mechanism and the same reason: a hosted
# header would be unpublished or blocked exactly as the figure was.
#
# It sits ABOVE the wordmark rather than replacing it. The publication name and
# issue number stay as live text, so a recipient with images off still knows what
# this is and which issue, and a screen reader reads a name rather than a
# filename. The image is decorative, which is also why its alt text describes it
# in one line instead of restating the masthead.
HEADER_CID = "header"
HEADER_ALT = ("Torn paper collage in blue and orange on cream: a fire station "
              "with the apparatus bay open, a hose coupling, a radio and turnout "
              "gear.")

CTA = "See the platform"
CTA_URL = "https://beta.expectvictims.com"
CTA_UNDER = ("That link is the beta. Have a look before anyone else does.")
PS = "Next week: the 3.84 false alarms you run for every fire. Bring coffee."

MISSION_KICKER = "What we are doing"
MISSION = ("EMR Inc. builds the exposure record the fire service never kept. "
           "Shift by shift, from dispatch data rather than memory. It belongs to "
           "the member, not the department.")

# A second door. The button above points at one beta; this points at everything
# else, for the reader who wants the research rather than the app. It sits inside
# the mission panel on purpose: that block is already the "who we are" block, so
# it does not compete with the beta CTA for the same click.
#
# The lead is prose and goes through assert_voice(). The domain does not, for the
# same reason CTA_URL does not: an address is not prose, and the hyphen in
# "EMR-Inc.net" is part of the name rather than a hyphen the style rule is about.
SUITE_LEAD = "Find out more about our full product and research suite at"
SUITE_DOMAIN = "EMR-Inc.net"
SUITE_URL = "https://emr-inc.net"

# A named human to write back to. The sender already sets replyTo, so Reply works
# without this, but a visible address is what makes a reader believe a person is
# on the other end, and it survives being forwarded out of the original thread.
#
# The subject is prefilled so replies land sorted by issue. If a client drops the
# query string it degrades to a blank compose to the right address, which is why
# the subject carries no information the message needs.
ASK_LEAD = "Questions, or an argument with any of this, go straight to"
ASK_EMAIL = "michael.harvey@emr-inc.net"
ASK_URL = f"mailto:{ASK_EMAIL}?subject=Field%20Notes%20{ISSUE}"


def label(t):
    return (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'border="0"><tr><td style="padding:0 0 7px 0;font-family:{MONO};'
            f'font-size:11px;line-height:16px;font-weight:bold;letter-spacing:1.6px;'
            f'text-transform:uppercase;color:{RED}">{esc(t)}</td></tr></table>')


def rule():
    return (f'<tr><td style="padding:34px 0 0 0;"><table role="presentation" '
            f'width="100%" cellpadding="0" cellspacing="0" border="0" '
            f'style="border-top:2px solid {INK};"><tr><td style="font-size:0;'
            f'line-height:0;">&nbsp;</td></tr></table></td></tr>')


WITH_HEADER = True


def email_html(d, alt):
    """Three hard edged fields, not one even column.

    design_system.md: "Generous stock colored space is part of the system. Cards
    are not the default organizing device." So the division is done by changing
    the ground, not by boxing things. The letter and the update sit on stock; the
    data sits on a full bleed ink field, and the figure lands on it as a cream
    plate. That inversion is the reference set's move: a bright specimen against
    a black ground, with the one saturated accent living inside the specimen.

    One boundary per group. The field change is the boundary, so the letter loses
    the left rule it used to carry and gets space instead.
    """
    paras = "".join(
        f'<p style="margin:0 0 15px 0;font-family:{BODY};font-size:17px;'
        f'line-height:27px;color:{INK};">{esc(t)}</p>' for t in LETTER)
    items = "".join(
        f'<p style="margin:0 0 13px 0;font-family:{BODY};font-size:16px;'
        f'line-height:25px;color:{INK};"><strong>{esc(h)}</strong> {esc(b)}</p>'
        for h, b in UPDATE)

    def kick(t, on_ink=False):
        c = STOCK if on_ink else RED
        return (f'<p style="margin:0 0 8px 0;font-family:{MONO};font-size:11px;'
                f'line-height:16px;font-weight:bold;letter-spacing:1.6px;'
                f'text-transform:uppercase;color:{c};">{esc(t)}</p>')

    def field(bg, inner, pad="40px 0 44px 0"):
        return (f'<tr><td align="center" bgcolor="{bg}" style="background-color:{bg};'
                f'padding:0 12px;"><table role="presentation" width="600" cellpadding="0" '
                f'cellspacing="0" border="0" style="width:600px;max-width:600px;">'
                f'<tr><td style="padding:{pad};">{inner}</td></tr></table></td></tr>')

    # Spans the full 600px column. Not literally full bleed: it sits inside the
    # section cell, so it keeps that cell's 24px above it and the outer 12px at
    # each side. That is deliberate. A torn edge jammed against the viewport edge
    # reads as a rendering fault rather than as a torn edge, and the 12px gutter
    # is what stops the email touching the sides on a phone.
    header_img = (
      f'<img src="cid:{HEADER_CID}" width="600" alt="{esc(HEADER_ALT)}" '
      f'style="display:block;width:100%;max-width:600px;height:auto;" border="0">'
      if WITH_HEADER else '')

    masthead = (
      header_img
      + f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
      f'border="0" style="border-top:4px solid {INK};"><tr>'
      f'<td align="left" style="padding:9px 0 9px 0;font-family:{DISPLAY};font-size:14px;'
      f'font-weight:bold;letter-spacing:1.3px;color:{INK};">EMR INC. FIELD NOTES</td>'
      f'<td align="right" style="padding:9px 0 9px 0;font-family:{MONO};font-size:11px;'
      f'font-weight:bold;letter-spacing:1.5px;color:{RED};">ISSUE {esc(ISSUE)}</td>'
      f'</tr></table>'
      f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
      f'style="border-top:1px solid {INK};"><tr><td style="font-size:0;line-height:0;">'
      f'&nbsp;</td></tr></table>')

    letter = (masthead + '<div style="height:34px;line-height:34px;font-size:0;">&nbsp;</div>'
      + kick("01 / dear chief")
      + f'<h1 style="margin:0 0 20px 0;font-family:{DISPLAY};font-size:46px;line-height:44px;'
        f'font-weight:bold;letter-spacing:-2px;text-transform:uppercase;color:{INK};">'
        f'DEAR CHIEF.</h1>' + paras
      + f'<p style="margin:18px 0 0 0;font-family:{BODY};font-size:15px;line-height:23px;'
        f'color:{INK};">{esc(LETTER_SIGN)}</p>')

    number = (kick("02 / the number", True)
      + f'<p style="margin:0;font-family:{DISPLAY};font-size:104px;line-height:92px;'
        f'font-weight:bold;letter-spacing:-5px;color:{STOCK};">{esc(BIG)}</p>'
      + f'<p style="margin:4px 0 0 0;font-family:{DISPLAY};font-size:40px;line-height:42px;'
        f'font-weight:bold;letter-spacing:-1.5px;color:{STOCK};">{esc(BIG_UNDER)}</p>'
      + f'<p style="margin:18px 0 26px 0;font-family:{BODY};font-size:17px;line-height:27px;'
        f'color:{STOCK};">{esc(DEK)}</p>'
      + f'<img src="cid:{FIGURE_CID}" width="600" alt="{esc(alt)}" style="display:block;'
        f'width:100%;max-width:600px;height:auto;" border="0">'
      + f'<p style="margin:26px 0 0 0;font-family:{BODY};font-size:17px;line-height:27px;'
        f'color:{STOCK};">{esc(TURN)}</p>')

    update = (kick("03 / we heard you")
      + f'<h2 style="margin:0 0 16px 0;font-family:{DISPLAY};font-size:30px;line-height:32px;'
        f'font-weight:bold;letter-spacing:-1px;text-transform:uppercase;color:{INK};">'
        f'POST EMS WORLD.</h2>'
      + f'<p style="margin:0 0 16px 0;font-family:{BODY};font-size:17px;line-height:27px;'
        f'color:{INK};">{esc(UPDATE_LEDE)}</p>' + items
      + f'<p style="margin:4px 0 30px 0;font-family:{BODY};font-size:17px;line-height:27px;'
        f'color:{INK};">{esc(UPDATE_CLOSE)}</p>'
      + f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>'
        f'<td bgcolor="{INK}" style="background-color:{INK};">'
        f'<a href="{CTA_URL}" style="display:inline-block;padding:17px 28px;'
        f'font-family:{MONO};font-size:13px;font-weight:bold;letter-spacing:1.5px;'
        f'text-transform:uppercase;color:{STOCK};text-decoration:none;">{esc(CTA)}</a>'
        f'</td></tr></table>'
      + f'<p style="margin:12px 0 0 0;font-family:{BODY};font-size:14px;line-height:21px;'
        f'color:{INK};">{esc(CTA_UNDER)}</p>'
      + f'<p style="margin:26px 0 0 0;font-family:{BODY};font-size:15px;line-height:23px;'
        f'color:{INK};">{esc(PS)}</p>'
      + f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'border="0" bgcolor="{INK}" style="background-color:{INK};margin-top:30px;">'
        f'<tr><td style="padding:24px 22px 26px 22px;">'
        f'<p style="margin:0 0 8px 0;font-family:{MONO};font-size:11px;line-height:16px;'
        f'font-weight:bold;letter-spacing:1.6px;text-transform:uppercase;color:{RED};">'
        f'{esc(MISSION_KICKER)}</p>'
        f'<p style="margin:0;font-family:{BODY};font-size:19px;line-height:29px;'
        f'color:{STOCK};">{esc(MISSION)}</p>'
        f'<p style="margin:15px 0 0 0;font-family:{BODY};font-size:16px;'
        f'line-height:25px;color:{STOCK};">{esc(SUITE_LEAD)}<br>'
        f'<a href="{SUITE_URL}" style="color:{STOCK};text-decoration:underline;">'
        f'{esc(SUITE_DOMAIN)}</a></p>'
        f'<p style="margin:9px 0 0 0;font-family:{BODY};font-size:16px;'
        f'line-height:25px;color:{STOCK};">{esc(ASK_LEAD)}<br>'
        f'<a href="{ASK_URL}" style="color:{STOCK};text-decoration:underline;">'
        f'{esc(ASK_EMAIL)}</a></p></td></tr></table>'
      + f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" '
        f'style="border-top:3px solid {INK};margin-top:26px;"><tr>'
        f'<td style="padding:12px 0 0 0;font-family:{MONO};font-size:11px;line-height:17px;'
        f'color:{INK};">Figure source: NFIRS basic incident module, pulled {PULLED}. '
        f'{esc(GUARD)}<br>{fmt(DENOMINATOR)} of {fmt(TOTAL_ROWS)} rows; {DROPPED} carry a '
        f'non numeric incident type.<br>EMR Inc. &#183; Emergency Medical Resolutions. '
        f'Individual records belong to the member.<br>'
        f'{{{{POSTAL_ADDRESS}}}}<br>'
        f'{{{{WHY_YOU_GET_THIS}}}} '
        f'<a href="{{{{UNSUBSCRIBE_URL}}}}" style="color:{INK};text-decoration:underline;">'
        f'Unsubscribe</a></td></tr></table>')

    return f'''<!doctype html>
<html lang="en" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="x-apple-disable-message-reformatting">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<title>{esc(SUBJECT)}</title>
<!--[if mso]><xml><o:OfficeDocumentSettings><o:PixelsPerInch>96</o:PixelsPerInch></o:OfficeDocumentSettings></xml><![endif]-->
</head>
<body style="margin:0;padding:0;background-color:{STOCK};">
<div style="display:none;font-size:1px;color:{STOCK};line-height:1px;max-height:0;max-width:0;opacity:0;overflow:hidden;">{esc(PREHEADER)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" bgcolor="{STOCK}" style="background-color:{STOCK};">
{field(STOCK, letter, "24px 0 48px 0")}
{field(INK, number, "48px 0 52px 0")}
{field(STOCK, update, "48px 0 40px 0")}
</table>
</body></html>
'''


def email_txt(d):
    import textwrap
    wrap = lambda t: textwrap.fill(t, 72)
    letter = "\n\n".join(wrap(t) for t in LETTER)
    items = "\n\n".join(wrap(f"{h} {b}") for h, b in UPDATE)
    return f"""EMR INC. FIELD NOTES / ISSUE {ISSUE}
{SUBJECT}

01 / DEAR CHIEF.

{letter}

{LETTER_SIGN}

------------------------------------------------------------------------

02 / THE NUMBER

  {BIG} {BIG_UNDER}

{wrap(DEK)}

{GUARD} {fmt(DENOMINATOR)} incidents, {FDIDS} departments.
Fire {d['fire_pct']:.2f}%. Rescue and EMS {d['ems_pct']:.2f}%.
A building fire is 1 in {d['one_in']:.0f} incidents.

{wrap(TURN)}

------------------------------------------------------------------------

03 / WE HEARD YOU. POST EMS WORLD.

{wrap(UPDATE_LEDE)}

{items}

{wrap(UPDATE_CLOSE)}

{CTA.upper()}: {CTA_URL}
{wrap(CTA_UNDER)}

{PS}

{MISSION_KICKER.upper()}
{wrap(MISSION)}

{SUITE_LEAD} {SUITE_URL}
{ASK_LEAD} {ASK_EMAIL}

--
Figure source: NFIRS basic incident module, pulled {PULLED}. {GUARD}
{fmt(DENOMINATOR)} of {fmt(TOTAL_ROWS)} rows; {DROPPED} carry a non numeric incident type.
EMR Inc. Individual records belong to the member.
{{{{POSTAL_ADDRESS}}}}

{{{{WHY_YOU_GET_THIS}}}}
To stop receiving Field Notes: {{{{UNSUBSCRIBE_URL}}}}
"""


def prose():
    """Every rendered string a reader sees, for the voice gate."""
    flat = [SUBJECT, PREHEADER, *LETTER, LETTER_SIGN, BIG, BIG_UNDER, DEK, TURN,
            UPDATE_LEDE, *[h for h, _ in UPDATE], *[b for _, b in UPDATE],
            UPDATE_CLOSE, CTA, CTA_UNDER, PS, MISSION_KICKER, MISSION,
            SUITE_LEAD, ASK_LEAD, GUARD,
            "DEAR CHIEF.", "POST EMS WORLD."]
    return " ".join(flat)


def assert_voice():
    blob = prose()
    low = blob.lower()
    for w in BANNED:
        if re.search(rf"\b{re.escape(w)}\b", low):
            sys.exit(f"BANNED WORD in copy: {w!r}. See brand_guidelines.md.")
    for ch in ("—", "–"):
        if ch in blob:
            sys.exit("em dash or en dash in prose; use a colon or restructure")
    m = re.search(r"\w-\w", blob)
    if m:
        sys.exit(f"hyphen in prose near: {blob[max(0, m.start()-40):m.start()+40]!r}")
    if "!" in blob:
        sys.exit("exclamation mark in prose; this audience reads it as a sales tell")
    # docs/ux_copy.md terminology table: one word per thing, everywhere.
    for bad, use in (("run report", "incident"), ("users", "member"),
                     ("wellness", "occupational health")):
        if bad in low:
            sys.exit(f"terminology: {bad!r} should be {use!r}")
    return len(BANNED)


def assert_sendable(h, t):
    """The Apps Script sender refuses to run without these, so the build must
    never hand it an artifact that cannot lawfully go to a list."""
    for name, doc in (("email.html", h), ("email.txt", t)):
        for token in ("{{UNSUBSCRIBE_URL}}", "{{POSTAL_ADDRESS}}",
                          "{{WHY_YOU_GET_THIS}}"):
            if token not in doc:
                sys.exit(f"{name} is missing {token}; it could not be sent to a list")
    if 'href="#"' in h:
        sys.exit('email.html still carries a href="#" placeholder link')


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
    svg, geom = figure_v2.build()
    alt = (f"A square stands for all {fmt(DENOMINATOR)} incidents Florida filed from "
           f"2020 to 2025. Rescue and EMS floods {d['ems_pct']:.2f}% of it from the "
           f"bottom. Fire is a small square covering {d['fire_pct']:.2f}% of the area, "
           f"straddling the rescue horizon so the two inks overprint. {GUARD}")

    checks = figure_v2.render(svg, geom)

    eh, et = email_html(d, alt), email_txt(d)
    assert_guard(figure_svg=svg, email_html=eh, email_txt=et, alt=alt)
    nbanned = assert_voice()
    assert_sendable(eh, et)
    nbytes = assert_email_safe(eh)

    (ROOT / "01-email.html").write_text(eh)
    (ROOT / "01-email.txt").write_text(et)

    sec = {"01 letter": sum(len(t.split()) for t in LETTER),
           "02 number": len((DEK + " " + TURN).split()),
           "03 update": len((UPDATE_LEDE + " " + UPDATE_CLOSE).split())
                        + sum(len((h + " " + b).split()) for h, b in UPDATE)}
    for n in ("01-figure.svg", "01-figure.png", "01-figure-mono.png",
              "01-email.html", "01-email.txt"):
        print(f"  {n:18s} {(ROOT / n).stat().st_size:>8,} bytes")
    print(f"\n  subject: {SUBJECT}")
    for k, v in sec.items():
        print(f"  {k}: {v} words")
    print(f"  total body copy: {sum(sec.values())} words")
    for n, a, b in checks:
        print(f"  mono gate {n:26s} {a:3d} vs {b:3d}")
    print(f"  voice gate: {nbanned} banned terms, no hyphen, em dash or '!'")
    print(f"  email.html {nbytes:,} bytes (Gmail clips at 102,400)")
    print(f"  guard in figure, html, txt and alt text")
    print(f"  unsubscribe and postal address placeholders present")


if __name__ == "__main__":
    main()
