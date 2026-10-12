# Field Notes · artist rotation

Follows `docs/visual_variation_protocol.md` and `docs/artist_reference_matrix.md`.

## The rule that shapes this

> Use at most one primary structural move and one secondary accent move on a
> given screen. The brand is built from OHPAH's incident semantics, not from a
> collage of ten recognizable artists.

So the ten are not a checklist for one issue. They are the variation engine for a
series, which is exactly what a weekly needs. One primary per issue. The lead
reference, Lupi and Posavec, sets the first read every week: countable marks with
an explicit key. What changes is the structure underneath it.

The matrix also sets the three read depths, and a weekly should hit all three:

1. **First read** feels like Dear Data. Many countable observations, each keyed.
2. **Second read** reveals the modernist construction. Terminal arcs, crossing
   evidence bands, strong editorial frames.
3. **Third read** is a product. Responsive, keyboard reachable, plain language,
   a direct route to source.

## Issues built

### 01 · Cardiac arrest and radio documented ROSC · `build_rosc.py`

| | |
| --- | --- |
| Primary | **Lupi and Posavec.** Repeated event field. One mark per incident, gaps drawn as gaps. |
| Secondary | **Aicher.** A constructed state vocabulary tested in monochrome. |
| Why this pair | The claim is about what reached the record, so the accent move reinforces the claim rather than decorating it. |

Green and blue sit at almost the same grayscale luminance, so the ROSC ring
reads as a **shape** and not a colour. `build_rosc.py` fails the build if the
ringed mark and a plain mark are not separable in grayscale.

### 02 · The NFIRS incident type index · `build_fire.py`

| | |
| --- | --- |
| Primary | **Sutnar.** A numbered index with visible provenance, each entry reaching its source. |
| Secondary | **Beall.** One declarative route: the fire series redrawn at its own scale, three nested counts from one origin. |
| Why this pair | NFIRS incident types already **are** a numbered index, codes 1 to 9. The figure prints NFIRS' own index in NFIRS' own order and does not sort it. The data falls where the external index puts it, which is the whole argument. |

The hard problem was range. Series 3 is 72.42% and series 2 is 0.05%, a ratio of
about 1450 to 1, so an honest shared scale makes six of the nine rows sub pixel.
Three answers, all of them declared rather than hidden:

- **Rule A** keeps true proportion and separates every segment with a stock
  coloured divider, so the boundaries survive without colour. Fire is red and
  rescue is blue, and those two are the **same luminance in grayscale**, so the
  dividers are what carry the construction. A gate samples a divider against the
  fill beside it.
- **The fire series is 17 px wide** at true proportion, too narrow to number. It
  is located by a bracket and a leader, which is shape and not colour. A second
  gate samples the bracket stem against stock.
- **Index rows under 4 px** are drawn as a hollow stub at minimum width with the
  true width printed beside them. A hollow stub is a different construction, so
  a reader can see it is not to scale. Distorting the bar silently was the one
  option not available.

The figure caption names the unnumbered series by reading them back off the
geometry, so it cannot drift from the drawing when a threshold or a count moves.

The email carries a **separate, smaller figure** rather than a crop of the
poster. The poster is 1380 px tall and sets the index in 10 and 11 px mono;
scaled into a 600 px email column that is five pixels high and the image becomes
decoration. The email figure draws rule A alone at 2x, and the index, the route
and the evidence band ship as live HTML, which is what survives images being
blocked.

#### Reuse test against 01

> Reject a draft if its chart, navigation and page layout could be swapped with
> the previous study after changing only data and headings.

Not swappable. 01 has no index, no leader, no nested subsets and no
minimum width declaration; 02 has no per mark field, no rings and no time axis.

| Dimension | 01 | 02 | |
| --- | --- | --- | --- |
| Silhouette | Vertical column field | Horizontal rule over a typographic index | changed |
| Coordinate system | Categorical by day | Ordinal by an external index, NFIRS code order | changed |
| Dominant move | Countable marks | Numbered index with provenance | changed |
| Depth mechanism | Ring and halo gap on a mark | Declared magnification, nested subsets at one origin | changed |
| Typography | Display claim over a mark field | The index numeral **is** the structure | changed |
| Interaction | Static email | Static email | unchanged |

Five of six. The protocol asks for four.

## The rotation

Change at least four of the six dimensions each issue: silhouette, coordinate
system, dominant move, depth mechanism, typography, interaction.

| Issue | Primary | Construction | Silhouette | Coordinate system | |
| --- | --- | --- | --- | --- | --- |
| 01 | Lupi and Posavec | Event field, marks stacked per day | Vertical columns | Categorical by day | **built** |
| 02 | Sutnar | Numbered index with visible provenance, each entry reaching its source | Typographic block | Ordinal list | **built** |
| 03 | de Harak | Serial covers, one panel per week, same frame, changing figure | Grid of panels | Repeated frame |
| 04 | Pintori | Terminal arcs from a declared origin, every arc ending on a real node | Radial | Polar |
| 05 | Nitsche | Two evidence bands crossing only where a documented join exists | Crossed bands | Two axes meeting |
| 06 | Beall | One declarative route, one sourced fact, legible at distance | Single flat form | Minimal, one route |
| 07 | Cooper | Overview to record to source, navigated through type | Nested type | Spatial zoom |
| 08 | Maeda | Deterministic geometry responding to a reader selection | Responsive field | Reader driven |

Huber is held for a transition or campaign moment rather than a scheduled slot,
since his move is directional energy for a bounded moment and a weekly does not
need energy every week.

## Matching the move to the data, not the calendar

The rotation is an order of preference, not an obligation. Each construction has a
precondition, and running one without it produces a figure that claims more than
the geometry shows:

| Move | Do not run it unless |
| --- | --- |
| Pintori | Every arc terminates on a record that exists. No arc ends in empty space. |
| Nitsche | There is a genuinely documented join. Two things on one time axis are not a join. |
| Cooper | A selected mark can actually reach its source record under current permissions. |
| Maeda | The response is deterministic. Refresh and resize cannot change the apparent data. |
| de Harak | The panels differ by real records. The boundary is "do not make every incident appear interchangeable." |

The week picks the move. If the week's data cannot support the scheduled
construction, take the next one that fits and move the other along.

## Reuse test

> Reject a draft if its chart, 3D object, navigation and page layout could be
> swapped with the previous study after changing only data and headings.

Run it against the previous three issues before drafting, not after.
