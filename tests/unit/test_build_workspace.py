from tnw_cli.common.workspace import build_workspace, remove_workspace


def test_clean_root_creates_both_files(tmp_path):
    assert build_workspace(tmp_path, "tnw: 1\n", "{}\n") == []
    assert (tmp_path / ".tnw" / "settings.yaml").read_text() == "tnw: 1\n"
    assert (tmp_path / ".vscode" / "settings.json").read_text() == "{}\n"


def test_refuses_when_tnw_exists(tmp_path):
    (tmp_path / ".tnw").mkdir()
    conflicts = build_workspace(tmp_path, "tnw: 1\n", "{}\n")
    assert conflicts == [tmp_path / ".tnw"]
    assert not (tmp_path / ".vscode").exists()


def test_refuses_without_touching_existing_vscode_settings(tmp_path):
    (tmp_path / ".vscode").mkdir()
    (tmp_path / ".vscode" / "settings.json").write_text("mine")
    conflicts = build_workspace(tmp_path, "tnw: 1\n", "{}\n")
    assert tmp_path / ".vscode" / "settings.json" in conflicts
    assert not (tmp_path / ".tnw").exists()
    assert (tmp_path / ".vscode" / "settings.json").read_text() == "mine"


def test_remove_workspace(tmp_path):
    build_workspace(tmp_path, "tnw: 1\n", "{}\n")
    (tmp_path / "notes.md").write_text("keep")
    remove_workspace(tmp_path)
    assert not (tmp_path / ".tnw").exists()
    assert not (tmp_path / ".vscode").exists()
    assert (tmp_path / "notes.md").exists()
