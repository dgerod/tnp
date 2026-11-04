from tnp_cli.common.workspace import build_workspace, remove_workspace


def test_clean_root_creates_both_files(tmp_path):
    assert build_workspace(tmp_path, "tnp: 1\n", "{}\n") == []
    assert (tmp_path / ".tnp" / "settings.yaml").read_text(encoding="utf-8") == "tnp: 1\n"
    assert (tmp_path / ".vscode" / "settings.json").read_text(encoding="utf-8") == "{}\n"


def test_refuses_when_tnp_exists(tmp_path):
    (tmp_path / ".tnp").mkdir()
    conflicts = build_workspace(tmp_path, "tnp: 1\n", "{}\n")
    assert conflicts == [tmp_path / ".tnp"]
    assert not (tmp_path / ".vscode").exists()


def test_refuses_without_touching_existing_vscode_settings(tmp_path):
    (tmp_path / ".vscode").mkdir()
    (tmp_path / ".vscode" / "settings.json").write_text("mine", encoding="utf-8")
    conflicts = build_workspace(tmp_path, "tnp: 1\n", "{}\n")
    assert tmp_path / ".vscode" / "settings.json" in conflicts
    assert not (tmp_path / ".tnp").exists()
    assert (tmp_path / ".vscode" / "settings.json").read_text(encoding="utf-8") == "mine"


def test_remove_workspace(tmp_path):
    build_workspace(tmp_path, "tnp: 1\n", "{}\n")
    (tmp_path / "notes.md").write_text("keep", encoding="utf-8")
    remove_workspace(tmp_path)
    assert not (tmp_path / ".tnp").exists()
    assert not (tmp_path / ".vscode").exists()
    assert (tmp_path / "notes.md").exists()
