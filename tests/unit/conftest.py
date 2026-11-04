import sys

import pytest

from tnp_cli import __version__
from tnp_cli.common.resource_locator import resource_path

# The filters are standalone scripts that import their siblings by name.
sys.path.insert(0, resource_path("pandoc-filters"))


@pytest.fixture
def make_workspace(tmp_path):
    """Create a `.tnp/settings.yaml` with the given text under tmp_path."""
    def make(settings='tnp_version: "%s"\n' % __version__):
        tnp_directory = tmp_path / ".tnp"
        tnp_directory.mkdir()
        (tnp_directory / "settings.yaml").write_text(settings, encoding="utf-8")
        return tmp_path
    return make
