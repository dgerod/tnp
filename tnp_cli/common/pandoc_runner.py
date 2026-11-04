import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

from tnp_cli.common.types import TnpError


_PACKAGE_PARENT = Path(__file__).resolve().parents[2]


def split_command(command):
    """Split a configured command line into argv, resolving the executable on PATH.

    Resolving through shutil.which lets a plain name such as `mmdc` find
    `mmdc.cmd` on Windows, which subprocess would not do by itself.
    """
    windows = os.name == "nt"
    parts = shlex.split(command, posix=not windows)
    if windows:
        # Non-POSIX shlex keeps the quotes around a quoted token.
        parts = [part[1:-1] if len(part) >= 2 and part[0] == part[-1] and part[0] in "\"'"
                 else part for part in parts]
    if parts:
        parts[0] = shutil.which(parts[0]) or parts[0]
    return parts


def command_available(command):
    """True when the executable of a configured command can be found."""
    parts = split_command(command)
    return bool(parts) and shutil.which(parts[0]) is not None


def filter_environment(extra_env=None):
    """Environment for pandoc so its `.py` filters run with tnp's own Python.

    pandoc launches a `.py` filter with the `python3` / `python` found on
    PATH, so the directory of the running interpreter (the one that has
    panflute) goes first, and tnp_cli is made importable for a checkout.
    """
    env = os.environ.copy()
    env["PATH"] = os.pathsep.join([os.path.dirname(sys.executable), env.get("PATH", "")])
    env["PYTHONPATH"] = os.pathsep.join(
        path for path in (str(_PACKAGE_PARENT), env.get("PYTHONPATH")) if path)
    env.update(extra_env or {})
    return env


def run_pandoc(command, extra_env=None):
    """Run a pandoc command line (argv list) and return its exit code."""
    env = filter_environment(extra_env)
    try:
        return subprocess.run(command, env=env).returncode
    except FileNotFoundError as error:
        raise TnpError("cannot run '%s': %s" % (command[0], error)) from error
