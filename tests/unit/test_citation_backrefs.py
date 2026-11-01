import panflute as pf

import citation_backrefs


def _cite(*keys):
    return pf.Cite(pf.Str("[n]"), citations=[pf.Citation(key) for key in keys])


def _entry(key):
    return pf.Div(pf.Para(pf.Str(key)), identifier="ref-" + key, classes=["csl-entry"])


def _links(elem):
    found = []
    elem.walk(lambda e, d: found.append(e) if isinstance(e, pf.Link) else None)
    return [(pf.stringify(link), link.url) for link in found]


def _run(*blocks):
    return citation_backrefs.main(pf.Doc(*blocks, format="html"))


def test_citations_are_anchored_in_order():
    doc = _run(pf.Para(_cite("a"), pf.Space(), _cite("a", "b")))
    anchors = [item for item in doc.content[0].content if isinstance(item, pf.Span)]
    assert [span.identifier for span in anchors] == ["cite-1", "cite-2"]
    assert isinstance(anchors[0].content[0], pf.Cite)


def test_backrefs_are_numbered_per_citation():
    doc = _run(pf.Para(_cite("a"), pf.Space(), _cite("a", "b")),
               pf.Div(_entry("a"), _entry("b"), identifier="refs"))
    refs = doc.content[1]
    assert _links(refs.content[0]) == [("↩1", "#cite-1"), ("↩2", "#cite-2")]
    assert _links(refs.content[1]) == [("↩", "#cite-2")]


def test_backref_goes_inside_numeric_entry_text():
    entry = pf.Div(pf.Para(pf.Span(pf.Str("[1]"), classes=["csl-left-margin"]),
                           pf.Span(pf.Str("text"), classes=["csl-right-inline"])),
                   identifier="ref-a")
    doc = _run(pf.Para(_cite("a")), pf.Div(entry, identifier="refs"))
    text_span = doc.content[1].content[0].content[0].content[1]
    assert _links(text_span) == [("↩", "#cite-1")]


def test_uncited_entry_has_no_backref():
    doc = _run(pf.Para(pf.Str("no citations")), pf.Div(_entry("nocited"), identifier="refs"))
    assert _links(doc) == []
