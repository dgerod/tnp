import os

import panflute as pf

import diagram_importer


def _para(*inlines):
    return pf.Para(*inlines)


def test_lone_tag_path():
    para = _para(pf.Str("::tnp-mmd{diagrams/flow.mmd}"))
    assert diagram_importer.lone_tag_path(para, "tnp-mmd") == "diagrams/flow.mmd"


def test_lone_tag_path_with_spaces():
    para = _para(pf.Str("::tnp-puml{my"), pf.Space(), pf.Str("dir/a.puml}"))
    assert diagram_importer.lone_tag_path(para, "tnp-puml") == "my dir/a.puml"


def test_tag_mixed_with_text_is_ignored():
    para = _para(pf.Str("see"), pf.Space(), pf.Str("::tnp-mmd{a.mmd}"))
    assert diagram_importer.lone_tag_path(para, "tnp-mmd") is None


def test_other_tag_or_element_is_ignored():
    assert diagram_importer.lone_tag_path(_para(pf.Str("::tnp-puml{a.puml}")), "tnp-mmd") is None
    assert diagram_importer.lone_tag_path(pf.CodeBlock("::tnp-mmd{a.mmd}"), "tnp-mmd") is None
    assert diagram_importer.lone_tag_path(_para(pf.Emph(pf.Str("::tnp-mmd{a.mmd}"))),
                                          "tnp-mmd") is None


def test_resolve_path_relative_to_document_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("TNP_DOCUMENT_DIR", str(tmp_path))
    assert diagram_importer.resolve_path("d/a.mmd") == os.path.join(str(tmp_path), "d", "a.mmd")
    absolute = os.path.join(str(tmp_path), "x.mmd")
    assert diagram_importer.resolve_path(absolute) == absolute


def test_classify(tmp_path):
    good = tmp_path / "a.mmd"
    good.write_text("graph LR\n")
    extensions = {".mmd", ".mermaid"}
    assert diagram_importer.classify(str(good), extensions) is None
    assert "not found" in diagram_importer.classify(str(tmp_path / "missing.mmd"), extensions)
    assert "extension" in diagram_importer.classify(str(tmp_path / "a.txt"), extensions)


def test_error_marker_is_visible():
    marker = diagram_importer.error_marker("tnp-mmd", "a.mmd", "file not found")
    assert isinstance(marker, pf.Para)
    assert "a.mmd" in pf.stringify(marker)
    assert marker.content[0].attributes["style"] == "color:red"
