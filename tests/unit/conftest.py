import sys

import pytest

from tnw_cli import __version__
from tnw_cli.common.resource_locator import resource_path

# The filters are standalone scripts that import their siblings by name.
sys.path.insert(0, resource_path("pandoc-filters"))


@pytest.fixture
def make_workspace(tmp_path):
    """Create a `.tnw/settings.yaml` with the given text under tmp_path."""
    def make(settings='tnw_version: "%s"\n' % __version__):
        tnw_directory = tmp_path / ".tnw"
        tnw_directory.mkdir()
        (tnw_directory / "settings.yaml").write_text(settings, encoding="utf-8")
        return tmp_path
    return make
