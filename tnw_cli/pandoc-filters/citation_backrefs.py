#!/usr/bin/env python3
"""Add return links from each bibliography entry to the places it is cited.

Runs after `--citeproc`: every in-text citation gets an anchor
(`cite-<n>`), and every references entry (`ref-<key>`) gets a return link
per citation: `↩` when cited once, `↩1`, `↩2`, ... when cited more often.
"""

import panflute as pf

ARROW = "↩"


def _anchor_citations(elem, doc):
    if not isinstance(elem, pf.Cite):
        return None
    doc.tnw_cite_count += 1
    anchor = "cite-%d" % doc.tnw_cite_count
    for citation in elem.citations:
        doc.tnw_backrefs.setdefault(citation.id, []).append(anchor)
    return pf.Span(elem, identifier=anchor, classes=["citation-anchor"])


def _backref_links(anchors):
    if len(anchors) == 1:
        labels = [ARROW]
    else:
        labels = ["%s%d" % (ARROW, number) for number in range(1, len(anchors) + 1)]
    inlines = []
    for label, anchor in zip(labels, anchors):
        inlines += [pf.Space(), pf.Link(pf.Str(label), url="#" + anchor,
                                        classes=["citation-backref"])]
    return inlines


def _add_backrefs(elem, doc):
    if not (isinstance(elem, pf.Div) and elem.identifier.startswith("ref-")):
        return None
    anchors = doc.tnw_backrefs.get(elem.identifier[len("ref-"):])
    if not anchors or not elem.content:
        return None
    last = elem.content[-1]
    if isinstance(last, (pf.Para, pf.Plain)):
        target = last
        # Numeric styles (IEEE) split the entry into a label and a
        # `csl-right-inline` text span; the links belong inside the text.
        if (last.content and isinstance(last.content[-1], pf.Span)
                and "csl-right-inline" in last.content[-1].classes):
            target = last.content[-1]
        target.content.extend(_backref_links(anchors))
    else:
        elem.content.append(pf.Plain(*_backref_links(anchors)[1:]))
    return None


def prepare(doc):
    doc.tnw_cite_count = 0
    doc.tnw_backrefs = {}


def main(doc=None):
    return pf.run_filters([_anchor_citations, _add_backrefs], prepare=prepare, doc=doc)


if __name__ == "__main__":
    main()
