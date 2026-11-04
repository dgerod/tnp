class TnpError(Exception):
    """Base class for the errors tnp reports to the user."""


class WorkspaceNotFoundError(TnpError):
    """No `.tnp` directory in the current directory or any parent."""


class ConfigurationError(TnpError):
    """`.tnp/settings.yaml` is missing or malformed."""
