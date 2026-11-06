"""The HTML templates rendered by the real pandoc."""

import os
import shutil
import subprocess

import pytest

from tnp_cli.common.resource_locator import resource_path

pytestmark = pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")


def _render(workdir, template, *metadata):
    (workdir / "doc.md").write_text("# Chapter\n\nText with $x^2$.\n\n## Section\n\nMore.\n", encoding="utf-8")
    command = ["pandoc", "doc.md", "--toc", "--standalone", "--embed-resources", "--mathjax",
               "--resource-path", os.pathsep.join([resource_path("pandoc-templates", "assets"),
                                                   str(workdir)]),
               "--template", resource_path("pandoc-templates", template),
               "-M", "title=The Title", "-M", "tnp_version=9.9.9", "-o", "out.html"]
    for item in metadata:
        command += ["-M", item]
    result = subprocess.run(command, cwd=workdir, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
    return (workdir / "out.html").read_text(encoding="utf-8")


@pytest.mark.parametrize("template, body_class", [("tnp_report.html", "tnp-report"),
                                                  ("tnp_book.html", "tnp-book")])
def test_template_structure(workdir, template, body_class):
    html = _render(workdir, template)
    assert 'class="tnp %s"' % body_class in html
    assert '<h1 class="title">The Title</h1>' in html
    assert 'class="tnp-toc"' in html and 'href="#section"' in html
    assert 'Generated with <a href="https://github.com/dgerod/tnp">tnp</a> 9.9.9' in html
    # Assets, MathJax included, are embedded: the page needs no network.
    assert "tnp-toc-toggle" in html and "setupCitationPopups" in html
    assert "tnp-toc-all" in html and "setupTargetFlash" in html
    assert "setupImageViewer" in html and ".tnp-viewer-stage" in html
    assert "anot-host" in html
    assert 'src="tnp-base.js"' not in html and 'src="annotator.js"' not in html
    assert 'src="mathjax/' not in html
    assert "enableMenu: false" in html
    assert len(html) > 2_000_000


def test_image_height_is_limited_on_screen_only(workdir):
    html = _render(workdir, "tnp_report.html")
    assert "#tnp-content img { max-width: 100%; max-height: 30vh;" in html
    assert "object-fit: contain" in html
    assert ".tnp-image { text-align: center; }" in html
    print_rules = html[html.index("@media print"):]
    assert "#tnp-content img { max-height: none; }" in print_rules


def test_mathjax_only_embedded_when_document_has_math(workdir):
    (workdir / "plain.md").write_text("# Chapter\n\nNo formulas here.\n", encoding="utf-8")
    result = subprocess.run(
        ["pandoc", "plain.md", "--standalone", "--embed-resources", "--mathjax",
         "--resource-path", resource_path("pandoc-templates", "assets"),
         "--template", resource_path("pandoc-templates", "tnp_report.html"),
         "-M", "title=T", "-o", "out.html"],
        cwd=workdir, capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
    assert len((workdir / "out.html").read_text(encoding="utf-8")) < 200_000


def test_metadata_box_hidden_without_metadata(workdir):
    assert 'class="tnp-meta"' not in _render(workdir, "tnp_report.html")


def test_metadata_box_shows_present_fields(workdir):
    html = _render(workdir, "tnp_report.html", "has_meta=1", "did=DOC-1",
                   "tags=a", "tags=b", "author=Me")
    assert 'class="tnp-meta"' in html
    assert "<dt>DID</dt><dd>DOC-1</dd>" in html
    assert '<p class="tnp-keywords"><span>Keywords:</span> a, b</p>' in html
    assert "<dt>Version</dt>" not in html
    assert '<p class="author">Me</p>' in html


def test_document_identity_passed_to_annotator(workdir):
    # The annotator copies these into its exported .json.
    html = _render(workdir, "tnp_report.html", "did=DOC-1", "version=A2", "date=2026-11-03")
    assert '<script data-did="DOC-1" data-version="A2" data-date="2026-11-03" data-tnp="9.9.9">' in html
    assert '<script data-did data-version data-date data-tnp="9.9.9">' in _render(workdir, "tnp_book.html")
