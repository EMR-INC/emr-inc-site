"""
Study 04. The collage register, and a measuring stick for the next one.

Several collage looks are in play, so this is not an argument for one of them.
It answers the question that is the same whichever wins: where does the line
fall between the expressive field and the data, and what does a given reference
actually cost at that line.

Point it at any reference and it reports on the same terms:

    python3 studies/collage.py path/to/reference.png

The first reference measured here is torn paper, duotone halftone photography,
technical line drawing, ink splash, dotted arcs ending on nodes, one hot orange
accent, all on a cream ground. Its inks, because the interesting thing is not
that it looks good.

    blue    #1644BB   grey  67.8
    warm    #F53807   grey 106.9
    ground  #E9D9C1   grey 219.0

    blue vs ground  151.2  passes
    warm vs ground  112.1  passes
    blue vs warm     39.1  FAILS

By the monochrome floor the two inks cannot be told apart. The image is not
broken, because it never asks them to be. Every photograph, every line drawing,
every arc is blue. The orange is torn strips, a triangle and one solid circle.
It is a field accent, never a category, so nothing depends on separating it from
the blue.

That is study 01's conclusion reached from the other direction. The room between
ink and stock fits two tonally distinct chromatic bands, so a third ink has to
earn its place by not being data. Here it does exactly that.

Worth noting the reference also spreads its two inks further than the system
does: 39.1 points apart where red and blue sit 1.6 apart.

So the question this study asks is not whether to adopt the look. It is where
the line falls between the expressive field and the data, because
design_system.md already draws it: screen print tooth, registration shift and
rough edges may affect nondata fields only, and may never distort text, values,
nodes, axes or legends.

    python3 studies/collage.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import lab
from lab import TOKENS, gray, separation, at_value, tonal_capacity

OUT = Path(__file__).resolve().parent / "out"
STOCK, INK = TOKENS["stock"], TOKENS["ink"]

# Measured off the reference, not eyedropped by feel. See the module docstring.
REF_BLUE, REF_WARM, REF_GROUND = "#1644BB", "#F53807", "#E9D9C1"
REF_NAME = "the first collage reference"

if len(sys.argv) > 1:
    # Any other collage look, measured on the same terms:
    #     python3 studies/collage.py path/to/reference.png
    _ref = lab.sample_reference(sys.argv[1])
    _i = _ref["inks"]
    REF_BLUE = _i.get("cool", REF_BLUE)
    REF_WARM = _i.get("warm", REF_WARM)
    REF_GROUND = _i.get("ground", REF_GROUND)
    REF_NAME = Path(sys.argv[1]).name

W, H = 1180, 620
M = 48


def halftone_def(ink, pitch=9, r=3.1, name="ht"):
    """
    A real dot screen, not a texture image. It is a <pattern>, so it tiles at any
    size and stays crisp, and because it is made of marks rather than pixels it
    can be put behind something without bleeding into it.
    """
    return (f'<defs><pattern id="{name}" width="{pitch}" height="{pitch}" '
            f'patternUnits="userSpaceOnUse">'
            f'<circle cx="{pitch/2}" cy="{pitch/2}" r="{r}" fill="{ink}"/>'
            f'</pattern></defs>')


def torn(x, y, w, h, fill, seed=0):
    """
    A torn edge along the bottom. Deterministic from the seed, because a figure
    that redraws differently every run cannot be reviewed.
    """
    import random
    rnd = random.Random(seed)
    steps = max(8, int(w / 26))
    pts = [f"{x:.1f},{y:.1f}", f"{x+w:.1f},{y:.1f}"]
    for i in range(steps + 1):
        px = x + w - (w * i / steps)
        py = y + h + rnd.uniform(-7, 7)
        pts.append(f"{px:.1f},{py:.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{fill}"/>'


def frame(title, claim, note):
    s = [lab.svg_open(W, H)]
    s.append(lab.text(M, 40, title.upper(), 14, REF_WARM, lab.MONO, "bold", spacing=1.6))
    s.append(lab.text(M, 84, claim, 29, INK, lab.DISPLAY, "bold", spacing=-0.8))
    s.append(lab.text(W - M, 40, note, 12, INK, lab.MONO, anchor="end", spacing=0.4))
    return s


def close(s, lines):
    y = H - 30 - 18 * len(lines)
    s.append(lab.line(M, y - 18, W - M, y - 18, INK, 2))
    for i, (txt, col) in enumerate(lines):
        s.append(lab.text(M, y + i * 18, txt, 12, col, lab.MONO,
                          weight="bold" if col == REF_WARM else "normal", spacing=0.3))
    s.append(lab.svg_close())
    return "".join(s)


def panel_inks():
    """What the reference is actually made of."""
    s = frame("01 · the reference, measured",
              "TWO INKS THAT CANNOT BE TOLD APART.",
              "sampled, not eyedropped")
    items = [("ground", REF_GROUND), ("blue", REF_BLUE), ("warm", REF_WARM)]
    x0, y0, sw, sh = M, 130, 300, 150
    for i, (name, hexv) in enumerate(items):
        x = x0 + i * (sw + 26)
        s.append(lab.rect(x, y0, sw, sh, hexv))
        g = gray(hexv)
        s.append(lab.rect(x, y0 + sh, sw, 56, lab.hx((g, g, g))))
        s.append(lab.text(x, y0 + sh + 82, f"{name}  {hexv}", 13, INK, lab.MONO))
        s.append(lab.text(x, y0 + sh + 100, f"grey {g:.1f}", 13, INK, lab.MONO, weight="bold"))
    y = y0 + sh + 140
    for i, (a, b, an, bn) in enumerate([(REF_BLUE, REF_GROUND, "blue", "ground"),
                                        (REF_WARM, REF_GROUND, "warm", "ground"),
                                        (REF_BLUE, REF_WARM, "blue", "warm")]):
        sep = separation(a, b)
        ok = sep >= lab.MONO_FLOOR
        s.append(lab.text(M, y + i * 22, f"{an} vs {bn}", 13, INK, lab.MONO))
        s.append(lab.text(M + 150, y + i * 22, f"{sep:6.1f}", 13, INK, lab.MONO, weight="bold"))
        s.append(lab.text(M + 230, y + i * 22, "passes" if ok else "FAILS",
                          13, INK if ok else REF_WARM, lab.MONO, weight="bold"))
    return close(s, [
        ("The image is not broken. It never asks the two inks to be told apart.", INK),
        ("Every photograph, drawing and arc is blue. The orange is torn strips, a "
         "triangle, one circle.", INK),
        ("A field accent, never a category. Study 01 reached the same place from "
         "the other direction.", REF_WARM)])


def panel_correct():
    """Texture on the field, data on top of it, clean."""
    s = frame("02 · where the line falls",
              "TOOTH ON THE FIELD. NOTHING ON THE DATA.",
              "design_system.md · nondata fields only")
    s.append(halftone_def(REF_BLUE, 9, 3.2, "ht_ok"))
    fx, fy, fw, fh = M, 126, 560, 300
    s.append(lab.rect(fx, fy, fw, fh, REF_GROUND))
    s.append(lab.rect(fx, fy, fw, fh, "url(#ht_ok)"))
    s.append(torn(fx, fy + fh - 10, fw, 10, STOCK, seed=4))
    s.append(lab.rect(fx + 40, fy + 150, 120, 26, REF_WARM))
    # The data sits on the field, drawn in flat ink with no screen anywhere near it.
    bx, by, bw = fx + fw + 56, fy + 16, 400
    for i, (label, pct) in enumerate([("Rescue and EMS", 72.42),
                                      ("Everything else", 27.58),
                                      ("All fire", 1.58)]):
        y = by + i * 72
        s.append(lab.rect(bx, y, max(bw * pct / 100, 3), 40, REF_BLUE))
        s.append(lab.rect(bx, y, bw, 40, "none", stroke=INK, stroke_width=1.5))
        s.append(lab.text(bx, y - 8, f"{label}  {pct}%", 13, INK, lab.MONO, weight="bold"))
    return close(s, [
        ("The halftone, the torn edge and the orange block are field. They carry no "
         "value.", INK),
        ("The bars, their outlines and every label are flat ink on flat colour, "
         "untouched by the screen.", INK),
        ("This is the whole rule: tooth may affect nondata fields only, and never "
         "text, values, nodes, axes or legends.", REF_WARM)])


def panel_wrong():
    """The same register applied through the data, which is what not to do."""
    s = frame("03 · the same moves, through the data",
              "WHAT IT COSTS WHEN THE TOOTH CROSSES OVER.",
              "this one does not ship")
    s.append(halftone_def(REF_BLUE, 9, 3.2, "ht_bad"))
    s.append(halftone_def(REF_WARM, 7, 2.6, "ht_bad2"))
    bx, by, bw = M, 140, 620
    for i, (label, pct) in enumerate([("Rescue and EMS", 72.42),
                                      ("Everything else", 27.58),
                                      ("All fire", 1.58)]):
        y = by + i * 78
        fill = "url(#ht_bad)" if i != 2 else "url(#ht_bad2)"
        # A screen is dots on nothing. Without a ground under it the bar is
        # mostly stock showing through and the failure stops being legible as a
        # failure, which is its own lesson about putting tooth on data.
        s.append(lab.rect(bx, y, max(bw * pct / 100, 4), 46, REF_GROUND))
        s.append(lab.rect(bx, y, max(bw * pct / 100, 4), 46, fill))
        s.append(torn(bx, y + 46 - 6, max(bw * pct / 100, 4), 6, STOCK, seed=i + 1))
        s.append(lab.text(bx + 14, y + 30, f"{label}  {pct}%", 14, STOCK,
                          lab.MONO, weight="bold"))
    s.append(lab.text(W - 400, by + 20, "Three things broke.", 15, REF_WARM,
                      lab.DISPLAY, "bold"))
    for i, t in enumerate([
            "1  The torn edge moved the bar end,",
            "   so the length no longer encodes",
            "   the value it claims to.",
            "2  Two series are separated by dot",
            "   pitch and hue, which is colour",
            "   carrying meaning on its own.",
            "3  Labels sit on a screen, so they",
            "   lose contrast at small sizes and",
            "   in every greyscale client."]):
        s.append(lab.text(W - 400, by + 56 + i * 20, t, 12, INK, lab.MONO))
    return close(s, [
        ("Nothing here is a matter of taste. Each one breaks a stated rule.", INK),
        ("A diagram fails if removing colour destroys meaning, or if the caption "
         "claims more than the geometry shows.", REF_WARM)])


def panel_arc():
    """The dotted arc ending on a node, which the reference already draws."""
    s = frame("04 · the arc the reference already draws",
              "A PATH THAT ENDS ON SOMETHING REAL.",
              "Pintori · terminal arcs")
    s.append(halftone_def(REF_BLUE, 11, 2.4, "ht_arc"))
    s.append(lab.rect(M, 126, W - 2 * M, 150, REF_GROUND))
    s.append(lab.rect(M, 126, W - 2 * M, 150, "url(#ht_arc)"))
    s.append(torn(M, 126 + 140, W - 2 * M, 10, STOCK, seed=9))
    stops = [("dispatched", 0.04), ("on scene", 0.3), ("transporting", 0.56),
             ("in service", 0.93)]
    y = 360
    x0, x1 = M + 40, W - M - 60
    for i, (label, t) in enumerate(stops):
        x = x0 + t * (x1 - x0)
        if i:
            px = x0 + stops[i - 1][1] * (x1 - x0)
            mid = (px + x) / 2
            s.append(f'<path d="M {px:.1f} {y} Q {mid:.1f} {y-54} {x:.1f} {y}" '
                     f'fill="none" stroke="{REF_BLUE}" stroke-width="2.5" '
                     f'stroke-dasharray="3 6"/>')
        last = i == len(stops) - 1
        s.append(f'<circle cx="{x:.1f}" cy="{y}" r="{10 if last else 7}" '
                 f'fill="{REF_WARM if last else REF_BLUE}" stroke="{INK}" '
                 f'stroke-width="2"/>')
        s.append(lab.text(x, y + 30, label, 12, INK, lab.MONO, anchor="middle"))
    s.append(lab.text(M, y + 76, "The dotted arc is the reference's own move, and it "
                      "is already in the system: a traced record whose path", 13, INK,
                      lab.MONO))
    s.append(lab.text(M, y + 96, "terminates visibly. The arcs are drawn over the "
                      "screened field, never through it, and the final node is the "
                      "one", 13, INK, lab.MONO))
    s.append(lab.text(M, y + 116, "place the accent ink is allowed to land, because "
                      "there it marks an endpoint rather than a category.", 13, INK,
                      lab.MONO))
    return close(s, [
        ("Nothing here needs a new rule. The register and the grammar already agree.", INK)])


PANELS = [
    ("The reference, measured", "two inks 39.1 apart, one of them never a category", panel_inks),
    ("Field and data", "tooth on one side of the line only", panel_correct),
    ("The same moves, misapplied", "what it costs, rule by rule", panel_wrong),
    ("Terminal arcs", "the reference's move, already in the grammar", panel_arc),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    panels = [lab.Panel(fn(), W, H, f"{i+1}. {name}", note)
              for i, (name, note, fn) in enumerate(PANELS)]
    sheet = lab.contact_sheet(panels, OUT / "04-collage.png", cols=1, scale=0.78)

    print(f"\n  study 04 · the collage register\n  {'=' * 64}\n")
    print(f"  reference: {REF_NAME}")
    print(f"\n  its own inks")
    for n, h in (("ground", REF_GROUND), ("blue", REF_BLUE), ("warm", REF_WARM)):
        print(f"    {n:7s} {h}  grey {gray(h):6.1f}")
    print(f"\n  against the {lab.MONO_FLOOR} floor")
    for a, b, an, bn in [(REF_BLUE, REF_GROUND, "blue", "ground"),
                         (REF_WARM, REF_GROUND, "warm", "ground"),
                         (REF_BLUE, REF_WARM, "blue", "warm")]:
        sep = separation(a, b)
        print(f"    {an:7s} vs {bn:7s} {sep:6.1f}  "
              f"{'passes' if sep >= lab.MONO_FLOOR else 'FAILS'}")
    print(f"\n  how far apart the two inks sit")
    print(f"    reference blue and warm   {separation(REF_BLUE, REF_WARM):5.1f}")
    print(f"    system red and blue       {separation(TOKENS['red'], TOKENS['blue']):5.1f}")
    print(f"\n  the reference does not break the rule. It never asks the two inks to")
    print(f"  be told apart: the orange is field, never a category. That is study 01's")
    print(f"  finding reached from the other direction.")
    print(f"\n  {sheet}")
    print(f"  {sheet.with_name(sheet.stem + '-mono.png')}")




# --------------------------------------------------------------- comparison ---

def panel_compare(refs, labels, w=1180, h=640):
    """
    Four candidate registers on one ruler.

    The point of measuring them identically is that the eye cannot do this. A
    hi-vis yellow on cream looks loud and is nearly invisible once hue is gone,
    and no amount of looking at a colour screen will tell you.
    """
    s = [lab.svg_open(w, h)]
    s.append(lab.text(M, 40, "05 · FOUR REGISTERS ON ONE RULER", 15, INK,
                      lab.DISPLAY, "bold", spacing=1.2))
    s.append(lab.text(w - M, 40, "every ink placed by its greyscale value", 12, INK,
                      lab.MONO, anchor="end"))

    x0, x1 = M + 118, w - M - 40
    def px(v):
        return x0 + (v / 255) * (x1 - x0)

    for i, (ref, name) in enumerate(zip(refs, labels)):
        y = 96 + i * 124
        s.append(lab.text(M, y + 6, name, 13, INK, lab.MONO, weight="bold"))
        s.append(lab.text(M, y + 24, "dark ground" if ref["dark_ground"] else "light ground",
                          11, INK, lab.MONO))
        hr = ref["headroom"]
        s.append(lab.text(M, y + 40, f"{hr['bands']} band(s) fit", 11,
                          TOKENS["red"] if hr["bands"] < 2 else INK, lab.MONO))
        # the ruler
        s.append(lab.line(x0, y + 46, x1, y + 46, INK, 1))
        for v in (0, 64, 128, 192, 255):
            s.append(lab.line(px(v), y + 42, px(v), y + 50, INK, 1))
        for ink_name, hexv in ref["inks"].items():
            if ref["shares"][ink_name] < 0.01:
                continue    # a tenth of a percent is a sampling artefact, not an ink
            g = gray(hexv)
            s.append(lab.rect(px(g) - 17, y + 2, 34, 36, hexv,
                              stroke=INK, stroke_width=1.5))
            s.append(lab.text(px(g), y + 68, f"{g:.0f}", 11, INK, lab.MONO,
                              anchor="middle"))
        # every failing pair that is not ground against an ink
        fails = [(k, v) for k, v in ref["pairs"].items() if v < lab.MONO_FLOOR]
        txt = ("every pair separates" if not fails else
               "collides: " + ", ".join(f"{k} {v:.0f}" for k, v in fails[:3]))
        s.append(lab.text(x0, y + 90, txt, 11,
                          INK if not fails else TOKENS["red"], lab.MONO,
                          weight="bold" if fails else "normal"))
    s.append(lab.text(M, h - 58, "Two swatches at the same mark are the same colour "
                      "once hue is gone, whatever they look like here.", 12, INK,
                      lab.MONO))
    s.append(lab.text(M, h - 36, "A swatch sitting on its own ground's mark has "
                      "disappeared into the paper.", 12, TOKENS["red"], lab.MONO,
                      weight="bold"))
    s.append(lab.svg_close())
    return "".join(s)


def compare(paths):
    """python3 studies/collage.py a.webp b.webp c.webp"""
    OUT.mkdir(parents=True, exist_ok=True)
    refs = [lab.sample_reference(p) for p in paths]
    names = [Path(p).name for p in paths]
    panel = lab.Panel(panel_compare(refs, names), 1180, 640,
                      "Four registers compared", "measured identically")
    sheet = lab.contact_sheet([panel], OUT / "05-references.png", cols=1, scale=0.9)

    print(f"\n  study 05 · candidate registers compared\n  {'=' * 64}")
    for ref, name in zip(refs, names):
        print(f"\n  {name}   {'DARK ground' if ref['dark_ground'] else 'light ground'}")
        for line in lab.describe_reference(ref):
            print("  " + line)
    clean = [n for r, n in zip(refs, names)
             if not any(v < lab.MONO_FLOOR for v in r["pairs"].values())]
    print(f"\n  registers where every ink pair separates: "
          f"{', '.join(clean) if clean else 'none'}")
    print(f"\n  {sheet}")
    print(f"  {sheet.with_name(sheet.stem + '-mono.png')}")


if __name__ == "__main__":
    # One path studies that register. Several compares them.
    if len(sys.argv) > 2:
        compare(sys.argv[1:])
    else:
        main()
