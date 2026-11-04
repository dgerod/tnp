import os

import pytest

from tnp_cli.common import pandoc_runner


@pytest.mark.parametrize("command, expected", [
    ("mmdc", ["mmdc"]),
    ("java -jar /opt/plantuml.jar", ["java", "-jar", "/opt/plantuml.jar"]),
    ('java -jar "/my tools/p.jar"', ["java", "-jar", "/my tools/p.jar"]),
    ("java -jar '/my tools/p.jar'", ["java", "-jar", "/my tools/p.jar"]),
])
@pytest.mark.parametrize("platform", ["posix", "nt"])
def test_split_command(command, expected, platform, monkeypatch):
    monkeypatch.setattr(pandoc_runner.os, "name", platform)
    monkeypatch.setattr(pandoc_runner.shutil, "which", lambda name: None)
    assert pandoc_runner.split_command(command) == expected


def test_executable_is_resolved_on_path(monkeypatch):
    monkeypatch.setattr(pandoc_runner.shutil, "which",
                        lambda name: os.path.join("bin", name + ".cmd") if name == "mmdc" else None)
    assert pandoc_runner.split_command("mmdc -i x") == [os.path.join("bin", "mmdc.cmd"), "-i", "x"]
