#!/usr/bin/env python3
"""The `tnp-todo` tag: inline `::tnp-todo{...}` and block `::: tnp-todo`.

Both render as black text on a yellow background. The deprecated `todo`
spelling (`::todo{...}`, `::: todo`) is still accepted. Keep the regex in
sync with mpe/parser.js.
"""

import re

import panflute as pf

INLINE_PATTERN = re.compile(r"::(?:tnp-todo|todo)\{([^}]*)\}")
BLOCK_CLASSES = {"tnp-todo", "todo"}
STYLE = "color:black;background-color:yellow"

_TEXT_INLINES = (pf.Str, pf.Space, pf.SoftBreak)


def _inlines(text):
    """Str / Space inlines for a plain text (whitespace collapses to Space)."""
    inlines = []
    for index, word in enumerate(text.split(" ")):
        if index:
            inlines.append(pf.Space())
        if word:
            inlines.append(pf.Str(word))
    return inlines


def _todo_span(content):
    return pf.Span(*_inlines(content), classes=["todo"], attributes={"style": STYLE})


def _replace_in_run(run):
    """New inlines for a run of Str/Space/SoftBreak, or None when it holds no tag."""
    text = "".join(" " if not isinstance(item, pf.Str) else item.text for item in run)
    if not INLINE_PATTERN.search(text):
        return None
    result = []
    position = 0
    for match in INLINE_PATTERN.finditer(text):
        result += _inlines(text[position:match.start()])
        result.append(_todo_span(match.group(1)))
        position = match.end()
    result += _inlines(text[position:])
    return result


def _replace_inline_tags(container):
    """Rewrite the tags found in the consecutive text runs of an inline list."""
    items = list(container.content)
    output = []
    changed = False
    index = 0
    while index < len(items):
        if not isinstance(items[index], _TEXT_INLINES):
            output.append(items[index])
            index += 1
            continue
        end = index
        while end < len(items) and isinstance(items[end], _TEXT_INLINES):
            end += 1
        run = items[index:end]
        replaced = _replace_in_run(run)
        if replaced is None:
            output += run
        else:
            output += replaced
            changed = True
        index = end
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
