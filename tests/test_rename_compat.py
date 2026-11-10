"""The package was renamed science_record_player (Nov 2026, ORCID brand guidance; BACKLOG INF-14).

The old import name, CLI commands and `python -m` entry points keep working as deprecated aliases.
"""
import importlib
import subprocess
import sys
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_old_import_name_returns_the_same_modules_with_a_deprecation_warning():
    for name in [n for n in sys.modules if n == "orcid_biosketch" or n.startswith("orcid_biosketch.")]:
        del sys.modules[name]
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        old = importlib.import_module("orcid_biosketch")
        old_core = importlib.import_module("orcid_biosketch.core")
        from orcid_biosketch.exporters import to_bibtex  # noqa: F401
    import science_record_player
    import science_record_player.core
    assert old is science_record_player and old_core is science_record_player.core
    assert any(issubclass(w.category, DeprecationWarning) and "science_record_player" in str(w.message) for w in caught)


def test_every_module_has_a_deprecated_alias():
    new = {p.stem for p in (ROOT / "src" / "science_record_player").glob("*.py")}
    old = {p.stem for p in (ROOT / "src" / "orcid_biosketch").glob("*.py")}
    assert new == old


def _run(*args):
    env = {"PYTHONPATH": str(ROOT / "src"), "PATH": "/usr/bin:/bin", "PYTHONWARNINGS": "ignore"}
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, env=env, cwd=ROOT, timeout=60)


def test_new_and_old_python_m_entry_points_work():
    assert "usage: srp" in _run("-m", "science_record_player.cli", "--help").stdout
    assert "usage: srp" in _run("-m", "orcid_biosketch.cli", "--help").stdout
    assert _run("-m", "orcid_biosketch.network", "--help").returncode == 0


def test_deprecated_commands_announce_the_new_name(capsys, monkeypatch):
    from science_record_player import cli, network
    monkeypatch.setattr(sys, "argv", ["orcid-biosketch", "--help"])
    try:
        cli.deprecated_main()
    except SystemExit:
        pass
    assert "`orcid-biosketch` is now `srp`" in capsys.readouterr().err
    try:
        network.deprecated_main(["--help"])
    except SystemExit:
        pass
    assert "`orcid-network` is now `srp-network`" in capsys.readouterr().err


def test_pyproject_exposes_new_and_deprecated_commands():
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for line in ('name = "science-record-player"', 'srp = "science_record_player.cli:main"',
                 'srp-network = "science_record_player.network:main"',
                 'orcid-biosketch = "science_record_player.cli:deprecated_main"',
                 'orcid-network = "science_record_player.network:deprecated_main"'):
        assert line in text
