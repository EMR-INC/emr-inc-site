"""
Study 02. The five primary structures, drawn from one dataset.

design_system.md requires a diagram to choose one primary structure:

    1. Repeated event field for accumulation
    2. Traced record for sequence
    3. Branching feed for source provenance
    4. Layered stack for joined records
    5. Bounded comparison for a defensible contrast

Issue 01 used the fifth. Deciding what issue 02 should use means seeing the
other four carrying the same numbers, because the choice is supposed to follow
from the shape of the claim, not from what was built last week.

Every form here uses the real NFIRS figures and is held to the same rules: the
chromatic budget study 01 established (stock, ink and two bands), and the three
layer test, claim then structure then evidence. Each is checked in monochrome.

    python3 studies/forms.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import lab
from lab import TOKENS, at_value, tonal_capacity, separation, multiply

OUT = Path(__file__).resolve().parent / "out"
STOCK, INK = TOKENS["stock"], TOKENS["ink"]
CAP = tonal_capacity()
DEEP, PALE = CAP["values"]

# The two chromatic bands study 01 landed on. Two, not three, because three
# never separates. Anything a third hue would have carried is carried by ink.
A = at_value("blue", PALE)    # the record layer, the big quiet mass
B = at_value("red", DEEP)     # the one declared category

# NFIRS basic incident module, pulled 2026-09-13. Florida only, 2020 to 2025.
DENOM, FIRE_N, EMS_N, FDIDS = 18_251_127, 289_121, 13_217_940, 396
FIRE_PCT, EMS_PCT = 1.58, 72.42
# Everything else is the published complement of rescue and EMS, and fire sits
# INSIDE it. Deriving it as 100 - EMS - FIRE gives 26.00%, which contradicts the
# figure already shipped in issue 01. The published pair is the source of truth.
ELSE_PCT, ELSE_N = 27.58, 5_033_187
assert abs(EMS_PCT + ELSE_PCT - 100) < 0.01, "the two shares must close on 100"
assert EMS_N + ELSE_N == DENOM, "the two counts must close on the denominator"
assert FIRE_N < ELSE_N, "fire sits inside everything else"

# One square stands for a round number, with the remainder disclosed rather than
# absorbed. An earlier version titled this 'ten thousand' over a grid where each
# square was really 16,899, which is the caption claiming more than the geometry
# shows. The system fails a diagram for exactly that.
GRID_COLS, GRID_ROWS = 40, 25
PER_SQUARE = DENOM // (GRID_COLS * GRID_ROWS)
REMAINDER = DENOM - PER_SQUARE * GRID_COLS * GRID_ROWS
GUARD = "Florida only, 2020 through 2025. Not a national record."
SRC = "NFIRS basic incident module, pulled 2026-09-13."

W, H = 1180, 620
M = 48
# A form gets the height its structure needs. One shared height meant the 1,000
# square field ran under its own key and evidence line, which a contact sheet
# shows immediately and a passing unit test never would.
HEIGHTS = {"repeated_event_field": 900}


def frame(title, claim, artist, move, h=H):
    """Claim, then room for the structure, then the evidence line. In that order."""
    s = [lab.svg_open(W, h)]
    s.append(lab.text(M, 40, title.upper(), 14, TOKENS["red"], lab.MONO, "bold", spacing=1.6))
    s.append(lab.text(M, 84, claim, 30, INK, lab.DISPLAY, "bold", spacing=-0.8))
    s.append(lab.text(W - M, 40, f"{artist} · {move}", 12, INK, lab.MONO,
                      anchor="end", spacing=0.4))
    return s


def evidence(s, h=H):
    y = h - 54
    s.append(lab.line(M, y - 16, W - M, y - 16, INK, 2))
    s.append(lab.text(M, y + 2, f"{DENOM:,} incidents across {FDIDS} departments. {SRC}",
                      11, INK, lab.MONO, spacing=0.3))
    s.append(lab.text(M, y + 20, GUARD, 11, TOKENS["red"], lab.MONO, "bold", spacing=0.3))
    s.append(lab.svg_close())
    return "".join(s)


def repeated_event_field():
    """
    1. Accumulation. One mark per unit, countable, with a key.
    Lupi and Posavec: many individual experiences, each legible as itself.
    """
    h = HEIGHTS["repeated_event_field"]
    s = frame("01 · repeated event field",
              f"ONE SQUARE IS {PER_SQUARE:,} INCIDENTS.",
              "Lupi and Posavec", "countable marks", h)
    cols, rows = GRID_COLS, GRID_ROWS
    cell, gap = 20, 4
    x0, y0 = M, 118
    total = cols * rows
    exact = FIRE_N / PER_SQUARE
    fire_cells = round(exact)
    for i in range(total):
        r, c = divmod(i, cols)
        x, y = x0 + c * (cell + gap), y0 + r * (cell + gap)
        s.append(lab.rect(x, y, cell, cell, B if i < fire_cells else A))
    key = y0 + rows * (cell + gap) + 30
    s.append(lab.rect(M, key - 12, 14, 14, B))
    s.append(lab.text(M + 24, key, f"fire, {fire_cells} squares of {total:,} "
                      f"= {FIRE_N:,} incidents = {FIRE_PCT}%", 13, INK, lab.MONO))
    s.append(lab.rect(M + 560, key - 12, 14, 14, A))
    s.append(lab.text(M + 584, key, f"everything else, {total - fire_cells:,} squares",
                      13, INK, lab.MONO))
    s.append(lab.text(M, key + 26, f"Fire is {exact:.2f} squares and is drawn as "
                      f"{fire_cells}. {REMAINDER:,} incidents do not fill a square "
                      f"and are not drawn.", 12, TOKENS["red"], lab.MONO, weight="bold"))
    return evidence(s, h)


def traced_record():
    """
    2. Sequence. A path that ends on a real node, never in empty space.
    Pintori: draw the system's output, arcs terminate visibly.
    """
    s = frame("02 · traced record", "ONE INCIDENT, END TO END.",
              "Pintori", "terminal arcs")
    stops = [("dispatched", 0), ("en route", 1.2), ("on scene", 6.4),
             ("transporting", 19.8), ("at hospital", 31.1), ("in service", 48.6)]
    x0, x1, y = M + 30, W - M - 190, 240
    span = stops[-1][1]
    for i, (label, t) in enumerate(stops):
        x = x0 + (t / span) * (x1 - x0)
        last = i == len(stops) - 1
        if i:
            px = x0 + (stops[i - 1][1] / span) * (x1 - x0)
            s.append(lab.line(px, y, x, y, INK, 3))
        # Every stop is a node, and the last one is closed, not trailing off.
        s.append(f'<circle cx="{x:.1f}" cy="{y}" r="{11 if last else 8}" '
                 f'fill="{B if last else A}" stroke="{INK}" stroke-width="2.5"/>')
        # Stops cluster at the start, so alternate the label height rather than
        # let "dispatched" and "en route" overprint each other.
        up = -28 if i % 2 == 0 else -50
        down = 34 if i % 2 == 0 else 54
        s.append(lab.text(x, y + up, label, 12, INK, lab.MONO, anchor="middle"))
        s.append(lab.text(x, y + down, f"{t:g} min", 12, INK, lab.MONO,
                          weight="bold", anchor="middle"))
    s.append(lab.text(M, y + 100, "The path stops at a node that exists. Nothing is "
                      "drawn past the last recorded timestamp.", 13, INK, lab.MONO))
    s.append(lab.text(M, y + 124, "Times are illustrative of the structure, not a "
                      "measured median. A shipped version reads them from the record.",
                      12, TOKENS["red"], lab.MONO, weight="bold"))
    return evidence(s)


def branching_feed():
    """
    3. Provenance. Where a record came from, as structure.
    Sutnar: navigation and cross reference are designed information.
    """
    s = frame("03 · branching feed", "WHERE ONE NUMBER COMES FROM.",
              "Sutnar", "designed provenance")
    root = (M + 150, 150)
    s.append(lab.rect(root[0] - 150, root[1] - 24, 300, 44, A, stroke=INK, stroke_width=2))
    s.append(lab.text(root[0], root[1] + 4, f"{FIRE_PCT}% was fire", 17, INK,
                      lab.MONO, weight="bold", anchor="middle"))
    kids = [("1  NFIRS basic incident module", "the table"),
            ("2  incident type, first two digits", "the field"),
            ("3  2020 through 2025, Florida", "the window"),
            ("4  18,251,127 of 18,251,138 rows", "the denominator"),
            ("5  11 rows, non numeric type", "what was dropped")]
    y = root[1] + 76
    for i, (label, role) in enumerate(kids):
        yy = y + i * 54
        s.append(lab.line(root[0] - 150 + 24, root[1] + 20, root[0] - 150 + 24, yy, INK, 2))
        s.append(lab.line(root[0] - 150 + 24, yy, root[0] - 150 + 56, yy, INK, 2))
        s.append(lab.rect(root[0] - 150 + 56, yy - 17, 12, 34, B if i == 4 else INK)
                 if i == 4 else lab.rect(root[0] - 150 + 56, yy - 17, 12, 34, INK))
        s.append(lab.text(root[0] - 150 + 80, yy + 5, label, 14, INK, lab.MONO))
        s.append(lab.text(root[0] + 430, yy + 5, role, 12, INK, lab.MONO))
    s.append(lab.text(M, H - 118, "Every step is numbered, so a reader can ask about "
                      "step 4 rather than about the number.", 13, INK, lab.MONO))
    return evidence(s)


def layered_stack():
    """
    4. Joined records. An intersection means a documented join.
    Nitsche via Huber: transparent structures, overprint where they actually meet.
    """
    s = frame("04 · layered stack", "WHERE TWO RECORDS AGREE.",
              "Nitsche and Huber", "overprint as evidence")
    x0, y0, w, h = M + 60, 150, 420, 230
    s.append(lab.rect(x0, y0, w, h, A))
    s.append(lab.text(x0 + 10, y0 - 12, "dispatch record", 13, INK, lab.MONO, weight="bold"))
    s.append(lab.rect(x0 + 250, y0 + 90, w, h, B))
    s.append(lab.text(x0 + 260, y0 + 82, "incident record", 13, INK, lab.MONO, weight="bold"))
    # The overlap is the multiply of the two, which is what the inks would do.
    s.append(lab.rect(x0 + 250, y0 + 90, w - 250, h - 90, multiply(A, B)))
    s.append(lab.text(x0 + 258, y0 + 118, "both", 15, STOCK, lab.MONO, weight="bold"))
    s.append(lab.text(W - M - 300, y0 + 30, "The overlap is not a graphic effect.", 13,
                      INK, lab.MONO))
    s.append(lab.text(W - M - 300, y0 + 52, "It is the set of incidents carried", 13,
                      INK, lab.MONO))
    s.append(lab.text(W - M - 300, y0 + 74, "by both records, 98.6% agreement.", 13,
                      INK, lab.MONO))
    s.append(lab.text(W - M - 300, y0 + 110, "Drawn any wider it would claim", 12,
                      TOKENS["red"], lab.MONO, weight="bold"))
    s.append(lab.text(W - M - 300, y0 + 130, "a join that was never measured.", 12,
                      TOKENS["red"], lab.MONO, weight="bold"))
    return evidence(s)


def bounded_comparison():
    """
    5. Defensible contrast. What issue 01 shipped, here for comparison.
    Beall: flat forms, legible at distance.
    """
    s = frame("05 · bounded comparison", "FIRE IS 1.58% OF THE JOB.",
              "Beall", "flat forms at distance")
    side = 300
    x0, y0 = M, 128
    s.append(lab.rect(x0, y0, side, side, STOCK, stroke=INK, stroke_width=2))
    hz = y0 + side * (1 - EMS_PCT / 100)
    s.append(lab.rect(x0, hz, side, y0 + side - hz, A))
    fs = (FIRE_PCT / 100) ** 0.5 * side
    fx, fy = x0 + side * 0.42, hz - fs / 2
    s.append(lab.rect(fx, fy, fs, fs / 2, B))
    s.append(lab.rect(fx, hz, fs, fs / 2, multiply(B, A)))
    tx = x0 + side + 56
    for i, (lab_, pct, n, col) in enumerate(
            [("RESCUE AND EMS", EMS_PCT, EMS_N, A),
             ("EVERYTHING ELSE", ELSE_PCT, ELSE_N, STOCK),
             ("ALL FIRE", FIRE_PCT, FIRE_N, B)]):
        yy = y0 + i * 96
        s.append(lab.rect(tx, yy, 26, 26, col, stroke=INK, stroke_width=1.5))
        s.append(lab.text(tx + 38, yy + 20, lab_, 15, INK, lab.DISPLAY, "bold", spacing=0.6))
        s.append(lab.text(tx + 38, yy + 48, f"{pct:.2f}%", 22, INK, lab.DISPLAY, "bold"))
        s.append(lab.text(tx + 38, yy + 70, f"{n:,} incidents", 12, INK, lab.MONO))
    s.append(lab.text(x0, y0 + side + 34, "Area is the encoding: a share of the area is "
                      "a share of the incidents.", 13, INK, lab.MONO))
    s.append(lab.text(x0, y0 + side + 56, "Fire sits inside everything else, which is "
                      "why the two shares close on 100 without it.", 12, INK, lab.MONO))
    return evidence(s)


FORMS = [
    ("Repeated event field", "accumulation", repeated_event_field),
    ("Traced record", "sequence", traced_record),
    ("Branching feed", "provenance", branching_feed),
    ("Layered stack", "joined records", layered_stack),
    ("Bounded comparison", "contrast  · shipped as issue 01", bounded_comparison),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lab.assert_chromatic_budget(["blue", "red"])
    checks = lab.assert_mono([
        ("record layer vs stock", A, STOCK),
        ("declared category vs stock", B, STOCK),
        ("record layer vs category", A, B),
        ("category vs ink", B, INK),
    ])

    panels = []
    for i, (name, use_for, fn) in enumerate(FORMS):
        svg = fn()
        ph = int(svg.split('height="')[1].split('"')[0])
        panels.append(lab.Panel(svg, W, ph, f"{i+1}. {name}", use_for,
                                [("worst sep", min(v for _, v in checks))]))
    sheet = lab.contact_sheet(panels, OUT / "02-forms.png", cols=1, scale=0.78)

    print(f"\n  study 02 · the five primary structures\n  {'=' * 64}")
    print(f"\n  two chromatic bands, per study 01")
    print(f"    record layer   blue pale  {A}  grey {lab.gray(A):.0f}")
    print(f"    category       red deep   {B}  grey {lab.gray(B):.0f}")
    print(f"    overprint      multiply   {multiply(A, B)}  grey {lab.gray(multiply(A, B)):.0f}")
    print(f"\n  monochrome separations, floor {lab.MONO_FLOOR}")
    for name, sep in checks:
        print(f"    {name:28s} {sep:6.1f}")
    print(f"\n  forms drawn")
    for i, (name, use_for, _) in enumerate(FORMS):
        print(f"    {i+1}. {name:22s} {use_for}")
    print(f"\n  {sheet}")
    print(f"  {sheet.with_name(sheet.stem + '-mono.png')}")


if __name__ == "__main__":
    main()
