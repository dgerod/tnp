import json

from tnp_cli.common.workspace import Status, diagnose_workspace, is_failure

MPE = "/opt/tnp/mpe"


def _statuses(results):
    return {result.name: result.status for result in results}


def _write_vscode(root, config_path=MPE):
    (root / ".vscode").mkdir()
    (root / ".vscode" / "settings.json").write_text(
        json.dumps({"markdown-preview-enhanced.configPath": config_path}))


def test_no_workspace(tmp_path):
    results = diagnose_workspace(tmp_path, expected_mpe=MPE)
    assert [(r.name, r.status) for r in results] == [("Workspace", Status.FAIL)]
    assert is_failure(results)


def test_fully_configured(make_workspace):
    root = make_workspace()
    _write_vscode(root)
    statuses = _statuses(diagnose_workspace(root, expected_mpe=MPE))
    for name in ("Workspace", "tnp directory", "tnp settings", "tnp version",
                 "VS Code directory", "VS Code settings", "MPE configPath"):
        assert statuses[name] is Status.OK, name


def test_missing_tnp_settings_fails(tmp_path):
    (tmp_path / ".tnp").mkdir()
    results = diagnose_workspace(tmp_path, expected_mpe=MPE)
    assert _statuses(results)["tnp settings"] is Status.FAIL
    assert is_failure(results)


def test_missing_vscode_settings_warns(make_workspace):
    root = make_workspace()
    (root / ".vscode").mkdir()
    statuses = _statuses(diagnose_workspace(root, expected_mpe=MPE))
    assert statuses["VS Code settings"] is Status.WARNING


def test_config_path_mismatch_warns(make_workspace):
    root = make_workspace()
    _write_vscode(root, "/somewhere/else")
    statuses = _statuses(diagnose_workspace(root, expected_mpe=MPE))
    assert statuses["MPE configPath"] is Status.WARNING


def test_minor_version_difference_warns(make_workspace):
    root = make_workspace('tnp_version: "0.0.1"\n')
    statuses = _statuses(diagnose_workspace(root, expected_mpe=MPE))
    assert statuses["tnp version"] is Status.WARNING


def test_newer_workspace_version_fails(make_workspace):
    root = make_workspace('tnp_version: "99.0.0"\n')
    results = diagnose_workspace(root, expected_mpe=MPE)
    assert _statuses(results)["tnp version"] is Status.FAIL
    assert is_failure(results)


def test_missing_optional_tool_only_warns(make_workspace):
    root = make_workspace('mermaid_bin: "no-such-mmdc-binary"\ntnp_version: "0.1.0"\n')
    statuses = _statuses(diagnose_workspace(root, expected_mpe=MPE))
    assert statuses["mermaid_bin"] is Status.WARNING


def test_missing_pandoc_fails(make_workspace):
    root = make_workspace('pandoc_bin: "no-such-pandoc-binary"\ntnp_version: "0.1.0"\n')
    statuses = _statuses(diagnose_workspace(root, expected_mpe=MPE))
    assert statuses["pandoc_bin"] is Status.FAIL
