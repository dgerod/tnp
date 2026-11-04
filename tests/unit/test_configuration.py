import pytest

from tnp_cli.common.configuration import Configuration
from tnp_cli.common.types import ConfigurationError, WorkspaceNotFoundError


def test_defaults_when_tool_keys_are_absent(make_workspace):
    root = make_workspace('tnp_version: "0.1.0"\n')
    configuration = Configuration(root)
    assert configuration.pandoc_bin() == "pandoc"
    assert configuration.plantuml_bin() == "java -jar plantuml.jar"
    assert configuration.mermaid_bin() == "mmdc"
    assert configuration.created_version() == "0.1.0"


def test_reads_tool_keys(make_workspace):
    root = make_workspace('pandoc_bin: "/opt/pandoc"\nplantuml_bin: "java -jar /x/p.jar"\n'
                          'mermaid_bin: "mmdc.cmd"\ntnp_version: "0.1.0"\n')
    configuration = Configuration(root)
    assert configuration.pandoc_bin() == "/opt/pandoc"
    assert configuration.plantuml_bin() == "java -jar /x/p.jar"
    assert configuration.mermaid_bin() == "mmdc.cmd"


def test_finds_workspace_from_subdirectory(make_workspace):
    root = make_workspace()
    nested = root / "notes" / "deep"
    nested.mkdir(parents=True)
    configuration = Configuration(nested)
    assert configuration.work_directory() == str(root.resolve())
    assert configuration.build_directory() == str(root.resolve() / "build")


def test_unquoted_version_is_read_as_string(make_workspace):
    assert Configuration(make_workspace("tnp_version: 0.1\n")).created_version() == "0.1"


def test_missing_version_is_an_error(make_workspace):
    with pytest.raises(ConfigurationError, match="tnp_version"):
        Configuration(make_workspace('pandoc_bin: "pandoc"\n'))


def test_malformed_settings_is_an_error(make_workspace):
    with pytest.raises(ConfigurationError):
        Configuration(make_workspace("tnp_version: [unclosed\n"))


def test_no_workspace(tmp_path):
    with pytest.raises(WorkspaceNotFoundError):
        Configuration(tmp_path)
