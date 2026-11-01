from tnw_cli import __version__


def test_version(tnw):
    for flag in ("--version", "-v"):
        result = tnw(flag)
        assert result.returncode == 0
        assert result.stdout.strip() == "tnw %s" % __version__


def test_help_lists_commands(tnw):
    result = tnw("-h")
    assert result.returncode == 0
    for command in ("init", "check", "show", "build_report", "build_book"):
        assert command in result.stdout


def test_subcommand_short_help(tnw):
    result = tnw("build_report", "-h")
    assert result.returncode == 0
    assert "DOCUMENT" in result.stdout
