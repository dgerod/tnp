import os

from tnw_cli.operations.build_report import report_output_path


def test_output_goes_to_build_directory_with_document_stem():
    build = os.path.join("root", "build")
    document = os.path.join("root", "notes", "deep", "my-note.md")
    assert report_output_path(build, document) == os.path.join(build, "my-note.html")
