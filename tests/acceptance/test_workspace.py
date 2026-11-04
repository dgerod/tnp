import json
import os

import yaml

from tnp_cli import __version__
from tnp_cli.common.resource_locator import mpe_directory


def _settings(root):
    return yaml.safe_load((root / ".tnp" / "settings.yaml").read_text())


def test_check_without_workspace_fails(tnp):
    result = tnp("check")
    assert result.returncode == 1
    assert "[FAIL] Workspace" in result.stdout


def test_show_without_workspace_fails(tnp):
    result = tnp("show")
    assert result.returncode == 1
    assert "no tnp workspace found" in result.stderr


def test_init_creates_workspace(tnp, workdir):
    result = tnp("init", "--plantuml", "/opt/plantuml.jar", "--mermaid", "mmdc")
    assert result.returncode == 0, result.stdout + result.stderr
    assert _settings(workdir) == {"plantuml_bin": "java -jar /opt/plantuml.jar",
                                  "mermaid_bin": "mmdc", "tnp_version": __version__}
    vscode = json.loads((workdir / ".vscode" / "settings.json").read_text())
    assert vscode["markdown-preview-enhanced.configPath"] == mpe_directory()
    assert vscode["markdown-preview-enhanced.plantumlJarPath"] == os.path.abspath("/opt/plantuml.jar")
    assert vscode["markdown-preview-enhanced.plantumlServer"] == ""


def test_check_after_init_is_healthy(tnp, workdir):
    tnp("init")
    result = tnp("check")
    assert "[OK ] tnp version" in result.stdout
    assert "[OK ] MPE configPath" in result.stdout
    # pandoc may be missing on the test machine; only that check may fail.
    failures = [line for line in result.stdout.splitlines() if line.startswith("[FAIL]")]
    assert all("pandoc_bin" in line for line in failures)


def test_show_from_subdirectory(tnp, workdir):
    tnp("init")
    nested = workdir / "notes" / "deep"
    nested.mkdir(parents=True)
    result = tnp("show", cwd=nested)
    assert result.returncode == 0
    assert "compatible" in result.stdout
    assert str(workdir / "build") in result.stdout


def test_reinit_declined_changes_nothing(tnp, workdir):
    tnp("init", "--mermaid", "first")
    result = tnp("init", "--mermaid", "second", input="n\n")
    assert result.returncode == 1
    assert _settings(workdir)["mermaid_bin"] == "first"


def test_reinit_force_from_subdirectory_overwrites_root(tnp, workdir):
    tnp("init", "--mermaid", "first")
    nested = workdir / "notes"
    nested.mkdir()
    result = tnp("init", "-f", "--mermaid", "second", cwd=nested)
    assert result.returncode == 0
    assert _settings(workdir)["mermaid_bin"] == "second"
    assert not (nested / ".tnp").exists()


def test_init_refuses_stray_vscode_settings(tnp, workdir):
    (workdir / ".vscode").mkdir()
    (workdir / ".vscode" / "settings.json").write_text("{}")
    result = tnp("init")
    assert result.returncode == 1
    assert not (workdir / ".tnp").exists()

