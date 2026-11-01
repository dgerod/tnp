from tabulate import tabulate

from tnw_cli import __version__
from tnw_cli.common.configuration import Configuration
from tnw_cli.common.resource_locator import mpe_directory
from tnw_cli.common.version_compare import Compatibility, compare


_COMPATIBILITY_LABEL = {
    Compatibility.OK: "compatible",
    Compatibility.WARNING: "compatible (minor version differs)",
    Compatibility.FAIL: "incompatible",
}


def show_information():
    configuration = Configuration()
    created = configuration.created_version()
    rows = [
        ("Workspace tnw version", created),
        ("Installed tnw version", __version__),
        ("Compatibility", _COMPATIBILITY_LABEL[compare(created, __version__)]),
        ("pandoc", configuration.pandoc_bin()),
        ("PlantUML", configuration.plantuml_bin()),
        ("Mermaid", configuration.mermaid_bin()),
        ("Workspace directory", configuration.work_directory()),
        ("Build directory", configuration.build_directory()),
        ("MPE config", mpe_directory()),
    ]
    print(tabulate(rows, tablefmt="plain"))
