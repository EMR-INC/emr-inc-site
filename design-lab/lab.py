"""
Shared harness for the design lab.

The point of this file is that an experiment should be looked at, not described.
Everything here exists to get from an idea to a picture on a contact sheet in one
command, with the system's own rules enforced on the way so a study cannot
quietly produce something that would fail in production.

Nothing here ships. See README.md.
"""
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "studies" / "out"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

# ------------------------------------------------------------------ tokens ---

# design_system.md, Color and material. Copied rather than imported: the design
# repo is a separate read only clone, and a study that silently changed when that
# repo moved would be unreproducible. If these drift, that is a finding.
TOKENS = {
    "stock":  "#F1EBDD",   # primary field
    "ink":    "#10213B",   # type, axes, rules, primary controls
    "red":    "#D5222A",   # one traced route or declared category
    "blue":   "#2363A0",   # record layer
    "green":  "#287443",   # connected field
    "yellow": "#E5C500",   # highlight or crossed band
    "orange": "#D95A25",   # optional transition or stack layer
    "dark":   "#161A20",   # high contrast inset
    "white":  "#FFFFFF",   # accessible document or input field
}
CHROMATIC = ("red", "blue", "green", "yellow", "orange")

DISPLAY = "Archivo Black, Archivo, Arial Black, Arial, sans-serif"
BODY    = "Archivo, Arial, Helvetica, sans-serif"
MONO    = "Courier Prime, Courier New, monospace"

# design_system.md: spacing scale and the two canvas families.
SPACING = (4, 8, 16, 24, 40, 64, 96, 144)
LANDSCAPE = (1600, 900)
PORTRAIT = (1080, 1350)

# ------------------------------------------------------------- colour math ---

def rgb(h: str) -> tuple[float, float, float]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def hx(t) -> str:
    return "#%02X%02X%02X" % tuple(max(0, min(255, round(c))) for c in t)


def gray(h: str) -> float:
    """Rec. 601 luma, which is what a greyscale conversion actually does."""
    r, g, b = rgb(h)
    return 0.299 * r + 0.587 * g + 0.114 * b


def multiply(a: str, b: str) -> str:
    """
    Two transparent inks on one sheet. This is what overprint actually does,
    and design_system.md allows it: a transparent overlap may create an
    additional apparent color when the contributing layers remain clear.
    """
    return hx(tuple(x * y / 255 for x, y in zip(rgb(a), rgb(b))))


def mix(a: str, b: str, t: float) -> str:
    """Straight interpolation. Not overprint; use multiply() for ink on ink."""
    return hx(tuple(x + (y - x) * t for x, y in zip(rgb(a), rgb(b))))


def over(fg: str, bg: str, alpha: float) -> str:
    """fg painted on bg at alpha, as a client would composite it."""
    return mix(bg, fg, alpha)


def separation(a: str, b: str) -> float:
    """How far apart two colours are once colour is gone. 0 to 255."""
    return abs(gray(a) - gray(b))


# ------------------------------------------------------------------- gates ---

MONO_FLOOR = 60  # the figure build uses 60; keep studies on the same bar


class GateFailure(Exception):
    """A study produced something the system would reject. Not a crash."""


def assert_mono(pairs, floor: int = MONO_FLOOR) -> list[tuple[str, float]]:
    """
    design_system.md: a diagram fails if removing color destroys meaning.

    pairs is (label, hex_a, hex_b). Returns the measurements so a study can
    print them, and raises on the first one that does not hold. Measuring the
    tokens is cheaper than rendering, but it is NOT a substitute for sampling
    real pixels after quantisation, which is what the figure build does.
    """
    out = []
    for label, a, b in pairs:
        sep = separation(a, b)
        out.append((label, sep))
        if sep < floor:
            raise GateFailure(
                f"{label}: {a} and {b} are {sep:.0f} apart in greyscale, "
                f"need {floor}. Colour alone would be carrying the meaning."
            )
    return out


def assert_chromatic_budget(used) -> None:
    """design_system.md: at most three chromatic inks on a surface."""
    chromatic = [u for u in used if u in CHROMATIC]
    if len(chromatic) > 3:
        raise GateFailure(
            f"{len(chromatic)} chromatic inks ({', '.join(chromatic)}). "
            "design_system.md allows three. Stock and ink do not count."
        )


# ------------------------------------------------------------------ render ---

@dataclass
class Panel:
    """One thing to look at, plus what it is and what was measured about it."""
    svg: str
    width: int
    height: int
    title: str
    note: str = ""
    readings: list = field(default_factory=list)


def render_svg(svg: str, w: int, h: int, out: Path, bg: str = None) -> Path:
    """One SVG to one PNG, through the same headless Chromium the figure uses."""
    bg = bg or TOKENS["stock"]
    out.parent.mkdir(parents=True, exist_ok=True)
    wrap = out.with_suffix(".tmp.html")
    wrap.write_text(
        f'<!doctype html><meta charset="utf-8"><style>html,body{{margin:0;'
        f'background:{bg}}}svg{{display:block}}</style>{svg}', encoding="utf-8")
    subprocess.run(
        [CHROME, "--headless=new", "--no-sandbox", "--disable-gpu",
         "--hide-scrollbars", f"--screenshot={out}",
         f"--window-size={w},{h + 320}",
         f"--default-background-color={bg.lstrip('#')}", wrap.as_uri()],
        capture_output=True, timeout=240)
    wrap.unlink(missing_ok=True)
    if not out.exists():
        sys.exit(f"render failed: {out}")
    from PIL import Image
    im = Image.open(out)
    if im.size != (w, h):
        # --window-size sizes the WINDOW, not the viewport. Always crop.
        im.crop((0, 0, w, h)).save(out)
    return out


def contact_sheet(panels, out: Path, cols: int = 2, scale: float = 1.0,
                  gutter: int = 40, also_mono: bool = True) -> Path:
    """
    Every panel on one sheet, captioned, so variants are compared side by side
    rather than one at a time. Writes a greyscale copy beside it, because the
    monochrome read is the one that catches a diagram leaning on hue.
    """
    from PIL import Image, ImageDraw

    tmp = OUT / "_panels"
    images = []
    for i, p in enumerate(panels):
        png = render_svg(p.svg, p.width, p.height, tmp / f"p{i:02d}.png")
        im = Image.open(png).convert("RGB")
        if scale != 1.0:
            im = im.resize((int(im.width * scale), int(im.height * scale)),
                           Image.LANCZOS)
        images.append(im)

    cap = 58
    cw = max(im.width for im in images)
    # Pack each row to its own tallest panel rather than to the tallest panel on
    # the sheet. Sizing every row to the global maximum left most of a one column
    # sheet empty, which makes the comparison harder, not easier.
    nrows = (len(images) + cols - 1) // cols
    row_h = [max(im.height for im in images[r * cols:(r + 1) * cols]) + cap
             for r in range(nrows)]
    row_y, acc = [], gutter
    for rh in row_h:
        row_y.append(acc)
        acc += rh + gutter
    W = gutter + cols * (cw + gutter)
    H = acc

    sheet = Image.new("RGB", (W, H), rgb(TOKENS["stock"]))
    d = ImageDraw.Draw(sheet)
    for i, (im, p) in enumerate(zip(images, panels)):
        r, c = divmod(i, cols)
        x = gutter + c * (cw + gutter)
        y = row_y[r]
        sheet.paste(im, (x, y))
        ty = y + im.height + 10
        d.text((x, ty), p.title, fill=rgb(TOKENS["ink"]))
        if p.note:
            d.text((x, ty + 14), p.note, fill=rgb(TOKENS["ink"]))
        if p.readings:
            txt = "   ".join(f"{k} {v:.0f}" for k, v in p.readings)
            d.text((x, ty + 28), txt, fill=rgb(TOKENS["red"]))

    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    if also_mono:
        sheet.convert("L").save(out.with_name(out.stem + "-mono.png"))
    for f in tmp.glob("*.png"):
        f.unlink()
    tmp.rmdir()
    return out


# ------------------------------------------------------------------ svg kit ---

def svg_open(w: int, h: int, bg: str = None) -> str:
    bg = bg or TOKENS["stock"]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
            f'viewBox="0 0 {w} {h}"><rect width="{w}" height="{h}" fill="{bg}"/>')


def rect(x, y, w, h, fill, **kw) -> str:
    extra = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in kw.items())
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{fill}"{extra}/>'


def line(x1, y1, x2, y2, stroke, width=2, **kw) -> str:
    extra = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in kw.items())
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
            f'stroke="{stroke}" stroke-width="{width}"{extra}/>')


def text(x, y, s, size=16, fill=None, family=None, weight="normal",
         anchor="start", spacing=0) -> str:
    fill = fill or TOKENS["ink"]
    family = family or MONO
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" '
            f'font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}" letter-spacing="{spacing}" '
            f'xml:space="preserve">{esc(s)}</text>')


def esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def svg_close() -> str:
    return "</svg>"


def at_value(hue: str, target: float, toward_light: str = None,
             toward_dark: str = None) -> str:
    """
    The nearest colour to `hue` that reads as `target` in greyscale.

    A tonal ladder has to be defined by the value it lands on, not by an
    operation applied to a hue. Multiplying every ink with ink looks like a
    ladder and is not one: it crushed all five darks into a band 11 points wide,
    below ink, which is the same flatness the ladder was meant to fix.

    Lighten toward stock, because that is what less ink on the sheet does.
    Darken toward the dark token rather than ink, so the hue is not dragged
    toward navy on its way down.
    """
    base = TOKENS[hue] if hue in TOKENS else hue
    light = toward_light or TOKENS["stock"]
    dark = toward_dark or TOKENS["dark"]
    end = light if target > gray(base) else dark
    lo, hi = 0.0, 1.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if (gray(mix(base, end, mid)) < target) == (gray(base) < target):
            lo = mid
        else:
            hi = mid
    return mix(base, end, (lo + hi) / 2)


def tonal_capacity(floor: int = None) -> dict:
    """
    How many chromatic bands actually fit between ink and stock.

    This is the question underneath "should we expand the palette". The answer
    is a property of the two fixed tokens, not of how many hues get added.
    """
    floor = floor or MONO_FLOOR
    lo, hi = gray(TOKENS["ink"]), gray(TOKENS["stock"])
    span = hi - lo
    bands = int(span // floor) - 1
    step = span / (bands + 1) if bands > 0 else 0
    return {"ink": lo, "stock": hi, "span": span, "floor": floor,
            "bands": bands,
            "values": [lo + step * (i + 1) for i in range(bands)],
            "gap": step}


# ------------------------------------------------------------ email checks ---

# The constructs that break in real clients. Same list the issue build enforces,
# kept here so a layout study cannot propose something that cannot ship.
EMAIL_FORBIDDEN = [
    (r"@import", "Gmail strips @import"),
    (r"::(before|after)", "Gmail drops pseudo elements"),
    (r"display\s*:\s*(flex|grid)", "Outlook ignores flex and grid"),
    (r"var\(--", "Outlook ignores custom properties"),
    (r"\d(vh|vw)\b", "viewport units are unreliable in mail"),
    (r"clamp\(", "clamp() is unreliable in mail"),
    (r"position\s*:\s*(absolute|fixed|sticky)", "positioning is unreliable"),
    (r"<style", "a style block is stripped by several clients"),
]
GMAIL_CLIP = 102_400


def check_email(html: str) -> list[str]:
    """What would break, and how close to the clip threshold it is."""
    import re
    bad = [why for pat, why in EMAIL_FORBIDDEN if re.search(pat, html, re.I)]
    n = len(html.encode())
    if n > GMAIL_CLIP:
        bad.append(f"{n:,} bytes, Gmail clips above {GMAIL_CLIP:,}")
    return bad


def render_html(html: str, w: int, h: int, out: Path, bg: str = None) -> Path:
    """An email body as a client would lay it out, at a real client width."""
    bg = bg or TOKENS["stock"]
    out.parent.mkdir(parents=True, exist_ok=True)
    page = out.with_suffix(".tmp.html")
    page.write_text(html, encoding="utf-8")
    subprocess.run(
        [CHROME, "--headless=new", "--no-sandbox", "--disable-gpu",
         "--hide-scrollbars", f"--screenshot={out}", f"--window-size={w},{h}",
         f"--default-background-color={bg.lstrip('#')}", page.as_uri()],
        capture_output=True, timeout=240)
    page.unlink(missing_ok=True)
    if not out.exists():
        sys.exit(f"render failed: {out}")
    return out


# -------------------------------------------------------------- references ---

def sample_reference(path, sat=0.55, warm_hue=30, cool=(200, 260)) -> dict:
    """
    The inks a reference image is actually made of.

    Quantising the whole image does not work for this: a hot accent covering five
    percent gets averaged into a muddy blend with whatever it sits next to. The
    first attempt at this returned #88506E, a purple that appears nowhere in the
    picture. So pull by saturation and hue family instead, and take the median of
    each family rather than the mean, which a few dark pixels would drag.

    Returns the inks plus every pairwise separation, so a new reference can be
    judged on the same terms as the last one.
    """
    import colorsys
    from PIL import Image

    im = Image.open(path).convert("RGB")
    px = list(im.resize((320, 320), Image.LANCZOS).getdata())
    fam = {"cool": [], "warm": [], "ground": []}
    for r, g, b in px:
        h, sv, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        deg = h * 360
        if sv > sat and cool[0] <= deg <= cool[1]:
            fam["cool"].append((r, g, b))
        elif sv > sat and (deg <= warm_hue or deg >= 345):
            fam["warm"].append((r, g, b))
        elif sv < 0.18 and v > 0.80:
            fam["ground"].append((r, g, b))

    inks, shares = {}, {}
    for name, pts in fam.items():
        if not pts:
            continue
        pts.sort(key=sum)
        inks[name] = hx(pts[len(pts) // 2])
        shares[name] = len(pts) / len(px)

    pairs = {}
    names = list(inks)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            pairs[f"{a} vs {b}"] = separation(inks[a], inks[b])
    return {"path": str(path), "inks": inks, "shares": shares, "pairs": pairs}


def describe_reference(ref: dict) -> list[str]:
    """The reading, in words, including what the numbers do and do not mean."""
    out = []
    for name, hexv in ref["inks"].items():
        out.append(f"  {name:7s} {hexv}  grey {gray(hexv):6.1f}  "
                   f"{ref['shares'][name] * 100:5.1f}% of the image")
    out.append("")
    for label, sep in ref["pairs"].items():
        ok = sep >= MONO_FLOOR
        out.append(f"  {label:20s} {sep:6.1f}  {'passes' if ok else 'FAILS'}")
    cw = ref["pairs"].get("cool vs warm")
    if cw is not None and cw < MONO_FLOOR:
        out += ["",
                "  The two inks cannot be told apart in greyscale. That is only a",
                "  problem if the reference asks them to be. Check what the accent",
                "  is doing: if it is field, an accent or an endpoint it is fine,",
                "  and if it is a second data category it is not."]
    return out
