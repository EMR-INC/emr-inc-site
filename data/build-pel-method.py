#!/usr/bin/env python3
"""Build pel-method.html, the public method file for the event load measure.

Renders templates/pel-method.html against data/pel-method.json. The JSON is
written by the-lab/tools/export-pel-method.mjs out of
packages/scoring/src/publication.ts, which is the only place the term list, the
class routes and the citation records exist. This script types no figure of its
own: every count, term, route and quotation below is read out of the payload,
and the template carries markers rather than numbers.

    python3 data/build-pel-method.py                       # default paths
    python3 data/build-pel-method.py --data path/to.json

Fails closed. It refuses to write a page when the payload is missing a key,
when a declared count does not reconcile with the terms actually present, when
a class cites an identifier the payload cannot resolve, when the payload is not
class 0, or when any template marker survives into the output. A method file
that is wrong is worse than no method file, because it is quotable.

One thing it deliberately does NOT check: whether the payload is current. It
cannot: the list lives in another repository. What it does instead is put the
list hash on the page, in the footer and in the embedded copy, so that a reader
and the lab can compare them.
"""
import argparse
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Keys the payload must carry. A missing one is a changed exporter, not a
# cosmetic problem, so it stops the build.
REQUIRED = {
    "data_class", "surface", "citationsVerifiedOn", "keywordList", "classes",
    "citations", "releaseStatus", "citedByNoClass", "citationsNotRead",
    "rejectedTerms",
}
REQUIRED_LIST = {"version", "authoredOn", "reviewed", "hash", "termCount", "factGroupCount"}

# The four moves the research declines, each one read out of a source record so
# the quotation on the page cannot drift from the quotation in the repository.
# (row key, citation id, which field, the consequence, which is ours to state)
DECLINED = [
    ("Event weights", "PC02", "limitations",
     "Seven of the eight classes carry “No default weight” as an explicit column. "
     "Any weight in this system is a guess and is labelled one."),
    ("Dispatch classification", "PC05", "limitations",
     "So a dispatch code does not classify an experience, and a decaying count with a "
     "fixed half life is not supported either."),
    ("A dose curve", "PC01", "supportedUse",
     "It is also the one source in the set whose finding is mixed rather than an "
     "association."),
    ("A route from an incident flag", "PC07", "limitations",
     "That sentence is the whole argument of this page, written by somebody other "
     "than us."),
]

# Human readable names for the two fields a reader meets as identifiers.
ROUTE_LABEL = {
    "required_corroboration": "Corroboration route",
    "exclusion_boundary": "Exclusion boundary",
}
ROUTE_MARK = {
    "required_corroboration": "mark--corroboration",
    "exclusion_boundary": "mark--boundary",
}


def esc(value):
    return html.escape(str(value), quote=True)


# ---------------------------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------------------------
def validate_payload(data):
    missing = REQUIRED - data.keys()
    if missing:
        raise ValueError(f"payload is missing required keys: {sorted(missing)}")
    if data["data_class"] != 0:
        raise ValueError("only a class 0 payload may be published")
    lst = data["keywordList"]
    missing = REQUIRED_LIST - lst.keys()
    if missing:
        raise ValueError(f"keywordList is missing required keys: {sorted(missing)}")
    if not isinstance(lst["reviewed"], bool):
        raise ValueError("the reviewed flag must be a boolean, since the page states it")
    if not data["classes"]:
        raise ValueError("the payload carries no class, so there is no method to publish")

    present = sum(len(k["terms"]) for k in data["classes"])
    if present != lst["termCount"]:
        raise ValueError(
            f"the payload holds {present} terms and declares {lst['termCount']}. "
            "The page would state a figure its own tables contradict."
        )
    for klass in data["classes"]:
        if klass["termCount"] != len(klass["terms"]):
            raise ValueError(f"{klass['id']} declares {klass['termCount']} terms and holds "
                             f"{len(klass['terms'])}")

    resolved = {c["id"] for c in data["citations"]}
    for klass in data["classes"]:
        unresolved = [c for c in klass["citations"] if c not in resolved]
        if unresolved:
            raise ValueError(f"{klass['id']} cites {unresolved}, which the payload cannot resolve")
    for cite in data["citations"]:
        for field in ("limitations", "supportedUse", "population", "design", "primaryUrl"):
            if not cite.get(field):
                raise ValueError(f"{cite['id']} has no {field}, and the page prints it")

    for key, cid, field, _ in DECLINED:
        if cid not in resolved:
            raise ValueError(f"the declined row {key!r} cites {cid}, which is not in the payload")

    # No organisation reaches a public page without owner approval, and none has
    # been given. The exporter asserts this too; asserted again here because
    # this is the last step before the file is served.
    blob = json.dumps(data)
    for word in ("Department of Health", "Fire Department", "Biospatial", "IAFF"):
        if word in blob:
            raise ValueError(f"the payload names an organisation: {word!r}")


def validate_output(page, data):
    leftover = re.findall(r"__[A-Z_]+__", page)
    if leftover:
        raise ValueError(f"template markers survived into the output: {sorted(set(leftover))}")
    # The claim is the page. If the headline is edited away, the build fails
    # rather than shipping a method file with no claim on it.
    if "A word is<br>not a finding." not in page:
        raise ValueError("the approved headline is missing")
    if "Nothing on this page is scored" not in page:
        raise ValueError("the unreviewed flag is missing from the hero")
    if data["keywordList"]["reviewed"] is False and "reviewed: no" not in page:
        raise ValueError("the list is unreviewed and the page does not say so")
    for klass in data["classes"]:
        for term in klass["terms"]:
            if esc(term["term"]) not in page:
                raise ValueError(f"term {term['term']!r} is in the payload and not on the page")
    if data["keywordList"]["hash"] not in page:
        raise ValueError("the list hash is not on the page, so staleness is undetectable")


# ---------------------------------------------------------------------------
# FIGURE 1 · THE ROUTE
#
# A branching feed. Every path terminates at a labelled fact, a refusal or a
# gate, because a line that ends in empty space fails the diagram test. The
# spine is traced in red, the record layer is blue, and the closed gate carries
# the yellow crossed band. Nothing encodes a quantity in colour.
# ---------------------------------------------------------------------------
def svg_open(width, height, aria):
    return (f'<svg class="fig-svg" viewBox="0 0 {width} {height}" role="img" '
            f'aria-label="{esc(aria)}">'
            '<defs>'
            '<marker id="pm-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
            'markerHeight="7" orient="auto-start-reverse">'
            '<path d="M 0 0 L 10 5 L 0 10 z" fill="#10213B"></path></marker>'
            '<pattern id="pm-hatch" width="6" height="6" patternTransform="rotate(45)" '
            'patternUnits="userSpaceOnUse">'
            '<line x1="0" y1="0" x2="0" y2="6" stroke="#10213B" stroke-width="2"></line>'
            '</pattern>'
            '</defs>')


def node(x, y, w, h, lines, fill="#F1EBDD", color="#10213B", stroke="#10213B", dash=None):
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" '
             f'stroke="{stroke}" stroke-width="2"'
             + (f' stroke-dasharray="{dash}"' if dash else "") + '></rect>']
    # Lines are (text, weight, size) or (text, weight, size, dx). The offset
    # exists because SVG collapses leading whitespace, so a line that has to
    # clear an inline mark is indented by coordinate and never by spaces.
    cursor = y + 26
    for line in lines:
        text, weight, size = line[0], line[1], line[2]
        dx = line[3] if len(line) > 3 else 0
        parts.append(
            f'<text x="{x + 14 + dx}" y="{cursor}" font-size="{size}" '
            f'font-weight="{weight}" fill="{color}">{esc(text)}</text>')
        cursor += size + 5
    return "".join(parts)


def arrow(x1, y1, x2, y2, label=None, color="#D5222A", dash=None, label_dy=-8):
    line = (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="2.5" marker-end="url(#pm-arrow)"'
            + (f' stroke-dasharray="{dash}"' if dash else "") + '></line>')
    if label is None:
        return line
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    return line + (f'<text x="{mx:.0f}" y="{my + label_dy:.0f}" font-size="11" '
                   f'font-weight="700" fill="#10213B" text-anchor="middle">{esc(label)}</text>')


def route_figure(data):
    classes = data["classes"]
    terms = [t for k in classes for t in k["terms"]]
    corroboration = sum(1 for t in terms if t["drawnFrom"] == "required_corroboration")
    boundary = sum(1 for t in terms if t["drawnFrom"] == "exclusion_boundary")
    insufficient = sum(1 for t in terms if t["namedInsufficient"])
    private = next((k for k in classes if k["id"] == "known_victim"), None)

    aria = (
        "A branching diagram. A radio transmission reaches a term match. "
        f"{corroboration} terms sit on a corroboration route and open a candidate for review; "
        f"{boundary} terms sit on an exclusion boundary, {insufficient} of which the research "
        "names as insufficient on their own, and these open a review and carry no weight. "
        "A candidate either reaches a corroborated event fact, which requires passing a "
        "clinical review that currently has no reviewer appointed, or is refused for want of "
        "corroboration. A separate lane shows the private class, which has no term route and "
        "is reached only when a member volunteers a confirmation."
    )
    s = [svg_open(960, 452, aria)]

    # Spine, left to right.
    s.append(node(8, 30, 152, 88, [("Radio", 700, 14), ("transmission", 700, 14),
                                   ("one talkgroup", 400, 12)]))
    s.append(node(216, 30, 184, 88, [("Term match", 700, 14),
                                     (f"{corroboration} on a route", 400, 12, 22),
                                     (f"{boundary} on a boundary", 400, 12, 22)]))
    # The two marks the legend names, drawn where the counts are, so the key
    # describes something the figure actually encodes.
    s.append('<rect x="230" y="64" width="11" height="11" fill="#2363A0" stroke="#10213B" '
             'stroke-width="2"></rect>')
    s.append('<rect x="230" y="81" width="11" height="11" fill="none" stroke="#10213B" '
             'stroke-width="2"></rect>')
    s.append(node(456, 30, 184, 88, [("Candidate", 700, 14), ("a person reads", 400, 12),
                                     ("the record", 400, 12)]))
    s.append(node(696, 30, 120, 88, [("Clinical", 700, 13), ("review", 700, 13),
                                     ("unassigned", 400, 12)], fill="#E5C500"))
    s.append(node(872, 30, 80, 88, [("Event", 700, 13), ("fact", 700, 13)],
                  fill="#2363A0", color="#F1EBDD", stroke="#10213B"))

    s.append(arrow(160, 74, 212, 74))
    s.append(arrow(400, 74, 452, 74, "matches"))
    s.append(arrow(640, 74, 692, 74, "submits"))
    # The last hop does not complete, and the drawing says so rather than the
    # caption saying it.
    s.append(arrow(816, 74, 868, 74, None, color="#10213B", dash="6 5"))
    s.append('<line x1="832" y1="54" x2="856" y2="94" stroke="#D5222A" stroke-width="3"></line>')
    s.append('<line x1="856" y1="54" x2="832" y2="94" stroke="#D5222A" stroke-width="3"></line>')
    s.append('<text x="952" y="138" font-size="11" font-weight="700" fill="#10213B" '
             'text-anchor="end">No path completes today</text>')

    # Branch down from the term match: the boundary terminal.
    s.append(arrow(308, 118, 308, 182, None))
    s.append(node(216, 184, 184, 96, [("Opens a review", 700, 13), ("and nothing else", 700, 13),
                                      (f"{insufficient} terms named", 400, 12, 20),
                                      ("insufficient alone", 400, 12, 20)]))
    s.append('<circle cx="228" cy="246" r="6" fill="#E5C500" stroke="#10213B" '
             'stroke-width="2"></circle>')

    # Branch down from the candidate: the refusal terminal.
    s.append(arrow(548, 118, 548, 182, None))
    s.append(node(456, 184, 184, 96, [("Refused", 700, 13), ("corroboration absent", 400, 12),
                                      ("and the class does", 400, 12),
                                      ("not attach", 400, 12)]))

    # The private lane. No arrow from anything above it: that is the point.
    s.append('<line x1="8" y1="318" x2="952" y2="318" stroke="#10213B" stroke-width="1" '
             'stroke-dasharray="3 4"></line>')
    s.append('<text x="8" y="342" font-size="11" font-weight="700" fill="#10213B">'
             'NO ROUTE FROM THE RADIO AT ALL</text>')
    s.append(node(8, 356, 248, 80, [("Member's own", 700, 14), ("confirmation", 700, 14),
                                    ("voluntary, private", 400, 12)],
                  fill="#2363A0", color="#F1EBDD"))
    s.append(arrow(256, 396, 324, 396, None, color="#2363A0"))
    s.append(node(328, 356, 340, 80,
                  [(private["label"] if private else "Private class", 700, 14),
                   ("never inferred, never shared", 400, 12)]))
    s.append('</svg>')
    return "".join(s)


# ---------------------------------------------------------------------------
# FIGURE 2 · WHAT STANDS BEHIND EACH CLASS
#
# A bounded comparison. Length is the term count; a filled mark is an empirical
# paper and an open hatched mark is the definition every class shares. Removing
# the colour leaves the meaning intact, which is the test.
# ---------------------------------------------------------------------------
def evidence_figure(data):
    classes = data["classes"]
    max_terms = max(k["termCount"] for k in classes) or 1
    row_h = 54
    top = 64
    height = top + row_h * len(classes) + 36
    bar_x, bar_w = 330, 230
    mark_x = 610

    pieces = []
    for k in classes:
        empirical = len(k["empiricalCitations"])
        pieces.append(f"{k['label']}: {k['termCount']} terms, "
                      f"{empirical} empirical source{'s' if empirical != 1 else ''} "
                      f"plus the shared definition")
    aria = ("A comparison across the eight event classes. " + ". ".join(pieces) + ".")

    s = [svg_open(960, height, aria)]
    for label, x in (("Class", 8), ("Terms", bar_x), ("Sources behind it", mark_x)):
        s.append(f'<text x="{x}" y="26" font-size="11" font-weight="700" fill="#10213B" '
                 f'letter-spacing="1.6">{esc(label.upper())}</text>')
    s.append(f'<line x1="8" y1="40" x2="952" y2="40" stroke="#10213B" stroke-width="2"></line>')
    # The scale, stated rather than implied.
    s.append(f'<text x="{bar_x}" y="{height - 12}" font-size="11" fill="#10213B">0</text>')
    s.append(f'<text x="{bar_x + bar_w}" y="{height - 12}" font-size="11" fill="#10213B" '
             f'text-anchor="end">{max_terms} terms</text>')
    s.append(f'<line x1="{bar_x}" y1="{top - 10}" x2="{bar_x}" y2="{height - 26}" '
             f'stroke="#10213B" stroke-width="1"></line>')
    s.append(f'<line x1="{bar_x + bar_w}" y1="{top - 10}" x2="{bar_x + bar_w}" '
             f'y2="{height - 26}" stroke="#10213B" stroke-width="1" '
             f'stroke-dasharray="3 4"></line>')

    for i, k in enumerate(classes):
        y = top + i * row_h
        mid = y + row_h / 2
        s.append(f'<line x1="8" y1="{y + row_h}" x2="952" y2="{y + row_h}" stroke="#10213B" '
                 f'stroke-width="1"></line>')
        s.append(f'<text x="8" y="{mid + 1:.0f}" font-size="13" font-weight="700" '
                 f'fill="#10213B">{esc(k["label"])}</text>')
        s.append(f'<text x="8" y="{mid + 16:.0f}" font-size="11" fill="#10213B">'
                 f'{esc(k["id"])}</text>')
        if k["termCount"]:
            w = max(3, k["termCount"] / max_terms * bar_w)
            s.append(f'<rect x="{bar_x}" y="{mid - 8:.0f}" width="{w:.1f}" height="16" '
                     f'fill="#10213B"></rect>')
            s.append(f'<text x="{bar_x + w + 8:.0f}" y="{mid + 5:.0f}" font-size="13" '
                     f'font-weight="700" fill="#10213B">{k["termCount"]}</text>')
        else:
            s.append(f'<text x="{bar_x}" y="{mid + 5:.0f}" font-size="12" font-weight="700" '
                     f'fill="#10213B">none, by decision</text>')
        # Marks: one filled square per empirical source, one hatched square for
        # the definition they all share.
        mx = mark_x
        for cid in k["empiricalCitations"]:
            s.append(f'<rect x="{mx}" y="{mid - 9:.0f}" width="18" height="18" fill="#2363A0" '
                     f'stroke="#10213B" stroke-width="2"></rect>')
            s.append(f'<text x="{mx + 9}" y="{mid + 24:.0f}" font-size="10" fill="#10213B" '
                     f'text-anchor="middle">{esc(cid)}</text>')
            mx += 30
        definition = [c for c in k["citations"] if c not in k["empiricalCitations"]]
        for cid in definition:
            s.append(f'<rect x="{mx}" y="{mid - 9:.0f}" width="18" height="18" '
                     f'fill="url(#pm-hatch)" stroke="#10213B" stroke-width="2"></rect>')
            s.append(f'<text x="{mx + 9}" y="{mid + 24:.0f}" font-size="10" fill="#10213B" '
                     f'text-anchor="middle">{esc(cid)}</text>')
            mx += 30
        s.append(f'<text x="{mx + 10}" y="{mid + 5:.0f}" font-size="12" fill="#10213B">'
                 f'{len(k["empiricalCitations"])} empirical, 1 definition</text>')
    s.append('</svg>')
    return "".join(s)


# ---------------------------------------------------------------------------
# BLOCKS
# ---------------------------------------------------------------------------
def class_rows(data):
    out = []
    for k in data["classes"]:
        # Plain word, not the "off by default" hatch: that mark means a dialect
        # term is disabled, and one symbol cannot carry two meanings.
        none = "<span class=\"small\">none</span>"
        terms = f'{k["termCount"]}' if k["termCount"] else none
        sources = " &middot; ".join(esc(c) for c in k["citations"])
        out.append(
            "<tr>"
            f'<th scope="row">{esc(k["id"])}<br><span class="small">{esc(k["label"])}</span></th>'
            f'<td>{esc(k["requiredCorroboration"])}</td>'
            f'<td>{esc(k["exclusionBoundary"])}</td>'
            f'<td class="n">{terms}</td>'
            f'<td class="data">{sources}</td>'
            "</tr>")
    return "".join(out)


def classes_without_terms(data):
    out = []
    for k in data["classes"]:
        if not k["withoutTermsBecause"]:
            continue
        out.append(f'<p class="small"><strong>{esc(k["label"])}</strong> '
                   f'<span class="data">{esc(k["id"])}</span>. '
                   f'{esc(k["withoutTermsBecause"])}</p>')
    if not out:
        raise ValueError("no class explains why it has no terms, and the page has a section for it")
    return "".join(out)


def term_sections(data, dialect_note):
    out = []
    for k in data["classes"]:
        if not k["termCount"]:
            continue
        rows = []
        for t in k["terms"]:
            marks = [f'<span class="mark {ROUTE_MARK[t["drawnFrom"]]}">'
                     f'{esc(ROUTE_LABEL[t["drawnFrom"]])}</span>']
            if t["namedInsufficient"]:
                marks.append('<span class="mark mark--insufficient">Named insufficient</span>')
            counted = (f'one fact with the rest of <span class="data">{esc(t["factGroup"])}</span>'
                       if t["factGroup"] else "its own fact")
            if t["matchedByDefault"]:
                default = "On"
            else:
                default = (f'<span class="mark mark--off">Off</span> '
                           f'<span class="small">{esc(t["dialect"])}</span>')
            rows.append("<tr>"
                        f'<th scope="row">{esc(t["term"])}</th>'
                        f'<td>{" ".join(marks)}</td>'
                        f'<td class="small">Counted as {counted}</td>'
                        f'<td class="small">{default}</td>'
                        "</tr>")
        empirical = ", ".join(esc(c) for c in k["empiricalCitations"])
        definition = ", ".join(esc(c) for c in k["citations"]
                              if c not in k["empiricalCitations"])
        out.append(
            '<div class="stack">'
            f'<div class="stack-8"><h3 class="h3">{esc(k["label"])}</h3>'
            f'<p class="data">{esc(k["id"])} &middot; {k["termCount"]} terms &middot; '
            f'empirical source {empirical} &middot; definition {definition}</p>'
            f'<p class="small measure"><strong>Requires</strong> '
            f'{esc(k["requiredCorroboration"])} <strong>Not enough</strong> '
            f'{esc(k["exclusionBoundary"])}</p></div>'
            '<div class="scroller"><table>'
            f'<caption>{esc(k["label"])} &middot; {k["termCount"]} terms</caption>'
            '<thead><tr><th scope="col">Term</th><th scope="col">How it was drawn</th>'
            '<th scope="col">Counting</th><th scope="col">Matched by default</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>'
            '</div>')
    out.append(f'<p class="small measure note">{esc(dialect_note)}</p>')
    return "".join(out)


def rejected_rows(data):
    return "".join(
        f'<tr><th scope="row">{esc(r["term"])}</th><td>{esc(r["reason"])}</td></tr>'
        for r in data["rejectedTerms"])


def locus(cite):
    if cite["pmid"]:
        bits = [f'<a href="{esc(cite["primaryUrl"])}">PMID {esc(cite["pmid"])}</a>']
        if cite["doi"]:
            bits.append(f'<a href="https://doi.org/{esc(cite["doi"])}">doi {esc(cite["doi"])}</a>')
        return " &middot; ".join(bits)
    return f'<a href="{esc(cite["primaryUrl"])}">{esc(cite["primaryUrl"])}</a>'


def citation_blocks(data):
    out = []
    for cite in data["citations"]:
        if cite["id"] in data["citedByNoClass"]:
            continue
        used_by = [k["id"] for k in data["classes"] if cite["id"] in k["citations"]]
        out.append(
            '<div class="panel panel--white stack-8">'
            f'<p class="eyebrow">{esc(cite["id"])} &middot; {esc(cite["direction"])} '
            f'&middot; {esc(cite["origin"].replace("_", " "))}</p>'
            f'<p class="body measure">{esc(cite["fullCitation"])}</p>'
            '<div class="rows">'
            f'<div class="row"><p class="row__key">Population</p>'
            f'<p class="body">{esc(cite["population"])} &middot; {esc(cite["design"])}</p></div>'
            f'<div class="row"><p class="row__key">Finding</p>'
            f'<p class="body">{esc(cite["finding"])}</p></div>'
            f'<div class="row"><p class="row__key">Supports</p>'
            f'<p class="body">{esc(cite["supportedUse"])}</p></div>'
            f'<div class="row"><p class="row__key">Does not support</p>'
            f'<p class="body">&ldquo;{esc(cite["limitations"])}&rdquo;</p></div>'
            f'<div class="row"><p class="row__key">Review depth</p>'
            f'<p class="body">{esc(cite["reviewDepth"])}. {esc(cite["pendingReview"])}</p></div>'
            f'<div class="row"><p class="row__key">Locus</p><p class="data">{locus(cite)}</p></div>'
            f'<div class="row"><p class="row__key">Carried by</p>'
            f'<p class="data">{" &middot; ".join(esc(u) for u in used_by)}</p></div>'
            '</div></div>')
    return "".join(out)


def unused_instrument(data):
    out = []
    for cid in data["citedByNoClass"]:
        cite = next(c for c in data["citations"] if c["id"] == cid)
        out.append(
            f'<p class="body measure"><span class="data">{esc(cid)}</span> is in the library and '
            f'no class cites it. {esc(cite["fullCitation"])} {esc(cite["finding"])}</p>'
            f'<p class="small measure">The rolling count of events has no threshold and no '
            f'instrument behind it, and an outside instrument is the intended route to '
            f'validating a figure. This is a candidate for that role and not part of the '
            f'measure. Its own limitation sets the shape of any such use: '
            f'&ldquo;{esc(cite["limitations"])}&rdquo; It may validate a figure. '
            f'It may never feed one.</p>')
    if not out:
        return ('<p class="body measure">Every source in the library is cited by at least one '
                'class.</p>')
    return "".join(out)


def declined_rows(data):
    by_id = {c["id"]: c for c in data["citations"]}
    out = []
    for key, cid, field, consequence in DECLINED:
        cite = by_id[cid]
        year = cite["year"] if re.fullmatch(r"\d{4}", cite["year"]) else cite["design"].lower()
        out.append(
            '<div class="row">'
            f'<p class="row__key">{esc(key)}</p>'
            f'<p class="body"><span class="data">{esc(cid)}</span>, {esc(year)}: '
            f'&ldquo;{esc(cite[field])}&rdquo; {esc(consequence)}</p>'
            '</div>')
    return "".join(out)


def entrapment_sentence(data):
    klass = next(k for k in data["classes"] if k["id"] == "member_entrapment")
    cid = klass["empiricalCitations"][0]
    cite = next(c for c in data["citations"] if c["id"] == cid)
    return (f'The {klass["termCount"]} terms about a member trapped or out of air stand on one '
            f'source: {esc(cite["population"])}, {esc(cite["design"].lower())}, '
            f'{esc(cite["year"])}.')


# ---------------------------------------------------------------------------
def render(data, template):
    lst = data["keywordList"]
    terms = [t for k in data["classes"] for t in k["terms"]]
    empirical = [c for c in data["citations"] if c["direction"] != "definition"]
    publications = [c for c in data["citations"] if c["pmid"]]
    single_paper = sum(1 for k in data["classes"] if len(k["empiricalCitations"]) == 1)
    with_terms = sum(1 for k in data["classes"] if k["termCount"])
    dialect_note = (
        "A dialect term carries the department whose code list it belongs to. The meaning was "
        "supplied internally and is not confirmed against any department published signal list, "
        "so every dialect term is off until the department that uses it confirms the code.")

    replacements = {
        "__GENERATED__": date.today().isoformat(),
        "__LIST_VERSION__": esc(lst["version"]),
        "__LIST_AUTHORED__": esc(lst["authoredOn"]),
        "__LIST_HASH__": esc(lst["hash"]),
        "__TERM_COUNT__": f'{lst["termCount"]:,}',
        "__CLASS_COUNT__": str(len(data["classes"])),
        "__CLASSES_WITH_TERMS__": str(with_terms),
        "__FACT_GROUP_COUNT__": str(lst["factGroupCount"]),
        "__NAMED_INSUFFICIENT_COUNT__": str(sum(1 for t in terms if t["namedInsufficient"])),
        "__DIALECT_COUNT__": str(sum(1 for t in terms if t["dialect"])),
        "__CITATION_COUNT__": str(len(data["citations"])),
        "__EMPIRICAL_CITATION_COUNT__": str(len(empirical)),
        "__PUBLICATION_COUNT__": str(len(publications)),
        "__SINGLE_PAPER_CLASSES__": str(single_paper),
        "__RELEASE_STATUS__": esc(data["releaseStatus"]),
        "__VERIFIED_ON__": esc(data["citationsVerifiedOn"]),
        "__CITATIONS_NOT_READ__": esc(data["citationsNotRead"]),
        "__ENTRAPMENT_SENTENCE__": entrapment_sentence(data),
        "__ROUTE_FIGURE__": route_figure(data),
        "__EVIDENCE_FIGURE__": evidence_figure(data),
        "__CLASS_ROWS__": class_rows(data),
        "__CLASSES_WITHOUT_TERMS__": classes_without_terms(data),
        "__TERM_SECTIONS__": term_sections(data, dialect_note),
        "__REJECTED_ROWS__": rejected_rows(data),
        "__CITATION_BLOCKS__": citation_blocks(data),
        "__UNUSED_INSTRUMENT__": unused_instrument(data),
        "__DECLINED_ROWS__": declined_rows(data),
        # The page carries its own source, so a reader can check the tables
        # against the payload without leaving the page.
        "__PAYLOAD_JSON__": json.dumps(data, separators=(",", ":")).replace("</", "<\\/"),
    }
    page = template
    for marker, value in replacements.items():
        if marker not in page:
            raise ValueError(f"template marker is missing: {marker}")
        page = page.replace(marker, value)
    return page


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=ROOT / "data" / "pel-method.json")
    ap.add_argument("--template", type=Path, default=ROOT / "templates" / "pel-method.html")
    ap.add_argument("--out", type=Path, default=ROOT / "pel-method.html")
    a = ap.parse_args()

    data = json.loads(a.data.read_text(encoding="utf-8"))
    validate_payload(data)
    page = render(data, a.template.read_text(encoding="utf-8"))
    validate_output(page, data)
    a.out.write_text(page, encoding="utf-8")

    lst = data["keywordList"]
    print(f"{a.out.name}: {len(page):,} bytes")
    print(f"  list     {lst['version']}  reviewed: {lst['reviewed']}  hash {lst['hash']}")
    print(f"  terms    {lst['termCount']} across {len(data['classes'])} classes")
    print(f"  sources  {len(data['citations'])} records, {len(data['citations']) and len([c for c in data['citations'] if c['direction'] != 'definition'])} empirical")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:                      # fail closed, and say why
        print(f"build-pel-method: {exc}", file=sys.stderr)
        sys.exit(1)
