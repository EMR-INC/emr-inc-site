#!/usr/bin/env python3
"""Field Notes issue 01, figure v2. Bounded comparison drawn as a scale jump.

Structure, per design_system.md: bounded comparison. One square is the whole
record. Area is the encoding, so a fraction of the area is a fraction of the
incidents and nothing is magnified.

Primary move, BEALL: flat forms make the claim legible at distance. One square,
one flood, one small square, read in a thumbnail.

Secondary accent, HUBER: controlled overprint. design_system.md permits it in
its own words, "a transparent overlap may create an additional apparent color
when the contributing layers remain clear". The fire square straddles the
rescue horizon, so its lower half prints over the blue field.

That overprint is not decoration, it is what makes the figure legal. Red and
blue are 88 and 87 in perceived value, so a red square sitting on a blue field
is invisible in greyscale. Multiplied, the overlap drops to 19 and separates
from both. The half above the horizon separates against stock. So each half of
the fire square is carried by a different contrast, and the diagram survives
colour being removed, which design_system.md requires.

From the reference set: the scale jump, hard horizon, one saturated accent as a
pure primitive, and generous stock ground. Composition only. No halftone, no
stipple, no 1 bit tone. That vocabulary is the retired Spotlight system and
brain.md 2026 08 27 records that merging the two produces something that
belongs to neither.
"""
from __future__ import annotations
import subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
STOCK, INK, RED, BLUE = "#F1EBDD", "#10213B", "#D5222A", "#2363A0"
DISPLAY = "Archivo Black, Archivo, Arial, sans-serif"
MONO = "Courier Prime, Courier New, monospace"

DENOM, FIRE_PCT, EMS_PCT = 18_251_127, 1.58, 72.42
FIRE_N, EMS_N, FDIDS = 289_121, 13_217_940, 396
GUARD = "Florida only, 2020 through 2025. Not a national record."

W, H = 1200, 910
M, S = 70, 560                      # margin, square side
X0, Y0 = M, 180                     # square top left
TYPE_X = 700

def rgb(h): return tuple(int(h[i:i+2], 16) for i in (1, 3, 5))
def hx(t): return "#%02X%02X%02X" % tuple(round(c) for c in t)
def gray(h):
    r, g, b = rgb(h); return 0.299*r + 0.587*g + 0.114*b
def multiply(a, b):
    """Two transparent inks on one sheet. This is what overprint actually does."""
    return hx(tuple(x*y/255 for x, y in zip(rgb(a), rgb(b))))

OVER = multiply(RED, BLUE)

def build():
    blue_h = EMS_PCT / 100 * S
    hz = Y0 + S - blue_h                       # the rescue horizon
    fire_s = (FIRE_PCT / 100) ** 0.5 * S       # AREA proportional, not height
    fx = X0 + S * 0.56
    fy = hz - fire_s / 2                       # straddles the horizon
    rest_pct = 100 - EMS_PCT
    rest_n = DENOM - EMS_N
    p = []

    def t(x, y, s, size, fam=MONO, fill=INK, w="bold", a="start", ls="1.4"):
        p.append(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" '
                 f'font-weight="{w}" fill="{fill}" text-anchor="{a}" '
                 f'letter-spacing="{ls}">{s}</text>')

    p.append(f'<rect x="0" y="0" width="{W}" height="6" fill="{INK}"/>')

    # The figure has to say what it is on its own, because it travels: forwarded,
    # screenshotted, pasted into a budget deck with none of the email around it.
    # Mono at a given size has a fixed advance, so a line that outruns the margin
    # is silently clipped by the viewBox rather than wrapped. Three lines shipped
    # clipped once already; now an overrun fails the build.
    def mono(x, y, txt, size=19, fill=INK, w="normal", ls=0.4):
        if x + len(txt) * (size * 0.6 + ls) > W - M:
            sys.exit(f"figure text overruns the right margin: {txt!r}")
        t(x, y, txt, size, MONO, fill, w, ls=str(ls))

    t(M, 54, "WHAT A FIRE DEPARTMENT ACTUALLY RUNS", 34, DISPLAY, INK, "bold", ls="-0.6")
    mono(M, 88,  "Every incident Florida filed, 2020 to 2025, by NFIRS incident type.")
    mono(M, 112, f"{DENOM:,} incidents across {FDIDS} departments. One square is the whole record.")
    mono(M, 136, "Area is the encoding: a share of the area is a share of the incidents.")

    p.append(f'<rect x="{X0}" y="{Y0}" width="{S}" height="{S}" fill="{STOCK}" '
             f'stroke="{INK}" stroke-width="3"/>')
    p.append(f'<rect x="{X0}" y="{hz:.1f}" width="{S}" height="{blue_h:.1f}" fill="{BLUE}"/>')
    # fire, in two halves so the overprint is explicit geometry and not a filter
    p.append(f'<rect x="{fx:.1f}" y="{fy:.1f}" width="{fire_s:.2f}" '
             f'height="{fire_s/2:.2f}" fill="{RED}"/>')
    p.append(f'<rect x="{fx:.1f}" y="{hz:.1f}" width="{fire_s:.2f}" '
             f'height="{fire_s/2:.2f}" fill="{OVER}"/>')
    p.append(f'<rect x="{X0}" y="{Y0}" width="{S}" height="{S}" fill="none" '
             f'stroke="{INK}" stroke-width="3"/>')
    p.append(f'<line x1="{X0}" y1="{hz:.1f}" x2="{X0+S}" y2="{hz:.1f}" '
             f'stroke="{INK}" stroke-width="2"/>')

    # Leader from the fire square to its key entry. It terminates on the square at
    # one end and on the legend at the other: design_system.md fails a diagram
    # whose line ends in empty space.
    ly = fy + fire_s / 2
    p.append(f'<line x1="{fx+fire_s:.1f}" y1="{ly:.1f}" x2="{TYPE_X-14}" y2="{ly:.1f}" '
             f'stroke="{INK}" stroke-width="2"/>')

    # The legend. Every region of the square gets an entry, and the entries sum to
    # the denominator, so nothing in the drawing is left unaccounted for.
    KEY = [("RESCUE AND EMS", EMS_PCT, EMS_N, BLUE, None),
           ("EVERYTHING ELSE", rest_pct, rest_n, STOCK, INK),
           ("ALL FIRE", FIRE_PCT, FIRE_N, RED, None)]
    ky = 196
    for label, pct, n, fill, stroke in KEY:
        p.append(f'<rect x="{TYPE_X}" y="{ky}" width="30" height="30" fill="{fill}" '
                 f'stroke="{stroke or fill}" stroke-width="2"/>')
        t(TYPE_X + 44, ky + 23, label, 23, DISPLAY, INK, "bold", ls="-0.4")
        t(TYPE_X + 44, ky + 60, f"{pct:.2f}%", 30, DISPLAY,
          RED if label == "ALL FIRE" else INK, "bold", ls="-0.8")
        mono(TYPE_X + 44, ky + 84, f"{n:,} incidents", 17)
        ky += 108

    mono(TYPE_X, ky + 8, "Fire sits inside everything else.", 17)
    p.append(f'<rect x="{TYPE_X}" y="{ky+26}" width="22" height="22" fill="{OVER}"/>')
    mono(TYPE_X + 32, ky + 43, "Where the fire square crosses the", 17)
    mono(TYPE_X + 32, ky + 64, "rescue field, the two inks overprint.", 17)

    by = Y0 + S + 44
    mono(M, by, "A building fire alone is 1 in 386 incidents.")
    mono(M, by + 26, "A false alarm is 3.84 times more likely than any fire at all.")
    mono(M, by + 54, GUARD.upper(), fill=RED, w="bold", ls=1.2)
    mono(M, by + 80, "NFIRS basic incident module, pulled 2026-09-13. EMR Inc.", 17)

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
           f'viewBox="0 0 {W} {H}"><rect width="{W}" height="{H}" fill="{STOCK}"/>'
           + "".join(p) + "</svg>\n")
    return svg, dict(hz=hz, fx=fx, fy=fy, fs=fire_s, blue_h=blue_h)


def render(svg, g):
    (ROOT / "01-figure.svg").write_text(svg)
    wrap = ROOT / "_fv2.html"
    wrap.write_text(f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;'
                    f'background:{STOCK}}}svg{{display:block}}</style>{svg}')
    png = ROOT / "01-figure.png"
    subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu",
                    "--hide-scrollbars", f"--screenshot={png}",
                    f"--window-size={W},{H+320}", "--default-background-color=F1EBDD",
                    wrap.as_uri()], capture_output=True, timeout=180)
    wrap.unlink()
    if not png.exists(): sys.exit("render failed")
    from PIL import Image
    im = Image.open(png)
    if im.size != (W, H): im.crop((0, 0, W, H)).save(png)

    gm = Image.open(png).convert("L")
    def at(x, y): return gm.getpixel((int(x), int(y)))
    cx = g["fx"] + g["fs"] / 2
    checks = [
        ("fire over stock vs stock", at(cx, g["fy"] + g["fs"] * 0.25),
                                     at(g["fx"] - 60, g["fy"] + g["fs"] * 0.25)),
        ("overprint vs blue field",  at(cx, g["hz"] + g["fs"] * 0.25),
                                     at(g["fx"] - 60, g["hz"] + g["fs"] * 0.25)),
        ("blue field vs stock",      at(X0 + 40, g["hz"] + 60), at(X0 + 40, g["hz"] - 60)),
    ]
    for name, a, b in checks:
        if abs(a - b) < 60:
            sys.exit(f"mono gate failed, {name}: {a} vs {b}, need 60 apart")
    gm.save(ROOT / "01-figure-mono.png")
    return checks


if __name__ == "__main__":
    svg, g = build()
    checks = render(svg, g)
    print(f"  overprint ink: {OVER}  (red {gray(RED):.0f}, blue {gray(BLUE):.0f}, "
          f"over {gray(OVER):.0f} in mono)")
    print(f"  fire square side {g['fs']:.1f}px of {S}px  "
          f"= {(g['fs']/S)**2*100:.2f}% area")
    for n, a, b in checks:
        print(f"  gate {n:26s} {a:3d} vs {b:3d}")
    print(f"  {(ROOT/'01-figure.png').stat().st_size:,} bytes")
