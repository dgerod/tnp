"""mpe/parser.js, evaluated with Node.js the way Markdown Preview Enhanced does."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

PARSER = Path(__file__).resolve().parents[2] / "mpe" / "parser.js"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")

RUNNER = """
const fs = require("fs");
const parser = eval(fs.readFileSync(process.argv[1], "utf8"));
let input = "";
process.stdin.on("data", (chunk) => { input += chunk; });
process.stdin.on("end", async () => {
  process.stdout.write(await parser.onWillParseMarkdown(JSON.parse(input)));
});
"""


def _parse(markdown):
    result = subprocess.run(["node", "-e", RUNNER, str(PARSER)], input=json.dumps(markdown),
                            capture_output=True, text=True, encoding="utf-8")
    assert result.returncode == 0, result.stderr
    return result.stdout


def test_inline_tags():
    assert _parse("a ::tnp-todo{one} b ::todo{two} c ::tnp-todo{}") == (
        'a <span class="todo">one</span> b <span class="todo">two</span> c <span class="todo"></span>')


def test_block_tag_and_other_divs():
    markdown = "::: tnp-todo\nnote\n\n::: other\nx\n:::\n:::\n\n::: note\ny\n:::"
    assert _parse(markdown) == (
        '<div class="todo">\n\nnote\n\n::: other\nx\n:::\n\n</div>\n\n::: note\ny\n:::')


def test_import_tags():
    assert _parse("::tnp-mmd{d/flow.mmd}\n\n  ::tnp-puml{ a.puml }\n\nsee ::tnp-mmd{x.mmd}") == (
        '@import "d/flow.mmd"\n\n@import "a.puml"\n\nsee ::tnp-mmd{x.mmd}')


def test_code_is_untouched():
    markdown = "```\n::tnp-todo{x}\n::: tnp-todo\n::tnp-mmd{a.mmd}\n```\n~~~\n```\n::todo{y}\n~~~"
    assert _parse(markdown) == markdown


def test_hooks_are_exposed():
    script = ("const p = eval(require('fs').readFileSync(process.argv[1], 'utf8'));"
              "p.onDidParseMarkdown('<p>x</p>').then((h) => process.stdout.write("
              "typeof p.onWillParseMarkdown + ' ' + h));")
    result = subprocess.run(["node", "-e", script, str(PARSER)], capture_output=True, text=True, encoding="utf-8")
    assert result.stdout == "function <p>x</p>"
