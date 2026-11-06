import panflute as pf
import pytest

import center_images


def _image():
    return pf.Image(url="a.svg")


def _run(*blocks):
    return center_images.main(pf.Doc(*blocks, format="html"))


@pytest.mark.parametrize("inlines", [
    [_image()],
    [_image(), pf.SoftBreak(), _image()],
    [pf.Link(_image(), url="https://example.com")],
])
def test_paragraph_of_images_is_marked(inlines):
    block = _run(pf.Para(*inlines)).content[0]
    assert isinstance(block, pf.Div) and block.classes == ["tnp-image"]
    assert isinstance(block.content[0], pf.Para)


@pytest.mark.parametrize("block", [
    pf.Para(pf.Str("icon"), pf.Space(), _image()),
    pf.Para(pf.Link(pf.Str("text"), url="https://example.com")),
    pf.Para(),
    pf.Plain(_image()),
])
def test_other_blocks_are_left_alone(block):
    assert not isinstance(_run(block).content[0], pf.Div)
