import re
from enum import Enum


_VERSION_PATTERN = re.compile(r"^\s*v?(\d+)\.(\d+)(?:\.(\d+))?\s*$")


class Compatibility(Enum):
    OK = "ok"
    WARNING = "warning"
    FAIL = "fail"


def parse(version):
    """`major.minor[.patch]` (optionally prefixed with `v`) as a tuple of ints, else None."""
    
    match = _VERSION_PATTERN.match(str(version))
    if not match:
        return None
    major, minor, patch = match.groups()
    return int(major), int(minor), int(patch or 0)


def compare(workspace_version, installed_version):
    """Compare by major.minor; an installed version older than the workspace fails."""
    
    workspace = parse(workspace_version)
    installed = parse(installed_version)
    if workspace is None or installed is None:
        return Compatibility.FAIL
    if installed < workspace:
        return Compatibility.FAIL
    if installed[0] != workspace[0]:
        return Compatibility.FAIL
    if installed[1] != workspace[1]:
        return Compatibility.WARNING
    return Compatibility.OK
