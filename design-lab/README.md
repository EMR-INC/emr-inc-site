# Design lab

A place to try things and look at them. Nothing here ships.

Every study renders to a contact sheet, in colour and in greyscale, because an
idea about a visual system should be looked at rather than described. The
greyscale sheet is the one that matters: `design_system.md` fails any diagram
whose meaning dies when colour is removed, and that failure is invisible on a
colour screen.

```
python3 run.py              # everything
python3 run.py palette      # one study
```

Sheets land in `studies/out/`, which is gitignored. Regenerate rather than
commit them.

## What is here

| | Study | Question |
| --- | --- | --- |
| 01 | `studies/palette.py` | Should the palette be expanded, and with what |
| 02 | `studies/forms.py` | Which of the five primary structures suits which claim |
| 03 | `studies/layout.py` | How else can a three section issue be held |
| 04 | `studies/collage.py` | Where the line falls between field and data |

`lab.py` is the shared harness: the tokens, the colour maths including overprint,
the gates, the two renderers and the contact sheet. A study that wants a new
capability should add it there rather than carry its own copy.

## Measuring a reference

Study 04 takes any image and reports its inks on the same terms, so collage
looks can be compared rather than argued about:

```
python3 studies/collage.py path/to/reference.png
```

It pulls inks by saturation and hue family and takes the median of each, because
quantising the whole image averages a small hot accent into a blend that appears
nowhere in the picture. The first attempt returned `#88506E`, a purple nothing in
the image was.

The first reference measured: ground `#E9D9C1` at grey 219.0, cool `#1644BB` at
67.8, warm `#F53807` at 106.9. Cool against ground 151.2 and warm against ground
112.1 both pass. **Cool against warm is 39.1 and fails.**

That is not a verdict on the image, which works. It never asks those two inks to
be told apart: every photograph, drawing and arc is the blue, and the warm is
torn strips, a triangle and one circle. A field accent, never a category. Which
is study 01's finding reached from the other direction, and the test to apply to
the next reference: when the two inks collide in greyscale, ask what the accent
is doing. Field, accent or endpoint is fine. A second data category is not.

Worth noting the reference spreads its two inks 39.1 apart where the system's
red and blue sit 1.6 apart.

## What came out of study 01

The brief was "expand the palette". Measuring first said something more useful,
and changed what the right answer is.

**Three of the five chromatic inks sit on one tonal value.** Red 88.4, blue 86.8,
green 87.7. Six of the ten pairs separate by less than the 60 the figure build
already enforces, and every failing pair involves red, blue or green against
each other. Any surface using two of those three is already leaning on hue.

**The constraint is not the number of hues.** Between ink (30.9) and stock
(235.2) there are 204.3 points of greyscale. At a floor of 60 that fits two
chromatic bands. Three would need 240. So no palette of any size can give three
chromatic inks that are all tonally distinct, which means `design_system.md`'s
"at most three chromatic inks" cannot be satisfied in monochrome. The safe
budget is two. A third ink has to earn its place another way: overprint,
pattern, or never sitting adjacent to the other two.

**The proposal is therefore not more hues.** It is the same five hues placed on
two measured bands, deep at 99 and pale at 167, each solved for the value rather
than produced by an operation:

| | deep · grey 99 | pale · grey 167 |
| --- | --- | --- |
| red | `#D73137` | `#E48E8A` |
| blue | `#346FA5` | `#92ACC1` |
| green | `#387D4F` | `#94B496` |
| yellow | `#766911` | `#CFB203` |
| orange | `#AA4B24` | `#E3946E` |

Solving for the value matters. The first version of this ladder darkened each
hue by multiplying it with ink, which looks like a method and is not one: it
crushed all five darks into a band eleven points wide, below ink, reproducing
the exact flatness the ladder was meant to fix.

None of this is adopted. It is a measurement and a proposal, and changing the
system is a decision for whoever owns `design_system.md`.

## What the contact sheet caught

Worth recording, because it is the argument for building the harness first.
Each of these passed every check that was not a picture:

- Study 02's first headline read "one square is ten thousand incidents" over a
  grid where each square was really 16,899. The caption claimed more than the
  geometry showed, which is the thing the three layer test exists to stop.
- Study 02 derived "everything else" as 100 minus rescue minus fire, giving
  26.00%, contradicting the 27.58% already shipped in issue 01. Fire sits inside
  everything else; the two shares close on 100 without it.
- Study 01's matrix silently clipped its last two rows against a hardcoded
  height, hiding four of the ten measurements.
- Four sets of labels overprinted each other.

## Rules a study is held to

- Stock and ink on every surface, with the chromatic budget study 01 arrived at.
- Claim, structure, evidence. In that order, every panel.
- Every figure carries its source, window and denominator. The Florida scope
  guard travels with any NFIRS number, because that data is Florida only and
  must never be described as a national record.
- Illustrative numbers are labelled illustrative, in red, on the panel.
- Email work is real HTML checked against the eight constructs that break in
  Gmail and Outlook and against the 102,400 byte clip.

## What this is not

Not a proposal to change `design_system.md`, not a new brand, and not connected
to the retired Spotlight 1 bit system. `brain.md` is explicit that the brand
system and that one are separate on purpose and every attempt to merge them has
produced something belonging to neither.
