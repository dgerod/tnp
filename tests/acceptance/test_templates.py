"""The HTML templates rendered by the real pandoc."""

import os
import shutil
import subprocess

import pytest

from tnw_cli.common.resource_locator import resource_path

pytestmark = pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")


def _render(workdir, template, *metadata):
    (workdir / "doc.md").write_text("# Chapter\n\nText with $x^2$.\n\n## Section\n\nMore.\n")
    command = ["pandoc", "doc.md", "--toc", "--standalone", "--embed-resources", "--mathjax",
               "--resource-path", os.pathsep.join([resource_path("pandoc-templates", "assets"),
                                                   str(workdir)]),
               "--template", resource_path("pandoc-templates", template),
               "-M", "title=The Title", "-M", "tnw_version=9.9.9", "-o", "out.html"]
    for item in metadata:
        command += ["-M", item]
    result = subprocess.run(command, cwd=workdir, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return (workdir / "out.html").read_text(encoding="utf-8")


@pytest.mark.parametrize("template, body_class", [("tnw_report.html", "tnw-report"),
                                                  ("tnw_book.html", "tnw-book")])
def test_template_structure(workdir, template, body_class):
    html = _render(workdir, template)
    assert 'class="tnw %s"' % body_class in html
    assert '<h1 class="title">The Title</h1>' in html
    assert 'class="tnw-toc"' in html and 'href="#section"' in html
    assert "Generated with tnw 9.9.9" in html
    # Assets, MathJax included, are embedded: the page needs no network.
    assert "tnw-toc-toggle" in html and "setupCitationPopups" in html
    assert "tnw-toc-all" in html
    assert "setupImageViewer" in html and ".tnw-viewer-stage" in html
    assert 'src="tnw.js"' not in html
    assert 'src="mathjax/' not in html
    assert "enableMenu: false" in html
    assert len(html) > 2_000_000


def test_mathjax_only_embedded_when_document_has_math(workdir):
    (workdir / "plain.md").write_text("# Chapter\n\nNo formulas here.\n")
    result = subprocess.run(
        ["pandoc", "plain.md", "--standalone", "--embed-resources", "--mathjax",
         "--resource-path", resource_path("pandoc-templates", "assets"),
         "--template", resource_path("pandoc-templates", "tnw_report.html"),
         "-M", "title=T", "-o", "out.html"],
        cwd=workdir, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert len((workdir / "out.html").read_text(encoding="utf-8")) < 200_000


def test_metadata_box_hidden_without_metadata(workdir):
    assert 'class="tnw-meta"' not in _render(workdir, "tnw_report.html")


def test_metadata_box_shows_present_fields(workdir):
    html = _render(workdir, "tnw_report.html", "has_meta=1", "did=DOC-1",
                   "tags=a", "tags=b", "author=Me")
    assert 'class="tnw-meta"' in html
    assert "<dt>DID</dt><dd>DOC-1</dd>" in html
    assert '<ul class="tnw-tags" aria-label="Keywords">\n<li>a</li>\n<li>b</li>\n' in html
    assert "<dt>Version</dt>" not in html
    assert '<p class="author">Me</p>' in html
