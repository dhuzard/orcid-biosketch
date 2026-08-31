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


def test_parses_funding_with_amount_and_grant_number():
    funding = build_biosketch(fixture())["fundings"]
    assert [x["title"] for x in funding] == [
        "Stress resilience across the lifespan",
        "Doctoral fellowship",
    ]
    grant = funding[0]
    assert grant["organization"] == "Agence Nationale de la Recherche"
    assert grant["type"] == "grant"
    assert (grant["amount"], grant["currency"]) == ("250000", "EUR")
    assert grant["grant_number"] == "ANR-20-CE37-0001"
    assert grant["identifiers"]["grant_url"] == "https://anr.fr/Project-ANR-20-CE37-0001"
    assert grant["start_date"] == "2020-01-01"
    assert grant["end_date"] == "2023-12-31"
    assert grant["source"]["name"] == "Damien Huzard"
    assert grant["orcid_put_code"] == 4001
    assert funding[1]["amount"] is None and funding[1]["end_date"] is None


def test_aggregates_peer_reviews_per_organization():
    reviews = build_biosketch(fixture())["peer_reviews"]
    assert [x["organization"] for x in reviews] == [
        "Psychoneuroendocrinology",
        "Frontiers in Behavioral Neuroscience",
    ]
    assert reviews[0]["review_count"] == 2
    assert reviews[0]["last_completed"] == "2022-11-02"
    assert reviews[0]["review_type"] == "review"
    assert reviews[0]["role"] == "reviewer"
    assert reviews[0]["review_group_id"] == "issn:0306-4530"
    assert reviews[1]["review_count"] == 1
    assert reviews[1]["role"] == "editor"


def test_parses_affiliation_shaped_sections():
    bio = build_biosketch(fixture())
    assert bio["distinctions"][0]["role"] == "Young Investigator Award"
    assert bio["memberships"][0]["organization"] == "Society for Neuroscience"
    assert bio["services"][0]["department"] == "Data stewardship"
    assert bio["services"][0]["end_date"] == "2024-06"
    assert bio["qualifications"][0]["organization"] == "Université de Lausanne"
    assert bio["invited_positions"][0]["role"] == "Visiting researcher"


def test_parses_research_resources():
    resource = build_biosketch(fixture())["research_resources"][0]
    assert resource["title"] == "Longitudinal rodent behaviour imaging platform"
    assert resource["hosts"] == ["Institut de Génomique Fonctionnelle", "CNRS"]
    assert (resource["start_date"], resource["end_date"]) == ("2022-02", "2022-08")
    assert resource["source"]["id"] == "0000-0003-4820-7951"


def test_minimal_record_degrades_to_empty_lists():
    bio = build_biosketch({"orcid-identifier": {"path": "0000-0003-4820-7951"}})
    for key in (
        "employment", "education", "works", "fundings", "peer_reviews", "distinctions",
        "memberships", "services", "qualifications", "invited_positions", "research_resources",
    ):
        assert bio[key] == []
    assert bio["schema_version"] == "0.2.0"
    schema = json.loads((Path(__file__).parents[1] / "schema" / "biosketch.schema.json").read_text())
    Draft202012Validator(schema).validate(bio)
    assert "## Funding" not in render_markdown(bio)
    assert to_jsonld(bio)["@type"] == "Person"


def test_null_activity_sections_do_not_raise():
    record = {
        "orcid-identifier": {"path": "0000-0003-4820-7951"},
        "activities-summary": {
            "fundings": None,
            "peer-reviews": {"group": None},
            "memberships": {"affiliation-group": [{"summaries": None}]},
            "services": {"affiliation-group": [{"summaries": [{}]}]},
            "research-resources": {"group": [{"research-resource-summary": [{}]}]},
        },
    }
    bio = build_biosketch(record)
    assert bio["fundings"] == [] and bio["peer_reviews"] == [] and bio["memberships"] == []
    assert bio["services"][0]["organization"] is None
    assert bio["research_resources"][0]["hosts"] == []


def test_renderers_surface_new_sections():
    bio = build_biosketch(fixture())
    markdown = render_markdown(bio)
    assert "## Funding" in markdown
    assert "250000 EUR" in markdown
    assert "## Peer review" in markdown
    assert "Psychoneuroendocrinology — 2 reviews as reviewer" in markdown
    assert "## Distinctions" in markdown
    assert "## Memberships" in markdown
    assert "## Service" in markdown
    jsonld = to_jsonld(bio)
    assert jsonld["funding"][0]["@type"] == "MonetaryGrant"
    assert jsonld["funding"][0]["funder"]["name"] == "Agence Nationale de la Recherche"
    assert jsonld["funding"][0]["amount"] == {
        "@type": "MonetaryAmount", "value": "250000", "currency": "EUR",
    }
    assert jsonld["memberOf"] == [{"@type": "Organization", "name": "Society for Neuroscience"}]
    assert jsonld["award"] == ["Young Investigator Award, European Behavioural Pharmacology Society"]
