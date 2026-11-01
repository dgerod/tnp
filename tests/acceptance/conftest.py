import base64
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).resolve().parents[2]
TNW_CLI = REPOSITORY / "tnw-cli.py"
FAKE_TOOLS = Path(__file__).resolve().parent / "fake_tools"


def fake_tool_command(script):
    """A tool command running a fake tool with this interpreter (any platform)."""
    return '"%s" "%s"' % (Path(sys.executable).as_posix(), (FAKE_TOOLS / script).as_posix())


def embedded_svgs(html):
    """The decoded SVG images embedded as data URIs in a generated page."""
    return [base64.b64decode(data).decode("utf-8", "replace")
            for data in re.findall(r'src="data:image/svg\+xml;base64,([^"]+)"', html)]


@pytest.fixture
def fake_workspace(workdir):
    """A workspace in workdir whose PlantUML / Mermaid are the fake tools."""
    (workdir / ".tnw").mkdir()
    (workdir / ".tnw" / "settings.yaml").write_text(
        "plantuml_bin: %s\nmermaid_bin: %s\ntnw_version: \"0.1.0\"\n"
        % (json.dumps(fake_tool_command("fake_plantuml.py")),
           json.dumps(fake_tool_command("fake_mmdc.py"))), encoding="utf-8")
    return workdir


@pytest.fixture
def examples_workspace(fake_workspace):
    """The repository examples copied into a fake-tool workspace."""
    shutil.copytree(REPOSITORY / "examples", fake_workspace / "examples")
    return fake_workspace


@pytest.fixture
def workdir(tmp_path):
    """A throwaway directory to run the CLI in."""
    return tmp_path


@pytest.fixture
def tnw(workdir):
    """Run `python tnw-cli.py <args>` in workdir (or `cwd`) and return the CompletedProcess."""
    def run(*args, cwd=None, input=None):
        return subprocess.run([sys.executable, str(TNW_CLI), *args],
                              cwd=cwd or workdir, input=input,
                              capture_output=True, text=True)
    return run
