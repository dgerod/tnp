from pathlib import Path


TNW_DIRECTORY = ".tnw"
SETTINGS_FILE = "settings.yaml"
VSCODE_DIRECTORY = ".vscode"
VSCODE_SETTINGS_FILE = "settings.json"
BUILD_DIRECTORY = "build"


def find_workspace_root(start=None):
    """Return the nearest directory (start or an ancestor) holding `.tnw`, else None."""
    current = Path(start or Path.cwd()).resolve()
    for directory in (current, *current.parents):
        if (directory / TNW_DIRECTORY).is_dir():
            return directory
    return None


def settings_path(root):
    return Path(root) / TNW_DIRECTORY / SETTINGS_FILE


def vscode_settings_path(root):
    return Path(root) / VSCODE_DIRECTORY / VSCODE_SETTINGS_FILE
