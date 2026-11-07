#!/usr/bin/env python3
"""The `tnp-todo` tag: inline `::tnp-todo{...}` and block `::: tnp-todo`.

Both render as black text on a yellow background. The deprecated `todo`
spelling (`::todo{...}`, `::: todo`) is still accepted. Keep the tag syntax
in sync with mpe/parser.js.
"""

import re

import panflute as pf

TAG_OPEN = re.compile(r"::(?:tnp-todo|todo)\{")
TAG_DELIMITER = re.compile(r"(%s|\})" % TAG_OPEN.pattern)
BLOCK_CLASSES = {"tnp-todo", "todo"}
STYLE = "color:black;background-color:yellow"


def _todo_span(content):
    return pf.Span(*content, classes=["todo"], attributes={"style": STYLE})


def _replace_inline_tags(container):
    """Wrap in a span the sibling inlines between each tag opening and its `}`.

    The delimiters are searched in the Str inlines only, so whatever Pandoc
    parsed between them (emphasis, code, quotes, links, ...) is kept as it is.
    A tag without closing brace at this level stays as text.
    """
    output = []
    tag_start = None
    changed = False
    for item in container.content:
        parts = TAG_DELIMITER.split(item.text) if isinstance(item, pf.Str) else [item]
        for part in parts:
            if isinstance(part, pf.Inline):
                output.append(part)
            elif part == "}" and tag_start is not None:
                output[tag_start:] = [_todo_span(output[tag_start + 1:])]
                tag_start = None
                changed = True
            elif part:
                if tag_start is None and TAG_OPEN.fullmatch(part):
                    tag_start = len(output)
                output.append(pf.Str(part))
    if changed:
        container.content = output


def _has_inline_content(elem):
    content = getattr(elem, "content", None)
    return (isinstance(content, pf.ListContainer) and len(content) > 0
            and all(isinstance(item, pf.Inline) for item in content))


def action(elem, doc):
    if isinstance(elem, pf.Div) and BLOCK_CLASSES & set(elem.classes):
        elem.attributes["style"] = STYLE
        return None
    if not isinstance(elem, (pf.Cite, pf.Link, pf.Image)) and _has_inline_content(elem):
        _replace_inline_tags(elem)
    return None


def main(doc=None):
    return pf.run_filter(action, doc=doc)


if __name__ == "__main__":
    main()
