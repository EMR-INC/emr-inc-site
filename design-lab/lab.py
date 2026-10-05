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

def sample_reference(path, n_inks=3, sat=0.42, min_share=0.01) -> dict:
    """
    The inks a reference is actually made of, without assuming what they are.

    Two earlier versions of this were wrong in instructive ways. Quantising the
    whole image averaged a small hot accent into its neighbours and returned a
    purple that appears nowhere in the picture. Then hardcoding "ground is the
    light desaturated pixels" broke the moment a reference arrived with a dark
    navy ground, which is not an edge case but a different and legitimate way to
    build the same system.

    So: find the ground as the most common low saturation colour whatever its
    value, then take the saturated families by hue, widest first. Median per
    family, because a few dark pixels drag a mean.
    """
    import colorsys
    from PIL import Image

    im = Image.open(path).convert("RGB")
    px = list(im.resize((320, 320), Image.LANCZOS).getdata())

    flat, sats = [], []
    for r, g, b in px:
        h, sv, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        (sats if sv > sat else flat).append(((r, g, b), h * 360, v))

    # Ground: the densest band of low saturation pixels, light or dark.
    ground = None
    if flat:
        bins = {}
        for col, _, v in flat:
            bins.setdefault(int(v * 8), []).append(col)
        pick = max(bins.values(), key=len)
        pick.sort(key=sum)
        ground = hx(pick[len(pick) // 2])
        ground_share = len(pick) / len(px)

    # Saturated inks, grouped into 24 degree hue buckets.
    buckets = {}
    for col, deg, _ in sats:
        buckets.setdefault(int(deg // 24), []).append(col)
    # Drop families too small to be an ink. A bucket holding a tenth of a percent
    # is an antialiasing seam or a jpeg artefact, and counting one as an ink made
    # a register look like it had a failing pair when the failure was against
    # something nobody put there.
    ranked = [(b, pts) for b, pts in
              sorted(buckets.items(), key=lambda kv: -len(kv[1]))
              if len(pts) / len(px) >= min_share][:n_inks]

    inks, shares = {}, {}
    if ground:
        inks["ground"] = ground
        shares["ground"] = ground_share
    for i, (b, pts) in enumerate(ranked):
        pts.sort(key=sum)
        inks[f"ink {i + 1}"] = hx(pts[len(pts) // 2])
        shares[f"ink {i + 1}"] = len(pts) / len(px)

    pairs, names = {}, list(inks)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            pairs[f"{a} vs {b}"] = separation(inks[a], inks[b])
    dark_ground = ground is not None and gray(ground) < 128
    return {"path": str(path), "inks": inks, "shares": shares, "pairs": pairs,
            "dark_ground": dark_ground,
            "headroom": tonal_headroom(ground) if ground else None}


def tonal_headroom(ground: str, floor: int = None) -> dict:
    """
    How many chromatic bands fit between this ground and the ink that sits on it.

    Study 01 worked this out for stock and ink. A reference with a dark ground
    has a different answer, which is the whole reason a dark ground is worth
    considering rather than a deviation to be corrected.
    """
    floor = floor or MONO_FLOOR
    g = gray(ground)
    # The far end is whatever the type has to be: ink on a light ground, stock
    # on a dark one.
    far = gray(TOKENS["ink"]) if g >= 128 else gray(TOKENS["stock"])
    span = abs(g - far)
    bands = max(0, int(span // floor) - 1)
    step = span / (bands + 1) if bands else 0
    lo = min(g, far)
    return {"span": span, "bands": bands,
            "values": [lo + step * (i + 1) for i in range(bands)]}


def describe_reference(ref: dict) -> list[str]:
    """The reading in words, including what the numbers do and do not mean."""
    out = []
    for name, hexv in ref["inks"].items():
        out.append(f"  {name:8s} {hexv}  grey {gray(hexv):6.1f}  "
                   f"{ref['shares'][name] * 100:5.1f}%")
    out.append("")
    for label, sep in ref["pairs"].items():
        out.append(f"  {label:22s} {sep:6.1f}  "
                   f"{'passes' if sep >= MONO_FLOOR else 'FAILS'}")
    hr = ref.get("headroom")
    if hr:
        out += ["", f"  ground to type is {hr['span']:.1f} points, which fits "
                    f"{hr['bands']} chromatic band(s)"]
    fails = [k for k, v in ref["pairs"].items() if v < MONO_FLOOR
             and "ground" not in k]
    if fails:
        out += ["",
                "  Inks that cannot be told apart in greyscale: "
                + ", ".join(fails) + ".",
                "  Only a problem if the reference asks them to be. Field, accent",
                "  or endpoint is fine. A second data category is not."]
    return out
