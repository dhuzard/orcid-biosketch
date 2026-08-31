import json
import re

import pytest
from orcid_biosketch.exporters import (
    available_templates,
    render_template,
    to_bibtex,
    to_csl_json,
    to_ris,
)


def fixture():
    """Inline biosketch contract sample; deliberately independent of tests/fixture.json."""
    return {
        "schema_version": "0.2.0",
        "person": {
            "name": "Damien Huzard",
            "given_names": "Damien",
            "family_name": "Huzard",
            "orcid": "0000-0003-4820-7951",
            "orcid_url": "https://orcid.org/0000-0003-4820-7951",
            "biography": "Behavioural neuroscience and research data.",
            "country": "FR",
            "keywords": ["neuroscience", "FAIR"],
            "urls": {"Personal website": "http://example.org"},
        },
        "employment": [
            {"organization": "Neuronautix", "role": "Founder", "start_date": "2023-01", "end_date": None},
            {"organization": "CNRS", "role": "Postdoc", "start_date": "2018", "end_date": "2022"},
        ],
        "education": [
            {"organization": "Université de Lyon", "role": "PhD", "start_date": "2012", "end_date": "2016"},
        ],
        "fundings": [
            {
                "title": "FAIR home-cage monitoring",
                "organization": "ANR",
                "start_date": "2024",
                "end_date": "2026",
                "amount": "250000",
                "currency": "EUR",
                "grant_number": "ANR-24-CE17",
                "identifiers": {"grant_number": "ANR-24-CE17"},
            }
        ],
        "peer_reviews": [{"organization": "eLife", "review_count": 3, "review_type": "review"}],
        "works": [
            {
                "title": "Data & metadata: 100% FAIR_workflows costing $5 {each}",
                "type": "journal-article",
                "publication_date": "2026-03-25",
                "journal": "Journal of Reproducible Science",
                "url": "",
                "identifiers": {"doi": "10.1234/abc.def"},
                "source": {"name": "Crossref", "id": None},
            },
            {
                "title": "Data sharing in preclinical research",
                "type": "book-chapter",
                "publication_date": "2026",
                "journal": "Handbook of Preclinical Methods",
                "url": "https://example.org/chapter",
                "identifiers": {"isbn": "9781234567897"},
                "source": {"name": "Damien Huzard", "id": "0000-0003-4820-7951"},
            },
            {
                "title": "A preprint about stress coping",
                "type": "preprint",
                "publication_date": None,
                "journal": "",
                "url": "",
                "identifiers": {},
                "source": {"name": "Damien Huzard", "id": None},
            },
            {
                "title": "Live Mouse Tracker analysis toolkit",
                "type": "software",
                "publication_date": "2021-06",
                "journal": "",
                "url": "https://zenodo.org/record/1",
                "identifiers": {"doi": "10.5281/ZENODO.1"},
                "source": {"name": "Zenodo", "id": None},
                "authors": [
                    {"family": "Huzard", "given": "Damien"},
                    {"name": "Chen Wang"},
                    {"name": "Rivière, Anne", "role": "editor"},
                ],
            },
        ],
        "provenance": {
            "primary_source": "https://orcid.org/0000-0003-4820-7951",
            "generated_at": "2026-08-30T09:00:00+00:00",
        },
    }


def parse_bibtex(text):
    """Strict-enough BibTeX reader: validates entry syntax and brace balance."""
    entries, pos = [], 0
    while pos < len(text):
        at = text.find("@", pos)
        if at < 0:
            assert text[pos:].strip() == "", f"trailing junk: {text[pos:]!r}"
            break
        head = re.compile(r"@(\w+)\{([^,\s]+),\s*").match(text, at)
        assert head, f"malformed entry header at {text[at:at + 40]!r}"
        pos, fields, depth = head.end(), {}, 1
        while True:
            field = re.compile(r"\s*(\w+)\s*=\s*\{").match(text, pos)
            assert field, f"malformed field at {text[pos:pos + 40]!r}"
            pos, start, depth = field.end(), field.end(), 1
            while depth:
                assert pos < len(text), "unbalanced braces in value"
                if text[pos] == "\\":
                    pos += 1
                elif text[pos] == "{":
                    depth += 1
                elif text[pos] == "}":
                    depth -= 1
                pos += 1
            fields[field.group(1)] = text[start:pos - 1]
            separator = re.compile(r"\s*(,|\})\s*").match(text, pos)
            assert separator, f"expected , or }} at {text[pos:pos + 40]!r}"
            pos = separator.end()
            if separator.group(1) == "}":
                break
        entries.append({"type": head.group(1), "key": head.group(2), "fields": fields})
    return entries


def parse_ris(text):
    records, current = [], None
    for line in text.splitlines():
        if not line.strip():
            continue
        match = re.match(r"^([A-Z][A-Z0-9])  - (.*)$", line)
        assert match, f"malformed RIS line: {line!r}"
        tag, value = match.group(1), match.group(2)
        if tag == "TY":
            current = {"TY": value}
        elif tag == "ER":
            records.append(current)
            current = None
        else:
            assert current is not None, "field outside a record"
            current.setdefault(tag, []).append(value)
    assert current is None, "record not terminated by ER"
    return records


def test_csl_json_shape_and_date_parts():
    items = to_csl_json(fixture())
    assert [item["type"] for item in items] == ["article-journal", "chapter", "article", "software"]
    assert items[0]["issued"] == {"date-parts": [[2026, 3, 25]]}
    assert items[1]["issued"] == {"date-parts": [[2026]]}
    assert "issued" not in items[2]
    assert items[3]["issued"] == {"date-parts": [[2021, 6]]}
    assert items[0]["DOI"] == "10.1234/abc.def"
    assert items[0]["URL"] == "https://doi.org/10.1234/abc.def"
    assert items[0]["container-title"] == "Journal of Reproducible Science"
    assert items[1]["ISBN"] == "9781234567897"
    assert {item["id"] for item in items} == set(item["id"] for item in items)
    assert json.loads(json.dumps(items)) == items


def test_csl_json_authors_light_up_when_the_contract_has_them():
    items = to_csl_json(fixture())
    assert "author" not in items[0]
    assert items[3]["author"] == [
        {"family": "Huzard", "given": "Damien"},
        {"family": "Wang", "given": "Chen"},
    ]
    assert items[3]["editor"] == [{"family": "Rivière", "given": "Anne"}]


def test_bibtex_keys_are_stable_and_collision_free():
    bio = fixture()
    entries = parse_bibtex(to_bibtex(bio))
    keys = [entry["key"] for entry in entries]
    assert keys[0] == "huzard_data_2026"
    assert keys[1] == "huzard_data_2026_2"
    assert keys[2] == "huzard_preprint_nodate"
    assert len(set(keys)) == len(keys)
    assert to_bibtex(bio) == to_bibtex(fixture())
    assert [item["id"] for item in to_csl_json(bio)] == keys


def test_bibtex_key_uses_the_first_author_when_present():
    bio = fixture()
    bio["works"][3]["authors"] = [{"family": "Wang", "given": "Chen"}]
    assert parse_bibtex(to_bibtex(bio))[3]["key"] == "wang_live_2021"


def test_bibtex_escapes_special_characters_and_protects_capitals():
    entry = parse_bibtex(to_bibtex(fixture()))[0]
    title = entry["fields"]["title"]
    assert title == r"Data \& metadata: 100\% {FAIR\_workflows} costing \$5 \{each\}"
    assert "#" not in title
    assert entry["fields"]["doi"] == "10.1234/abc.def"


def test_bibtex_escapes_the_remaining_special_characters():
    bio = {"person": {"family_name": "Doe"}, "works": [{"title": "C# ~ x^2 back\\slash", "type": "report"}]}
    entry = parse_bibtex(to_bibtex(bio))[0]
    assert entry["fields"]["title"] == (
        r"C\# \textasciitilde{} x\textasciicircum{}2 back\textbackslash{}slash"
    )


def test_bibtex_entry_types_and_fields():
    entries = parse_bibtex(to_bibtex(fixture()))
    assert [entry["type"] for entry in entries] == ["article", "incollection", "misc", "misc"]
    assert entries[0]["fields"]["journal"] == "Journal of Reproducible Science"
    assert entries[0]["fields"]["year"] == "2026"
    assert entries[0]["fields"]["month"] == "3"
    assert entries[1]["fields"]["booktitle"] == "Handbook of Preclinical Methods"
    assert "year" not in entries[2]["fields"]
    assert entries[3]["fields"]["author"] == "Huzard, Damien and Wang, Chen"
    assert entries[3]["fields"]["editor"] == "Rivière, Anne"


def test_bibtex_round_trips_through_bibtexparser_when_available():
    bibtexparser = pytest.importorskip("bibtexparser")
    database = bibtexparser.loads(to_bibtex(fixture()))
    assert len(database.entries) == 4


def test_ris_tags_and_mapping():
    records = parse_ris(to_ris(fixture()))
    assert [record["TY"] for record in records] == ["JOUR", "CHAP", "UNPB", "COMP"]
    assert records[0]["TI"] == ["Data & metadata: 100% FAIR_workflows costing $5 {each}"]
    assert records[0]["T2"] == ["Journal of Reproducible Science"]
    assert records[0]["PY"] == ["2026"]
    assert records[0]["DA"] == ["2026/3/25/"]
    assert records[0]["DO"] == ["10.1234/abc.def"]
    assert records[3]["AU"] == ["Huzard, Damien", "Wang, Chen"]
    assert records[3]["A2"] == ["Rivière, Anne"]
    assert "PY" not in records[2]
    assert to_ris(fixture()).endswith("ER  - \n")


def test_templates_are_discovered_and_rendered():
    assert {"nih", "erc"} <= set(available_templates())
    assert available_templates() == sorted(available_templates())
    rendered = render_template(fixture(), "nih")
    assert "Damien Huzard" in rendered
    assert "Founder, Neuronautix" in rendered
    assert "2018–2022 — Postdoc, CNRS" in rendered
    assert "ANR-24-CE17" in rendered
    assert "1. Data & metadata" in rendered
    assert "{{" not in rendered and "}}" not in rendered
    assert rendered == render_template(fixture(), "nih")
    assert render_template(fixture(), "nih.md") == rendered
    for name in available_templates():
        assert "{{" not in render_template(fixture(), name)


def test_template_loops_pick_up_sections_added_later():
    bio = fixture()
    assert "Honors and distinctions" not in render_template(bio, "nih")
    bio["distinctions"] = [{"organization": "Academy", "role": "Prize", "start_date": "2025", "end_date": None}]
    rendered = render_template(bio, "nih")
    assert "### Honors and distinctions" in rendered
    # A distinction with no end date is point-in-time, not ongoing.
    assert "2025 — Prize, Academy" in rendered
    assert "2025–present" not in rendered
    assert "eLife" in render_template(bio, "erc")


def test_unknown_template_is_reported_with_the_available_names():
    with pytest.raises(ValueError, match="nih"):
        render_template(fixture(), "does-not-exist")


def test_sparse_records_do_not_crash_any_exporter():
    sparse = {
        "person": {},
        "works": [
            {"title": "Untitled work"},
            {},
            {"title": "On the state of the art", "type": "mystery-type", "identifiers": None},
        ],
    }
    items = to_csl_json(sparse)
    assert [item["type"] for item in items] == ["document", "document", "document"]
    assert [item["id"] for item in items] == ["anon_untitled_nodate", "anon_untitled_nodate_2", "anon_state_nodate"]
    entries = parse_bibtex(to_bibtex(sparse))
    assert entries[1]["fields"]["note"] == "No metadata available"
    assert parse_ris(to_ris(sparse))[0]["TY"] == "GEN"
    for name in available_templates():
        assert render_template(sparse, name)
    assert to_bibtex({}) == "" and to_ris({}) == "" and to_csl_json({}) == []
