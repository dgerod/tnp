"""Command-line interface of tnw (`click` command group)."""

import functools
import sys

import click

from tnw_cli import __version__
from tnw_cli.common.types import TnwError
from tnw_cli.operations import build_book, build_report, show, workspace

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


def _report_errors(command):
    """Turn a TnwError into a clean error message and exit code 1."""
    @functools.wraps(command)
    def wrapper(*args, **kwargs):
        try:
            return command(*args, **kwargs)
        except TnwError as error:
            raise click.ClickException(str(error)) from error
    return wrapper


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(__version__, "-v", "--version", prog_name="tnw",
                      message="%(prog)s %(version)s")
def cli():
    """Technical Notes Writer: manage Markdown notes and build them to HTML."""


@cli.command()
@click.option("--pandoc", metavar="COMMAND", help="Command to run pandoc (default: pandoc on PATH).")
@click.option("--plantuml", metavar="JAR", help="Path to plantuml.jar (run with java -jar).")
@click.option("--mermaid", metavar="COMMAND", help="Command to run the Mermaid CLI (default: mmdc on PATH).")
@click.option("-f", "--force", is_flag=True, help="Overwrite an existing workspace without asking.")
@_report_errors
def init(pandoc, plantuml, mermaid, force):
    """Create the workspace (.tnw/, .vscode/) in the current directory."""
    created = workspace.create_workspace(pandoc=pandoc, plantuml=plantuml, mermaid=mermaid,
                                         force=force,
                                         confirm=lambda message: click.confirm(message, default=False))
    if not created:
        sys.exit(1)


@cli.command()
@_report_errors
def check():
    """Diagnose the workspace containing the current directory."""
    if not workspace.check_workspace():
        sys.exit(1)


@cli.command(name="show")
@_report_errors
def show_command():
    """Show the workspace information."""
    show.show_information()


def _check_extension(extensions):
    def check(ctx, param, value):
        if value is not None and not value.lower().endswith(extensions):
            raise click.BadParameter("expected a %s file" % " or ".join(extensions))
        return value
    return check


def _check_output_format(ctx, param, value):
    if value.lower() != "html":
        raise click.BadParameter("'%s' is not supported; tnw only builds html" % value)
    return "html"


EXISTING_FILE = click.Path(exists=True, dir_okay=False)


@cli.command(name="build_report")
@click.argument("file_type", metavar="html", callback=_check_output_format)
@click.argument("document", type=EXISTING_FILE, callback=_check_extension((".md",)))
@click.option("-b", "--biblio", type=EXISTING_FILE, callback=_check_extension((".bib",)),
              help="Bibliography (.bib); overrides the front-matter 'bibliography'.")
@_report_errors
def build_report_command(file_type, document, biblio):
    """Build one note (DOCUMENT.md) to <workspace>/build/DOCUMENT.html."""
    build_report.make_html_report(document, biblio)


@cli.command(name="build_book")
@click.argument("file_type", metavar="html", callback=_check_output_format)
@click.argument("config", type=EXISTING_FILE, callback=_check_extension((".yaml", ".yml")))
@_report_errors
def build_book_command(file_type, config):
    """Build the book described by CONFIG (book.yaml) to <workspace>/build/<file>.html."""
    build_book.make_html_book(config)


def main():
    cli(prog_name="tnw")
