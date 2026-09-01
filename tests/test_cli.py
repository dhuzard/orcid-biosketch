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


def test_card_embeds_a_supplied_orcid_qr_png(biosketch, tmp_path):
    qr = tmp_path / "orcid.png"
    qr.write_bytes(b"\x89PNG\r\n\x1a\n" + b"official-qr-bytes")
    target = tmp_path / "card.svg"
    assert cli.main([
        "card", "--biosketch", str(biosketch), "--qr", str(qr), "-o", str(target),
    ]) == 0
    assert "data:image/png;base64," in target.read_text(encoding="utf-8")


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


def test_biosketch_of_the_wrong_shape_is_a_clean_error(tmp_path, capsys):
    wrong = tmp_path / "csl.json"
    wrong.write_text('[{"id": "x", "type": "article-journal"}]', encoding="utf-8")
    assert cli.main(["lint", "--biosketch", str(wrong)]) == 2
    assert "not a biosketch document" in capsys.readouterr().err


def test_naming_a_template_selects_template_mode(tmp_path, capsys):
    out = tmp_path / "nih.md"
    assert cli.main(["export", "--record", str(FIXTURE), "--template", "nih", "-o", str(out)]) == 0
    assert "NIH Biographical Sketch" in out.read_text(encoding="utf-8")


def test_custom_template_path_is_accepted(tmp_path):
    template = tmp_path / "custom.md"
    template.write_text("# {{ person.name }}\n", encoding="utf-8")
    out = tmp_path / "custom-output.md"
    assert cli.main([
        "export", "--record", str(FIXTURE), "--template", str(template), "-o", str(out),
    ]) == 0
    assert out.read_text(encoding="utf-8").startswith("# Damien Huzard")


def test_unknown_template_is_a_clean_error(capsys):
    assert cli.main(["export", "--record", str(FIXTURE), "--template", "nope"]) == 2
    assert "Unknown template" in capsys.readouterr().err
