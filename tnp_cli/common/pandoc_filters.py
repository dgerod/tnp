from tnp_cli.common.resource_locator import resource_path


FILTERS = ("plantuml", "mermaid", "todo_tag", "citation_backrefs", "center_images")


def filter_path(name):
    if name not in FILTERS:
        raise ValueError("unknown pandoc filter: %s" % name)
    return resource_path("pandoc-filters", "%s.py" % name)
