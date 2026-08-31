from __future__ import annotations

import json
from datetime import datetime, timezone

from orcid_biosketch.lint import CHECKS, TOTAL_WEIGHT, lint, render_report, to_badge

NOW = datetime(2026, 8, 31, tzinfo=timezone.utc)
ORCID = "0000-0003-4820-7951"
BIOGRAPHY = (
    "Behavioural neuroscientist working on reproducible preclinical research, home-cage "
    "monitoring and machine-actionable metadata. I build open tooling for experimental "
    "provenance and advise academic groups, CROs and infrastructures on making their data "
    "reusable, interoperable and honest about where each measurement came from."
)


def work(**overrides):
    base = {
        "title": "A study of something",
        "type": "journal-article",
        "publication_date": "2025-04-01",
        "journal": "Journal of Testing",
        "url": "",
        "identifiers": {"doi": "10.1/aaa"},
        "source": {"name": "Crossref", "id": "APP-CROSSREF"},
        "orcid_put_code": 1,
    }
    base.update(overrides)
    return base


def perfect_bio():
    return {
        "schema_version": "0.2.0",
        "person": {
            "name": "Damien Huzard",
            "orcid": ORCID,
            "orcid_url": f"https://orcid.org/{ORCID}",
            "biography": BIOGRAPHY,
            "keywords": ["neuroscience", "metadata", "reproducibility"],
            "urls": {"Personal website": "https://example.org"},
        },
        "employment": [{"organization": "Neuronautix", "role": "Lead Scientist"}],
        "education": [{"organization": "University of Testing", "role": "PhD"}],
        "works": [
            work(title="First paper", identifiers={"doi": "10.1/aaa"}, orcid_put_code=1),
            work(title="Second paper", identifiers={"doi": "10.1/bbb"}, orcid_put_code=2),
        ],
        "fundings": [{"title": "A grant", "organization": "ANR", "grant_number": "ANR-1"}],
        "provenance": {
            "primary_source": f"https://orcid.org/{ORCID}",
            "orcid_last_modified": int(datetime(2026, 6, 1, tzinfo=timezone.utc).timestamp() * 1000),
            "generated_at": "2026-06-01T00:00:00+00:00",
        },
    }


def poor_bio():
    return {
        "person": {
            "name": "Nobody",
            "orcid": ORCID,
            "biography": "",
            "keywords": [],
            "urls": {},
        },
        "employment": [],
        "education": [],
        "works": [
            work(title="", identifiers={}, publication_date=None, journal="",
                 source={"name": "Nobody", "id": ORCID}, orcid_put_code=10),
            work(title="Duplicated title", identifiers={"doi": "10.1/dup"},
                 source={"name": "Nobody", "id": ORCID}, orcid_put_code=11),
            work(title="Duplicated  Title!", identifiers={},
                 source={"name": "Nobody", "id": ORCID}, orcid_put_code=12),
            work(title="Same doi twice", identifiers={"doi": "10.1/DUP"},
                 source={"name": "Nobody", "id": ORCID}, orcid_put_code=13),
        ],
        "provenance": {
            "primary_source": f"https://orcid.org/{ORCID}",
            "orcid_last_modified": int(datetime(2022, 1, 1, tzinfo=timezone.utc).timestamp() * 1000),
            "generated_at": "2022-01-01T00:00:00+00:00",
        },
    }


def checks(result):
    return {finding["check"]: finding for finding in result["findings"]}


def test_perfect_record_scores_full_marks():
    result = lint(perfect_bio(), now=NOW)
    assert result["findings"] == []
    assert result["percentage"] == 100
    assert result["grade"] == "A+"
    # org_ids is not assessable while the contract carries no organisation identifiers.
    assert result["max_score"] == TOTAL_WEIGHT - 5
    assert result["score"] == result["max_score"]


def test_poor_record_triggers_every_check():
    result = lint(poor_bio(), now=NOW)
    found = checks(result)
    for expected in (
        "works.identifiers",
        "works.publication_date",
        "works.venue",
        "works.title",
        "works.self_asserted",
        "works.duplicates",
        "person.biography",
        "person.keywords",
        "person.urls",
        "affiliations.employment",
        "affiliations.education",
        "fundings",
        "provenance.freshness",
    ):
        assert expected in found, expected
    assert found["works.title"]["severity"] == "error"
    assert found["works.title"]["count"] == 1
    assert found["works.title"]["examples"] == ["(untitled) [10]"]
    assert found["person.biography"]["severity"] == "error"
    assert result["percentage"] < 40
    assert result["grade"] == "F"


def test_findings_carry_an_actionable_fix():
    result = lint(poor_bio(), now=NOW)
    for finding in result["findings"]:
        assert set(("check", "severity", "message", "fix", "count", "examples")) <= set(finding)
        assert finding["severity"] in {"error", "warning", "info"}
        assert len(finding["fix"]) > 40
        assert "ORCID" in finding["fix"]


def test_duplicate_detection_by_title_and_doi():
    finding = checks(lint(poor_bio(), now=NOW))["works.duplicates"]
    # Title match joins 11 and 12, DOI match joins 11 and 13: one group of three.
    assert finding["count"] == 2
    assert finding["examples"] == ["Duplicated title [11] x3"]


def test_self_assertion_detected_only_against_own_orcid():
    finding = checks(lint(poor_bio(), now=NOW))["works.self_asserted"]
    assert finding["count"] == 4
    assert finding["severity"] == "info"
    assert "works.self_asserted" not in checks(lint(perfect_bio(), now=NOW))


def test_stale_record_scored_by_age():
    bio = perfect_bio()
    bio["provenance"] = {"generated_at": "2024-01-01T00:00:00+00:00"}
    result = lint(bio, now=NOW)
    finding = checks(result)["provenance.freshness"]
    assert "days ago" in finding["message"]
    assert result["percentage"] < 100


def test_missing_timestamp_is_reported_not_crashed():
    bio = perfect_bio()
    bio["provenance"] = {}
    finding = checks(lint(bio, now=NOW))["provenance.freshness"]
    assert finding["severity"] == "info"


def test_empty_record_does_not_crash():
    result = lint({}, now=NOW)
    assert result["score"] == 0
    assert result["grade"] == "F"
    assert "works.missing" in checks(result)
    # Work-level checks are skipped rather than failed when there are no works.
    skipped = [c["check"] for c in result["checks"] if not c["applicable"]]
    assert "works.identifiers" in skipped
    assert render_report(result)


def test_junk_shaped_contract_does_not_crash():
    result = lint({"person": None, "works": ["nonsense", {"title": None}], "fundings": {}}, now=NOW)
    assert 0 <= result["percentage"] <= 100
    assert render_report(result)


def test_sections_added_later_light_up():
    bio = perfect_bio()
    assert "fundings" not in checks(lint(bio, now=NOW))
    del bio["fundings"]
    assert "fundings" in checks(lint(bio, now=NOW))

    bio = perfect_bio()
    bio["memberships"] = [{"organization": "Society", "ror": None}]
    finding = checks(lint(bio, now=NOW))["affiliations.org_ids"]
    assert finding["count"] == 1
    assert finding["examples"] == ["Society"]

    bio["memberships"] = [{"organization": "Society", "ror": "https://ror.org/012345678"}]
    assert "affiliations.org_ids" not in checks(lint(bio, now=NOW))


def test_org_id_check_reads_nested_organization_objects():
    bio = perfect_bio()
    bio["employment"] = [{"organization": {"name": "Neuronautix", "ror": ""}}]
    assert checks(lint(bio, now=NOW))["affiliations.org_ids"]["count"] == 1


def test_venue_check_ignores_types_without_a_venue():
    bio = perfect_bio()
    bio["works"] = [work(type="data-set", journal="", identifiers={"doi": "10.1/ccc"})]
    assert "works.venue" not in checks(lint(bio, now=NOW))
    assert [c for c in lint(bio, now=NOW)["checks"] if c["check"] == "works.venue"][0]["applicable"] is False


def test_rubric_weights_are_documented_and_total_one_hundred():
    assert TOTAL_WEIGHT == 100
    assert len(CHECKS) == 14
    docstring = __import__("orcid_biosketch.lint", fromlist=["lint"]).__doc__ or ""
    for name, weight, _ in CHECKS:
        assert f"`{name}`" in docstring
        assert f"| {weight:2d} " in docstring or f"|{weight:3d} " in docstring


def test_score_is_the_sum_of_the_documented_breakdown():
    result = lint(poor_bio(), now=NOW)
    assert result["score"] == round(sum(c["points"] for c in result["checks"]))
    assert result["max_score"] == round(sum(c["max_points"] for c in result["checks"]))


def test_findings_are_ordered_by_cost_then_severity():
    findings = lint(poor_bio(), now=NOW)["findings"]
    keys = [(-f["points_lost"], f["severity"], f["check"]) for f in findings]
    assert keys == sorted(keys, key=lambda k: (k[0], {"error": 0, "warning": 1, "info": 2}[k[1]], k[2]))


def test_deterministic_output():
    first = lint(poor_bio(), now=NOW)
    second = lint(poor_bio(), now=NOW)
    assert json.dumps(first, sort_keys=False) == json.dumps(second, sort_keys=False)
    assert render_report(first) == render_report(second)
    assert to_badge(first) == to_badge(second)


def test_report_is_plain_text_and_mentions_the_fixes():
    report = render_report(lint(poor_bio(), now=NOW))
    assert "\x1b[" not in report
    assert "ORCID record quality report" in report
    assert "Grade F" in report
    assert "works.identifiers" in report
    assert "Fix:" in report
    assert report.endswith("\n")
    assert max(len(line) for line in report.splitlines()) <= 78


def test_report_clips_long_example_titles():
    bio = poor_bio()
    bio["works"][0]["title"] = "T" * 300
    report = render_report(lint(bio, now=NOW))
    assert max(len(line) for line in report.splitlines()) <= 78
    assert "\u2026" in report


def test_report_of_a_perfect_record_says_so():
    assert "Nothing to fix" in render_report(lint(perfect_bio(), now=NOW))


def test_badge_is_valid_shields_endpoint_json():
    badge = to_badge(lint(perfect_bio(), now=NOW))
    assert badge == {
        "schemaVersion": 1,
        "label": "ORCID record",
        "message": "100% (A+)",
        "color": "brightgreen",
    }
    assert json.loads(json.dumps(badge)) == badge
    assert to_badge(lint(poor_bio(), now=NOW))["color"] == "red"
    assert to_badge(lint(perfect_bio(), now=NOW), label="record")["label"] == "record"


def test_grade_thresholds():
    grades = []
    bio = perfect_bio()
    for count, drop in enumerate([[], ["fundings"], ["fundings", "education"]]):
        candidate = perfect_bio()
        for key in drop:
            del candidate[key]
        grades.append(lint(candidate, now=NOW)["grade"])
    assert grades == ["A+", "A", "B"]
    assert lint(bio, now=NOW)["grade"] == "A+"
    assert lint({}, now=NOW)["grade"] == "F"
