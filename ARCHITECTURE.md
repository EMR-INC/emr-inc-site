# emr-inc.net: current architecture

Surveyed 2026-09-29 against `main`, the GitHub Actions history, the Vercel
account, the `EMR-INC/call-sign` source, and public DNS. This describes what is
running, not what is planned. Where the code and the running system disagree,
the disagreement is the finding and is called out rather than smoothed over.

This replaces an earlier version of this file that described the site as hosted
on Vercel. That was true on 2026-09-27 and is not true now.

**Updated later the same day.** While this was being written, `main` was
rewritten: `d264a90` stopped publishing the row-level dispatch record and
`257e6ef` removed `data/dispatch-events.csv` from the repository and from the
history. That is the first remedy in section 9 item 1, already taken, for the
file that mattered most. The sections below say so where it changes them, and
the finding that produced it is kept rather than deleted, because the reasoning
is what stops it happening again.

Companion documents: `docs/OPEN_DATA_PIPELINE.md` for the daily publication
contract, `DESIGN-BRIEF.md` for the visual system, `MIGRATION.md` for the Wix
history.

---

## 1. The short version

A static site of hand-written HTML and one stylesheet, served by **GitHub
Pages**, with two GitHub Actions crons that regenerate three of its pages from
an aggregate-only API and commit the result. No framework, no build step for the
site itself, no server.

Two things are worth knowing before anything else:

1. **The site is on GitHub Pages, but both crons deploy to Vercel.** Only the
   first of those actually publishes. Section 2.
2. **Because of that, `.vercelignore` does not govern the apex.** Every file it
   lists is served from `emr-inc.net` regardless. The repository now says this
   itself, in a note added to the file on 2026-09-29. Section 2.

---

## 2. Hosting: two deploy paths, one of which is inert

| Path | Trigger | Serves `emr-inc.net`? |
|---|---|---|
| GitHub Pages (`pages build and deployment`) | every push to `main` | **yes** |
| Vercel CLI (`vercel deploy --prod`, in both crons) | after each cron commit | no |

GitHub Pages is the live host. `CNAME` contains `emr-inc.net`, the apex resolves
to GitHub's Pages addresses, `www` is a CNAME to `emr-inc.github.io`, and the
`pages build and deployment` workflow has been running and succeeding on every
push to `main`.

Both cron workflows also run `npx vercel@60 deploy --prod` against project
`emr-inc-site` (`prj_kiJjgBMbwd070fbCefZ3zz1Uv9E4`, team
`team_rwxqo0kDlEjDlDdXAJv9y7e6`). Those deploys succeed. `VERCEL_TOKEN` is set.
They land on a project that no longer has the domain attached, so they publish to
nobody.

Both workflows carry a long comment built on a premise that has since become
false:

> PUSHING TO main DOES NOT DEPLOY THIS SITE. The Vercel project has no Git
> integration connected, so a commit reaching main updates the repository and
> nothing else.

The second sentence is still true. The first is not: a push to `main` is now
exactly what deploys the site. The Vercel step was added to close a real gap
that the move to Pages had already closed by other means.

The Vercel Git integration is genuinely absent, and the reason is recorded in
`dispatch-views.yml`: the Vercel account signs into GitHub as
`mikeharvey941-wq`, which is not a member of the `EMR-INC` org, and Vercel will
not mint a deploy hook for an unconnected project. That is why the crons shell
out to the CLI. It is sound reasoning about a host that is no longer serving the
site.

### What this breaks

`.vercelignore` is a Vercel file. GitHub Pages does not read it. There is no
`_config.yml`, so nothing else excludes anything either. **Pages serves the
repository root as it stands.** Everything on the ignore list is therefore
published:

- `dns/emr-inc.net.cloudflare.zone`, `MIGRATION.md`, `DESIGN-BRIEF.md`,
  `build-standalone.py`, `*-standalone.html`, `experiments/`

**The case that proved it, now closed.** `data/dispatch-events.csv` was the
row-level dispatch record, one row per transmission located to the street.
Commit `266e8f3` removed it from the site deliberately and said so: *"Excluded
from the deployment in `.vercelignore`, which is what actually stops it being
served; removing the link alone would have left the URL fetchable."* Under Pages
that is exactly backwards: the link was removed and the URL stayed fetchable,
which is the outcome the commit set out to avoid. On 2026-09-29 the file left
the repository and the history, and `.vercelignore` gained a note stating the
rule in general terms: *"Withholding a file from emr-inc.net means keeping it
out of the branch. This was learned the hard way while unpublishing the dispatch
capture: an entry here looked like it had worked and had not."* `.gitignore`
now carries a matching line so it cannot be committed again by accident.

Separately, and for the same reason, `internal/research.html` is served with no
gate. `middleware.js`, `api/auth/*` and the `vercel.json` headers that protected
it are all Vercel features that Pages cannot execute. The page's own
`<meta name="robots" content="noindex">` discourages crawlers and restricts
nobody. `api/auth/*.mjs` and `middleware.js` are themselves served as source
text, which is not a secret leak, the repository is public, but is a good
illustration of the point.

### A related leak the code already warned about

`data/build-dispatch-views.py` takes deliberate care not to copy
`nfirs-hour-of-day.json`'s `source` or `scope.note` into a public caption, and
says why:

> That file is not published; this one is, and it is read straight into a caption
> on a public page. Do not pass `nf["source"]` or `nf["scope"]["note"]` through.
> [...] naming the project reference is a small credential leak.

The premise is wrong in two ways. `data/nfirs-hour-of-day.json` is committed to a
**public repository**, so it has always been readable, and it is not in
`.vercelignore`, so it was never excluded from the Vercel deploy either. Under
Pages it is also served at `emr-inc.net/data/nfirs-hour-of-day.json`. Its
`source` field reads:

```
ohpah-research Supabase, table nfirs_basicincident, project casmwfxrxlysqizxahcw
```

The caption discipline is right and should stay. What is missing is that the
file itself needs the same treatment: strip the internal provenance fields from
the committed copy and keep them somewhere unpublished, or accept that the
project reference is public and stop calling it a leak. The two halves have to
agree, and right now the code is defending a boundary that the repository does
not hold.

**This was inference when written, and is no longer.** The container's egress
proxy blocks `emr-inc.net` and `emr-inc.github.io`, so it could not be confirmed
by request here. It followed from: Pages is the host, the files are committed,
and no exclude mechanism Pages honours is present. The note added to
`.vercelignore` on 2026-09-29 confirms it first-hand, from someone who watched
an entry in that file fail to withhold anything. The remaining entries are
working files rather than records about people, so what is left is untidy rather
than urgent. One `curl -I` still settles the exact list.

### One claim I could not reconcile

The `.gitignore` note added on 2026-09-29 says *"The Cloudflare Pages deploy
uploads a staged copy of 13 named files."* Nothing in this repository does that.
There is no Cloudflare Pages workflow, and both crons still shell out to
`vercel deploy --prod`. So either a third deploy path is configured outside the
repository, in a dashboard, or that sentence describes an intention rather than
what runs. It matters because the two readings disagree about what is published
and by what, which is the same class of mistake as the `.vercelignore` one.
Worth settling before anyone relies on it.

### The fix, in the order it should happen

1. Decide which host is authoritative. Pages is already winning by default.
2. If Pages stays: delete the `vercel deploy` step from both workflows, and
   replace `.vercelignore` with something Pages honours. Files that must not be
   served have to leave the repository or move behind a host that can gate them,
   because Pages has no access control at all.
3. If Vercel is meant to be authoritative: reattach the domain and connect Git
   integration, at which point both deploy steps must be deleted or every
   refresh builds to production twice, and the workflows say this themselves.

---

## 3. The build: three jobs

### Daily open-data publication

`.github/workflows/open_data_daily.yml`. Two UTC cron entries (12:00 and 13:00)
with a `TZ=America/New_York` hour check, so it fires once at 08:00 Eastern on
both sides of the daylight saving boundary. Also `workflow_dispatch`.

`scripts/update_research.py` fetches
`https://spotlight.ohpah.app/api/open-data-snapshot`, overridable by the Actions
variable `OHPAH_OPEN_DATA_SOURCE_URL`, and writes three artifacts:

- `data/research.json`, the machine-readable snapshot
- `research.html`, the human-readable source and method record
- `open-data.html`, generated from `templates/open-data.html`

Then `scripts/validate_generated.mjs` checks the generated pages against the
JSON: the approved split-display title survives, the template placeholder does
not reach production, every inline script parses, and the embedded
`generated_at_utc` matches the snapshot.

The publisher fails closed, and the list of conditions is the useful part:
source unavailable, unsupported schema version, missing aggregate-only
assertion, a method object that is not exactly four checks, an empty daily
series, or daily and call-type counts that do not reconcile to
`total_alert_candidates`. It also rejects the forbidden keys `transcript`,
`address`, `audio_url`, `id`, `source_row`, `person` if they ever appear.

**This is the only job whose output changes because the data changed.**

### Dispatch views

`.github/workflows/dispatch-views.yml`. Monday, Wednesday and Friday at 11:00
UTC, chosen because it is 06:00 or 07:00 Eastern year-round, the same weekday on
both sides of the clock change. Also `workflow_dispatch`.

`data/build-dispatch-views.py` rewrites `data/dispatch-views.json`, which
`dispatch-views.html` draws. Its input, `data/dispatch-events.csv`, is **no
longer in the repository**, so every scheduled run now takes the script's
restamp path, which the workflow states is byte for byte identical to a full
rebuild on the same date. Refreshing the capture is a deliberate local step:
put the new CSV in `data/`, run the script once by hand, commit the JSON only.

**The numbers do not change.** They never did, because the capture is static,
and now they cannot: the counts are carried in the committed JSON. What changes is the edition, derived from
the build stamp: camera angle, ground plane elevation, lighting direction, the
mark used for the nights figure, bar sort order, section order. A failed run is
not a data outage and nobody should be paged for it.

The script is standard library only (`csv`, `json`, `datetime`, `zoneinfo`) on
purpose, so that a reader could run it without a toolchain. That rationale is now
partly historical: the CSV it needs is no longer published, so the reproduction
it was designed for is not available to outsiders. What remains, and what the
pages now claim, is that the method can be audited even though the rows cannot be
refetched.

The script also documents what it deliberately does not compute: no station
grain (a department view is the sum of its rostered units; pushing that down to a
station is the ecological fallacy, cited to Robinson 1950 and Diez-Roux 1998), and
nothing per person (Sleep Debt and Fire Exposure sit behind the consent firewall
in migration 00071). Both exclusions are governed by
`OHPAH_Department_Unit_Timeframe_Views_2026-09-04`.

### Pages build and deployment

Automatic on every push to `main`. Nobody configured it in this repository and
nothing in the repository documents it. It is the actual publish step.

---

## 4. Pages: what is generated and what is not

| Page | Source | Refresh |
|---|---|---|
| `research.html` | generated by `update_research.py` | daily, 08:00 ET |
| `open-data.html` | generated from `templates/open-data.html` | daily, 08:00 ET |
| `dispatch-views.html` | static shell; reads `data/dispatch-views.json` | JSON redrawn Mon/Wed/Fri |
| `index.html`, `call-sign.html`, `contact.html`, `member-research.html`, `internal/research.html` | hand-written | on edit only |

`call-sign/index.html`, `open-data/index.html` and `research/index.html` are
meta-refresh shims that preserve clean routes under Pages.

Nav and footer are hand-copied into every page. There is no template step for the
static pages, and `internal/research.html` says so in a comment. A nav change is a
six-file edit.

**Do not hand-edit `research.html` or `open-data.html`.** The next cron run
overwrites them. Edit `templates/open-data.html` or the publisher.

---

## 5. DNS and domains

Authoritative nameservers for `emr-inc.net` are still `ns2.wixdns.net` and
`ns3.wixdns.net`. **The registrar transfer off Wix has not completed.** Wix
serves the DNS that points at everything else, including the Google Workspace MX
records, so cancelling Wix still takes down the site and the mail together.

| Host | Points at | Serves |
|---|---|---|
| `emr-inc.net` | `185.199.108–111.153` | GitHub Pages |
| `www.emr-inc.net` | `emr-inc.github.io` | GitHub Pages |
| `callsign.emr-inc.net` | `cname.vercel-dns.com` | Vercel → Cloudflare (section 6) |
| `command-center.emr-inc.net` | `185.158.133.1` | Lovable app, outside this repo |
| `en.emr-inc.net` | `cdn1.wixdns.net` | orphan from the Wix site |
| `emr-inc.net` MX ×5 | Google Workspace | mail |

Mail has SPF and a Google site-verification TXT record. `google._domainkey` and
`_dmarc` both return NXDOMAIN: **no DKIM, no DMARC.**

Finishing the registrar transfer is the single highest-leverage item on this
list. It removes Wix as a dependency, unblocks DKIM and DMARC, and collapses the
Vercel hop described next.

---

## 6. CALL/SIGN

Source: `EMR-INC/call-sign` (private). Next.js 16 built with
`opennextjs-cloudflare` and deployed as a Cloudflare Worker named `call-sign`,
on the custom domain `callsign.ohpah.app`.

### Two entrances, one app

```
callsign.emr-inc.net  ->  Vercel (call-sign-2546)  --host-scope rewrite-->  Worker
callsign.ohpah.app    ->  Cloudflare Worker (direct)
```

The Vercel hop is load-bearing and must not be "simplified" to a CNAME pointing
at the Worker. `emr-inc.net` is on Wix nameservers, so the zone is not in the
Cloudflare account, so a Workers Custom Domain on that hostname is impossible; a
direct CNAME reaches Cloudflare matching no zone and fails at TLS, which presents
as a certificate problem and is not one. The hop disappears on its own once the
registrar transfer completes.

The Worker uses a custom domain rather than `workers.dev` because Cisco Umbrella,
the DNS filter on the target users' machines, blocks `workers.dev` wholesale and
answers with a forged certificate. A hostname on an owned zone is not filtered.

### The login is a shared password, not an identity system

`src/lib/auth.ts` states this in its own header, and the description is accurate:

- One shared `DEMO_EMAIL` and `DEMO_PASSWORD`, plus `AUTH_SECRET`, as Cloudflare
  Worker secrets set with `wrangler secret put`
- HMAC-SHA256 signed `cs_session` cookie, 12-hour TTL, expiry inside the signed
  payload rather than only in `Max-Age`
- Constant-time comparison through HMACs, so neither length nor prefix leaks
- Fails closed: absent secrets mean "not configured", not "let everyone through"
- Enforced in `src/proxy.ts` at the edge on `matcher: ["/dash/:path*"]`, so a new
  route under `/dash` is protected the moment it exists

What it cannot do, in its own words: it does not identify a person, so nothing
can answer *who looked at this record*; it has no accounts, no revocation and no
password reset; and the org picker on `/select` is a signpost, **not a permission
boundary**.

The read layer, `src/lib/research.ts`, holds
`RESEARCH_SUPABASE_SERVICE_ROLE_KEY`, which bypasses every row-level security
policy on the research database. The only boundary is which columns the module
chooses to select. It is careful: `import "server-only"` on line 1 turns a
client-component import into a build failure, and there is a written standing
rule against ever selecting `dispatch_transcripts.transcript`. But that boundary
lives in a convention, not in the database.

### The gap against what the site claims

`call-sign.html` tells members *"Accounts are issued to the local, not requested
here"* and *"scoped to that local's own departments."* Today there are no
accounts and no scoping. `auth.ts` names the replacement, per-user Supabase auth
with an audit trail, and says to delete the file rather than extend it.

Given the company sells to IAFF locals on the argument that a member's record
belongs to the member, closing this is the prerequisite for widening access
beyond a demo.

---

## 7. Data and provenance

| Artifact | Source | Notes |
|---|---|---|
| `data/research.json` | `spotlight.ohpah.app/api/open-data-snapshot` | rolling 7-day aggregate, refreshed daily |
| `data/dispatch-events.csv` | `ohpah-app` `dispatch_events`, via the Spotlight workbook | static 2026-09-04 capture; **no longer in the repository or its history** (`257e6ef`); working copy is kept outside the repo |
| `data/dispatch-views.json` | built from the CSV above | redrawn Mon/Wed/Fri |
| `data/nfirs-hour-of-day.json` | `ohpah-research` Supabase (`casmwfxrxlysqizxahcw`) | pulled 2026-09-13; **a live input** to `build-dispatch-views.py`, supplying the hour-of-day baseline |
| `data/nfirs-incident-composition.json` | same | pulled 2026-09-13; referenced by nothing |

The aggregate endpoint selects only `dispatch_ts`, `call_type`,
`unit_normalized`, `neris_type` and `talkgroup`. Transcript, address, row ID,
audio and person-level fields are never selected. The Supabase service-role
credential stays inside the Spotlight Cloudflare Worker and never reaches this
repository or its Actions.

The NFIRS extracts are **Florida only** (396 distinct FDIDs, 2020 onward) and
must not be described as a national record.

The figures in `research.html` come from the snapshot. The figures on the
research SVG are literals. `data/*.json` is provenance for numbers that are
hard-coded elsewhere, which matters before anyone "updates the data" and expects
a page to move.

`docs/OPEN_DATA_PIPELINE.md` is accurate except for step 8, which says *"the
existing Vercel Git integration deploys the commit."* There is no Git
integration, and Pages does the deploying.

---

## 8. Everything connected

### Owned hosts

Seven hosts across three DNS providers and two registrars. Only `emr-inc.net` is
in the migration. See section 5.

### Third-party runtime dependencies

- **Google Fonts**: every page, render-blocking, preconnected
- **Google Forms**: `contact.html` embeds form
  `1FXXOZsZu6endmH4xCkZWJ3StrX3s7w-r0k2CAmFuuow`; submissions land in a Google
  account, not this repository
- **Google Workspace**: all mail
- **Cloudflare**: the `call-sign` Worker, the `ohpah-spotlight` Worker, and the
  `ohpah.app` zone
- **Vercel**: the `callsign.emr-inc.net` rewrite hop, and two crons deploying to
  a project that serves nothing
- **cdnjs**: `p5.js` in `experiments/quiet-enclosure/` only

### Sibling repositories

Nine in `EMR-INC`; `emr-inc-site` is the only public one.

| Repo | Relationship |
|---|---|
| `OHPAH-DESIGN` | source of the design system this repo implements, by hand-copy |
| `ohpah-research` | the dispatch and NFIRS corpus; Supabase `casmwfxrxlysqizxahcw` |
| `ohpah-spotlight` | the Worker serving `/api/open-data-snapshot` and the union portal at `spotlight.ohpah.app/unions/*` |
| `call-sign` | the CALL/SIGN app (section 6) |
| `OHPAH-app` | React Native / Expo, Supabase, Cloudflare dispatch worker |
| `ohpah-ops` | Layer 1 deterministic algorithms, Layer 2 LLM interpretation |
| `ohpah-command-center` | likely behind `command-center.emr-inc.net` |
| `ohpah-brain-vault` | Obsidian notes |

This repository is downstream of `OHPAH-DESIGN` and `ohpah-research` by
hand-copy, with no sync and no check.

---

## 9. Risks, in the order I would deal with them

1. **`internal/research.html` is served with no gate.** Its protection was
   `middleware.js`, `api/auth/*` and the `vercel.json` headers, none of which
   Pages can execute, and `.vercelignore` does not govern the apex. The
   dispatch-record half of this item was resolved on 2026-09-29 by deleting the
   file from the repository and the history, which is the right remedy and the
   only one Pages leaves available: a file is withheld from `emr-inc.net` by not
   being in the branch. This page has not had that treatment. Either remove it
   or move it behind a host that can gate it.
2. **CALL/SIGN has one shared password and no audit trail**, in front of a read
   layer holding a service-role key that bypasses RLS, while the public site
   promises per-local accounts and per-local scoping. Replace with per-user
   Supabase auth before access widens past a demo.
3. **Wix is still a live dependency** for DNS and therefore for mail. Finish the
   registrar transfer; it also unblocks items 4 and 6.
4. **No DKIM, no DMARC.** SPF alone.
5. **Both crons deploy to a host that serves nothing.** Delete the step, or
   reattach the domain, but not both, and the workflows explain why.
6. **The `callsign.emr-inc.net` rewrite hop** exists only because the zone is on
   Wix. It collapses when item 3 lands.
7. **Nav and footer are copy-pasted across six pages** and have drifted before.
8. **`data/nfirs-hour-of-day.json` publishes the Supabase project reference**
   that `build-dispatch-views.py` calls a small credential leak and takes care to
   keep out of captions. Strip the internal fields from the committed copy, or
   drop the claim.
9. **`data/nfirs-incident-composition.json` is unreferenced**, and
   `dispatch-views.json`'s input is frozen at the 2026-09-04 capture, so that
   page redraws without the figures ever moving.

---

## 10. A back-of-house research platform

Sketched here because the question comes up and the answer depends on facts in
the sections above.

Much of a Palantir- or Peregrine-shaped system already exists in pieces: a corpus
with real lineage (`ohpah-research`), a deterministic metric layer separated from
an LLM interpretation layer (`ohpah-ops`), an aggregate-only egress boundary with
a validating publisher (`ohpah-spotlight` plus `update_research.py`), a governed
view catalogue whose exclusions are argued from the literature rather than
asserted, and a documentation culture in which the reasoning survives in the
file. That last one is rare and is most of what makes such a system trustworthy
rather than merely capable.

What is missing is the substrate those products actually sell:

| Capability | Status |
|---|---|
| Per-user identity, roles, revocation | one shared password |
| Audit trail: who saw which record, when | impossible by construction |
| Access enforced in the database | service-role key bypassing RLS |
| Ontology: units, people, departments, incidents as linked entities | tables plus conventions |
| Lineage from a published figure back to source rows | strong in the publisher, absent in the app |
| Saved investigations, annotations, case state | none |
| Export control, watermarking | none |

**The order matters.** Per-user auth with an audit trail comes first, not because
it is the most interesting piece but because everything else is downstream: the
consent firewall cannot open, per-person metrics cannot ship, per-local scoping
cannot become real, and export controls are meaningless while one password is the
whole boundary. Then move the read layer onto per-user JWTs with RLS policies
encoding local-to-department scope, so the boundary sits in Postgres rather than
in a comment. Then the ontology and lineage layer, which is what lets a figure on
a union dashboard be walked back to the transmissions behind it without exposing
them. That is the specific property that makes this credible in a grievance hearing.
Case state and export controls last.

The thing to resist is building the ontology first because it is the interesting
part. Over a shared password, a richer entity graph increases blast radius rather
than capability.
