import os
from pathlib import Path

from tnp_cli.common import workspace
from tnp_cli.common.workspace import Status
from tnp_cli.common.workspace_locator import TNP_DIRECTORY, find_workspace_root


_STATUS_LABEL = {
    Status.OK: "[OK ]",
    Status.WARNING: "[WARN]",
    Status.FAIL: "[FAIL]",
}


def _plantuml_command(jar_path):
    if any(character.isspace() for character in jar_path):
        jar_path = '"%s"' % jar_path
    return "java -jar %s" % jar_path


def create_workspace(pandoc=None, plantuml=None, mermaid=None, force=False,
                     confirm=None, cwd=None):
    """Create a workspace in `cwd`, or overwrite the one found walking up.

    `confirm(message) -> bool` is asked before overwriting unless `force`.
    Returns True when a workspace was written.
    """
    cwd = Path(cwd or Path.cwd()).resolve()
    tnp_settings = workspace.render_tnp_settings(
        pandoc_bin=pandoc,
        plantuml_bin=_plantuml_command(plantuml) if plantuml else None,
        mermaid_bin=mermaid)
    
    vscode_settings = workspace.render_vscode_settings(
        plantuml_jar=os.path.abspath(plantuml) if plantuml else None)

    root = find_workspace_root(cwd)
    if root is not None:
        print("A tnp workspace already exists at %s" % root)
        print("Reinitializing OVERWRITES its .tnp and .vscode directories; "
              "back up %s first if you want to keep it." % (root / TNP_DIRECTORY))
        if not force and not (confirm and confirm("Overwrite the workspace?")):
            print("Aborted: nothing changed.")
            return False
        workspace.remove_workspace(root)
    else:
        root = cwd

    conflicts = workspace.build_workspace(root, tnp_settings, vscode_settings)
    if conflicts:
        print("Cannot create the workspace; these paths already exist:")
        for path in conflicts:
            print("  %s" % path)
        print("Nothing was created.")
        return False
    print("Workspace initialized at %s" % root)
    return True


def check_workspace(cwd=None):
    """Print one line per check; True when the workspace is healthy."""
    results = workspace.diagnose_workspace(cwd)
    for result in results:
        print("%s %s: %s" % (_STATUS_LABEL[result.status], result.name, result.detail))
    return not workspace.is_failure(results)
