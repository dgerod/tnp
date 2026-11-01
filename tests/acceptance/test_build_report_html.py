"""`build_report html` on the example report, with fake diagram tools."""

import shutil

import pytest

from conftest import embedded_svgs

pytestmark = pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")


@pytest.fixture
def report_html(tnw, examples_workspace):
    result = tnw("build_report", "html", "examples/report/example-report.md")
    assert result.returncode == 0, result.stdout + result.stderr
    return (examples_workspace / "build" / "example-report.html").read_text(encoding="utf-8")


def test_title_metadata_and_toc(report_html):
    assert '<h1 class="title">Example report</h1>' in report_html
    assert '<p class="author">Myself / The Universe</p>' in report_html
    assert "<dt>DID</dt><dd>002</dd>" in report_html
    assert '<ul class="tnw-tags" aria-label="Keywords">\n<li>tnw</li>\n<li>example</li>\n<li>report</li>\n' in report_html
    assert 'href="#abstract"' in report_html


def test_metadata_values_are_kept_as_written(tnw, fake_workspace):
    (fake_workspace / "note.md").write_text(
        "---\ndid: 007\nversion: 1.10\ntags: [2024, x]\n---\n# Note\n")
    result = tnw("build_report", "html", "note.md")
    assert result.returncode == 0, result.stderr
    html = (fake_workspace / "build" / "note.html").read_text()
    assert "<dt>DID</dt><dd>007</dd>" in html
    assert "<dt>Version</dt><dd>1.10</dd>" in html
    assert '<ul class="tnw-tags" aria-label="Keywords">\n<li>2024</li>\n<li>x</li>\n' in html


def test_todo_tags(report_html):
    assert '<span class="todo" style="color:black;background-color:yellow">check the figures</span>' \
        in report_html.replace("\n", " ")
    assert 'class="tnw-todo" style="color:black;background-color:yellow"' in report_html


def test_diagrams_and_image_are_embedded(report_html):
    svgs = embedded_svgs(report_html)
    assert sum("fake plantuml" in svg for svg in svgs) == 2  # fenced block + imported file
    assert sum("fake mermaid" in svg for svg in svgs) == 2
    assert any(">tnw</text>" in svg for svg in svgs)       # images/tnw-logo.svg


def test_citations_and_math(report_html):
    assert 'href="#ref-shannon1948"' in report_html
    assert 'class="citation-backref"' in report_html
    assert "Shannon" in report_html
    assert "enableMenu: false" in report_html  # MathJax embedded


def test_output_goes_to_workspace_build_from_any_directory(tnw, examples_workspace):
    result = tnw("build_report", "html", "example-report.md",
                 cwd=examples_workspace / "examples" / "report")
    assert result.returncode == 0, result.stderr
    assert (examples_workspace / "build" / "example-report.html").is_file()
    assert not (examples_workspace / "examples" / "report" / "build").exists()


def test_report_without_bibliography(tnw, examples_workspace):
    result = tnw("build_report", "html",
                 "examples/report_no_biblio/example-report-no-biblio.md")
    assert result.returncode == 0, result.stderr
    html = (examples_workspace / "build" / "example-report-no-biblio.html").read_text()
    assert 'id="refs"' not in html and 'class="citation"' not in html
    assert '<h1 class="title">Example report without bibliography</h1>' in html
    svgs = embedded_svgs(html)
    assert sum("fake plantuml" in svg for svg in svgs) == 2
    assert sum("fake mermaid" in svg for svg in svgs) == 2
    assert any(">tnw</text>" in svg for svg in svgs)


def test_biblio_option_overrides_front_matter(tnw, examples_workspace):
    report = examples_workspace / "examples" / "report"
    (report / "other.bib").write_text(
        "@misc{shannon1948, title={Overridden entry}, author={Someone, Else}, year={2000}}\n"
        "@misc{pandoc, title={P}, year={2000}}\n@misc{mmdc, title={M}, year={2000}}\n"
        "@misc{knuth1984, title={K}, year={2000}}\n")
    result = tnw("build_report", "html", "examples/report/example-report.md",
                 "-b", "examples/report/other.bib")
    assert result.returncode == 0, result.stderr
    assert "Overridden entry" in (examples_workspace / "build" / "example-report.html").read_text()


def test_pdf_is_rejected(tnw, examples_workspace):
    result = tnw("build_report", "pdf", "examples/report/example-report.md")
    assert result.returncode == 2
    assert "only builds html" in result.stderr


def test_wrong_extension_is_rejected(tnw, examples_workspace):
    result = tnw("build_report", "html", "examples/report/refs.bib")
    assert result.returncode == 2
    assert ".md" in result.stderr


def test_outside_a_workspace(tnw, workdir):
    (workdir / "note.md").write_text("# Note\n")
    result = tnw("build_report", "html", "note.md")
    assert result.returncode == 1
    assert "no tnw workspace found" in result.stderr
