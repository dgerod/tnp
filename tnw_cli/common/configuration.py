import yaml

from tnw_cli.common.types import ConfigurationError, WorkspaceNotFoundError
from tnw_cli.common.workspace_locator import BUILD_DIRECTORY, find_workspace_root, settings_path


DEFAULT_PANDOC_BIN = "pandoc"
DEFAULT_PLANTUML_BIN = "java -jar plantuml.jar"
DEFAULT_MERMAID_BIN = "mmdc"

TOOL_KEYS = ("pandoc_bin", "plantuml_bin", "mermaid_bin")


def load_settings(root):
    """Read and validate `.tnw/settings.yaml` under `root`.

    The tool keys are optional (absent means "on PATH"); `tnw_version` is
    required. Raises ConfigurationError when the file is missing or malformed.
    """
    path = settings_path(root)
    if not path.is_file():
        raise ConfigurationError("settings file not found: %s" % path)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as error:
        raise ConfigurationError("cannot parse %s: %s" % (path, error)) from error
    if not isinstance(data, dict):
        raise ConfigurationError("%s is not a mapping of settings" % path)
    for key in TOOL_KEYS:
        if key in data and not isinstance(data[key], str):
            raise ConfigurationError("%s: '%s' must be a string" % (path, key))
    if not data.get("tnw_version"):
        raise ConfigurationError("%s: missing required 'tnw_version'" % path)
    # An unquoted version such as 0.1 is read by YAML as a float.
    data["tnw_version"] = str(data["tnw_version"])
    return data


class Configuration:

    def __init__(self, start=None):
        root = find_workspace_root(start)
        if root is None:
            raise WorkspaceNotFoundError(
                "no tnw workspace found (no .tnw directory here or in any parent); run 'tnw init'")
        self._root = root
        self._settings = load_settings(root)

    def work_directory(self):
        return str(self._root)

    def build_directory(self):
        return str(self._root / BUILD_DIRECTORY)

    def pandoc_bin(self):
        return self._settings.get("pandoc_bin") or DEFAULT_PANDOC_BIN

    def plantuml_bin(self):
        return self._settings.get("plantuml_bin") or DEFAULT_PLANTUML_BIN

    def mermaid_bin(self):
        return self._settings.get("mermaid_bin") or DEFAULT_MERMAID_BIN

    def created_version(self):
        return self._settings["tnw_version"]
