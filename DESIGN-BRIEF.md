# Prompt for Claude design

Paste everything below the line, and attach `emr-inc-standalone.html` and
`emr-inc-research-standalone.html`. Fill in the bracketed direction in §1 before
sending; everything else is standing context that should not need editing.

Kept in the repo so the next revision round starts from the same brief instead of
a fresh description of the constraints.

---

I'm attaching two self-contained HTML files for **emr-inc.net**, the landing page
for EMR Inc. (Emergency Medical Resolutions Inc.). Both files are complete and
runnable: styles are inlined, there is no JavaScript, and internal links are
stubbed. `emr-inc-standalone.html` is the landing page. `emr-inc-research-standalone.html`
is the research page.

I want a visual design revision. Read both files first, then work from the
constraints below.

## 1. What I want changed

[REPLACE THIS. Be specific about the problem, not the solution. For example:
"the landing page reads as a wall of stacked full-width sections and I want more
compositional variety" or "the three product cards are three identical boxes and
the hierarchy between them is wrong" or "the research page figure is strong but
the page around it is plain."]

Everything not named here should stay as it is.

## 2. Who this is for

EMR Inc. builds software for firefighters and EMS personnel, sold through IAFF
locals rather than to departments or employers. The audience is a working
firefighter and a union officer, not a healthcare executive. The company's
argument is that publicly funded emergency dispatch and incident data is being
closed off, and that this is measurable harm.

The tone that works: plain, evidence-first, slightly adversarial toward the
institutions closing the data. The tone that fails: startup optimism, safety-
industry stock photography, anything that reads like a hospital brochure or a
government portal.

## 3. Design system — these are fixed

Implementation of `EMR-INC/OHPAH-DESIGN · design_system.md v1.1`. Do not
substitute your own palette, type scale, or spacing.

**Color**
```
--ink-900   #0A1017    --steel-400  #5A6B7D    --white     #FFFFFF
--navy-700  #12243F    --steel-150  #C9D2DA    --beam-500  #F2A33C
--navy-500  #1E3A5F    --ivory-50   #F6F3EC    --beam-700  #C97C1C
```
Amber (`--beam-500`) is the **only** accent and it is nearly always wrong to add
more of it. On the research page figure it already carries a specific meaning:
"cause code that the NFIRS specification does not define." Do not reuse it
elsewhere on that page for anything decorative.

**Type** — three families, each with one job.
- **Archivo** (600/700) sets display and headings. It never sets a paragraph.
- **DM Sans** (400/500/600) sets body copy and h3.
- **IBM Plex Mono** (500/600) carries measurements, labels, and data. Nothing else.
- 15px is the floor. Body is 17/26. Max line length 68 characters.

**Spacing** — 8pt base: 4, 8, 16, 24, 40, 64, 96, 144. Container 1200px, gutter 24px.

**Radius** — 4px controls, 6px containers, 3px chips. Never a pill, never a circle
on a control. "999 nowhere."

**Section fields** — every section sits on exactly one of `field-ivory`,
`field-white`, `field-navy`, `field-ink`, and its type colors flip accordingly.
If you move a component between fields, check its color variant. Specifically:
`.btn--line` is ivory text for dark fields and becomes invisible on white; the
light-field variant is `.btn--line-dark`.

## 4. Copy rules — hard constraints

- **No em dashes.** Anywhere. Use a comma, a colon, or a full stop.
- **Never the word "heroes"**, or any variant of heroism, sacrifice, or "the
  brave men and women."
- **No causal health claims.** The product measures dispatch activity. It does not
  diagnose, predict, or establish that anything causes cancer, sleep disorders, or
  injury. Existing disclaimers to that effect must survive the revision verbatim.
- **Departments see aggregates only.** Do not write copy implying an employer can
  see an individual member's record.
- Product naming is settled and must not drift: **Expect Victims** is the platform
  (Red Team is the OSINT tool, Blue Team is **OHPAH**, the log and leaderboard).
  **Expect Fire** is a companion product. **CALL/SIGN: DASHBOARD** is the union
  side. OHPAH is a set of metrics inside the platform, not a peer product.

## 5. The data on the research page — do not restyle this into being wrong

The figure on the research page is two panels encoding one finding. Its geometry
is load-bearing.

- **Panel 1, stacked bars.** They run from a true zero baseline against a *fixed*
  25% ceiling. The point of the panel is that the two totals, 23.34% and 23.26%,
  land about two pixels apart. If you rescale to fit, sort the bars, truncate the
  axis, or start it anywhere but zero, that near-identity stops being visible and
  the panel no longer says anything.
- **Panel 2, slope chart.** The two series cross, and **the crossing is the
  finding**: across all fires the larger unresolved group is "undetermined after
  investigation," but on structure fires it inverts to "still under investigation."
  Never sort the slope, never align its endpoints, never separate the lines to
  make it tidier.
- Segment widths sum exactly to the printed totals. There is a fourth segment in
  both bars, under one pixel wide at this scale. Do not enlarge it to make it
  visible and do not drop it to make the arithmetic tidy.
- **Do not change, round, or recompute any number.** Every figure is a real count
  from public records.

**The percentages are not interchangeable.** 23.34% and 23.26% are the share of
reports *that carry a Fire Module* whose cause of ignition is unresolved. 56.20%
uses a wider denominator: it also counts the 35,416 structure fires filed with no
Fire Module at all. The landing page deliberately carries only 56.20%, because the
narrower figures are meaningless without the chart beside them. If you move a
figure between pages, its explanatory sentence moves with it.

## 6. Structural intent

**The landing page argues. The research page proves.** Charts, per-code
breakdowns and source notes belong on the research page. The landing page gets at
most one number per section, with a link out. It was recently cut from nine
sections to five and I do not want length added back.

One hero element per section. Three levels of hierarchy, never four.

## 7. Technical constraints

- **The page must render completely with JavaScript disabled.** JS is for
  progressive enhancement only, never for content, layout, or revealing text.
- Static HTML and CSS. No framework, no build step, no component library, no
  runtime charting library. The figure is hand-authored inline SVG with literal
  coordinates and it should stay that way.
- This will be ported into a Wix editor shell later, so avoid anything exotic that
  will not survive being lifted out.
- Responsive at 1280 / 1024 / 768 / 480. The figure keeps a 660px minimum width and
  scrolls inside its own wrapper on phones rather than scaling its labels down.
- Keep the accessibility work: the SVG's `<title>`/`<desc>`, the `role="img"`, and
  `aria-labelledby`. If the figure changes, update the `<desc>` to match.

## 8. What to give me back

Complete, runnable HTML for whichever page you changed, in the same self-contained
form as the input, so I can diff it against the original. If you changed both
pages, give me both files separately. Tell me plainly what you changed and why,
and flag anything you were tempted to change but left alone because of the
constraints above.
