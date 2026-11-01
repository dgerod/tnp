import importlib
import os

import pytest

from tnw_cli.common.pandoc_filters import FILTERS, filter_path


@pytest.mark.parametrize("name", FILTERS)
def test_filter_loads_and_exposes_main(name):
    assert os.path.isfile(filter_path(name))
    module = importlib.import_module(name)
    assert callable(module.main)


def test_unknown_filter():
    with pytest.raises(ValueError):
        filter_path("nope")
