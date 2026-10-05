"""
Study 03. Three ways to hold the same three sections.

Issue 01 ships as three hard edged full bleed fields: stock, ink, stock. It
works, but it is one answer, and a weekly email that looks identical every week
stops being looked at. docs/visual_variation_protocol.md exists for this reason.

The constraint is that an email is not a canvas. No flex, no grid, no custom
properties, no style block, no positioning, tables only, every style inlined,
and the whole thing under the 102,400 bytes where Gmail clips. A layout idea
that cannot survive that is not a layout idea. So each variant here is real
HTML, rendered at the width a client actually gives it, and checked.

    python3 studies/layout.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import lab
from lab import TOKENS, at_value, tonal_capacity

OUT = Path(__file__).resolve().parent / "out"
STOCK, INK = TOKENS["stock"], TOKENS["ink"]
RED = TOKENS["red"]
CAP = tonal_capacity()
PALE = at_value("blue", CAP["values"][1])

EMAIL_W = 600          # the width every mail client gives a table
SHOT_H = 1500          # tall enough to catch the whole body
DISPLAY = "Archivo Black, Archivo, Arial, sans-serif"
MONO = "Courier Prime, Courier New, monospace"
BODY = "Archivo, Arial, Helvetica, sans-serif"

SECTIONS = [
    ("01 / dear chief", "DEAR CHIEF.",
     "Your engine has a file. Every pump test since the day it was delivered. "
     "Your people have a hire date and an emergency contact."),
    ("02 / the number", "1.58% WAS FIRE.",
     "All of it. Structure, brush, car, dumpster, and the pan somebody had "
     "already smothered with a lid before you got there."),
    ("03 / we heard you", "POST EMS WORLD.",
     "Four things came up at the booth more than anything else, and one of them "
     "we are still thinking about."),
]


def shell(body):
    return ('<!doctype html><html><head><meta charset="utf-8">'
            f'</head><body style="margin:0;padding:0;background-color:{STOCK};">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'border="0" bgcolor="{STOCK}"><tr><td align="center">'
            f'<table role="presentation" width="{EMAIL_W}" cellpadding="0" '
            f'cellspacing="0" border="0" style="width:{EMAIL_W}px;">{body}'
            '</table></td></tr></table></body></html>')


def variant_fields():
    """As shipped. Three full bleed fields, alternating stock and ink."""
    rows = []
    for i, (kicker, head, text) in enumerate(SECTIONS):
        dark = i == 1
        bg, fg = (INK, STOCK) if dark else (STOCK, INK)
        kick = STOCK if dark else RED
        rows.append(
            f'<tr><td bgcolor="{bg}" style="background-color:{bg};padding:40px 28px;">'
            f'<p style="margin:0 0 8px 0;font-family:{MONO};font-size:11px;'
            f'font-weight:bold;letter-spacing:1.6px;text-transform:uppercase;'
            f'color:{kick};">{kicker}</p>'
            f'<h1 style="margin:0 0 14px 0;font-family:{DISPLAY};font-size:38px;'
            f'line-height:38px;letter-spacing:-1.6px;color:{fg};">{head}</h1>'
            f'<p style="margin:0;font-family:{BODY};font-size:16px;line-height:25px;'
            f'color:{fg};">{text}</p></td></tr>')
    return shell("".join(rows))


def variant_index():
    """
    Sutnar. The issue opens with a designed contents block, so a reader knows
    what they are holding before they start, and can go to section three first.
    """
    idx = "".join(
        f'<tr><td width="34" style="padding:5px 0;font-family:{MONO};font-size:13px;'
        f'font-weight:bold;color:{RED};">{i+1}</td>'
        f'<td style="padding:5px 0;font-family:{MONO};font-size:13px;color:{INK};">'
        f'{kicker.split("/")[1].strip()}</td></tr>'
        for i, (kicker, _, _) in enumerate(SECTIONS))
    head = (f'<tr><td style="padding:30px 28px 10px 28px;">'
            f'<p style="margin:0 0 4px 0;font-family:{MONO};font-size:11px;'
            f'font-weight:bold;letter-spacing:1.8px;color:{RED};">EMR INC. FIELD NOTES</p>'
            f'<p style="margin:0 0 18px 0;font-family:{MONO};font-size:11px;'
            f'letter-spacing:1.2px;color:{INK};">ISSUE 01 · IN THIS ONE</p>'
            f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
            f'width="100%" style="border-top:3px solid {INK};border-bottom:1px solid '
            f'{INK};">{idx}</table></td></tr>')
    rows = [head]
    for i, (kicker, headline, text) in enumerate(SECTIONS):
        rows.append(
            f'<tr><td style="padding:30px 28px;">'
            f'<table role="presentation" cellpadding="0" cellspacing="0" border="0">'
            f'<tr><td valign="top" width="40" style="font-family:{MONO};font-size:28px;'
            f'font-weight:bold;color:{RED};">{i+1}</td><td>'
            f'<h1 style="margin:0 0 12px 0;font-family:{DISPLAY};font-size:30px;'
            f'line-height:31px;letter-spacing:-1.2px;color:{INK};">{headline}</h1>'
            f'<p style="margin:0;font-family:{BODY};font-size:16px;line-height:25px;'
            f'color:{INK};">{text}</p></td></tr></table></td></tr>')
    return shell("".join(rows))


def variant_serial():
    """
    de Harak. A fixed masthead system where one element changes each week, so
    the series is recognisable and the issue is still distinct.
    """
    plate = (f'<tr><td bgcolor="{INK}" style="background-color:{INK};padding:0;">'
             f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
             f'border="0"><tr>'
             f'<td width="200" bgcolor="{PALE}" style="background-color:{PALE};'
             f'height:200px;font-family:{DISPLAY};font-size:84px;color:{INK};'
             f'text-align:center;vertical-align:middle;">01</td>'
             f'<td style="padding:0 24px;font-family:{MONO};font-size:12px;'
             f'line-height:19px;color:{STOCK};letter-spacing:0.6px;">'
             f'EMR INC. FIELD NOTES<br>WEEKLY<br><br>'
             f'THIS WEEK<br>1.58% WAS FIRE</td></tr></table></td></tr>')
    rows = [plate]
    for i, (kicker, headline, text) in enumerate(SECTIONS):
        rule = f'border-top:1px solid {INK};' if i else ''
        rows.append(
            f'<tr><td style="padding:26px 28px;{rule}">'
            f'<p style="margin:0 0 6px 0;font-family:{MONO};font-size:11px;'
            f'font-weight:bold;letter-spacing:1.6px;text-transform:uppercase;'
            f'color:{RED};">{kicker}</p>'
            f'<h1 style="margin:0 0 12px 0;font-family:{DISPLAY};font-size:30px;'
            f'line-height:31px;letter-spacing:-1.2px;color:{INK};">{headline}</h1>'
            f'<p style="margin:0;font-family:{BODY};font-size:16px;line-height:25px;'
            f'color:{INK};">{text}</p></td></tr>')
    return shell("".join(rows))


VARIANTS = [
    ("Three fields", "as shipped in issue 01", variant_fields),
    ("Numbered index", "Sutnar · provenance and navigation as design", variant_index),
    ("Serial plate", "de Harak · one system, one changing figure", variant_serial),
]


def trim_to_content(im, tol=10):
    """Crop away the trailing run of rows that are pure stock."""
    px = im.load()
    target = lab.rgb(STOCK)
    last = 0
    for y in range(im.height):
        for x in range(0, im.width, 7):   # sampling is enough to find the edge
            r, g, b = px[x, y]
            if abs(r - target[0]) + abs(g - target[1]) + abs(b - target[2]) > tol:
                last = y
                break
    return im.crop((0, 0, im.width, min(im.height, last + 28)))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = OUT / "_layout"
    from PIL import Image

    shots, notes = [], []
    for name, _, fn in VARIANTS:
        html = fn()
        problems = lab.check_email(html)
        notes.append((name, len(html.encode()), problems))
        png = lab.render_html(html, EMAIL_W, SHOT_H,
                              tmp / f"{name.lower().replace(' ', '-')}.png")
        im = Image.open(png).convert("RGB")
        # Trim the dead space below the body so variants compare at true length.
        # Thresholding on brightness does not work here: stock is 235 and would
        # itself read as content, which left two thirds of the sheet empty.
        # Measure distance from stock instead.
        im = trim_to_content(im)
        shots.append(im)

    gutter, cap = 36, 72
    cw, ch = EMAIL_W, max(i.height for i in shots) + cap
    sheet = Image.new("RGB", (gutter + 3 * (cw + gutter), gutter + ch + gutter),
                      lab.rgb(STOCK))
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    for i, (im, (name, use, _)) in enumerate(zip(shots, VARIANTS)):
        x = gutter + i * (cw + gutter)
        sheet.paste(im, (x, gutter))
        y = gutter + im.height + 12
        d.text((x, y), f"{i+1}. {name}", fill=lab.rgb(INK))
        d.text((x, y + 15), use, fill=lab.rgb(INK))
        n, probs = notes[i][1], notes[i][2]
        d.text((x, y + 33), f"{n:,} bytes", fill=lab.rgb(INK))
        d.text((x, y + 48), "ships" if not probs else "; ".join(probs),
               fill=lab.rgb(INK if not probs else RED))
    out = OUT / "03-layout.png"
    sheet.save(out)
    sheet.convert("L").save(out.with_name(out.stem + "-mono.png"))
    for f in tmp.glob("*.png"):
        f.unlink()
    tmp.rmdir()

    print(f"\n  study 03 · three ways to hold the same three sections\n  {'=' * 64}\n")
    for (name, use, _), (_, n, probs) in zip(VARIANTS, notes):
        state = "ships" if not probs else "BREAKS: " + "; ".join(probs)
        print(f"    {name:18s} {n:7,} bytes   {state}")
        print(f"    {'':18s} {use}")
    print(f"\n    all three are under the {lab.GMAIL_CLIP:,} byte Gmail clip, "
          f"and carry none of the {len(lab.EMAIL_FORBIDDEN)} constructs that break.")
    print(f"\n  {out}")
    print(f"  {out.with_name(out.stem + '-mono.png')}")


if __name__ == "__main__":
    main()
