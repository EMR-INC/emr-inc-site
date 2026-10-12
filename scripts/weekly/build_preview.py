#!/usr/bin/env python3
"""Send proof harness. Renders an issue the way recipients will actually meet it.

Takes the built email and produces a review page: the inbox row, the email with
images on and off, phone width, the section structure, and the gates that passed.

Placeholder tokens are wrapped in @@ because the embedded PNG is base64, whose
alphabet is A-Za-z0-9+/= . A bare uppercase token such as TXT occurs inside a
45 KB base64 payload and str.replace will happily corrupt the image with it.
That is not hypothetical: it shipped once.
"""

from __future__ import annotations

import base64, html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PREFIX = sys.argv[1] if len(sys.argv) > 1 else "01"

email = (ROOT / f"{PREFIX}-email.html").read_text()
body = re.search(r"<body[^>]*>(.*)</body>", email, re.S).group(1)
body = re.sub(r'<div style="display:none.*?</div>\s*', "", body, flags=re.S)
fig = base64.b64encode((ROOT / f"{PREFIX}-figure.png").read_bytes()).decode()
alt = re.search(r'alt="([^"]*)"', email).group(1)
# The email now points at the hosted figure, so match whatever src it carries
# rather than a filename that moved.
img = re.search(r'<img [^>]*?>', email, re.S).group(0)

body_on = body.replace(img, re.sub(r'src="[^"]*"',
                                    f'src="data:image/png;base64,{fig}"', img))
body_off = body.replace(img, (
    f'<div style="border:1px solid #10213B;background:#E7E0D1;padding:18px 16px;'
    f'font-family:Courier Prime,Courier New,monospace;font-size:12px;line-height:19px;'
    f'color:#10213B;">{alt}</div>'))

subject = re.search(r"<title>(.*?)</title>", email, re.S).group(1)
pre = re.search(r'overflow:hidden;">(.*?)</div>', email, re.S).group(1)
txt = html.escape((ROOT / f"{PREFIX}-email.txt").read_text())
nbytes = len(email.encode())

SECTIONS = [("01", "Dear Chief", "118 words",
             "New every issue. Biting, ironic, its own provocation rather than a "
             "set up for the figure."),
            ("02", "The number", "68 words",
             "Bounded comparison drawn as a scale jump: Beall flat forms, Huber "
             "overprint. Full bleed ink field, cream plate."),
            ("03", "We heard you", "163 words",
             "Product and business update. This issue: post EMS World Expo.")]

GATES = [("Length", "2,167 px", "", "Three sections, 349 words of body copy."),
         ("Payload", f"{nbytes:,} B", "", "Gmail clips above 102,400 bytes."),
         ("Client safety", "8 / 8 clear", "pass",
          "No @import, pseudo element, flex, grid, custom property, vh, clamp or positioning."),
         ("Voice gate", "18 terms", "pass",
          "Banned vocabulary, hyphens, em dashes and exclamation marks each fail the build."),
         ("Grayscale", "3 gates pass", "pass",
          "Red 88 and blue 87 are the same tone, so the overprint at 19 is what separates "
          "the fire square from the field it sits on."),
         ("Scope guard", "4 places", "pass",
          "Florida only, not a national record: in the figure, the HTML, the text part and "
          "the alt text.")]

FLAGS = [("The Gmail API tool strips every img tag",
          'Three test sends confirmed it. Reading each message back shows the '
          '&lt;img&gt; element absent from the stored HTML entirely, not merely '
          'unloaded: with a cid: attachment, with a raw.githubusercontent URL, and '
          'with the figure served from emr-inc.net. The same sanitizer drops '
          '<code>role="presentation"</code>, <code>opacity:0</code>, and rewrites '
          '<code>href="#"</code> to <code>javascript:void(0)</code>. The email HTML '
          'below is correct and renders through a normal client; the send path is '
          'what breaks it. A real ESP is needed to test the figure in an inbox.'),
         ("Why it looked washed out",
          'Gmail preserved every hex value exactly, lowercased but unchanged. The red '
          'and the blue live only inside the figure, so with the img stripped the '
          'email was cream, navy and two small red kickers. Almost no colour at all. '
          'That is what you were seeing.'),
         ("Gmail wraps every link",
          'The CTA arrives as <code>google.com/url?q=</code>, which shows an '
          'interstitial because the link domain (beta.expectvictims.com) does not '
          'match the sending domain (emr-inc.net). Fixing it is a DNS and reputation '
          'job: align the domains, or redirect through emr-inc.net.'),
         ("One characterisation to check",
          'Section 03 renders your "grouchy boomer" as <strong>one of the old heads</strong>. '
          'You described the person; the phrasing is mine.')]

PAGE = r'''<title>Field Notes Issue 01</title>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@400;600;700&family=Archivo+Black&family=Courier+Prime:wght@400;700&display=swap">
<style>
/* Layout: a graphite instrument bench; the cream email sits on it as a physical sheet.
   The bench is theme aware. The sheet is not: it reproduces a fixed deliverable, so its
   colours stay the locked OHPAH brand values and never shift with the viewer's theme. */
:root{
  --bench:#15181D; --bench-2:#1D222A; --rule:#2E3741; --fg:#E6E9ED; --fg-dim:#98A3B0;
  --accent:#D5222A; --ok:#4F9D69; --focus:#7FB2E5;
  --display:"Archivo Black","Archivo",system-ui,sans-serif;
  --body:"Archivo",system-ui,-apple-system,sans-serif;
  --mono:"Courier Prime","Courier New",monospace;
}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){
  --bench:#0E1116; --bench-2:#161A21; --rule:#272F39; --fg:#E6E9ED; --fg-dim:#8E99A6;
  --accent:#E8434A; --ok:#5FAF79; --focus:#7FB2E5; color-scheme:dark}}
:root[data-theme="dark"]{
  --bench:#0E1116; --bench-2:#161A21; --rule:#272F39; --fg:#E6E9ED; --fg-dim:#8E99A6;
  --accent:#E8434A; --ok:#5FAF79; --focus:#7FB2E5; color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bench);color:var(--fg);font-family:var(--body);
  -webkit-font-smoothing:antialiased}
.wrap{max-width:1040px;margin:0 auto;padding-block:28px 56px;padding-left:16px;padding-right:16px}
:is(button,a,[tabindex]):focus-visible{outline:2px solid var(--focus);outline-offset:2px}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
.lede{display:flex;flex-wrap:wrap;gap:14px;align-items:baseline;
  border-top:3px solid var(--fg);padding-top:12px}
.lede h1{margin:0;font-family:var(--display);font-size:clamp(19px,3.4vw,25px);
  letter-spacing:.4px;text-wrap:balance;min-width:0}
.lede .tag{font-family:var(--mono);font-size:11px;font-weight:700;letter-spacing:1.6px;
  text-transform:uppercase;color:var(--accent)}
.lede p{margin:0;flex:1 1 260px;min-width:0;color:var(--fg-dim);font-size:14px;line-height:21px}
h2.sec{margin:34px 0 10px;font-family:var(--mono);font-size:11px;font-weight:700;
  letter-spacing:1.7px;text-transform:uppercase;color:var(--fg-dim)}
.inbox{background:var(--bench-2);border:1px solid var(--rule);border-left:3px solid var(--accent);
  padding:13px 15px;display:grid;gap:3px}
.inbox .from{font-size:13px;font-weight:700}
.inbox .subj{font-size:15px;font-weight:600}
.inbox .pre{font-size:13px;color:var(--fg-dim);line-height:19px}
.secs{display:grid;gap:1px;background:var(--rule);border:1px solid var(--rule)}
.srow{background:var(--bench-2);padding:12px 14px;display:flex;flex-wrap:wrap;gap:4px 14px;
  align-items:baseline}
.srow .n{font-family:var(--display);font-size:16px;color:var(--accent);min-width:22px}
.srow .t{font-family:var(--body);font-size:15px;font-weight:700}
.srow .w{font-family:var(--mono);font-size:11px;color:var(--fg-dim);
  font-variant-numeric:tabular-nums}
.srow .d{flex:1 1 100%;font-size:13px;line-height:19px;color:var(--fg-dim);min-width:0}
.bar{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0 16px}
.grp{display:flex;border:1px solid var(--rule);background:var(--bench-2)}
.grp button{appearance:none;border:0;background:transparent;color:var(--fg-dim);
  font-family:var(--mono);font-size:11px;font-weight:700;letter-spacing:1.2px;
  text-transform:uppercase;padding:9px 13px;cursor:pointer}
.grp button+button{border-left:1px solid var(--rule)}
.grp button[aria-pressed="true"]{background:var(--fg);color:var(--bench)}
.stage{background:var(--bench-2);border:1px solid var(--rule);padding:22px 12px;
  display:flex;justify-content:center;overflow-x:auto}
/* The email's outer cell adds 12px of side padding to a 600px table, so the sheet is 624. */
.sheetwrap{width:624px;max-width:100%;overflow:hidden}
.sheet{width:624px;transform-origin:top left;box-shadow:0 14px 34px rgba(0,0,0,.45)}
.stage[data-w="phone"] .sheetwrap{width:390px}
.stage[data-w="phone"] .sheet{transform:scale(.625)}
.sheet table{border-collapse:collapse}
.sheet img{display:block;max-width:100%}
pre.txt{margin:0;background:var(--bench-2);border:1px solid var(--rule);padding:16px;
  overflow-x:auto;font-family:var(--mono);font-size:12px;line-height:19px;color:var(--fg);
  white-space:pre-wrap;word-break:break-word}
.gates{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:1px;
  background:var(--rule);border:1px solid var(--rule)}
.gate{background:var(--bench-2);padding:13px 14px;min-width:0}
.gate .k{font-family:var(--mono);font-size:10px;font-weight:700;letter-spacing:1.3px;
  text-transform:uppercase;color:var(--fg-dim)}
.gate .v{font-family:var(--display);font-size:21px;margin-top:4px;
  font-variant-numeric:tabular-nums}
.gate .n{font-size:12px;line-height:18px;color:var(--fg-dim);margin-top:3px}
.gate .v.pass{color:var(--ok)}
.flag{margin-top:12px;border:1px solid var(--accent);border-left:3px solid var(--accent);
  background:var(--bench-2);padding:13px 15px;font-size:14px;line-height:21px}
.flag b{font-family:var(--mono);font-size:11px;letter-spacing:1.4px;text-transform:uppercase;
  color:var(--accent);display:block;margin-bottom:4px}
.flag code{font-family:var(--mono);font-size:13px;background:var(--bench);padding:1px 5px}
</style>
<div class="wrap">
  <div class="lede">
    <span class="tag">EMR Inc. Field Notes</span>
    <h1>Issue 01 &middot; Send proof</h1>
    <p>Three sections: the letter, the number, the update. Switch images off, since that
       is what a lot of this list sees first.</p>
  </div>

  <h2 class="sec">What lands in the inbox</h2>
  <div class="inbox">
    <div class="from">EMR Inc. Field Notes</div>
    <div class="subj">@@SUBJ@@</div>
    <div class="pre">@@PRE@@</div>
  </div>

  <h2 class="sec">Structure</h2>
  <div class="secs">@@SECS@@</div>

  <h2 class="sec">The email</h2>
  <div class="bar">
    <div class="grp" role="group" aria-label="Images">
      <button type="button" data-img="on" aria-pressed="true">Images on</button>
      <button type="button" data-img="off" aria-pressed="false">Images off</button>
    </div>
    <div class="grp" role="group" aria-label="Width">
      <button type="button" data-w="desktop" aria-pressed="true">Desktop 600</button>
      <button type="button" data-w="phone" aria-pressed="false">Phone 375</button>
    </div>
  </div>
  <div class="stage" id="stage" data-w="desktop">
    <div class="sheetwrap" id="sheetwrap"><div class="sheet" id="sheet">@@BODY@@</div></div>
  </div>

  <h2 class="sec">Verified before send</h2>
  <div class="gates">@@GATES@@</div>
  @@FLAGS@@

  <h2 class="sec">Plain text part</h2>
  <pre class="txt">@@TEXTPART@@</pre>
</div>
<script>@@DATA@@</script>
<script>
(function(){
  var sheet=document.getElementById("sheet"),wrap=document.getElementById("sheetwrap"),
      stage=document.getElementById("stage");
  function fit(){
    var s=stage.dataset.w==="phone"?0.625:1;
    wrap.style.height=Math.ceil(sheet.scrollHeight*s)+"px";
  }
  function group(sel,fn){
    var b=document.querySelectorAll(sel);
    b.forEach(function(el){el.addEventListener("click",function(){
      b.forEach(function(o){o.setAttribute("aria-pressed",String(o===el));});
      fn(el); requestAnimationFrame(fit);
    });});
  }
  group("button[data-img]",function(el){
    sheet.innerHTML = el.dataset.img==="on" ? window.__on : window.__off;});
  group("button[data-w]",function(el){ stage.dataset.w=el.dataset.w;});
  if(document.fonts&&document.fonts.ready)document.fonts.ready.then(fit);
  window.addEventListener("load",fit); fit();
})();
</script>
'''

secs = "".join(f'<div class="srow"><span class="n">{n}</span><span class="t">{t}</span>'
               f'<span class="w">{w}</span><span class="d">{d}</span></div>'
               for n, t, w, d in SECTIONS)
gates = "".join(f'<div class="gate"><div class="k">{k}</div>'
                f'<div class="v {c}">{v}</div><div class="n">{n}</div></div>'
                for k, v, c, n in GATES)
flags = "".join(f'<div class="flag"><b>{t}</b>{b}</div>' for t, b in FLAGS)
data = f"window.__on={json.dumps(body_on)};window.__off={json.dumps(body_off)};"

page = PAGE
for tok, val in (("@@SUBJ@@", subject), ("@@PRE@@", pre), ("@@SECS@@", secs),
                 ("@@GATES@@", gates), ("@@FLAGS@@", flags),
                 ("@@TEXTPART@@", txt), ("@@DATA@@", data), ("@@BODY@@", body_on)):
    assert page.count(tok) == 1, f"token {tok} appears {page.count(tok)} times"
    page = page.replace(tok, val)

out = ROOT / f"{PREFIX}-preview.html"
out.write_text(page)

i = page.find("data:image/png;base64,") + 22
raw = base64.b64decode(page[i:page.find('"', i)], validate=True)
assert raw == (ROOT / f"{PREFIX}-figure.png").read_bytes(), "embedded PNG corrupted"
print(f"{out.name}: {len(page.encode()):,} bytes; PNG verified intact ({len(raw):,} B)")
