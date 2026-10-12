# Field Notes, the weekly email chassis

Generates the EMR Inc. Field Notes email: an HTML part, a plain text part, the
figure as SVG and PNG, and a send proof page for review.

Nothing here is served. These are build scripts, and the repository root is
public, so the rendered email is deliberately gitignored rather than committed.

## Running it

```
python3 build_issue01.py     # the issue: email.html, email.txt, figure
python3 build_preview.py 01  # the send proof page
python3 palette/build.py     # the palette study
```

Fonts come from the system: Archivo, Archivo Black and Courier Prime. The
renderer is headless Chromium.

## Files

| File | Role |
| --- | --- |
| `build_issue01.py` | The issue. Three sections, copy, email assembly, voice gate |
| `figure_v2.py` | The figure. Bounded comparison drawn as a scale jump |
| `build_02.py` | NFIRS data layer, fail closed derive, the shared gates |
| `build_rosc.py` | An alternate issue on cardiac arrest and radio documented ROSC |
| `build_preview.py` | Send proof: inbox row, images on and off, phone width |
| `palette/build.py` | The palette study, measured rather than asserted |
| `ROTATION.md` | Artist rotation and the variation protocol across issues |

## Structure of an issue

Set by the client, three sections:

1. **Dear Chief.** A new letter every issue. Biting, ironic, its own provocation
   rather than a set up for the figure.
2. **The number.** One figure with the data art.
3. **The update.** Product or business news.

## What the build refuses to ship

The scripts fail closed. If any of these trips, nothing is written.

- **The scope guard.** This NFIRS data is Florida only. `data/nfirs-incident-composition.json`
  states that a count of distinct states over the table returns 1 and that it must
  never be described as a national record. The guard has to survive into the
  figure, the HTML, the text part and the alt text.
- **The arithmetic.** Series counts must sum to the published denominator, and
  that denominator plus the dropped rows must equal the row total. Every number
  that appears in the copy is checked back against the data.
- **The voice gate.** Banned vocabulary from `brand_guidelines.md`, plus hyphens,
  em dashes and exclamation marks, each fail the build.
- **The monochrome gates.** `design_system.md` fails any diagram whose meaning
  dies when colour is removed. Red is 88 and blue is 87 in perceived value, so
  the figure cannot lean on hue; the gates sample the rendered pixels and prove
  each element separates by construction.
- **Email client safety.** Eight constructs that break in Gmail or Outlook, and
  the 102,400 byte ceiling where Gmail clips.

## Before a send

1. The figure needs an absolute hosted URL. It is a relative path here.
2. Preference and unsubscribe destinations are `#`.
3. Dark mode is untested. Apple Mail and Gmail will invert the cream stock.
4. Test in real clients. The static checks prove the markup avoids known
   breakage; they are not Litmus or Email on Acid.
5. `docs/limits.md` in the design repo requires a human who knows the category to
   approve anything external before it ships. The build does not clear anything.
