import os
import shlex
import subprocess

import yaml

from tnw_cli import __version__
from tnw_cli.common import pandoc_filters
from tnw_cli.common.configuration import Configuration
from tnw_cli.common.pandoc_runner import run_pandoc, split_command
from tnw_cli.common.resource_locator import resource_path
from tnw_cli.common.types import TnwError


ASSETS_DIRECTORY = resource_path("pandoc-templates", "assets")
CSL_FILE = resource_path("pandoc-csl", "ieee-with-url.csl")
FILTERS = ("plantuml", "mermaid", "todo_tag", "citation_backrefs")
META_FIELDS = ("did", "version", "date", "tags")
TEMPLATE = "tnw_book.html"
REQUIRED_FIELDS = ("title", "file", "toc")


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
               "--template", resource_path("pandoc-templates", TEMPLATE)]
    for name in FILTERS:
        command += ["--filter", pandoc_filters.filter_path(name)]
    command += ["--mathjax", "--metadata=link-citations:true",
                "--metadata=tnw_version:%s" % __version__]
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
        "TNW_DOCUMENT_DIR": document_dir,
        "TNW_WORKSPACE_DIR": configuration.work_directory(),
    })
    if returncode != 0:
        raise TnwError("pandoc failed with exit code %d; %s was not built" % (returncode, output))
    print("Output: %s" % output)
    return output


def _resolve_existing(path, base_dir, what):
    """Absolute path of `path` (relative to base_dir), which must be an existing file."""
    resolved = os.path.normpath(os.path.join(base_dir, os.path.expanduser(str(path))))
    if not os.path.isfile(resolved):
        raise TnwError("%s not found: %s" % (what, resolved))
    return resolved


def _read_configuration(config_file):
    """Validated book configuration; paths are resolved against its directory.

    Values are read as plain strings (BaseLoader) so `did: 001` or a date
    reach the output exactly as written.
    """
    config_file = os.path.abspath(config_file)
    base_dir = os.path.dirname(config_file)
    try:
        with open(config_file, encoding="utf-8") as source:
            data = yaml.load(source, Loader=yaml.BaseLoader)
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as error:
        raise TnwError("cannot read %s: %s" % (config_file, error)) from error
    if not isinstance(data, dict):
        raise TnwError("%s is not a mapping" % config_file)

    missing = [field for field in REQUIRED_FIELDS if not data.get(field)]
    if missing:
        raise TnwError("%s: missing required field(s): %s" % (config_file, ", ".join(missing)))
    for field in ("title", "file"):
        if not isinstance(data[field], str):
            raise TnwError("%s: '%s' must be a string" % (config_file, field))
    if os.path.basename(data["file"]) != data["file"]:
        raise TnwError("%s: 'file' must be a file name without directories" % config_file)
    if not isinstance(data["toc"], list) or not all(isinstance(c, str) for c in data["toc"]):
        raise TnwError("%s: 'toc' must be a list of chapter files" % config_file)

    tags = data.get("tags") or []
    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(",") if tag.strip()]
    for field in ("author", "did", "version", "date"):
        if field in data and not isinstance(data[field], str):
            raise TnwError("%s: '%s' must be a single value" % (config_file, field))

    chapters = [_resolve_existing(chapter, base_dir, "chapter") for chapter in data["toc"]]
    bibliography = None
    if data.get("bibliography"):
        bibliography = _resolve_existing(data["bibliography"], base_dir, "bibliography")
    return data["title"], data["file"], tags, chapters, bibliography, base_dir, data


def _tags_metadata(tags):
    return [("tags", tag) for tag in tags]


def make_html_book(config_file):
    title, file_name, tags, chapters, biblio, base_dir, data = _read_configuration(config_file)
    configuration = Configuration()

    metadata = [("title", title)]
    metadata += [(field, data[field]) for field in ("did", "version", "author", "date")
                 if data.get(field)]
    metadata += _tags_metadata(tags)
    if _has_meta({**data, "tags": tags}):
        metadata.append(("has_meta", "1"))

    output = os.path.join(configuration.build_directory(), file_name + ".html")
    command = _html_command(configuration, base_dir, chapters, output, metadata, biblio)
    return _run_build(configuration, command, base_dir, output)
