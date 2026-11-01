from tnw_cli.operations.build_report import read_front_matter


def test_front_matter():
    assert read_front_matter("---\ntags: [a, b]\n---\n# T\n") == {"tags": ["a", "b"]}
    assert read_front_matter("# no front matter\n") == {}
    assert read_front_matter("---\n: bad: yaml\n---\n") == {}
    assert read_front_matter("---\n- a list\n---\n") == {}


def test_scalars_kept_as_written():
    assert read_front_matter("---\ndid: 002\nversion: 1.10\n---\n") == {"did": "002",
                                                                        "version": "1.10"}
