import os

import pytest

from tnw_cli.common.types import TnwError
from tnw_cli.operations.build_book import _read_configuration


@pytest.fixture
def book(tmp_path):
    (tmp_path / "c1.md").write_text("# One\n")
    (tmp_path / "c2.md").write_text("# Two\n")
    (tmp_path / "refs.bib").write_text("")

    def write(text):
        path = tmp_path / "book.yaml"
        path.write_text(text)
        return str(path)
    return write


def test_reads_values_as_written(book, tmp_path):
    title, file_name, tags, chapters, biblio, base_dir, data = _read_configuration(book(
        "title: My Book\nfile: my-book\ndid: 001\ndate: 2026-10-04\nversion: 1.10\n"
        "tags: [a, b]\nbibliography: refs.bib\ntoc: [c1.md, c2.md]\n"))
    assert (title, file_name, tags) == ("My Book", "my-book", ["a", "b"])
    assert (data["did"], data["date"], data["version"]) == ("001", "2026-10-04", "1.10")
    assert chapters == [str(tmp_path / "c1.md"), str(tmp_path / "c2.md")]
    assert biblio == str(tmp_path / "refs.bib")
    assert base_dir == str(tmp_path)


def test_optional_fields(book):
    _, _, tags, _, biblio, _, data = _read_configuration(
        book("title: T\nfile: f\ntoc: [c1.md]\n"))
    assert tags == [] and biblio is None and "did" not in data


@pytest.mark.parametrize("text, message", [
    ("file: f\ntoc: [c1.md]\n", "title"),
    ("title: T\ntoc: [c1.md]\n", "file"),
    ("title: T\nfile: f\n", "toc"),
    ("title: T\nfile: f\ntoc: []\n", "toc"),
    ("title: T\nfile: f\ntoc: c1.md\n", "toc"),
    ("title: T\nfile: sub/f\ntoc: [c1.md]\n", "file"),
    ("title: T\nfile: f\ntoc: [missing.md]\n", "chapter not found"),
    ("title: T\nfile: f\nbibliography: nope.bib\ntoc: [c1.md]\n", "bibliography not found"),
    ("- just\n- a list\n", "mapping"),
])
def test_invalid_configuration(book, text, message):
    with pytest.raises(TnwError, match=message):
        _read_configuration(book(text))


def test_missing_file(tmp_path):
    with pytest.raises(TnwError, match="cannot read"):
        _read_configuration(os.path.join(str(tmp_path), "book.yaml"))
