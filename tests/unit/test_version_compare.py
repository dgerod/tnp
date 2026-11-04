import pytest

from tnp_cli.common.version_compare import Compatibility, compare, parse


@pytest.mark.parametrize("workspace, installed, expected", [
    ("0.1.0", "0.1.0", Compatibility.OK),
    ("0.1.0", "0.1.5", Compatibility.OK),          # patch ignored
    ("0.1.0", "0.2.0", Compatibility.WARNING),     # same major, newer minor
    ("1.0.0", "2.0.0", Compatibility.FAIL),        # different major
    ("0.2.0", "0.1.9", Compatibility.FAIL),        # installed older
    ("0.1.2", "0.1.1", Compatibility.FAIL),        # installed older by patch
    ("garbage", "0.1.0", Compatibility.FAIL),
    ("0.1.0", "", Compatibility.FAIL),
])
def test_compare(workspace, installed, expected):
    assert compare(workspace, installed) is expected


def test_parse_accepts_v_prefix_and_two_components():
    assert parse("v1.2.3") == (1, 2, 3)
    assert parse("1.2") == (1, 2, 0)
    assert parse("1") is None
