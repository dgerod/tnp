from pathlib import Path


TNP_DIRECTORY = ".tnp"
SETTINGS_FILE = "settings.yaml"
VSCODE_DIRECTORY = ".vscode"
VSCODE_SETTINGS_FILE = "settings.json"
BUILD_DIRECTORY = "build"


def find_workspace_root(start=None):
    """Return the nearest directory (start or an ancestor) holding `.tnp`, else None."""
    current = Path(start or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        if (directory / TNP_DIRECTORY).is_dir():
            return directory
    return None


def settings_path(root):
    return Path(root) / TNP_DIRECTORY / SETTINGS_FILE


def vscode_settings_path(root):
    return Path(root) / VSCODE_DIRECTORY / VSCODE_SETTINGS_FILE
