"""Tests for the playful outputs. Fixtures are inline and self-contained."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from orcid_biosketch.fun import (
    fortune,
    heatmap_svg,
    render_wrapped,
    trading_card_svg,
    wrapped,
)


def _work(title, date, journal="", type_="journal-article", doi=None, **extra):
    return {
        "title": title,
        "type": type_,
        "publication_date": date,
        "journal": journal,
        "url": "",
        "identifiers": {"doi": doi} if doi else {},
        **extra,
    }


# Hand-computable fixture. Dated outputs, ascending:
#   2015        Analytical Engines and Their Notes   Notes on Computing
#   2016-03     Stress Coping in Rodents             Journal of Behaviour
#   2016-07     Coping Strategies and Rodents        Journal of Behaviour
#   2019-03     Cardiac Regulation in Rodents        Heart Reports
#   2021-05     Metadata Standards for Behaviour     FAIR Data Reports
#   2021-05     Machine Actionable Metadata          FAIR Data Reports
#   2021-11     Home Cage Monitoring Metadata        Cage Monitoring Letters
# plus one undated output.
BIO = {
    "person": {
        "name": "Ada Rodent",
        "orcid": "0000-0002-1825-0097",
        "headline": "Behaviour and metadata",
        "keywords": ["behaviour", "metadata", "rodents"],
    },
    "employment": [{"organization": "Lab", "start_date": "2014-01", "end_date": None}],
    "education": [{"organization": "School", "start_date": "2009-09", "end_date": "2014-06"}],
    "works": [
        _work("Home Cage Monitoring Metadata", "2021-11", "Cage Monitoring Letters"),
        _work("Machine Actionable Metadata", "2021-05", "FAIR Data Reports", doi="10.1234/abc"),
        _work("Metadata Standards for Behaviour", "2021-05", "FAIR Data Reports"),
        _work("Cardiac Regulation in Rodents", "2019-03", "Heart Reports"),
        _work("Coping Strategies and Rodents", "2016-07", "Journal of Behaviour"),
        _work("Stress Coping in Rodents", "2016-03", "Journal of Behaviour"),
        _work("Analytical Engines and Their Notes", "2015", "Notes on Computing"),
        _work("Undated Preprint", None, "", "preprint"),
    ],
}

MESSY = {
    "person": {"name": "Ampersand & Angle <Lab>", "orcid": "0000-0001-0000-0000", "keywords": ["R&D <core>"]},
    "works": [
        _work('Tags & "quotes" <angles>', "2020-06", "Journal of & <Things>"),
        _work("Second & Work", "2020", ""),
    ],
}

EMPTY: dict = {}


def test_wrapped_defaults_to_latest_dated_year():
    data = wrapped(BIO)
    assert data["year"] == 2021
    assert data["output_count"] == 3
    assert data["totals"] == {"outputs": 8, "dated": 7, "undated": 1}


def test_wrapped_year_statistics_are_hand_checkable():
    data = wrapped(BIO, 2021)
    assert data["top_venue"] == {"name": "FAIR Data Reports", "count": 2}
    assert data["most_prolific_month"] == {"month": 5, "name": "May", "count": 2}
    assert data["first_time_venues"] == ["Cage Monitoring Letters", "FAIR Data Reports"]
    assert data["output_types"] == {"journal-article": 3}
    # Same-month outputs are ordered by title, so the result is stable.
    assert [o["title"] for o in data["outputs"]] == [
        "Machine Actionable Metadata",
        "Metadata Standards for Behaviour",
        "Home Cage Monitoring Metadata",
    ]


def test_wrapped_career_statistics():
    data = wrapped(BIO)
    assert data["busiest_year"] == {"year": 2021, "count": 3}
    assert data["career"] == {"first_output_year": 2015, "last_output_year": 2021, "span_years": 7}
    # 2016-07 -> 2019-03 is the widest interval: 32 months.
    assert data["longest_gap"] == {"months": 32, "from": "2016-07", "to": "2019-03"}


def test_wrapped_keyword_drift_uses_title_vocabulary():
    drift = wrapped(BIO)["keyword_drift"]
    assert drift["early_period"] == "2015-2016"
    assert drift["recent_period"] == "2021"
    assert "analytical" in drift["early_terms"]
    assert "metadata" not in drift["early_terms"]
    assert "metadata" in drift["recent_terms"]
    assert "metadata" in drift["emerged"]
    assert all(term not in drift["early_terms"] for term in drift["emerged"])


def test_wrapped_omits_statistics_it_cannot_compute():
    data = wrapped(BIO, 2018)
    assert data["output_count"] == 0
    assert data["outputs"] == []
    for key in ("top_venue", "most_prolific_month", "first_time_venues", "output_types"):
        assert key not in data
    assert data["nearest_outputs"]["before"]["date"] == "2016-07"
    assert data["nearest_outputs"]["after"]["date"] == "2019-03"


def test_wrapped_reports_undated_outputs_in_notes():
    notes = " ".join(wrapped(BIO)["notes"])
    assert "1 output(s) carry no publication date" in notes


def test_wrapped_first_time_coauthors_only_when_authors_asserted():
    assert "first_time_coauthors" not in wrapped(BIO)
    bio = {
        "works": [
            _work("Early", "2019-01", authors=["Kay Lin", "Ada Rodent"]),
            _work("Later", "2020-01", authors=[{"name": "Kay Lin"}, {"name": "Noor Haddad"}]),
        ]
    }
    assert wrapped(bio, 2020)["first_time_coauthors"] == ["Noor Haddad"]


def test_wrapped_handles_year_only_and_broken_dates():
    bio = {"works": [
        _work("Year only", "2019"),
        _work("Month only", "2019-03"),
        _work("Junk", "not-a-date"),
        _work("Impossible month", "2020-19"),
        _work("Missing", None),
        "not a dict",
    ]}
    data = wrapped(bio)
    assert data["year"] == 2020
    assert data["totals"] == {"outputs": 5, "dated": 3, "undated": 2}
    assert "most_prolific_month" not in data  # 2020 output has no usable month
    assert render_wrapped(data)


def test_empty_and_sparse_records_do_not_crash():
    for bio in (EMPTY, {"works": []}, {"works": [_work("Only one", "2022")]}):
        data = wrapped(bio)
        text = render_wrapped(data)
        assert text.endswith("\n")
        assert ET.fromstring(trading_card_svg(bio)) is not None
        assert ET.fromstring(heatmap_svg(bio)) is not None
        assert fortune(bio, seed=1)
    assert wrapped(EMPTY)["year"] is None
    assert wrapped(EMPTY)["output_count"] == 0


def test_render_wrapped_is_a_rectangular_card():
    text = render_wrapped(wrapped(BIO))
    widths = {len(line) for line in text.splitlines()}
    assert len(widths) == 1
    assert text.splitlines()[0].startswith("┌")
    assert "ORCID WRAPPED  2021" in text


def test_render_wrapped_states_no_opinion_about_a_sparse_year():
    text = render_wrapped(wrapped({"works": [_work("A", "2022-01"), _work("B", "2022-05")]}))
    assert "Outputs in 2022         2" in text
    for word in ("only", "just", "quiet", "slow", "productiv", "unfortunately"):
        assert word not in text.lower()


@pytest.mark.parametrize("render", [trading_card_svg, heatmap_svg])
def test_svg_is_well_formed(render):
    root = ET.fromstring(render(BIO))
    assert root.tag.endswith("svg")
    assert root.get("width") and root.get("height")


@pytest.mark.parametrize("render", [trading_card_svg, heatmap_svg])
def test_svg_escapes_record_data(render):
    svg = render(MESSY)
    root = ET.fromstring(svg)
    text = " ".join(node.text or "" for node in root.iter())
    assert "Ampersand & Angle <Lab>" in text
    assert "&amp;" in svg  # escaped on the wire, unescaped after parsing


def test_trading_card_uses_only_asserted_values():
    svg = trading_card_svg(BIO)
    text = " ".join(node.text or "" for node in ET.fromstring(svg).iter())
    assert "0000-0002-1825-0097" in text
    assert "Ada Rodent" in text
    assert "Behaviour and metadata" in text
    assert "8" in text  # output count
    assert any(keyword in text for keyword in BIO["person"]["keywords"])
    assert "Home Cage Monitoring Metadata" in text.replace("  ", " ")


def test_trading_card_special_ability_comes_from_the_record():
    bio = {"person": {"name": "N", "orcid": "0000-0002-1825-0097", "keywords": ["exactly one keyword"]}}
    text = " ".join(node.text or "" for node in ET.fromstring(trading_card_svg(bio)).iter())
    assert "exactly one keyword" in text
    no_keywords = {"person": {"name": "N", "orcid": "0000-0002-1825-0097"}}
    assert "SPECIAL ABILITY" not in trading_card_svg(no_keywords)


def test_heatmap_covers_every_year_and_labels_axes():
    svg = heatmap_svg(BIO)
    root = ET.fromstring(svg)
    text = [node.text or "" for node in root.iter()]
    for year in ("2015", "2016", "2019", "2021"):
        assert year in text
    for month in ("Jan", "Jun", "Dec"):
        assert month in text
    assert "n/d" in text  # the 2015 output records a year only
    assert "less" in text and "more" in text
    assert "prefers-color-scheme: dark" in svg


def test_heatmap_stays_bounded_for_a_long_career():
    works = [_work(f"Work {year}", f"{year}-0{1 + year % 9}") for year in range(1995, 2026)]
    root = ET.fromstring(heatmap_svg({"person": {"name": "Long Career"}, "works": works}))
    assert float(root.get("width")) < 400
    assert 700 < float(root.get("height")) < 800


def test_heatmap_without_dates_is_still_valid_svg():
    root = ET.fromstring(heatmap_svg({"works": [_work("No date", None)]}))
    text = " ".join(node.text or "" for node in root.iter())
    assert "No publication dates" in text


@pytest.mark.parametrize(
    "render", [lambda b: render_wrapped(wrapped(b)), trading_card_svg, heatmap_svg, lambda b: fortune(b, seed=5)]
)
def test_outputs_are_deterministic(render):
    assert render(BIO) == render(BIO)
    assert render(MESSY) == render(MESSY)


def test_fortune_is_stable_for_a_fixed_seed_and_quotes_a_real_title():
    first = fortune(BIO, seed=42)
    assert first == fortune(BIO, seed=42)
    normalized = " ".join(first.split())
    assert any(work["title"] in normalized for work in BIO["works"])
    assert "Ada Rodent" in normalized


def test_fortune_varies_across_seeds_and_reports_an_empty_record():
    picks = {" ".join(fortune(BIO, seed=seed).split()) for seed in range(20)}
    assert len(picks) > 1
    assert fortune(EMPTY) == "No works are recorded in this ORCID record.\n"


def test_fortune_includes_a_doi_when_the_record_has_one():
    bio = {"person": {"name": "N"}, "works": [_work("Only", "2020", doi="10.1234/abc")]}
    assert "https://doi.org/10.1234/abc" in fortune(bio, seed=0)
