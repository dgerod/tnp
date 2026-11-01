import json
import os

import yaml

from tnw_cli import __version__
from tnw_cli.common.resource_locator import mpe_directory


def _settings(root):
    return yaml.safe_load((root / ".tnw" / "settings.yaml").read_text())


def test_check_without_workspace_fails(tnw):
    result = tnw("check")
    assert result.returncode == 1
    assert "[FAIL] Workspace" in result.stdout


def test_show_without_workspace_fails(tnw):
    result = tnw("show")
    assert result.returncode == 1
    assert "no tnw workspace found" in result.stderr


def test_init_creates_workspace(tnw, workdir):
    result = tnw("init", "--plantuml", "/opt/plantuml.jar", "--mermaid", "mmdc")
    assert result.returncode == 0, result.stdout + result.stderr
    assert _settings(workdir) == {"plantuml_bin": "java -jar /opt/plantuml.jar",
                                  "mermaid_bin": "mmdc", "tnw_version": __version__}
    vscode = json.loads((workdir / ".vscode" / "settings.json").read_text())
    assert vscode["markdown-preview-enhanced.configPath"] == mpe_directory()
    assert vscode["markdown-preview-enhanced.plantumlJarPath"] == os.path.abspath("/opt/plantuml.jar")
    assert vscode["markdown-preview-enhanced.plantumlServer"] == ""


def test_check_after_init_is_healthy(tnw, workdir):
    tnw("init")
    result = tnw("check")
    assert "[OK ] tnw version" in result.stdout
    assert "[OK ] MPE configPath" in result.stdout
    # pandoc may be missing on the test machine; only that check may fail.
    failures = [line for line in result.stdout.splitlines() if line.startswith("[FAIL]")]
    assert all("pandoc_bin" in line for line in failures)


def test_show_from_subdirectory(tnw, workdir):
    tnw("init")
    nested = workdir / "notes" / "deep"
    nested.mkdir(parents=True)
    result = tnw("show", cwd=nested)
    assert result.returncode == 0
    assert "compatible" in result.stdout
    assert str(workdir / "build") in result.stdout


def test_reinit_declined_changes_nothing(tnw, workdir):
    tnw("init", "--mermaid", "first")
    result = tnw("init", "--mermaid", "second", input="n\n")
    assert result.returncode == 1
    assert _settings(workdir)["mermaid_bin"] == "first"


def test_reinit_force_from_subdirectory_overwrites_root(tnw, workdir):
    tnw("init", "--mermaid", "first")
    nested = workdir / "notes"
    nested.mkdir()
    result = tnw("init", "-f", "--mermaid", "second", cwd=nested)
    assert result.returncode == 0
    assert _settings(workdir)["mermaid_bin"] == "second"
    assert not (nested / ".tnw").exists()


def test_init_refuses_stray_vscode_settings(tnw, workdir):
    (workdir / ".vscode").mkdir()
    (workdir / ".vscode" / "settings.json").write_text("{}")
    result = tnw("init")
    assert result.returncode == 1
    assert not (workdir / ".tnw").exists()

