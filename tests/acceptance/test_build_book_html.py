"""`build_book html` on the example book, with fake diagram tools."""

import shutil

import pytest

from conftest import embedded_svgs

pytestmark = pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")


@pytest.fixture
def book_html(tnw, examples_workspace):
    result = tnw("build_book", "html", "examples/book/book.yaml")
    assert result.returncode == 0, result.stdout + result.stderr
    return (examples_workspace / "build" / "example-book.html").read_text(encoding="utf-8")


def test_title_and_metadata_from_book_yaml(book_html):
    assert '<h1 class="title">Example Book</h1>' in book_html
    assert "<dt>DID</dt><dd>001</dd>" in book_html
    assert "<dt>Date</dt><dd>2026-10-31</dd>" in book_html
    assert '<ul class="tnw-tags" aria-label="Keywords">\n<li>tnw</li>\n<li>example</li>\n<li>book</li>\n<li>biblio</li>\n<li>plantuml</li>\n<li>mermaid</li>\n<li>mathjax</li>\n' \
        in book_html


def test_toc_lists_chapters_in_order(book_html):
    chapters = ["#introduction", "#figures-and-diagrams", "#mathematics",
                "#notes-and-links", "#conclusions", "#references"]
    positions = [book_html.index('href="%s"' % anchor) for anchor in chapters]
    assert positions == sorted(positions)


def test_diagrams_and_image_are_embedded(book_html):
    svgs = embedded_svgs(book_html)
    assert sum("fake plantuml" in svg for svg in svgs) == 2  # fenced block + imported file
    assert sum("fake mermaid" in svg for svg in svgs) == 2
    assert any(">tnw</text>" in svg for svg in svgs)       # images/tnw-logo.svg


def test_todo_tags(book_html):
    text = book_html.replace("\n", " ")
    assert '<span class="todo" style="color:black;background-color:yellow">like this one</span>' in text
    assert 'class="tnw-todo" style="color:black;background-color:yellow"' in book_html


def test_bibliography(book_html):
    for key in ("pandoc", "shannon1948", "mmdc", "knuth1984"):
        assert 'id="ref-%s"' % key in book_html
    # pandoc is cited three times: numbered return links.
    assert "↩︎3" in book_html or "↩3" in book_html


def test_missing_chapter_is_reported(tnw, examples_workspace):
    (examples_workspace / "examples" / "book" / "chapter3_math.md").unlink()
    result = tnw("build_book", "html", "examples/book/book.yaml")
    assert result.returncode == 1
    assert "chapter not found" in result.stderr
    assert not (examples_workspace / "build" / "example-book.html").exists()
