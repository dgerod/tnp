import panflute as pf

import todo_tag


def _para(text):
    return pf.Para(*todo_tag._inlines(text))


def _run(*blocks):
    doc = pf.Doc(*blocks, format="html")
    doc.walk(todo_tag.action)
    return doc


def _spans(elem):
    found = []
    elem.walk(lambda e, d: found.append(e) if isinstance(e, pf.Span) else None)
    return found


def test_inline_tag_becomes_styled_span():
    doc = _run(_para("Normal text ::tnw-todo{this is a note} and the text continues."))
    [span] = _spans(doc)
    assert span.classes == ["todo"]
    assert span.attributes["style"] == todo_tag.STYLE
    assert pf.stringify(span) == "this is a note"
    assert pf.stringify(doc) == "Normal text this is a note and the text continues.\n\n"


def test_several_tags_on_one_line():
    doc = _run(_para("::tnw-todo{one} middle ::tnw-todo{two}"))
    assert [pf.stringify(span) for span in _spans(doc)] == ["one", "two"]


def test_empty_tag():
    doc = _run(_para("before ::tnw-todo{} after"))
    [span] = _spans(doc)
    assert pf.stringify(span) == ""


def test_deprecated_spelling():
    doc = _run(_para("x ::todo{old} y"))
    assert [pf.stringify(span) for span in _spans(doc)] == ["old"]


def test_line_without_tag_is_untouched():
    para = _para("nothing to see :: here {x}")
    before = pf.stringify(para)
    doc = _run(para)
    assert _spans(doc) == []
    assert pf.stringify(doc.content[0]) == before


def test_tag_across_soft_break():
    para = pf.Para(pf.Str("::tnw-todo{a"), pf.SoftBreak(), pf.Str("b}"))
    assert [pf.stringify(span) for span in _spans(_run(para))] == ["a b"]


def test_tag_inside_emphasis_and_header():
    doc = _run(pf.Header(*todo_tag._inlines("Title ::tnw-todo{h}"), level=2),
               pf.Para(pf.Emph(*todo_tag._inlines("::tnw-todo{e}"))))
    assert [pf.stringify(span) for span in _spans(doc)] == ["h", "e"]


def test_code_is_untouched():
    doc = _run(pf.Para(pf.Code("::tnw-todo{x}")), pf.CodeBlock("::tnw-todo{y}"))
    assert _spans(doc) == []


def test_block_tag_is_styled():
    for cls in ("tnw-todo", "todo"):
        doc = _run(pf.Div(_para("block note"), classes=[cls]))
        assert doc.content[0].attributes["style"] == todo_tag.STYLE


def test_other_div_is_untouched():
    doc = _run(pf.Div(_para("x"), classes=["note"]))
    assert "style" not in doc.content[0].attributes
