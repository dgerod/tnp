class TnwError(Exception):
    """Base class for the errors tnw reports to the user."""


class WorkspaceNotFoundError(TnwError):
    """No `.tnw` directory in the current directory or any parent."""


class ConfigurationError(TnwError):
    """`.tnw/settings.yaml` is missing or malformed."""
