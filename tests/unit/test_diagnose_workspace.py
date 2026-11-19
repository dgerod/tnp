import json

from tnp_cli import __version__
from tnp_cli.common.workspace import Status, diagnose_workspace, is_failure

MPE = "/opt/tnp/mpe"


def _statuses(results):
    return {result.name: result.status for result in results}


def _write_vscode(root, config_path=MPE):
    (root / ".vscode").mkdir()
    (root / ".vscode" / "settings.json").write_text(
        json.dumps({"markdown-preview-enhanced.configPath": config_path}), encoding="utf-8")


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


def test_vscode_settings_with_comments_and_trailing_commas(make_workspace):
    root = make_workspace()
    (root / ".vscode").mkdir()
    (root / ".vscode" / "settings.json").write_text(
        '{\n  // a comment\n  /* a block\n     comment */\n'
        '  "markdown-preview-enhanced.configPath": "%s",\n'
        '  "url": "http://example.com/*not-a-comment*/",\n'
        '  "list": ["a,]", "b",  // trailing comma before a comment\n  ],\n}\n' % MPE, encoding="utf-8")
    statuses = _statuses(diagnose_workspace(root, expected_mpe=MPE))
    assert statuses["VS Code settings"] is Status.OK
    assert statuses["MPE configPath"] is Status.OK


def _write_code_workspace(directory, folders, config_path=MPE):
    settings = {"markdown-preview-enhanced.configPath": config_path} if config_path else {}
    (directory / "notes.code-workspace").write_text(
        '{\n\t// multi-root\n\t"folders": %s,\n\t"settings": %s,\n}\n'
        % (json.dumps([{"path": folder} for folder in folders]), json.dumps(settings)),
        encoding="utf-8")


def _nested_workspace(tmp_path):
    root = tmp_path / "notes"
    (root / ".tnp").mkdir(parents=True)
    (root / ".tnp" / "settings.yaml").write_text('tnp_version: "%s"\n' % __version__, encoding="utf-8")
    return root


def test_config_path_read_from_parent_code_workspace(tmp_path):
    root = _nested_workspace(tmp_path)
    _write_vscode(root, "/ignored/in/multi-root")
    _write_code_workspace(root.parent, ["other", root.name])
    results = diagnose_workspace(root, expected_mpe=MPE)
    statuses = _statuses(results)
    assert statuses["VS Code workspace"] is Status.OK
    assert statuses["MPE configPath"] is Status.OK
    assert "notes.code-workspace" in {r.name: r.detail for r in results}["MPE configPath"]


def test_config_path_missing_in_code_workspace_warns(make_workspace):
    root = make_workspace()
    _write_vscode(root)
    _write_code_workspace(root, ["."], config_path=None)
    statuses = _statuses(diagnose_workspace(root, expected_mpe=MPE))
    assert statuses["MPE configPath"] is Status.WARNING


def test_code_workspace_not_listing_the_folder_is_ignored(tmp_path):
    root = _nested_workspace(tmp_path)
    _write_vscode(root)
    _write_code_workspace(root.parent, ["other"], config_path="/somewhere/else")
    statuses = _statuses(diagnose_workspace(root, expected_mpe=MPE))
    assert "VS Code workspace" not in statuses
    assert statuses["MPE configPath"] is Status.OK


def test_invalid_vscode_settings_and_code_workspace_warn(tmp_path):
    root = _nested_workspace(tmp_path)
    (root / ".vscode").mkdir()
    (root / ".vscode" / "settings.json").write_text("[1, 2]", encoding="utf-8")
    (tmp_path / "broken.code-workspace").write_text("{ not json", encoding="utf-8")
    statuses = _statuses(diagnose_workspace(root, expected_mpe=MPE))
    assert statuses["VS Code settings"] is Status.WARNING
    assert "VS Code workspace" not in statuses
    (root / ".vscode" / "settings.json").write_text("{ not json", encoding="utf-8")
    assert _statuses(diagnose_workspace(root, expected_mpe=MPE))["VS Code settings"] is Status.WARNING
