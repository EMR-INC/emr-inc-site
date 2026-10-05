"""
Study 01. The palette is not too small. It is tonally flat, and the tonal room
it has is smaller than the rule it is asked to satisfy.

The brief was "expand the palette". Measuring first says something more useful.

Of five chromatic inks, three land on one tonal value: red 88.4, blue 86.8,
green 87.7. Six of the ten pairs separate by less than the 60 the figure build
already enforces. design_system.md fails any diagram whose meaning dies when
colour is removed, so most two ink combinations are already relying on hue.

Adding more hues cannot fix that, because the constraint is not the number of
hues. Between ink (30.9) and stock (235.2) there are 204.3 points of greyscale.
At a floor of 60 that fits TWO chromatic bands, not three. So the system's own
"at most three chromatic inks" cannot be met tonally by any palette at all. A
third ink has to earn its place another way: overprint, pattern, or never
sitting adjacent to the other two.

The proposal is therefore not more hues. It is the same five hues placed on two
measured bands, so a surface can pick inks that are tonally distinct by
construction rather than by luck.

    python3 studies/palette.py
"""
import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import lab
from lab import TOKENS, CHROMATIC, gray, hx, at_value, separation, tonal_capacity

OUT = Path(__file__).resolve().parent / "out"
STOCK, INK = TOKENS["stock"], TOKENS["ink"]
CAP = tonal_capacity()
BAND_NAMES = ("deep", "pale")

LADDER = {}
for h in CHROMATIC:
    for name, v in zip(BAND_NAMES, CAP["values"]):
        LADDER[f"{h} {name}"] = at_value(h, v)
COLS = {n: TOKENS[n] for n in CHROMATIC} | LADDER
# Every surface already uses the field and the ink. Judging chromatic inks
# without them answers the wrong question.
ALL = COLS | {"stock": STOCK, "ink": INK}


def swatches(pairs, title, note, w=1180, h=304):
    """A row of swatches, each sitting directly above itself with hue removed."""
    s = [lab.svg_open(w, h)]
    pad, top, n = 40, 58, len(pairs)
    cw = (w - pad * 2) / n
    sw, sh = cw - 10, 104
    s.append(lab.text(pad, 36, title.upper(), 15, INK, lab.DISPLAY, "bold", spacing=1.2))
    for i, (label, hexv) in enumerate(pairs):
        x = pad + i * cw
        g = gray(hexv)
        s.append(lab.rect(x, top, sw, sh, hexv))
        s.append(lab.rect(x, top + sh, sw, 50, hx((g, g, g))))
        s.append(lab.text(x, top + sh + 74, label, 11, INK, lab.MONO, spacing=0.4))
        s.append(lab.text(x, top + sh + 90, hexv, 11, INK, lab.MONO, spacing=0.4))
        s.append(lab.text(x, top + sh + 106, f"grey {g:.0f}", 11, TOKENS["red"],
                          lab.MONO, weight="bold", spacing=0.4))
    s.append(lab.text(pad, h - 16, note, 12, INK, lab.MONO, spacing=0.3))
    s.append(lab.svg_close())
    return "".join(s)


def matrix(names, title, note, w=1180, h=None):
    """Every pair measured. Failures are filled red, so the pattern reads first."""
    n = len(names)
    left, top = 210, 96
    cell = min(100, (w - left - 60) / n)
    # Size to the content. The first version hardcoded 470 and silently clipped
    # the last two rows, which is exactly the kind of thing a contact sheet is
    # for catching.
    h = h or int(top + n * cell + 86)
    s = [lab.svg_open(w, h)]
    s.append(lab.text(40, 36, title.upper(), 15, INK, lab.DISPLAY, "bold", spacing=1.2))
    for j, b in enumerate(names):
        parts = b.split()
        s.append(lab.text(left + j * cell + cell / 2, top - 18, parts[0][:8], 11,
                          INK, lab.MONO, anchor="middle"))
        if len(parts) > 1:
            s.append(lab.text(left + j * cell + cell / 2, top - 5, parts[1][:8], 10,
                              INK, lab.MONO, anchor="middle"))
    fails = 0
    for i, a in enumerate(names):
        y = top + i * cell
        s.append(lab.text(left - 14, y + cell / 2 + 4, a, 11, INK, lab.MONO, anchor="end"))
        for j, b in enumerate(names):
            x = left + j * cell
            if i == j:
                s.append(lab.rect(x, y, cell - 3, cell - 3, STOCK, stroke=INK,
                                  stroke_width=1, stroke_dasharray="2 3"))
                continue
            sep = separation(COLS[a], COLS[b])
            bad = sep < lab.MONO_FLOOR
            if bad and i < j:
                fails += 1
            v = min(255, 55 + sep * 0.8)
            s.append(lab.rect(x, y, cell - 3, cell - 3,
                              TOKENS["red"] if bad else hx((v, v, v))))
            s.append(lab.text(x + cell / 2, y + cell / 2 + 5, f"{sep:.0f}", 15,
                              STOCK if bad or v < 140 else INK, lab.MONO,
                              weight="bold", anchor="middle"))
    s.append(lab.text(40, h - 44, note.format(fails=fails,
                      total=n * (n - 1) // 2), 12, INK, lab.MONO, spacing=0.3))
    s.append(lab.text(40, h - 22, f"Red cells fall below {lab.MONO_FLOOR}. Below it "
                      "colour alone carries the distinction, and the diagram fails.",
                      12, INK, lab.MONO, spacing=0.3))
    s.append(lab.svg_close())
    return "".join(s)


def capacity_panel(w=1180, h=330):
    """
    The constraint drawn as what it is: a ruler with two fixed ends and only so
    much room between them.
    """
    s = [lab.svg_open(w, h)]
    s.append(lab.text(40, 36, "03 · HOW MUCH TONAL ROOM THERE ACTUALLY IS", 15,
                      INK, lab.DISPLAY, "bold", spacing=1.2))
    x0, x1, y = 40, w - 40, 110
    def px(v):  # greyscale value to x position
        return x0 + (v / 255) * (x1 - x0)
    # the whole 0..255 scale as a gradient of flat steps, so it is countable
    for i in range(0, 255, 5):
        s.append(lab.rect(px(i), y, (x1 - x0) * 5 / 255 + 1, 44, hx((i, i, i))))
    s.append(lab.rect(x0, y, x1 - x0, 44, "none", stroke=INK, stroke_width=1))
    for label, v, col in (("ink", CAP["ink"], TOKENS["ink"]),
                          ("stock", CAP["stock"], TOKENS["ink"])):
        s.append(lab.line(px(v), y - 12, px(v), y + 56, col, 2))
        s.append(lab.text(px(v), y - 20, f"{label} {v:.0f}", 12, col, lab.MONO,
                          weight="bold", anchor="middle"))
    for i, v in enumerate(CAP["values"]):
        s.append(lab.line(px(v), y + 44, px(v), y + 78, TOKENS["red"], 2))
        s.append(lab.text(px(v), y + 94, f"band {i+1}", 12, TOKENS["red"], lab.MONO,
                          weight="bold", anchor="middle"))
        s.append(lab.text(px(v), y + 108, f"{v:.0f}", 11, TOKENS["red"], lab.MONO,
                          anchor="middle"))
    s.append(lab.text(40, h - 72, f"ink to stock is {CAP['span']:.1f} points of "
             f"greyscale. Each gap must be at least {CAP['floor']}.", 13, INK,
             lab.MONO, spacing=0.3))
    s.append(lab.text(40, h - 50, f"{CAP['bands']} bands need {CAP['bands']+1} gaps "
             f"= {(CAP['bands']+1)*CAP['floor']}, which fits. 3 bands need "
             f"{4*CAP['floor']}, which does not.", 13, INK, lab.MONO, spacing=0.3))
    s.append(lab.text(40, h - 24, "So three chromatic inks can never all be tonally "
             "distinct. The third has to earn its place another way.", 13,
             TOKENS["red"], lab.MONO, weight="bold", spacing=0.3))
    s.append(lab.svg_close())
    return "".join(s)


def demo(trio, title, note, w=1180, h=330):
    """
    The test that matters: a real bounded comparison, not swatches. Does it
    survive having its colour removed.
    """
    s = [lab.svg_open(w, h)]
    s.append(lab.text(40, 36, title.upper(), 15, INK, lab.DISPLAY, "bold", spacing=1.2))
    series = [("Rescue and EMS", 72.42), ("Everything else", 25.95), ("All fire", 1.58)]
    x0, y0, bw, bh = 40, 66, w - 430, 54
    for i, ((label, pct), col) in enumerate(zip(series, trio)):
        y = y0 + i * (bh + 16)
        s.append(lab.rect(x0, y, max(bw * pct / 100, 3), bh, col))
        s.append(lab.rect(x0, y, bw, bh, "none", stroke=INK, stroke_width=1))
        s.append(lab.text(x0 + bw + 20, y + bh / 2 + 5, f"{label}  {pct}%", 14,
                          INK, lab.MONO, spacing=0.3))
    s.append(lab.text(40, h - 44, note, 12, INK, lab.MONO, spacing=0.3))
    s.append(lab.text(40, h - 22, "18,251,127 incidents. Florida only, 2020 through "
                      "2025. Not a national record.", 11, INK, lab.MONO, spacing=0.3))
    s.append(lab.svg_close())
    return "".join(s)


def best_set(pool, k, must=()):
    """
    The most tonally spread k from pool, optionally forced to include `must`.

    stock and ink belong in `must` for any honest answer: every surface already
    uses both, so a chromatic ink that separates from the others but collides
    with the field it sits on has not solved anything.
    """
    best = None
    for combo in combinations([p for p in pool if p not in must], k):
        full = tuple(must) + combo
        worst = min(separation(ALL[a], ALL[b]) for a, b in combinations(full, 2))
        if best is None or worst > best[0]:
            best = (worst, full)
    return best


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    today = [(n, TOKENS[n]) for n in CHROMATIC]
    names5 = [n for n, _ in today]
    global MATRIX_SVG, MATRIX_H
    MATRIX_SVG = matrix(names5, "02 · every pair of the five, measured",
                        "{fails} of {total} pairs fail. Every one of them involves "
                        "red, blue or green against each other.")
    MATRIX_H = int(MATRIX_SVG.split('height="')[1].split('"')[0])
    fails_now = [(a, b, separation(TOKENS[a], TOKENS[b]))
                 for a, b in combinations(names5, 2)
                 if separation(TOKENS[a], TOKENS[b]) < lab.MONO_FLOOR]

    panels = [
        lab.Panel(swatches(today, "01 · the five chromatic inks today",
                           "Each swatch sits directly above itself with hue removed."),
                  1180, 304, "The collision",
                  "red, blue and green land on one value. Only orange and yellow separate.",
                  [("spread", max(gray(h) for _, h in today) - min(gray(h) for _, h in today))]),

        lab.Panel(MATRIX_SVG, 1180, MATRIX_H, "Where it fails",
                  f"{len(fails_now)} of 10 pairs below the floor",
                  [("failing pairs", len(fails_now))]),

        lab.Panel(capacity_panel(), 1180, 330, "The actual constraint",
                  "this is a property of ink and stock, not of how many hues exist",
                  [("span", CAP["span"]), ("bands", CAP["bands"])]),

        lab.Panel(swatches([(k, v) for k, v in LADDER.items() if k.endswith("deep")],
                           f"04 · band 1, every hue at grey {CAP['values'][0]:.0f}",
                           "Solved for the value, not produced by an operation."),
                  1180, 304, "The proposal, deep band",
                  "five hues, one tonal value, mutually safe against ink and stock"),

        lab.Panel(swatches([(k, v) for k, v in LADDER.items() if k.endswith("pale")],
                           f"05 · band 2, every hue at grey {CAP['values'][1]:.0f}",
                           "Lightened toward stock, which is what less ink on the sheet does."),
                  1180, 304, "The proposal, pale band",
                  "same five hues, the second value"),
    ]

    # With stock and ink forced in, because every surface uses them.
    w3_now, set3_now = best_set(names5, 3, must=("stock", "ink"))
    w3_all, set3_all = best_set(list(COLS), 3, must=("stock", "ink"))
    w2_all, set2_all = best_set(list(COLS), 2, must=("stock", "ink"))
    trio_now = [n for n in set3_now if n not in ("stock", "ink")]
    pair_new = [n for n in set2_all if n not in ("stock", "ink")]

    panels += [
        lab.Panel(demo([COLS[n] for n in trio_now], "06 · best three available today",
                       f"{' · '.join(trio_now)}, on stock, with ink. Closest pair "
                       f"{w3_now:.0f}, under the {lab.MONO_FLOOR} floor. Adding the "
                       f"bands does not help: the best three anywhere is still "
                       f"{w3_all:.0f}."),
                  1180, 330, "Three inks, today and at best",
                  "no choice of hue passes, so this panel is also the ceiling",
                  [("worst pair", w3_now)]),
        lab.Panel(demo([COLS[pair_new[0]], COLS[pair_new[1]], INK],
                       "07 · two bands plus ink, which does pass",
                       f"{' · '.join(pair_new)} and ink, on stock. Closest pair "
                       f"{w2_all:.0f}. The third series is carried by ink, not by a "
                       f"third hue."),
                  1180, 330, "What actually works",
                  f"stock + ink + {' + '.join(pair_new)}",
                  [("worst pair", w2_all)]),
    ]

    sheet = lab.contact_sheet(panels, OUT / "01-palette.png", cols=1, scale=0.74)

    print(f"\n  study 01 · palette\n  {'=' * 64}")
    print(f"\n  the five chromatic inks, in greyscale")
    for n, h in today:
        print(f"    {n:8s} {h}  {gray(h):6.1f}")
    print(f"\n  pairs below the {lab.MONO_FLOOR} floor: {len(fails_now)} of 10")
    for a, b, s in fails_now:
        print(f"    {a:8s} vs {b:8s} {s:5.1f}")
    print(f"\n  tonal capacity between ink and stock")
    print(f"    range            {CAP['ink']:.1f} to {CAP['stock']:.1f}  = {CAP['span']:.1f}")
    print(f"    floor            {CAP['floor']}")
    print(f"    bands that fit   {CAP['bands']}   at {', '.join(f'{v:.0f}' for v in CAP['values'])}")
    print(f"    3 bands would need {4*CAP['floor']} and there are only {CAP['span']:.0f}")
    print(f"\n  the bands, solved per hue")
    for n, h in LADDER.items():
        print(f"    {n:14s} {h}  {gray(h):6.1f}")
    print(f"\n  with stock and ink counted, because every surface uses them")
    def verdict(w):
        return "passes" if w >= lab.MONO_FLOOR else "FAILS"
    for k in (1, 2, 3):
        w, c = best_set(list(COLS), k, must=("stock", "ink"))
        inks = ", ".join(n for n in c if n not in ("stock", "ink"))
        print(f"    stock + ink + {k} chromatic  {inks:38s} worst {w:5.1f}  {verdict(w)}")
    print(f"\n  so the safe chromatic budget is 2, not the 3 design_system.md allows.")
    print(f"  a third ink cannot be made tonally distinct by any choice of hue.")
    print(f"\n  {sheet}")
    print(f"  {sheet.with_name(sheet.stem + '-mono.png')}   <- the read that matters")


if __name__ == "__main__":
    main()
