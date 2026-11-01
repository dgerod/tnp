import json

import yaml

from tnw_cli.common.workspace import render_tnw_settings, render_vscode_settings


def test_vscode_settings_is_valid_json_with_config_path():
    data = json.loads(render_vscode_settings("/opt/tnw/mpe"))
    assert data["markdown-preview-enhanced.configPath"] == "/opt/tnw/mpe"
    assert data["better-todo-tree.general.tags"] == ["::tnw-todo"]


def test_vscode_settings_escapes_windows_backslashes():
    data = json.loads(render_vscode_settings("C:\\tools\\tnw\\mpe"))
    assert data["markdown-preview-enhanced.configPath"] == "C:\\tools\\tnw\\mpe"


def test_vscode_settings_without_plantuml_jar_keeps_mpe_defaults():
    data = json.loads(render_vscode_settings("/opt/tnw/mpe"))
    assert "markdown-preview-enhanced.plantumlJarPath" not in data
    assert "markdown-preview-enhanced.plantumlServer" not in data


def test_vscode_settings_with_plantuml_jar_renders_locally():
    data = json.loads(render_vscode_settings("/opt/tnw/mpe", plantuml_jar="C:\\a b\\p.jar"))
    assert data["markdown-preview-enhanced.plantumlJarPath"] == "C:\\a b\\p.jar"
    assert data["markdown-preview-enhanced.plantumlServer"] == ""


def test_tnw_settings_omits_absent_tools():
    data = yaml.safe_load(render_tnw_settings(plantuml_bin='java -jar "C:\\a b\\p.jar"',
                                              tnw_version="0.1.1"))
    assert data == {"plantuml_bin": 'java -jar "C:\\a b\\p.jar"', "tnw_version": "0.1.1"}
