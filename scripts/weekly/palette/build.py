#!/usr/bin/env python3
"""OHPAH palette study. Every swatch and every number comes out of one source."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
def rgb(h): return tuple(int(h[i:i+2],16) for i in (1,3,5))
def hx(t): return "#%02X%02X%02X" % tuple(max(0,min(255,round(c))) for c in t)
def gray(h):
    r,g,b = rgb(h); return 0.299*r+0.587*g+0.114*b           # perceived / photocopy
def greyhex(h):
    v = gray(h); return hx((v,v,v))

TOK = [("stock","#F1EBDD","Primary field"), ("ink","#10213B","Type, axes, rules"),
       ("red","#D5222A","One traced route or declared category"),
       ("blue","#2363A0","Record layer"), ("green","#287443","Connected field"),
       ("yellow","#E5C500","Highlight or crossed band"),
       ("orange","#D95A25","Optional transition or stack layer"),
       ("dark","#161A20","High contrast inset"), ("white","#FFFFFF","Document field")]

STOCK, INK = "#F1EBDD", "#10213B"
def blend(t):
    lo, hi, s, i = 0.0, 1.0, rgb(STOCK), rgb(INK)
    for _ in range(40):
        m = (lo+hi)/2
        if gray(hx(tuple(s[k]+(i[k]-s[k])*m for k in range(3)))) > t: lo = m
        else: hi = m
    return hx(tuple(s[k]+(i[k]-s[k])*((lo+hi)/2) for k in range(3)))

# Eight steps, because the index has eight series once fire is pulled out for the
# accent. The targets deliberately straddle red's 88 rather than landing near it:
# a neutral step within ~12 points of the accent would collide in mono and undo
# the whole point of the exercise.
FILL_T = (205, 180, 155, 130, 108, 68, 48, 31)
RAMP = [(f"n{t}", INK if t == 31 else blend(t)) for t in FILL_T]

# NFIRS series, code order, with the share that sets each one's tone.
SER = [("1","Fire",1.58),("2","Overpressure",0.05),("3","Rescue and EMS",72.42),
       ("4","Hazardous",1.49),("5","Service call",7.18),("6","Good intent",10.97),
       ("7","False alarm",6.08),("8","Severe weather",0.08),("9","Special",0.14)]

# Today: ink for everything, red for fire, blue for the one big one. Three values.
NOW = {"1":"#D5222A","3":"#2363A0"}
# Proposed: tone carries magnitude, red stays the declared category. Rank the
# eight non fire series by share and give each its own step of the ramp.
rank = sorted([s for s in SER if s[0] != "1"], key=lambda s: -s[2])
steps = [h for _, h in RAMP][::-1]               # darkest first
assert len(steps) == len(rank), f"{len(steps)} steps for {len(rank)} series"
NEW = {"1": "#D5222A"}
for idx, (c, _, _) in enumerate(rank): NEW[c] = steps[idx]

W, BW, BH = 1000, 940, 70
def bar(mapping, grey=False):
    conv = greyhex if grey else (lambda h: h)
    bg, frame = conv(STOCK), conv(INK)
    x, out, divs = 30.0, [], []
    for c, lab, pct in SER:
        w = pct / 100 * BW
        out.append(f'<rect x="{x:.1f}" y="18" width="{max(w, 0.5):.2f}" '
                   f'height="{BH}" fill="{conv(mapping.get(c, INK))}"/>')
        x += w
        divs.append(f'<rect x="{x-1.5:.1f}" y="18" width="3" height="{BH}" fill="{bg}"/>')
    return (f'<svg viewBox="0 0 {W} 106" width="100%" role="img">'
            f'<rect width="{W}" height="106" fill="{bg}"/>' + "".join(out)
            + "".join(divs[:-1])
            + f'<rect x="30" y="18" width="{BW}" height="{BH}" fill="none" '
              f'stroke="{frame}" stroke-width="2.5"/></svg>')

def count_distinct(mapping):
    vals = sorted(round(gray(mapping.get(c,"#10213B"))) for c,_,_ in SER)
    n, last = 1, vals[0]
    for v in vals[1:]:
        if v - last >= 12: n += 1; last = v
    return n

sw = lambda h: f'<span class="chip" style="background:{h}"></span>'
tokrows = "".join(
    f'<tr><td class="tk">{n}</td><td class="hx">{h}</td>'
    f'<td>{sw(h)}</td><td>{sw(greyhex(h))}</td>'
    f'<td class="num">{gray(h):.0f}</td><td class="role">{r}</td></tr>'
    for n,h,r in TOK)
ramprows = "".join(
    f'<div class="rc"><span class="chip wide" style="background:{h}"></span>'
    f'<span class="chip wide" style="background:{greyhex(h)}"></span>'
    f'<b>{n}</b><code>{h}</code><span class="num">{gray(h):.0f}</span></div>'
    for n, h in RAMP)

HTML = f'''<title>OHPAH Palette Study</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700&family=Archivo+Black&family=Courier+Prime:wght@400;700&display=swap">
<style>
/* Layout: a spec sheet on a graphite bench. Specimens sit on their own cream
   ground, because that is the only ground these inks ever print on. */
:root{{--bench:#15181D;--bench-2:#1D222A;--rule:#2E3741;--fg:#E6E9ED;--fg-dim:#98A3B0;
  --accent:#D5222A;--ok:#4F9D69;--focus:#7FB2E5;
  --display:"Archivo Black","Archivo",system-ui,sans-serif;
  --body:"Archivo",system-ui,-apple-system,sans-serif;
  --mono:"Courier Prime","Courier New",monospace;}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{
  --bench:#0E1116;--bench-2:#161A21;--rule:#272F39;--fg:#E6E9ED;--fg-dim:#8E99A6;
  --accent:#E8434A;--ok:#5FAF79;--focus:#7FB2E5;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bench:#0E1116;--bench-2:#161A21;--rule:#272F39;--fg:#E6E9ED;
  --fg-dim:#8E99A6;--accent:#E8434A;--ok:#5FAF79;--focus:#7FB2E5;color-scheme:dark}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bench);color:var(--fg);font-family:var(--body)}}
.wrap{{max-width:980px;margin:0 auto;padding-block:30px 60px;padding-left:16px;padding-right:16px}}
:is(a,button):focus-visible{{outline:2px solid var(--focus);outline-offset:2px}}
.lede{{border-top:3px solid var(--fg);padding-top:12px}}
.tag{{font-family:var(--mono);font-size:11px;font-weight:700;letter-spacing:1.6px;
  text-transform:uppercase;color:var(--accent)}}
h1{{margin:6px 0 10px;font-family:var(--display);font-size:clamp(23px,4.4vw,34px);
  letter-spacing:-.4px;text-wrap:balance}}
.lede p{{margin:0;max-width:62ch;color:var(--fg-dim);font-size:15px;line-height:23px}}
h2{{margin:40px 0 6px;font-family:var(--display);font-size:20px;letter-spacing:-.2px}}
h2 .k{{font-family:var(--mono);font-size:11px;font-weight:700;letter-spacing:1.6px;
  color:var(--accent);display:block;margin-bottom:5px}}
p.b{{margin:0 0 12px;max-width:66ch;font-size:15px;line-height:24px;color:var(--fg)}}
p.b.dim{{color:var(--fg-dim)}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th{{text-align:left;font-family:var(--mono);font-size:10px;letter-spacing:1.2px;
  text-transform:uppercase;color:var(--fg-dim);font-weight:700;padding:0 8px 7px 0;
  border-bottom:1px solid var(--rule)}}
td{{padding:6px 8px 6px 0;border-bottom:1px solid var(--rule);vertical-align:middle}}
.tk{{font-weight:700}} .hx,.num{{font-family:var(--mono);font-variant-numeric:tabular-nums}}
.num{{text-align:right}} .role{{color:var(--fg-dim)}}
.chip{{display:inline-block;width:40px;height:20px;border:1px solid var(--rule);
  vertical-align:middle}}
.chip.wide{{width:84px;height:26px}}
.rc{{display:flex;align-items:center;gap:12px;padding:5px 0;flex-wrap:wrap}}
.rc b{{min-width:46px;font-size:13px}}
.rc code{{font-family:var(--mono);font-size:12px;color:var(--fg-dim)}}
.rc .num{{font-family:var(--mono);font-size:12px;color:var(--fg-dim);min-width:34px}}
.hit{{border:1px solid var(--accent);border-left:3px solid var(--accent);
  background:var(--bench-2);padding:14px 16px;margin:14px 0}}
.hit b{{font-family:var(--mono);font-size:11px;letter-spacing:1.4px;text-transform:uppercase;
  color:var(--accent);display:block;margin-bottom:5px}}
.hit p{{margin:0 0 8px;font-size:14px;line-height:22px}} .hit p:last-child{{margin:0}}
.spec{{background:var(--bench-2);border:1px solid var(--rule);padding:16px;margin:12px 0}}
.spec .cap{{font-family:var(--mono);font-size:10px;letter-spacing:1.3px;text-transform:uppercase;
  color:var(--fg-dim);margin:0 0 8px}}
.spec .cap b{{color:var(--fg)}}
.two{{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:12px}}
.score{{font-family:var(--display);font-size:26px;margin-top:6px}}
.score.bad{{color:var(--accent)}} .score.good{{color:var(--ok)}}
ul.t{{margin:0 0 12px;padding-left:19px;max-width:66ch}}
ul.t li{{font-size:15px;line-height:24px;margin-bottom:5px}}
</style>
<div class="wrap">
  <div class="lede">
    <span class="tag">OHPAH design &middot; palette</span>
    <h1>The palette is not too small. It is too flat.</h1>
    <p>Nine tokens are already defined in <code>design_system.md</code>. The problem is
       that five of them are chromatic inks sitting on three tonal values, and three of
       those five land on the same one.</p>
  </div>

  <h2><span class="k">The measurement</span>Three inks, one tone</h2>
  <p class="b">Perceived value, the 0.299 / 0.587 / 0.114 weighting that governs a
     photocopy, a greyscale print and most colour vision deficiency. Second swatch is the
     first one converted.</p>
  <div class="spec">
    <table><thead><tr><th>Token</th><th>Hex</th><th>Ink</th><th>Mono</th>
      <th style="text-align:right">Value</th><th>Role</th></tr></thead>
      <tbody>{tokrows}</tbody></table>
  </div>
  <div class="hit">
    <b>Red 88 &middot; green 88 &middot; blue 87</b>
    <p>Three of the five chromatic inks are within 1.6 points of each other. In greyscale,
       in a fax, on a photocopied grievance packet, and for a reader with the most common
       colour vision deficiency, they are one colour.</p>
    <p>Only orange (122) and yellow (184) carry their own tone. So a figure can hold three
       categories, not five, and <code>design_system.md</code> caps a surface at three
       chromatic inks anyway.</p>
  </div>

  <h2><span class="k">The reference set</span>What those posts are actually doing</h2>
  <p class="b">Four of the six are a cream ground, flat black mass, and exactly one
     saturated accent: a red circle, an orange penguin. That is the move OHPAH already
     owns. The other two drop a polychrome painted burst into an otherwise monochrome
     frame, which reads as a rupture rather than a palette.</p>
  <ul class="t">
    <li>Cream paper ground, near identical to <code>stock</code>.</li>
    <li>One accent, used as a pure geometric primitive against photographic collage.</li>
    <li>Tone carried by <strong>halftone and stipple density</strong>, not by hue.</li>
  </ul>
  <p class="b dim">The third one is the interesting one, and it is also the trap.</p>

  <h2><span class="k">The trap</span>That texture is the retired system</h2>
  <div class="hit">
    <b>brain.md, 2026 08 27</b>
    <p>&ldquo;The brand system and the Spotlight 1 bit system are separate on purpose and
       every attempt to merge them has produced something that belongs to neither.&rdquo;</p>
    <p>Halftone density carrying magnitude is the Spotlight 1 bit vocabulary, and it is
       retired. Importing it is the exact move that note was written about.</p>
  </div>
  <p class="b">There is a legal version of the same instinct, already in the system:
     <em>screen print tooth, registration shift and rough edges may affect nondata fields
     only. They may never distort text, values, nodes, axes or legends.</em> Texture on the
     ground, never on the data. What the reference set really argues for is tonal range,
     and tone is free.</p>

  <h2><span class="k">Proposal</span>A neutral ramp, which does not exist today</h2>
  <p class="b">Between <code>stock</code> at 235 and <code>ink</code> at 31 there is
     currently nothing. Eight steps along the cream to navy axis, ending on <code>ink</code>
     itself, so the ramp carries the brand's own warm to cool journey instead of passing
     through a dead grey. The gap between 108 and 68 is deliberate: it keeps every neutral
     clear of red at 88.</p>
  <div class="spec">
    <p class="cap">Ink &middot; mono &middot; token &middot; hex &middot; <b>value</b></p>
    {ramprows}
  </div>

  <h2><span class="k">Worked example</span>The NFIRS index, nine series</h2>
  <p class="b">True proportion, NFIRS code order. Left is what the current palette allows.
     Right uses the ramp, with tone carrying share and red held for the one declared
     category. Each is shown converted to mono underneath.</p>
  <div class="spec">
    <p class="cap">Today &middot; <b>{count_distinct(NOW)} separable values</b> for nine series</p>
    {bar(NOW)}{bar(NOW, True)}
  </div>
  <div class="spec">
    <p class="cap">Proposed &middot; <b>{count_distinct(NEW)} separable values</b></p>
    {bar(NEW)}{bar(NEW, True)}
  </div>
  <p class="b">Nine categories, no new hue, still one chromatic ink on the surface. Tone
     encodes magnitude, which is a declared data definition, so it satisfies the rule that
     colour never carries category on its own.</p>

  <h2><span class="k">Unchanged</span>What this does not touch</h2>
  <ul class="t">
    <li>Three chromatic inks per surface. The ramp is neutral, so it does not spend one.</li>
    <li>Colour never carries status or category alone. Tone here is paired with the label
        and the value, exactly as now.</li>
    <li>No retired token returns. Nothing here reintroduces navy, steel, beam, amber or the
        1 bit system.</li>
    <li>Red stays the declared category, not danger. Green stays connection, not good.</li>
  </ul>
  <p class="b dim">If this holds up, the change to <code>design_system.md</code> is one new
     row group in the colour table and one sentence under it. I have not touched the repo.</p>
</div>
'''
(ROOT / "index.html").write_text(HTML)
print(f"wrote {len((ROOT/'index.html').read_text().encode()):,} bytes")
print(f"today separable: {count_distinct(NOW)}   proposed: {count_distinct(NEW)}")
print("ramp:", " ".join(f"{n}={gray(h):.0f}" for n,h in RAMP))
