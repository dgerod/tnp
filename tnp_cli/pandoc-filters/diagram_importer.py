"""Engine-agnostic support for the `::tnp-mmd{file}` / `::tnp-puml{file}` import tags."""

import os
import re
import sys

import panflute as pf


def lone_tag_path(elem, tag):
    """The path of a paragraph made only of `::<tag>{path}`, else None.

    The tag is block-level: a tag mixed with other text is left untouched.
    """
    if not isinstance(elem, pf.Para):
        return None
    if not all(isinstance(item, (pf.Str, pf.Space, pf.SoftBreak)) for item in elem.content):
        return None
    text = pf.stringify(elem).strip()
    match = re.fullmatch(r"::%s\{([^}]+)\}" % re.escape(tag), text)
    if not match:
        return None
    return match.group(1).strip() or None


def resolve_path(path, base=None):
    """Absolute path, relative to TNP_DOCUMENT_DIR (the document's directory)."""
    path = os.path.expanduser(path)
    if os.path.isabs(path):
        return os.path.normpath(path)
    base = base or os.environ.get("TNP_DOCUMENT_DIR") or os.getcwd()
    return os.path.normpath(os.path.join(base, path))


def has_valid_extension(path, extensions):
    return os.path.splitext(path)[1].lower() in extensions


def classify(path, extensions):
    """None when `path` can be imported, else the reason it cannot."""
    if not has_valid_extension(path, extensions):
        return "invalid extension (expected %s)" % ", ".join(sorted(extensions))
    if not os.path.isfile(path):
        return "file not found"
    return None


def read_code_from_file(path):
    with open(path, encoding="utf-8") as source:
        return source.read()


def _inlines(text):
    """Str / Space inlines for a plain text."""
    inlines = []
    for index, word in enumerate(text.split(" ")):
        if index:
            inlines.append(pf.Space())
        if word:
            inlines.append(pf.Str(word))
    return inlines


def error_marker(tag, raw_path, message):
    """A visible, non-fatal red marker in place of a diagram that cannot be imported."""
    text = "[::%s{%s}: %s]" % (tag, raw_path, message)
    sys.stderr.write("tnp: warning: %s\n" % text)
    return pf.Para(pf.Span(pf.Strong(*_inlines(text)), classes=["tnp-error"],
                           attributes={"style": "color:red"}))
