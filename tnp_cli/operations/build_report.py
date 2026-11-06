import os
import re
import shlex
import subprocess

import yaml

from tnp_cli import __version__
from tnp_cli.common import pandoc_filters
from tnp_cli.common.configuration import Configuration
from tnp_cli.common.pandoc_runner import run_pandoc, split_command
from tnp_cli.common.resource_locator import resource_path
from tnp_cli.common.types import TnpError


ASSETS_DIRECTORY = resource_path("pandoc-templates", "assets")
CSL_FILE = resource_path("pandoc-csl", "ieee-with-url.csl")
FILTERS = ("plantuml", "mermaid", "todo_tag", "citation_backrefs", "center_images")
META_FIELDS = ("did", "version", "date", "tags")
TEMPLATE = "tnp_report.html"

_FRONT_MATTER = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n(?:---|\.\.\.)[ \t]*(?:\r?\n|\Z)", re.DOTALL)
_ATX_H1 = re.compile(r"^ {0,3}#(?:[ \t]+|$)")
_SETEXT_H1 = re.compile(r"^ {0,3}=+[ \t]*$")
_FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_YAML_OPEN = re.compile(r"^---[ \t]*$")
_YAML_CLOSE = re.compile(r"^(?:---|\.\.\.)[ \t]*$")


def _has_meta(data):
    """True when the sidebar metadata box has something to show."""
    return any(data.get(field) for field in META_FIELDS)


def _html_command(configuration, document_dir, inputs, output, metadata, bibliography):
    """The pandoc argv that builds `inputs` into a self-contained HTML `output`.

    `--citeproc` comes before the filters so citation_backrefs sees the
    rendered citations.
    """
    command = [*split_command(configuration.pandoc_bin()),
               "--citeproc", "--toc", "--standalone", "--embed-resources",
               "--resource-path", os.pathsep.join([ASSETS_DIRECTORY, document_dir]),
               "--template", resource_path("pandoc-templates", TEMPLATE),
               # The single '#' heading becomes the title; '##' sections become the TOC.
               "--shift-heading-level-by=-1"]
    for name in FILTERS:
        command += ["--filter", pandoc_filters.filter_path(name)]
    command += ["--mathjax", "--metadata=link-citations:true",
                "--metadata=tnp_version:%s" % __version__]
    for key, value in metadata:
        command.append("--metadata=%s:%s" % (key, value))
    if bibliography:
        command += ["--bibliography", bibliography, "--csl", CSL_FILE]
    command += ["-f", "markdown", *inputs, "-t", "html", "-o", output]
    return command


def _quote_command(command):
    """The command line as it would be typed in the platform's shell."""
    if os.name == "nt":
        return subprocess.list2cmdline(command)
    return shlex.join(command)


def _run_build(configuration, command, document_dir, output):
    os.makedirs(configuration.build_directory(), exist_ok=True)
    print("Execute: %s" % _quote_command(command))
    returncode = run_pandoc(command, extra_env={
        "TNP_DOCUMENT_DIR": document_dir,
        "TNP_WORKSPACE_DIR": configuration.work_directory(),
    })
    if returncode != 0:
        raise TnpError("pandoc failed with exit code %d; %s was not built" % (returncode, output))
    print("Output: %s" % output)
    return output


def _resolve_existing(path, base_dir, what):
    """Absolute path of `path` (relative to base_dir), which must be an existing file."""
    resolved = os.path.normpath(os.path.join(base_dir, os.path.expanduser(str(path))))
    if not os.path.isfile(resolved):
        raise TnpError("%s not found: %s" % (what, resolved))
    return resolved


def read_front_matter(text):
    """The YAML front-matter as a dict, scalars kept as written ({} if absent or invalid)."""
    match = _FRONT_MATTER.match(text)
    if not match:
        return {}
    try:
        data = yaml.load(match.group(1), Loader=yaml.BaseLoader)
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _metadata_block_end(lines, index):
    """Index of the line closing a pandoc YAML block opened at `index`, or None.

    As in pandoc, `---` opens one when the line above is blank and the line
    below is not; otherwise it is a horizontal rule or a setext underline.
    """
    if not _YAML_OPEN.match(lines[index]) or (index > 0 and lines[index - 1].strip()):
        return None
    if index + 1 >= len(lines) or not lines[index + 1].strip():
        return None
    for end in range(index + 1, len(lines)):
        if _YAML_CLOSE.match(lines[end]):
            return end
    return None


def count_body_h1(text):
    """Number of level-1 headings in a Markdown body (YAML blocks and code ignored)."""
    lines = _FRONT_MATTER.sub("", text, count=1).splitlines()
    count = 0
    fence = None
    previous = ""
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        fence_match = _FENCE.match(line)
        if fence:
            if fence_match and fence_match.group(1)[0] == fence[0] \
                    and len(fence_match.group(1)) >= len(fence):
                fence = None
            previous = ""
            continue
        if fence_match:
            fence = fence_match.group(1)
            previous = ""
            continue
        end = _metadata_block_end(lines, index - 1)
        if end is not None:
            index = end + 1
            previous = ""
            continue
        if _ATX_H1.match(line):
            count += 1
        elif _SETEXT_H1.match(line) and previous.strip() and not _ATX_H1.match(previous):
            count += 1
        previous = line
    return count


def report_output_path(build_directory, document):
    return os.path.join(build_directory, os.path.splitext(os.path.basename(document))[0] + ".html")


def make_html_report(document, biblio=None):
    configuration = Configuration()
    document = os.path.abspath(document)
    document_dir = os.path.dirname(document)
    try:
        with open(document, encoding="utf-8") as source:
            text = source.read()
    except (OSError, UnicodeDecodeError) as error:
        raise TnpError("cannot read %s: %s" % (document, error)) from error

    front_matter = read_front_matter(text)
    if "title" in front_matter:
        raise TnpError("%s: a report takes its title from its single '#' heading; "
                       "remove 'title' from the front-matter" % document)
    headings = count_body_h1(text)
    if headings != 1:
        raise TnpError("%s: a report must have exactly one top-level '#' heading (its title), "
                       "found %d" % (document, headings))

    # -b overrides the front-matter; both are resolved to absolute paths
    # because pandoc would resolve them against the current directory.
    if biblio:
        bibliography = _resolve_existing(biblio, os.getcwd(), "bibliography")
    elif front_matter.get("bibliography"):
        bibliography = _resolve_existing(front_matter["bibliography"], document_dir, "bibliography")
    else:
        bibliography = None

    output = report_output_path(configuration.build_directory(), document)
    # pandoc reads `did: 002` as 2 and `version: 1.10` as 1.1; passing the
    # values as written on the command line overrides its reading.
    metadata = [(field, front_matter[field]) for field in ("did", "version", "date")
                if isinstance(front_matter.get(field), str) and front_matter[field]]
    tags = front_matter.get("tags")
    if isinstance(tags, list):
        metadata += [("tags", tag) for tag in tags if isinstance(tag, str)]
    if _has_meta(front_matter):
        metadata.append(("has_meta", "1"))
    command = _html_command(configuration, document_dir, [document], output, metadata,
                            bibliography)
    return _run_build(configuration, command, document_dir, output)
