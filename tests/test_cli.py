import json
from pathlib import Path

import pytest
from orcid_biosketch import cli

FIXTURE = Path(__file__).parent / "fixture.json"


@pytest.fixture()
def biosketch(tmp_path):
    """A generated biosketch on disk, so CLI tests never touch the network."""
    path = tmp_path / "biosketch.json"
    from orcid_biosketch.core import build_biosketch, load_record
    path.write_text(json.dumps(build_biosketch(load_record(FIXTURE))), encoding="utf-8")
    return path


def test_generate_writes_all_three_outputs(tmp_path):
    out = tmp_path / "generated"
    assert cli.main(["generate", "--record", str(FIXTURE), "--output", str(out)]) == 0
    assert {p.name for p in out.iterdir()} == {"biosketch.json", "biosketch.jsonld", "biosketch.md"}


def test_bare_orcid_still_generates(tmp_path):
    """The pre-subcommand invocation must keep working."""
    out = tmp_path / "generated"
    assert cli.main(["--record", str(FIXTURE), "--output", str(out)]) == 0
    assert (out / "biosketch.json").exists()


@pytest.mark.parametrize("command", ["lint", "wrapped", "card", "heatmap", "fortune", "badge"])
def test_commands_write_to_a_file(biosketch, tmp_path, command):
    target = tmp_path / f"{command}.out"
    assert cli.main([command, "--biosketch", str(biosketch), "-o", str(target)]) == 0
    assert target.read_text(encoding="utf-8").strip()


@pytest.mark.parametrize("fmt", ["csl", "bibtex", "ris", "template"])
def test_export_formats(biosketch, tmp_path, fmt):
    target = tmp_path / fmt
    assert cli.main(["export", "--biosketch", str(biosketch), "--format", fmt, "-o", str(target)]) == 0
    assert target.read_text(encoding="utf-8").strip()


def test_lint_fail_under_gates_ci(biosketch):
    assert cli.main(["lint", "--biosketch", str(biosketch), "--fail-under", "0"]) == 0
    assert cli.main(["lint", "--biosketch", str(biosketch), "--fail-under", "101"]) == 1


def test_badge_is_shields_endpoint_json(biosketch, tmp_path, capsys):
    assert cli.main(["badge", "--biosketch", str(biosketch)]) == 0
    badge = json.loads(capsys.readouterr().out)
    assert badge["schemaVersion"] == 1 and badge["color"]


def test_invalid_orcid_exits_without_fetching(capsys):
    assert cli.main(["lint", "0000-0002-1825-0098"]) == 2
    assert "checksum" in capsys.readouterr().err


def test_missing_source_is_explained(capsys):
    assert cli.main(["lint"]) == 2
    assert "--record" in capsys.readouterr().err


def test_unknown_template_is_reported(biosketch, capsys):
    assert cli.main(["export", "--biosketch", str(biosketch), "--format", "template", "--template", "nope"]) == 2
    assert "nope" in capsys.readouterr().err
