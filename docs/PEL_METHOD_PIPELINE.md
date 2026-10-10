# The event load method file

`pel-method.html` is the public method surface for the event load measure. It
publishes the event classes, the radio term list, the resolved research
citations and the scope of work, and it states at first sight that none of it
is reviewed or scored.

It is generated. Edit `templates/pel-method.html`, never the output.

## The chain, which crosses two repositories

1. `EMR-INC/the-lab`, `packages/scoring/src/pel-keywords.ts` holds the term
   list and `pel-citations.ts` holds the resolved citation records. These are
   the only places either exists.
2. `packages/scoring/src/publication.ts` builds the publication payload from
   them. It is pure, so the same list produces a byte identical payload, and it
   refuses to build one that names an organisation, carries the person who
   supplied a radio code, declares a count its own tables contradict, or is not
   class 0.
3. `tools/export-pel-method.mjs` writes `data/pel-method.json`, canonical and
   on one line.
4. That file is copied into this repository at `data/pel-method.json`.
5. `data/build-pel-method.py` renders the template against it and writes
   `pel-method.html`.

```bash
# in the-lab
node tools/export-pel-method.mjs ../emr-inc-site/data/pel-method.json
# in this repo
python3 data/build-pel-method.py
```

## Why a committed file rather than a hand kept copy

This site has no build step and cannot import a TypeScript package.
`member-research.html` already carries a hand kept copy of a list that lives in
another repository and says in its own comment that it goes stale silently. One
copy like that is a known cost. A second copy, of eight classes, seventy six
terms and eight citation records, would be wrong within a month.

So nothing on the page is typed by hand. Every count, term, class route and
quotation is read out of the payload, and the template carries markers rather
than numbers. If you find yourself typing a figure into the template, the chain
is broken and the page has started lying.

## Staleness

The builder cannot tell whether the payload is current: the list lives in
another repository. What it does instead is put the list hash on the page, in
the hero row and in the footer, and embed the whole payload in the page as
`<script id="pel_method_data" type="application/json">`. Compare the hash on
the page with `pelKeywordListHash(PROPOSED_PEL_KEYWORDS)` in the lab to see
whether a refresh is due.

## The boundaries this page holds

* **No member grain, ever.** The page describes a method and carries no record,
  no incident, no member and no computed figure. `emr-inc.net` has no login on
  any public page, so there is nowhere on this site for a member figure to sit.
  A member's own figure is read inside the union portal.
* **No organisation is named.** Not the pilot department, the state agency, the
  data provider or the union affiliate. None has approved being named in
  public. The export asserts it and the builder asserts it again.
* **No dialect source.** A radio code carries who supplied its meaning, and in
  the list that is a person by name. The public form keeps the fact that the
  meaning is unconfirmed and drops who supplied it.
* **The unreviewed flag is load bearing.** The build fails if the hero loses
  it, the same way the open-data build fails if its headline changes.

## Fail closed

The builder refuses to write a page when the payload is missing a key, when a
declared count does not reconcile with the terms present, when a class cites an
identifier the payload cannot resolve, when the payload is not class 0, when a
citation has no limitation to print, when an organisation is named, when a
template marker survives into the output, when the headline or the unreviewed
flag is gone, when a term in the payload is absent from the page, or when the
list hash is not on the page. A method file that is wrong is worse than no
method file, because it is quotable.

## Local verification

```bash
python3 data/build-pel-method.py
```

The page carries no executable script beyond the site's analytics snippet, so
it is complete with JavaScript switched off.
