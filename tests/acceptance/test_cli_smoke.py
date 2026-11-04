from tnp_cli import __version__


def test_version(tnp):
    for flag in ("--version", "-v"):
        result = tnp(flag)
        assert result.returncode == 0
        assert result.stdout.strip() == "tnp %s" % __version__


def test_help_lists_commands(tnp):
    result = tnp("-h")
    assert result.returncode == 0
    for command in ("init", "check", "show", "build_report", "build_book"):
        assert command in result.stdout


def test_subcommand_short_help(tnp):
    result = tnp("build_report", "-h")
    assert result.returncode == 0
    assert "DOCUMENT" in result.stdout
