import panflute as pf

import todo_tag


def _inlines(text):
    inlines = []
    for index, word in enumerate(text.split(" ")):
        if index:
            inlines.append(pf.Space())
        if word:
            inlines.append(pf.Str(word))
    return inlines


def _para(text):
    return pf.Para(*_inlines(text))


def _run(*blocks):
    doc = pf.Doc(*blocks, format="html")
    doc.walk(todo_tag.action)
    return doc


def _spans(elem):
    found = []
    elem.walk(lambda e, d: found.append(e) if isinstance(e, pf.Span) else None)
    return found


def test_inline_tag_becomes_styled_span():
    doc = _run(_para("Normal text ::tnp-todo{this is a note} and the text continues."))
    [span] = _spans(doc)
    assert span.classes == ["todo"]
    assert span.attributes["style"] == todo_tag.STYLE
    assert pf.stringify(span) == "this is a note"
    assert pf.stringify(doc) == "Normal text this is a note and the text continues.\n\n"


def test_several_tags_on_one_line():
    doc = _run(_para("::tnp-todo{one} middle ::tnp-todo{two}"))
    assert [pf.stringify(span) for span in _spans(doc)] == ["one", "two"]


def test_empty_tag():
    doc = _run(_para("before ::tnp-todo{} after"))
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
    para = pf.Para(pf.Str("::tnp-todo{a"), pf.SoftBreak(), pf.Str("b}"))
    assert [pf.stringify(span) for span in _spans(_run(para))] == ["a b"]


def test_quotes_inside_tag_are_kept():
    para = pf.Para(pf.Str("::tnp-todo{say"), pf.Space(),
                   pf.Quoted(pf.Str("hi"), quote_type="DoubleQuote"), pf.Space(), pf.Str("now}"))
    [span] = _spans(_run(para))
    assert isinstance(span.content[2], pf.Quoted)
    assert span.content[2].quote_type == "DoubleQuote"
    assert span.content[2].content[0].text == "hi"


def test_quotes_around_tag_are_kept():
    doc = _run(pf.Para(pf.Quoted(pf.Str("::tnp-todo{x}"), quote_type="DoubleQuote")))
    assert isinstance(doc.content[0].content[0], pf.Quoted)
    assert [span.content[0].text for span in _spans(doc)] == ["x"]


def test_formatting_inside_tag_is_kept():
    para = pf.Para(pf.Str("::tnp-todo{"), pf.Emph(pf.Str("a")), pf.Space(), pf.Strong(pf.Str("b")),
                   pf.Space(), pf.Code("c}"), pf.Str("}"), pf.Str("after"))
    doc = _run(para)
    [span] = _spans(doc)
    assert [type(item) for item in span.content] == [pf.Emph, pf.Space, pf.Strong, pf.Space, pf.Code]
    assert isinstance(doc.content[0].content[-1], pf.Str)


def test_closing_brace_inside_formatting_does_not_close_the_tag():
    para = pf.Para(pf.Str("::tnp-todo{a"), pf.Emph(pf.Str("b}")))
    doc = _run(para)
    assert _spans(doc) == []
    assert pf.stringify(doc) == "::tnp-todo{ab}\n\n"


def test_unclosed_tag_after_a_closed_one_stays_as_text():
    doc = _run(_para("::tnp-todo{a} and ::tnp-todo{b"))
    assert [pf.stringify(span) for span in _spans(doc)] == ["a"]
    assert pf.stringify(doc).endswith("and ::tnp-todo{b\n\n")


def test_text_around_tag_in_one_word():
    doc = _run(_para("x::tnp-todo{a}y}"))
    assert [pf.stringify(span) for span in _spans(doc)] == ["a"]
    assert pf.stringify(doc) == "xay}\n\n"


def test_tag_inside_emphasis_and_header():
    doc = _run(pf.Header(*_inlines("Title ::tnp-todo{h}"), level=2),
               pf.Para(pf.Emph(*_inlines("::tnp-todo{e}"))))
    assert [pf.stringify(span) for span in _spans(doc)] == ["h", "e"]


def test_code_is_untouched():
    doc = _run(pf.Para(pf.Code("::tnp-todo{x}")), pf.CodeBlock("::tnp-todo{y}"))
    assert _spans(doc) == []


def test_block_tag_is_styled():
    for cls in ("tnp-todo", "todo"):
        doc = _run(pf.Div(_para("block note"), classes=[cls]))
        assert doc.content[0].attributes["style"] == todo_tag.STYLE


def test_other_div_is_untouched():
    doc = _run(pf.Div(_para("x"), classes=["note"]))
    assert "style" not in doc.content[0].attributes
