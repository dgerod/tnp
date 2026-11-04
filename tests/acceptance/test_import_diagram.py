"""Diagram error policy in a real build: imports degrade, fenced blocks abort."""

import shutil

import pytest

from conftest import embedded_svgs

pytestmark = pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")


def _build(tnp, workspace, body):
    (workspace / "notes").mkdir(exist_ok=True)
    (workspace / "notes" / "note.md").write_text("# Note\n\n" + body)
    return tnp("build_report", "html", "notes/note.md")


def test_import_resolves_relative_to_the_document(tnp, fake_workspace):
    (fake_workspace / "notes").mkdir()
    (fake_workspace / "notes" / "d.puml").write_text("A -> B\n")
    result = _build(tnp, fake_workspace, "::tnp-puml{d.puml}\n")
    assert result.returncode == 0, result.stderr
    html = (fake_workspace / "build" / "note.html").read_text()
    assert any("fake plantuml" in svg for svg in embedded_svgs(html))


@pytest.mark.parametrize("body, shown", [
    ("::tnp-mmd{missing.mmd}\n", "file not found"),
    ("::tnp-mmd{wrong.txt}\n", "invalid extension"),
])
def test_bad_import_shows_marker_and_build_continues(tnp, fake_workspace, body, shown):
    (fake_workspace / "notes").mkdir()
    (fake_workspace / "notes" / "wrong.txt").write_text("x")
    result = _build(tnp, fake_workspace, body + "\nafter the diagram\n")
    assert result.returncode == 0, result.stderr
    html = (fake_workspace / "build" / "note.html").read_text().replace("\n", " ")
    assert "tnp-error" in html and shown in html
    assert "after the diagram" in html


def test_failing_imported_diagram_shows_marker(tnp, fake_workspace):
    (fake_workspace / "notes").mkdir()
    (fake_workspace / "notes" / "bad.mmd").write_text("FAIL\n")
    result = _build(tnp, fake_workspace, "::tnp-mmd{bad.mmd}\n")
    assert result.returncode == 0, result.stderr
    assert "tnp-error" in (fake_workspace / "build" / "note.html").read_text()


def test_failing_fenced_block_aborts_the_build(tnp, fake_workspace):
    result = _build(tnp, fake_workspace, "```mermaid\nFAIL\n```\n")
    assert result.returncode == 1
    assert "pandoc failed" in result.stderr
    assert not (fake_workspace / "build" / "note.html").exists()
