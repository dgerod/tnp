"""The pandoc filters run by the real pandoc, as the builds will run them."""

import os
import shutil
import subprocess
import sys

import pytest

from tnp_cli.common.pandoc_filters import filter_path
from tnp_cli.common.pandoc_runner import filter_environment

pytestmark = pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")

FAKE_MMDC = """\
import sys
sys.argv.index("-i")
with open(sys.argv[sys.argv.index("-o") + 1], "w") as target:
    target.write('<svg xmlns="http://www.w3.org/2000/svg"><text>fake</text></svg>')
"""


def _pandoc(workdir, *args, extra_env=None):
    result = subprocess.run(["pandoc", "-t", "html", "--wrap=none", *args], cwd=workdir,
                            env=filter_environment(extra_env), capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_todo_tag_and_backrefs(workdir):
    (workdir / "refs.bib").write_text("@misc{pandoc, title={Pandoc}, author={MacFarlane, John}, year={2024}}\n", encoding="utf-8")
    (workdir / "doc.md").write_text(
        "Text ::tnp-todo{a note} here [@pandoc] and [@pandoc].\n\n"
        "::: tnp-todo\nblock\n:::\n", encoding="utf-8")
    html = _pandoc(workdir, "doc.md", "--citeproc", "--bibliography", "refs.bib",
                   "-M", "link-citations=true",
                   "--filter", filter_path("todo_tag"),
                   "--filter", filter_path("citation_backrefs"))
    assert '<span class="todo" style="color:black;background-color:yellow">a note</span>' in html
    assert 'class="tnp-todo" style="color:black;background-color:yellow"' in html
    assert 'href="#cite-1"' in html and 'href="#cite-2"' in html


@pytest.mark.skipif(os.name == "nt", reason="the fake tool relies on a shebang")
def test_mermaid_filter_reads_workspace_configuration(workdir):
    fake = workdir / "fake-mmdc"
    fake.write_text("#!%s\n%s" % (sys.executable, FAKE_MMDC), encoding="utf-8")
    fake.chmod(0o755)
    (workdir / ".tnp").mkdir()
    (workdir / ".tnp" / "settings.yaml").write_text(
        'mermaid_bin: "%s"\ntnp_version: "0.1.0"\n' % fake.as_posix(), encoding="utf-8")
    (workdir / "diagrams").mkdir()
    (workdir / "diagrams" / "flow.mmd").write_text("graph LR\n  A --> B\n", encoding="utf-8")
    (workdir / "doc.md").write_text(
        "```mermaid\ngraph LR\n  X --> Y\n```\n\n::tnp-mmd{diagrams/flow.mmd}\n\n::tnp-mmd{nope.mmd}\n", encoding="utf-8")
    html = _pandoc(workdir, "doc.md", "--filter", filter_path("mermaid"),
                   extra_env={"TNP_WORKSPACE_DIR": str(workdir),
                              "TNP_DOCUMENT_DIR": str(workdir)})
    images = sorted((workdir / "build").glob("mermaid-*.svg"))
    assert len(images) == 2
    for image in images:
        assert str(image) in html
    assert "tnp-error" in html and "nope.mmd" in html
