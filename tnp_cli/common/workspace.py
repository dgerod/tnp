import json
import os
import re
import shutil
from collections import namedtuple
from enum import Enum
from pathlib import Path
from string import Template

from tnp_cli import __version__
from tnp_cli.common.configuration import (DEFAULT_MERMAID_BIN, DEFAULT_PANDOC_BIN,
                                          DEFAULT_PLANTUML_BIN, load_settings)
from tnp_cli.common.pandoc_runner import split_command
from tnp_cli.common.resource_locator import mpe_directory, resource_path
from tnp_cli.common.types import ConfigurationError
from tnp_cli.common.version_compare import Compatibility, compare
from tnp_cli.common.workspace_locator import (TNP_DIRECTORY, VSCODE_DIRECTORY,
                                              find_workspace_root, settings_path,
                                              vscode_settings_path)


MPE_CONFIG_KEY = "markdown-preview-enhanced.configPath"
MPE_PLANTUML_JAR_KEY = "markdown-preview-enhanced.plantumlJarPath"


class Status(Enum):
    OK = "ok"
    WARNING = "warning"
    FAIL = "fail"


CheckResult = namedtuple("CheckResult", ["name", "status", "detail"])


def is_failure(results):
    """A workspace is healthy when no check FAILs (a WARNING does not fail it)."""
    return any(result.status is Status.FAIL for result in results)


# --- rendering -------------------------------------------------------------

def _yaml_line(key, value):
    # A JSON string is a valid double-quoted YAML scalar, backslashes included.
    if value:
        return "%s: %s" % (key, json.dumps(value))
    return "# %s: (on PATH)" % key


def render_tnp_settings(pandoc_bin=None, plantuml_bin=None, mermaid_bin=None,
                        tnp_version=__version__):
    template = Template(Path(resource_path("templates", "tnp-settings.yaml.template"))
                        .read_text(encoding="utf-8"))
    return template.substitute(pandoc_line=_yaml_line("pandoc_bin", pandoc_bin),
                               plantuml_line=_yaml_line("plantuml_bin", plantuml_bin),
                               mermaid_line=_yaml_line("mermaid_bin", mermaid_bin),
                               tnp_version=tnp_version)


def _optional_mpe_settings(plantuml_jar):
    # Without a jar MPE keeps its own defaults; with one, an empty server
    # makes it render locally with that jar (java must be on PATH).
    if not plantuml_jar:
        return ""
    return ('  "%s": %s,\n  "markdown-preview-enhanced.plantumlServer": "",'
            % (MPE_PLANTUML_JAR_KEY, json.dumps(plantuml_jar)))


def render_vscode_settings(mpe_path=None, plantuml_jar=None):
    template = Template(Path(resource_path("templates", "vsc-settings.json.template"))
                        .read_text(encoding="utf-8"))
    # Escape for a JSON string literal (the template already has the quotes).
    escaped = json.dumps(mpe_path or mpe_directory())[1:-1]
    return template.safe_substitute(PathToMpe=escaped,
                                    OptionalMpeSettings=_optional_mpe_settings(plantuml_jar))


# --- creation --------------------------------------------------------------

def workspace_targets(root):
    root = Path(root)
    return [root / TNP_DIRECTORY, settings_path(root),
            root / VSCODE_DIRECTORY, vscode_settings_path(root)]


def build_workspace(root, tnp_settings_text, vscode_settings_text):
    """Create `.tnp/settings.yaml` and `.vscode/settings.json` under `root`.

    Atomic: if any target already exists nothing is created and the list of
    conflicting paths is returned. Returns an empty list on success.
    """
    conflicts = [path for path in workspace_targets(root) if path.exists()]
    if conflicts:
        return conflicts
    settings_file = settings_path(root)
    vscode_file = vscode_settings_path(root)
    settings_file.parent.mkdir(parents=True)
    vscode_file.parent.mkdir(parents=True)
    settings_file.write_text(tnp_settings_text, encoding="utf-8")
    vscode_file.write_text(vscode_settings_text, encoding="utf-8")
    return []


def remove_workspace(root):
    """Delete the `.tnp` and `.vscode` directories of a workspace."""
    for name in (TNP_DIRECTORY, VSCODE_DIRECTORY):
        directory = Path(root) / name
        if directory.is_dir():
            shutil.rmtree(directory)
        elif directory.exists():
            directory.unlink()


# --- diagnosis -------------------------------------------------------------

_COMPATIBILITY_STATUS = {
    Compatibility.OK: Status.OK,
    Compatibility.WARNING: Status.WARNING,
    Compatibility.FAIL: Status.FAIL,
}


def _same_path(a, b):
    return os.path.normcase(os.path.normpath(str(a))) == os.path.normcase(os.path.normpath(str(b)))


def _check_tool(key, command, required):
    """The executable must be reachable; for `java -jar X`, X must exist too."""
    missing_status = Status.FAIL if required else Status.WARNING
    parts = split_command(command)
    if not parts or shutil.which(parts[0]) is None:
        return CheckResult(key, missing_status, "'%s': executable not found" % command)
    if "-jar" in parts:
        index = parts.index("-jar") + 1
        if index >= len(parts) or not Path(parts[index]).is_file():
            return CheckResult(key, missing_status, "'%s': jar file not found" % command)
    return CheckResult(key, Status.OK, command)


def _diagnose_tnp(root):
    results = [CheckResult("tnp directory", Status.OK, str(root / TNP_DIRECTORY))]
    try:
        settings = load_settings(root)
    except ConfigurationError as error:
        results.append(CheckResult("tnp settings", Status.FAIL, str(error)))
        return results
    results.append(CheckResult("tnp settings", Status.OK, str(settings_path(root))))

    created = settings["tnp_version"]
    verdict = compare(created, __version__)
    results.append(CheckResult("tnp version", _COMPATIBILITY_STATUS[verdict],
                               "workspace %s, installed %s" % (created, __version__)))

    results.append(_check_tool("pandoc_bin", settings.get("pandoc_bin") or DEFAULT_PANDOC_BIN,
                               required=True))
    results.append(_check_tool("plantuml_bin", settings.get("plantuml_bin") or DEFAULT_PLANTUML_BIN,
                               required=False))
    results.append(_check_tool("mermaid_bin", settings.get("mermaid_bin") or DEFAULT_MERMAID_BIN,
                               required=False))
    return results


_JSON_STRING = r'"(?:\\.|[^"\\])*"'
_JSONC_COMMENT = re.compile(r'%s|//[^\n]*|/\*.*?\*/' % _JSON_STRING, re.DOTALL)
_JSONC_TRAILING_COMMA = re.compile(r'%s|,(?=\s*[}\]])' % _JSON_STRING)


def _drop_outside_strings(pattern, text):
    return pattern.sub(lambda match: match.group(0) if match.group(0).startswith('"') else "", text)


def load_jsonc(text):
    """Parse a VS Code settings file: JSON with comments and trailing commas."""
    # Comments first, so that a comma followed by a comment is still trailing.
    text = _drop_outside_strings(_JSONC_COMMENT, text)
    return json.loads(_drop_outside_strings(_JSONC_TRAILING_COMMA, text))


def _read_jsonc(path):
    """(data, None) for a JSONC object file, or (None, error message)."""
    try:
        data = load_jsonc(path.read_text(encoding="utf-8"))
    except (ValueError, OSError) as error:
        return None, "cannot parse %s: %s" % (path, error)
    if not isinstance(data, dict):
        return None, "cannot parse %s: not a JSON object" % path
    return data, None


def find_code_workspace(root):
    """The `*.code-workspace` files, in `root` or its parent, that list `root` as a folder."""
    root = Path(root).resolve()
    found = []
    for directory in dict.fromkeys((root, root.parent)):
        for path in sorted(directory.glob("*.code-workspace")):
            data, _ = _read_jsonc(path)
            folders = data.get("folders") if data else None
            if not isinstance(folders, list):
                continue
            for folder in folders:
                folder_path = folder.get("path") if isinstance(folder, dict) else None
                if isinstance(folder_path, str) and \
                        _same_path((directory / folder_path).resolve(), root):
                    found.append((path, data))
                    break
    return found


def _check_config_path(config_path, expected_mpe, source):
    if not config_path:
        return CheckResult("MPE configPath", Status.WARNING,
                           "'%s' not set in %s; expected %s" % (MPE_CONFIG_KEY, source, expected_mpe))
    if not _same_path(config_path, expected_mpe):
        return CheckResult("MPE configPath", Status.WARNING,
                           "%s (in %s) does not match %s" % (config_path, source, expected_mpe))
    return CheckResult("MPE configPath", Status.OK, "%s (in %s)" % (config_path, source))


def _diagnose_vscode(root, expected_mpe):
    # VS Code is optional for building, so its problems are warnings.
    results = []
    folder_data = None
    directory = root / VSCODE_DIRECTORY
    path = vscode_settings_path(root)
    if not directory.is_dir():
        results.append(CheckResult("VS Code directory", Status.WARNING, "%s not found" % directory))
    else:
        results.append(CheckResult("VS Code directory", Status.OK, str(directory)))
        if not path.is_file():
            results.append(CheckResult("VS Code settings", Status.WARNING, "%s not found" % path))
        else:
            folder_data, error = _read_jsonc(path)
            results.append(CheckResult("VS Code settings", Status.WARNING, error) if error
                           else CheckResult("VS Code settings", Status.OK, str(path)))

    # In a multi-root workspace VS Code reads the MPE configPath (a window
    # setting) from the .code-workspace file and ignores the folder's value.
    code_workspaces = find_code_workspace(root)
    for workspace_path, data in code_workspaces:
        results.append(CheckResult("VS Code workspace", Status.OK, str(workspace_path)))
        settings = data.get("settings")
        config_path = settings.get(MPE_CONFIG_KEY) if isinstance(settings, dict) else None
        results.append(_check_config_path(config_path, expected_mpe, workspace_path))
    if not code_workspaces and folder_data is not None:
        results.append(_check_config_path(folder_data.get(MPE_CONFIG_KEY), expected_mpe, path))
    return results


def diagnose_workspace(start=None, expected_mpe=None):
    """Return one CheckResult per check of the workspace containing `start`."""
    root = find_workspace_root(start)
    if root is None:
        return [CheckResult("Workspace", Status.FAIL,
                            "no .tnp directory here or in any parent")]
    results = [CheckResult("Workspace", Status.OK, str(root))]
    results += _diagnose_tnp(root)
    results += _diagnose_vscode(root, expected_mpe or mpe_directory())
    return results
