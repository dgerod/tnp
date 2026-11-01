"""The pandoc filters run by the real pandoc, as the builds will run them."""

import os
import shutil
import subprocess
import sys

import pytest

from tnw_cli.common.pandoc_filters import filter_path
from tnw_cli.common.pandoc_runner import filter_environment

pytestmark = pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")

FAKE_MMDC = """\
import sys
sys.argv.index("-i")
with open(sys.argv[sys.argv.index("-o") + 1], "w") as target:
    target.write('<svg xmlns="http://www.w3.org/2000/svg"><text>fake</text></svg>')
"""


def _pandoc(workdir, *args, extra_env=None):
    result = subprocess.run(["pandoc", "-t", "html", "--wrap=none", *args], cwd=workdir,
                            env=filter_environment(extra_env), capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_todo_tag_and_backrefs(workdir):
    (workdir / "refs.bib").write_text("@misc{pandoc, title={Pandoc}, author={MacFarlane, John}, year={2024}}\n")
    (workdir / "doc.md").write_text(
        "Text ::tnw-todo{a note} here [@pandoc] and [@pandoc].\n\n"
        "::: tnw-todo\nblock\n:::\n")
    html = _pandoc(workdir, "doc.md", "--citeproc", "--bibliography", "refs.bib",
                   "-M", "link-citations=true",
                   "--filter", filter_path("todo_tag"),
                   "--filter", filter_path("citation_backrefs"))
    assert '<span class="todo" style="color:black;background-color:yellow">a note</span>' in html
    assert 'class="tnw-todo" style="color:black;background-color:yellow"' in html
    assert 'href="#cite-1"' in html and 'href="#cite-2"' in html


@pytest.mark.skipif(os.name == "nt", reason="the fake tool relies on a shebang")
def test_mermaid_filter_reads_workspace_configuration(workdir):
    fake = workdir / "fake-mmdc"
    fake.write_text("#!%s\n%s" % (sys.executable, FAKE_MMDC))
    fake.chmod(0o755)
    (workdir / ".tnw").mkdir()
    (workdir / ".tnw" / "settings.yaml").write_text(
        'mermaid_bin: "%s"\ntnw_version: "0.1.0"\n' % fake.as_posix())
    (workdir / "diagrams").mkdir()
    (workdir / "diagrams" / "flow.mmd").write_text("graph LR\n  A --> B\n")
    (workdir / "doc.md").write_text(
        "```mermaid\ngraph LR\n  X --> Y\n```\n\n::tnw-mmd{diagrams/flow.mmd}\n\n::tnw-mmd{nope.mmd}\n")
    html = _pandoc(workdir, "doc.md", "--filter", filter_path("mermaid"),
                   extra_env={"TNW_WORKSPACE_DIR": str(workdir),
                              "TNW_DOCUMENT_DIR": str(workdir)})
    images = sorted((workdir / "build").glob("mermaid-*.svg"))
    assert len(images) == 2
    for image in images:
        assert str(image) in html
    assert "tnw-error" in html and "nope.mmd" in html
