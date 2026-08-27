import json
from pathlib import Path

from jsonschema import Draft202012Validator
from orcid_biosketch import build_biosketch, render_markdown, to_jsonld


def fixture():
    return json.loads((Path(__file__).parent / "fixture.json").read_text())


def test_builds_normalized_biosketch():
    bio = build_biosketch(fixture(), {"person": {"headline": "Researcher"}})
    assert bio["person"]["name"] == "Damien Huzard"
    assert bio["person"]["headline"] == "Researcher"
    assert bio["works"][0]["identifiers"]["doi"] == "10.1/test"
    assert bio["provenance"]["override_applied"] is True


def test_renders_machine_and_human_formats():
    bio = build_biosketch(fixture())
    assert to_jsonld(bio)["@type"] == "Person"
    assert "https://doi.org/10.1/test" in render_markdown(bio)


def test_output_matches_public_schema():
    bio = build_biosketch(fixture(), {"selection": {"max_works": 5}})
    schema = json.loads((Path(__file__).parents[1] / "schema" / "biosketch.schema.json").read_text())
    Draft202012Validator(schema).validate(bio)
