"""plantuml and mermaid filters, with the external tool replaced by a fake."""

import os
from types import SimpleNamespace

import panflute as pf
import pytest

import mermaid
import plantuml
import utils

IMAGE = b"<svg/>"


class FakeTool:
    """Stands in for subprocess.run inside utils.run_renderer."""

    def __init__(self, returncode=0, image=IMAGE):
        self.returncode = returncode
        self.image = image
        self.calls = []

    def __call__(self, argv, input=None, capture_output=True):
        self.calls.append(SimpleNamespace(argv=argv, input=input))
        if "-o" in argv:  # mermaid writes the file named by -o
            if self.image is not None and self.returncode == 0:
                with open(argv[argv.index("-o") + 1], "wb") as target:
                    target.write(self.image)
            return SimpleNamespace(returncode=self.returncode, stdout=b"", stderr=b"boom")
        return SimpleNamespace(returncode=self.returncode, stdout=self.image or b"",
                               stderr=b"boom")


@pytest.fixture
def tool(monkeypatch):
    def install(**kwargs):
        fake = FakeTool(**kwargs)
        monkeypatch.setattr(utils.subprocess, "run", fake)
        return fake
    return install


def _doc(tmp_path, output_format="html"):
    doc = pf.Doc(format=output_format)
    doc.tnp_command = "fake-tool"
    doc.tnp_build_dir = str(tmp_path / "build")
    return doc


def _image_url(result):
    assert isinstance(result, pf.Para)
    assert isinstance(result.content[0], pf.Image)
    return result.content[0].url


ENGINES = [
    pytest.param(plantuml, "plantuml", "tnp-puml", "a.puml", id="plantuml"),
    pytest.param(mermaid, "mermaid", "tnp-mmd", "a.mmd", id="mermaid"),
]


@pytest.mark.parametrize("module, cls, tag, file_name", ENGINES)
def test_code_block_becomes_cached_image(module, cls, tag, file_name, tmp_path, tool):
    fake = tool()
    doc = _doc(tmp_path)
    url = _image_url(module.action(pf.CodeBlock("A -> B", classes=[cls]), doc))
    assert url.endswith(".svg") and os.path.getsize(url) == len(IMAGE)
    # Same source again: served from the cache, the tool is not run.
    assert _image_url(module.action(pf.CodeBlock("A -> B", classes=[cls]), doc)) == url
    assert len(fake.calls) == 1


@pytest.mark.parametrize("module, cls, tag, file_name", ENGINES)
def test_non_html_output_uses_png(module, cls, tag, file_name, tmp_path, tool):
    tool()
    url = _image_url(module.action(pf.CodeBlock("x", classes=[cls]), _doc(tmp_path, "docx")))
    assert url.endswith(".png")


@pytest.mark.parametrize("module, cls, tag, file_name", ENGINES)
def test_other_blocks_are_untouched(module, cls, tag, file_name, tmp_path, tool):
    fake = tool()
    assert module.action(pf.CodeBlock("x", classes=["python"]), _doc(tmp_path)) is None
    assert module.action(pf.Para(pf.Str("text")), _doc(tmp_path)) is None
    assert fake.calls == []


@pytest.mark.parametrize("module, cls, tag, file_name", ENGINES)
@pytest.mark.parametrize("returncode, image", [(1, IMAGE), (0, b""), (0, None)])
def test_code_block_failure_aborts(module, cls, tag, file_name, returncode, image,
                                   tmp_path, tool):
    tool(returncode=returncode, image=image)
    with pytest.raises(utils.RenderError):
        module.action(pf.CodeBlock("x", classes=[cls]), _doc(tmp_path))


@pytest.mark.parametrize("module, cls, tag, file_name", ENGINES)
def test_import_tag_renders_file(module, cls, tag, file_name, tmp_path, tool, monkeypatch):
    fake = tool()
    monkeypatch.setenv("TNP_DOCUMENT_DIR", str(tmp_path))
    (tmp_path / file_name).write_text("A -> B\n")
    para = pf.Para(pf.Str("::%s{%s}" % (tag, file_name)))
    url = _image_url(module.action(para, _doc(tmp_path)))
    assert os.path.isfile(url)
    # Editing the imported file produces a new image.
    (tmp_path / file_name).write_text("A -> C\n")
    assert _image_url(module.action(para, _doc(tmp_path))) != url
    assert len(fake.calls) == 2


@pytest.mark.parametrize("module, cls, tag, file_name", ENGINES)
@pytest.mark.parametrize("problem", ["missing", "extension", "tool"])
def test_import_tag_failure_is_a_marker(module, cls, tag, file_name, problem,
                                        tmp_path, tool, monkeypatch):
    tool(returncode=1 if problem == "tool" else 0)
    monkeypatch.setenv("TNP_DOCUMENT_DIR", str(tmp_path))
    if problem == "extension":
        file_name = "a.txt"
    if problem != "missing":
        (tmp_path / file_name).write_text("A -> B\n")
    result = module.action(pf.Para(pf.Str("::%s{%s}" % (tag, file_name))), _doc(tmp_path))
    assert result.content[0].classes == ["tnp-error"]


def test_plantuml_wraps_source(tmp_path, tool):
    fake = tool()
    plantuml.action(pf.CodeBlock("A -> B", classes=["plantuml"]), _doc(tmp_path))
    assert fake.calls[0].input.decode() == "@startuml\nA -> B\n@enduml\n"
    assert "-tsvg" in fake.calls[0].argv


def test_plantuml_keeps_explicit_startuml(tmp_path, tool):
    fake = tool()
    source = "@startuml\nA -> B\n@enduml"
    plantuml.action(pf.CodeBlock(source, classes=["plantuml"]), _doc(tmp_path))
    assert fake.calls[0].input.decode() == source


def test_mermaid_passes_source_verbatim_and_cleans_up(tmp_path, monkeypatch):
    seen = {}

    def fake_run(argv, input=None, capture_output=True):
        source = argv[argv.index("-i") + 1]
        with open(source) as f:
            seen["source"] = f.read()
        with open(argv[argv.index("-o") + 1], "wb") as target:
            target.write(IMAGE)
        return SimpleNamespace(returncode=0, stdout=b"", stderr=b"")

    monkeypatch.setattr(utils.subprocess, "run", fake_run)
    mermaid.action(pf.CodeBlock("graph LR\n  A --> B", classes=["mermaid"]), _doc(tmp_path))
    assert seen["source"] == "graph LR\n  A --> B"
    assert not [name for name in os.listdir(tmp_path / "build") if name.endswith(".mmd")]
