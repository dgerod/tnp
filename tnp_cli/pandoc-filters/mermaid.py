#!/usr/bin/env python3
"""Render Mermaid diagrams: fenced `mermaid` blocks and `::tnp-mmd{file}` tags."""

import os

import panflute as pf

import diagram_importer
import utils
from tnp_cli.common.configuration import Configuration
from tnp_cli.common.pandoc_runner import split_command

CODE_CLASS = "mermaid"
IMPORT_TAG = "tnp-mmd"
EXTENSIONS = {".mermaid", ".mmd"}


def _render(code, key, doc):
    """Render `code` (cached by `key`) and return the image path. Raises RenderError."""
    ext = utils.extension(doc.format)
    target = utils.filename_for_code(doc.tnp_build_dir, "mermaid", key, ext)
    if os.path.isfile(target) and os.path.getsize(target) > 0:
        return target
    source = os.path.splitext(target)[0] + ".mmd"
    with open(source, "w", encoding="utf-8") as source_file:
        source_file.write(code)
    try:
        argv = split_command(doc.tnp_command) + ["-i", source, "-o", target]
        return utils.run_renderer(argv, target)
    finally:
        os.remove(source)


def _image_from_code(path):
    return pf.Para(pf.Image(url=path))


def action(elem, doc):
    if isinstance(elem, pf.CodeBlock) and CODE_CLASS in elem.classes:
        # A failing fenced block aborts the build (RenderError propagates).
        return _image_from_code(_render(elem.text, elem.text, doc))

    raw_path = diagram_importer.lone_tag_path(elem, IMPORT_TAG)
    if raw_path is None:
        return None
    path = diagram_importer.resolve_path(raw_path)
    problem = diagram_importer.classify(path, EXTENSIONS)
    if problem:
        return diagram_importer.error_marker(IMPORT_TAG, raw_path, problem)
    code = diagram_importer.read_code_from_file(path)
    try:
        # Path plus content: the cache follows edits to the imported file.
        return _image_from_code(_render(code, path + "\n" + code, doc))
    except utils.RenderError as error:
        return diagram_importer.error_marker(IMPORT_TAG, raw_path, str(error))


def prepare(doc):
    configuration = Configuration(os.environ.get("TNP_WORKSPACE_DIR"))
    doc.tnp_command = configuration.mermaid_bin()
    doc.tnp_build_dir = configuration.build_directory()


def main(doc=None):
    return pf.run_filter(action, prepare=prepare, doc=doc)


if __name__ == "__main__":
    main()
