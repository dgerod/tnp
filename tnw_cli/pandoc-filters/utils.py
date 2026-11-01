"""Stdlib-only helpers shared by the diagram filters."""

import hashlib
import os
import subprocess


class RenderError(Exception):
    """A diagram tool failed or produced no image."""


def extension(output_format):
    """Image type for an output format: svg for HTML, png otherwise."""
    return "svg" if output_format.startswith("html") else "png"


def filename_for_code(directory, prefix, key, ext):
    """Cache path `<directory>/<prefix>-<sha1(key)>.<ext>` (directory created)."""
    os.makedirs(directory, exist_ok=True)
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
    return os.path.join(directory, "%s-%s.%s" % (prefix, digest, ext))


def run_renderer(argv, target, stdin_text=None):
    """Run a diagram tool and check it left a non-empty `target` image.

    With `stdin_text`, the source is piped in and the tool's stdout is the
    image (written to `target`). Raises RenderError on any failure.
    """
    try:
        result = subprocess.run(argv, input=stdin_text.encode("utf-8") if stdin_text else None,
                                capture_output=True)
    except OSError as error:
        raise RenderError("cannot run '%s': %s" % (argv[0], error)) from error
    if result.returncode != 0:
        details = result.stderr.decode("utf-8", "replace").strip()
        raise RenderError("'%s' exited with status %d%s"
                          % (" ".join(argv), result.returncode, ": " + details if details else ""))
    if stdin_text is not None:
        with open(target, "wb") as image:
            image.write(result.stdout)
    if not os.path.isfile(target) or os.path.getsize(target) == 0:
        if os.path.isfile(target):
            os.remove(target)
        raise RenderError("'%s' produced no image (%s)" % (" ".join(argv), target))
    return target
