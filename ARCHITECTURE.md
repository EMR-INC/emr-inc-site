# emr-inc.net: current architecture

Surveyed 2026-09-27 against the live repo, the Vercel account, and public DNS.
This is a description of what exists right now, not a plan. Where the live state
and the repo disagree, the disagreement is the finding, and it is called out.

Companion documents: `MIGRATION.md` is the runbook for the Wix move. `DESIGN-BRIEF.md` is the standing brief for visual revisions.

---

## 1. The short version

`emr-inc.net` is a hand-written static site: five to seven HTML files, one
stylesheet, one small progressive-enhancement script, no framework and no build
step. It is served by Vercel. Its DNS is still served by Wix. Its mail is Google
Workspace. Nothing else in the company runs on this repo.

The thing to know before reading further: **the content that is live is not the
content on `main`.** That was true until 2026-09-27, when PR #1 was merged and
the two were reconciled. Section 2 records what changed.

---

## 2. Repository and branches

`EMR-INC/emr-inc-site` (public, GitHub, default branch `main`).

Until 2026-09-27 two lines of work diverged from a common ancestor, `2f7b038`
(2026-09-13, the corkboard landing page), and the live site ran the one that was
not `main`:

| Line | Head | Added on top of `2f7b038` | Was deployed? |
|---|---|---|---|
| `main` | `2fe9078` | `call-sign.html`, `member-research.html` | never |
| PR #1 `claude/wix-to-vercel-cloudflare-wyu0ka` | `a3812a2` (2026-09-26) | Vercel config, contact page, `/internal` auth gate, DNS zone, runbook | yes, this was live |

Every one of the eight Vercel deployments, including both production promotions,
came off the PR #1 branch. `main` had never been deployed at all.

### The reconciliation

[PR #1](https://github.com/EMR-INC/emr-inc-site/pull/1) was merged to `main` as
`c8cecd8`. `main` now holds both lines: the Vercel configuration and the auth
gate from PR #1, and the Call/Sign and member-research pages that were only ever
on `main`.

The merge was clean, and that was the thing to watch rather than a reassurance.
PR #1 edited the headline in `index.html` and `main`'s extra commit did not touch
that file, so Git would have silently adopted PR #1's wording over `main`'s "The
civil service has a data problem." with nobody asked. The headline was therefore
decided deliberately rather than by default, and set to:

> **Emergency Services has a data problem.**

It appears in three places that have to agree: the `<h1>` in `index.html`, that
page's `<meta name="description">`, and the content guard in
`build-standalone.py`. The guard is what makes the third one load-bearing: the
build asserts the string survives the rewrite, so a headline change that misses
`build-standalone.py` fails the build rather than shipping quietly.

Note the capitalisation is deliberate and is the one place the site departs from
sentence case in a headline.

PR #1's "Still open" note was stale where it said `call-sign.html` did not exist
yet; `main` had carried it since `2fe9078`.

### Where that leaves the link graph

`open-data.html` was the only broken link left, on all six pages. It was built
after this survey and the link graph now resolves end to end: see section 5,
which was rechecked on 2026-10-10.

## 3. Hosting

**Vercel**, team `mikeharvey941-gmailcoms-projects`
(`team_rwxqo0kDlEjDlDdXAJv9y7e6`), project `emr-inc-site`
(`prj_kiJjgBMbwd070fbCefZ3zz1Uv9E4`), created 2026-09-25 10:31 UTC.

- Framework: none. No build step; files are uploaded as-is.
- Node 24.x (for the middleware and the auth functions only).
- Live production deployment: `dpl_EAWPHJtBswuLtqdRABWtiT3uGvT5`, built
  2026-09-25 10:45 UTC from commit `0842763` on the PR #1 branch.
- The newest deployment (`dpl_3xw2cym68XsKFt3wiRs8Rhj73ty9`, 2026-09-26 01:12
  UTC, commit `a3812a2`) is a **preview**, not production. The auth gate and the
  public/internal research split are in that preview and are *not* on the live
  site.
- Vercel SSO protection is on for everything except custom domains, so the
  `*.vercel.app` preview URLs are private and `emr-inc.net` is public.

`vercel.json` sets `cleanUrls` (so `/research` serves `research.html`),
`trailingSlash: false`, a week of `public` caching on `/assets/*`,
`private, no-store` plus `X-Robots-Tag: noindex, nofollow` on `/internal/*`, and
`nosniff` / `strict-origin-when-cross-origin` / `SAMEORIGIN` site-wide.

`.vercelignore` keeps `DESIGN-BRIEF.md`, `MIGRATION.md`, `build-standalone.py`,
`*-standalone.html`, `experiments/` and `dns/` off the served site. They are still
in the public Git repo; `.vercelignore` only controls what Vercel serves.

### A second, unrelated Vercel project

`call-sign-2546` (`prj_XvzmZcTLG2FTmPNoWZqS6lmvhWeR`, created 2026-09-14) sits in
the same team. It has no custom domain and is not what `callsign.ohpah.app`
resolves to. It is a detached deploy, presumably from `EMR-INC/call-sign`.

### The stale Cloudflare Pages assumption

`.gitignore` on `main` still carries a warning written for a Cloudflare Pages
deploy ("the Cloudflare Pages deploy uploads a staged copy of 13 named files")
and ignores `.wrangler/` and `wrangler-account.json`. No Cloudflare deploy exists
for this site. `MIGRATION.md` records the reason: the plan was Wix → Cloudflare,
it changed to Wix → Vercel, and the `.gitignore` comment plus the
`dns/emr-inc.net.cloudflare.zone` filename are leftovers from the abandoned plan.

The same `.gitignore` also asserts that GitHub Pages serves this repo's root. If
that is still switched on, the repo root is world-readable at a github.io URL in
addition to being a public repo. Worth confirming in repo settings.

---

## 4. DNS and domain

**The registrar transfer is not finished.** Authoritative nameservers for
`emr-inc.net` are still `ns2.wixdns.net` and `ns3.wixdns.net`. Vercel's account
domain list is empty, so nothing has landed in Vercel DNS yet.

Live records, as resolved:

| Name | Type | Value | Points at |
|---|---|---|---|
| `emr-inc.net` | A | `76.76.21.21` | Vercel |
| `www.emr-inc.net` | CNAME | `cname.vercel-dns.com` | Vercel, 308 → apex |
| `en.emr-inc.net` | CNAME | `cdn1.wixdns.net` | **still Wix** |
| `command-center.emr-inc.net` | A | `185.158.133.1` | Lovable app |
| `emr-inc.net` | MX ×5 | `aspmx.l.google.com` + 4 alts | Google Workspace |
| `emr-inc.net` | TXT | `v=spf1 include:_spf.google.com ~all` | SPF |
| `emr-inc.net` | TXT | `google-site-verification=…` | Workspace verification |
| `_lovable.command-center` | TXT | `lovable_verify=…` | Lovable verification |

Both `emr-inc.net` and `www.emr-inc.net` are attached to the Vercel project and
verified (attached 2026-09-25 17:14 UTC).

So the current shape is: **Wix serves the DNS that points away from Wix.** Wix
does not permit changing nameservers on a domain it registered, which is why the
registration itself has to move first. Until it does, Wix is a live dependency
and cancelling Wix Premium would take the site and the mail down. `MIGRATION.md`
step 7 has this ordering right; it is worth not skipping.

`dns/emr-inc.net.cloudflare.zone` is an exact 2026-09-25 copy of
the Wix zone, kept as the reference for what has to survive the move. Note it
records the pre-move apex (`185.230.63.x`, Wix) and `www` (`cdn3.wixdns.net`),
not the current Vercel values. It is a snapshot of the starting point, not of
today.

### Mail authentication gaps

`google._domainkey.emr-inc.net` and `_dmarc.emr-inc.net` both return NXDOMAIN.
There is SPF, but **no DKIM and no DMARC**. Mail from `emr-inc.net` is therefore
easier to spoof than it should be, which matters for an organisation whose
outbound mail asks union officers to trust a link.

---

## 5. Pages and content

Files on `main` after the merge: `index.html`, `research.html`,
`call-sign.html`, `member-research.html`, `contact.html` and
`internal/research.html`, plus `styles.css` (30 KB, the whole design system) and
`reveal.js`. Since the survey, two more: `open-data.html` and
`dispatch-views.html`, with their data and template files. A third,
`pel-method.html`, was added and withdrawn on 2026-10-10: see below.

### Internal links, rechecked 2026-10-10

**Every internal link on every page now resolves.** `open-data.html` was built
after this survey was written and the finding below is closed. The record is
kept because the shape of the failure is the interesting part.

| Link target | `main` before the merge | Deployed branch before | Now |
|---|---|---|---|
| `open-data.html` | missing | missing | **present, generated daily** |
| `contact.html` | missing | present | present |
| `call-sign.html` | present | missing | present |
| `member-research.html` | present | not linked | present |

### Two kinds of page now live here

The site has split into hand written pages and generated ones, and they do not
look alike because they are not built alike.

| | Hand written | Generated |
|---|---|---|
| Pages | `index.html`, `call-sign.html`, `member-research.html`, `contact.html`, `dispatch-views.html` | `research.html`, `open-data.html` |
| Styling | `styles.css`, which implements OHPAH-DESIGN `design_system.md` **v1.1**, the retired navy, ivory, steel and beam palette | self contained CSS implementing **v3.0**, the stock and ink diagrammatic modernism palette |
| Figures | written into the markup | read from a committed JSON file at build time |
| Edit | the `.html` | the template plus the builder, never the output |

The generated pages have a pipeline document of their own:
`docs/OPEN_DATA_PIPELINE.md`.

### The event load method file, published and withdrawn on 2026-10-10

`pel-method.html` shipped at 17:06 UTC and was removed the same hour. It
carried the event load method: eight event classes, seventy six radio terms,
and the research citations behind them. It was withdrawn on the owner's
instruction to make it sign in only.

**Moving it under `internal/` would not have achieved that, and the reason was
already written in this repository.** The note at the top of `.vercelignore`,
dated 2026-10-08, measures it: this repository is public, so every committed
file is world-readable on github.com whatever Vercel serves; GitHub Pages is
enabled and builds every push to `main` as a second published copy; and
`middleware.js` exists only on Vercel, so `internal/` means nothing to Pages.
Confirmed again on 2026-10-10: `emr-inc.github.io/emr-inc-site/pel-method.html`
and `.../data/pel-method.json` both returned 200 while the files were on `main`.

So the files were removed from the branch entirely rather than relocated. Two
things that removal does **not** do, and that remain open:

1. **The content is still in this repository's history** and is reachable by
   commit. Unpublishing it needs a history purge, which rewrites `main`.
2. **GitHub Pages is still enabled** and still builds a parallel copy of every
   push. `.vercelignore` already flags this as a loose end worth deciding on.
   Nothing in this repo can switch it off; it is a repository setting.

The sources moved to `EMR-INC/the-lab`, which is private, under
`apps/lab/src/method/`. `docs/method_page.md` there replaces the pipeline
document that used to sit here.

The design system's own rule is that a legacy surface may stay as it is until
it is touched, and moves to v3.0 once it is. That is why a new page is in the
new system and the old pages are not, and it is also a live inconsistency a
reader will notice. Restyling the five hand written pages is the outstanding
work.

Every hand written page carries a hand-copied nav and footer.
`internal/research.html` says so in a comment: there is no template step, so a
nav change is a four-to-six file edit and drift between pages is the expected
failure. **It has already drifted again:** `dispatch-views.html` is in its own
footer and in no other page's. `pel-method.html` was added to all five hand
written footers at once, which is the only reason it is consistent.

### The `/internal` gate

`research.html` is a public summary and the full research page lives at
`internal/research.html`, gated by `middleware.js`:

- `middleware.js` matches `/internal` and `/internal/:path*`, verifies an
  HMAC-SHA256 signed cookie (`emr_internal`, 8-hour life), and 302s to
  `/api/auth/login` otherwise.
- `api/auth/login.mjs` → Google OAuth (`scope: openid email`, `hd=emr-inc.net`),
  with the `state` carried in a separate signed cookie scoped to `/api/auth`.
- `api/auth/callback.mjs` enforces the domain properly: `aud`, `iss`, `exp`,
  `email_verified`, `hd`, and the email domain. The `hd` parameter on the login
  URL only pre-selects the account; it is not treated as a control.
- `api/_lib/session.mjs` is Web Crypto only, so the same code runs in Edge
  middleware and in Node functions. `verify()` returns `null` when no secret is
  configured, so a misconfigured deploy **fails closed**.
- `safeNext()` restricts the post-login redirect to `/internal/…`, so the flow
  cannot be used as an open redirect.

The design is sound. Two things about its current state:

1. **The Vercel project has zero environment variables.** `SESSION_SECRET`,
   `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are all unset. Sign-in returns
   "Internal sign-in is not configured yet." and the gate refuses everyone.
   Fail-closed is the right default, but right now nobody can reach the internal
   page, including the people it is for.
2. **The merge makes this live.** Before it, the deployed build predated the
   gate and `/research` served the full research page to anyone. Now `/research`
   is the public summary and the full page sits at `/internal/research` behind a
   sign-in that no one can complete. Until the three variables are set, the full
   research page is reachable by nobody, including the staff it was gated for.
   Setting them in the Vercel project is the whole fix.

---

## 6. Build and tooling

`build-standalone.py` produces designer-facing single-file exports
(`emr-inc-standalone.html`, `emr-inc-research-standalone.html`, both
`.gitignore`d). It inlines `styles.css`, strips `<script>`, neutralises
`.reveal`, rewrites internal `.html` links to `#`, base64-inlines every
`assets/` image in both markup and CSS `url()`, and leaves the Google Fonts links
alone.

Its useful property is the `PAGES` table: each page names literal strings that
must survive the rewrite (`"56.20%"`, `"23.34%"`, `"82,503"`, …) and the build
asserts on each one. A regex that silently ate a figure would fail the build.

This is not part of the deploy. It is run by hand, feeding the revision loop
described in `DESIGN-BRIEF.md`.

`reveal.js` is the only JavaScript that ships: an IntersectionObserver fade-and-
rise, 400ms / 12px / 60ms stagger, with a no-observer fallback that reveals
everything. Per `DESIGN-BRIEF.md` §7, the site must render completely with
JavaScript disabled, and it does.

---

## 7. Design system

The site implements `EMR-INC/OHPAH-DESIGN · design_system.md v1.1`, which lives
in a **separate private repo**. `styles.css` and `DESIGN-BRIEF.md` are the only
copies of it that this repo has; the source of truth is elsewhere, and there is
no automated check that the two stay in sync.

Fixed: a nine-colour palette with amber `--beam-500` as the only accent; three
typefaces with one job each (Archivo display, DM Sans body, IBM Plex Mono for
data); an 8pt spacing scale; 4/6/3px radii and never a pill. Every section sits
on exactly one of four "fields" (`field-ivory`, `field-white`, `field-navy`,
`field-ink`) and type colours flip with the field.

Copy rules are hard constraints, not preferences: no em dashes, never "heroes" or
any heroism framing, no causal health claims, and no copy implying a department
can see an individual member's record. Product naming is settled: Expect Victims
is the platform (Red Team the OSINT tool, Blue Team is OHPAH), Expect Fire the
companion, CALL/SIGN: DASHBOARD the union side.

`DESIGN-BRIEF.md` §5 is the part to read before touching the research figure: the
two-panel SVG is hand-authored with literal coordinates, its geometry is
load-bearing (a fixed 25% ceiling from true zero; a slope chart whose *crossing*
is the finding), and the percentages are not interchangeable — 23.34%/23.26% use
a Fire-Module denominator, 56.20% uses the wider one that includes the 35,416
structure fires filed with no Fire Module.

---

## 8. Data

`data/nfirs-hour-of-day.json` and `data/nfirs-incident-composition.json` are
pulled 2026-09-13 from the **`ohpah-research` Supabase project
(`casmwfxrxlysqizxahcw`)**, table `nfirs_basicincident`.

Neither file is referenced by any page. The figures in `research.html` are typed
into the SVG as literals. The JSON is provenance for numbers that are hard-coded
elsewhere, which is worth knowing before anyone "updates the data" and expects
the page to change.

Both files carry a scope note worth preserving: the data is **Florida only**
(396 distinct FDIDs, 2020 onward). It must not be described as a national record.

---

## 9. Everything connected to it

### Owned domains

| Host | DNS | Serves | Relationship |
|---|---|---|---|
| `emr-inc.net` | Wix NS | Vercel (this repo) | the site |
| `www.emr-inc.net` | Wix NS | Vercel, 308 → apex | — |
| `en.emr-inc.net` | Wix NS | Wix CDN | orphan from the Wix site |
| `callsign.emr-inc.net` | Wix NS | Vercel (this project), host-scoped rewrite → the Cloudflare Worker | the live CALL/SIGN app on the company domain |
| `command-center.emr-inc.net` | Wix NS | Lovable (`185.158.133.1`) | internal tool, outside this repo |
| `ohpah.app`, `callsign.ohpah.app` | **Cloudflare** | Cloudflare proxy | OHPAH product + the live CALL/SIGN app |
| `expectvictims.com` | **GoDaddy** | `216.150.1.1` | product site, linked from every page |
| `expectfire.com` | **GoDaddy** | `216.150.1.1` | product site, linked from every page |

Three separate DNS providers and at least two registrars across seven hosts. Only
`emr-inc.net` is in the migration.

The union-facing product now answers on the company domain as well as the OHPAH
one. `callsign.emr-inc.net` is a CNAME to `cname.vercel-dns.com`, attached to this
Vercel project, with a host-scoped rewrite forwarding every path to the Cloudflare
Worker behind `spotlight.ohpah.app`. `callsign.ohpah.app` still serves, so links
already in circulation keep working.

The earlier claim here — that `callsign.emr-inc.net` "cannot" exist while
`emr-inc.net` is on Wix nameservers — was too strong, but the constraint behind it
is real and worth stating precisely, because the obvious simplification is broken:

- A Workers **Custom Domain** requires the zone to be active in the Cloudflare
  account. `emr-inc.net` NS are `ns2`/`ns3.wixdns.net`, so it is not, so this
  hostname cannot be attached to the Worker directly.
- A bare CNAME from Wix straight to `spotlight.ohpah.app` does **not** work either.
  The request arrives at Cloudflare with `Host: callsign.emr-inc.net`, matches no
  zone and no route, and fails at TLS — which presents as a certificate error and
  is not one.
- So the Vercel hop is load-bearing, not incidental. It can be dropped for a
  Workers Custom Domain only after the zone moves to Cloudflare.

Host-scoping the rewrite is also not a style choice. `/assets/` is occupied on both
sides: this site serves `/assets/emr-inc-logo.png`, and the Worker's Vite build is
`base: "/"` so it emits `/assets/*` and `/fonts/*` at the root. A path-scoped
rewrite under `emr-inc.net/call-sign` would return a 200 HTML document whose JS
404s — unstyled and inert, and green on every status check.

### Third-party runtime dependencies

Everything the browser fetches from somewhere other than Vercel:

- **Google Fonts** (`fonts.googleapis.com`, `fonts.gstatic.com`) — every page,
  render-blocking, preconnected.
- **Google Forms** — `contact.html` iframes form
  `1FXXOZsZu6endmH4xCkZWJ3StrX3s7w-r0k2CAmFuuow`, with a new-tab link as the
  no-iframe fallback. The contact path depends on Google, and submissions land in
  a Google account, not in this repo.
- **Google OAuth / Workspace** — the `/internal` gate and all mail.
- **cdnjs** (`p5.js` 1.7.0) — `experiments/quiet-enclosure/` only, and that
  directory is `.vercelignore`d, so it never ships.
- **Instagram** `@ohpah.app` — outbound footer link.
- `mailto:michael.harvey@emr-inc.net` — in every footer.

### Sibling repositories

Nine repos in `EMR-INC`; this is the only public one.

| Repo | Visibility | Relationship to this site |
|---|---|---|
| `emr-inc-site` | public | this repo |
| `OHPAH-DESIGN` | private | **source of the design system this repo implements** |
| `ohpah-research` | private | **source of `data/*.json`** (Supabase `casmwfxrxlysqizxahcw`) |
| `call-sign` | private | the app, reached at `callsign.emr-inc.net` (also `callsign.ohpah.app`) |
| `OHPAH-app` | private | React Native / Expo + Supabase + Cloudflare dispatch worker |
| `ohpah-ops` | private | algorithm + LLM interpretation layers |
| `ohpah-spotlight` | private | — |
| `ohpah-command-center` | private | likely behind `command-center.emr-inc.net` |
| `ohpah-brain-vault` | private | Obsidian notes |

The two that matter operationally are `OHPAH-DESIGN` and `ohpah-research`: this
repo is downstream of both by hand-copy, with no sync and no check.

---

## 10. Risks, in the order I would deal with them

1. **The `/internal` gate is unusable, and the merge made it live.**
   `SESSION_SECRET`, `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are unset in
   the Vercel project, so sign-in returns "Internal sign-in is not configured
   yet." and the gate refuses everyone. `/research` is now the public summary, so
   the full research page is reachable by nobody. Setting the three variables is
   the whole fix.
2. **Wix is still a live dependency.** Wix serves the DNS, including the MX
   records. Losing or cancelling it before the registrar transfer completes takes
   down both the site and company mail. Finish steps 5 to 7 of `MIGRATION.md`, in
   that order.
3. **No DKIM, no DMARC.** SPF alone. Add both in whichever DNS is authoritative
   at the time.
4. ~~**`open-data.html` is linked everywhere and exists nowhere.**~~ Closed.
   The page was built and is regenerated daily by `.github/workflows/open_data_daily.yml`.
   What replaces it on this list: **`build-standalone.py` no longer runs.** It
   asserts every `src="assets/..."` resolves on disk, and `index.html` now
   carries `assets/emr-hidden-data-disguise.png?v=2`, so the query string is
   treated as part of the filename and the build stops. The fix is to strip the
   query before resolving the path; the script is `.vercelignore`d so nothing
   served is affected, but the standalone export cannot be produced until it is
   fixed.
5. **Confirm Vercel's production branch is `main`.** Every deployment so far came
   off the old PR #1 branch, so this was never exercised. If it is not `main`, a
   merge still does not reach the site and the repo goes back to disagreeing with
   production.
6. **A public repo holds the DNS zone, including verification tokens.** `dns/` is
   `.vercelignore`d but still committed. Low severity on its own, but worth a
   look alongside whether GitHub Pages is still serving the repo root.
7. **Nav and footer are copy-pasted across six files.** Already drifted once. The
   next page makes it worse.

### Closed by the 2026-09-27 merge

- Production ran an unmerged draft branch while `main` had never shipped. PR #1
  merged as `c8cecd8`, with the headline decided deliberately rather than taken
  by Git's silent default.
- Each branch fixed half the link graph. `main` now carries all six pages.
