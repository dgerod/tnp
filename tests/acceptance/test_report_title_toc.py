"""The report title rule: exactly one `#` heading, no `title` in the front-matter."""

import shutil

import pytest

pytestmark = pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")


def _build(tnp, workspace, text):
    (workspace / "note.md").write_text(text)
    return tnp("build_report", "html", "note.md")


def test_single_h1_becomes_title_and_sections_the_toc(tnp, fake_workspace):
    result = _build(tnp, fake_workspace, "# My Title\n\n## First\n\ntext\n\n## Second\n")
    assert result.returncode == 0, result.stderr
    html = (fake_workspace / "build" / "note.html").read_text()
    assert '<h1 class="title">My Title</h1>' in html
    assert 'href="#first"' in html and 'href="#second"' in html
    assert 'href="#my-title"' not in html
    assert '<h1 id="first">' in html.replace("\n", " ") or 'id="first"' in html


@pytest.mark.parametrize("text, message", [
    ("---\ntitle: Nope\n---\n# Title\n", "remove 'title'"),
    ("## No title\n", "found 0"),
    ("# One\n\n# Two\n", "found 2"),
])
def test_invalid_titles_are_rejected(tnp, fake_workspace, text, message):
    result = _build(tnp, fake_workspace, text)
    assert result.returncode == 1
    assert message in result.stderr
    assert not (fake_workspace / "build" / "note.html").exists()
