import pytest

from tnw_cli.operations.build_report import count_body_h1


@pytest.mark.parametrize("text, expected", [
    ("# Title\n\n## A\n\n## B\n", 1),
    ("---\ntitle: x\n# not a heading\n---\n# Title\n", 1),  # front-matter ignored
    ("## Only sections\n", 0),
    ("# One\n\n# Two\n", 2),
    ("Title\n=====\n\ntext\n", 1),                           # setext
    ("#hashtag is not a heading\n", 0),
    ("   # indented up to three spaces\n", 1),
    ("    # four spaces is code\n", 0),
    ("# Title\n\n```sh\n# a comment\n```\n", 1),             # fenced code
    ("# Title\n\n~~~~\n# x\n~~~\n# still code\n~~~~\n", 1),  # longer fence
    ("# Title\n\n```\nTitle\n===\n```\n", 1),
    ("\n===\n", 0),                                          # no text above
])
def test_count_body_h1(text, expected):
    assert count_body_h1(text) == expected
