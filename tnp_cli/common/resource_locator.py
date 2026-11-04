from pathlib import Path


_PACKAGE_DIRECTORY = Path(__file__).resolve().parent.parent


def resource_path(*parts):
    """Absolute path of a resource inside the tnp_cli package."""
    return str(_PACKAGE_DIRECTORY.joinpath(*parts))


def mpe_directory():
    """Absolute path of tnp's Markdown Preview Enhanced config directory.

    An installed package carries it as `tnp_cli/mpe`; a checkout keeps it at
    the repository root (`mpe/`). Forward slashes are used on every platform
    so the value can be written as-is into `.vscode/settings.json`.
    """
    installed = _PACKAGE_DIRECTORY / "mpe"
    if installed.is_dir():
        return installed.as_posix()
    return (_PACKAGE_DIRECTORY.parent / "mpe").as_posix()
