#!/usr/bin/env python3
"""Mark the paragraphs that hold only images, so the page can center them.

Pandoc only makes a `figure` of an image with a caption alone in its paragraph.
Diagrams and images without a caption stay in a plain paragraph, while an image
inside a sentence must keep flowing with the text.
"""

import panflute as pf

CLASS = "tnp-image"
WHITESPACE = (pf.Space, pf.SoftBreak, pf.LineBreak)


def _is_image(inline):
    if isinstance(inline, pf.Link):
        return len(inline.content) == 1 and isinstance(inline.content[0], pf.Image)
    return isinstance(inline, pf.Image)


def action(elem, doc):
    if not isinstance(elem, pf.Para):
        return None
    inlines = [inline for inline in elem.content if not isinstance(inline, WHITESPACE)]
    if inlines and all(_is_image(inline) for inline in inlines):
        return pf.Div(elem, classes=[CLASS])
    return None


def main(doc=None):
    return pf.run_filter(action, doc=doc)


if __name__ == "__main__":
    main()
