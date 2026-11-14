"""Regression assertions for scientific claims and privacy wording (#55).

These guard the wording audited in communications/claims-privacy-audit.md:
shared DOI is not verified collaboration, an ORCID iD is not a verified
credential, local roles are not consented membership, funder exports are
drafts, feed observation time is not a publication date, and cloud Teams are
not advertised as available before a production verification.
"""
import importlib.util
import json
import re
from pathlib import Path

import pytest

from science_record_player.collaboration import collaboration_graph
from science_record_player.exporters import available_templates, render_template

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = json.loads((ROOT / "tests" / "fixture.json").read_text(encoding="utf-8"))


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _surfaces() -> list[Path]:
    """User-facing copy: hosted pages and scripts, docs, demo overlays and posts."""
    patterns = [
        "web/playground/*.html", "web/playground/*.js", "web/playground/*.webmanifest",
        "web/network/index.html", "web/network/app.js", "web/srp-*.js",
        "docs/source/*.md", "demo/*.mjs", "demo/README.md",
        "communications/launch-copy.md", "communications/video-storyboard.md", "README.md",
    ]
    files = sorted({p for pattern in patterns for p in ROOT.glob(pattern)})
    assert len(files) > 20
    return files


# Phrases that overclaim regardless of context.
FORBIDDEN = [
    r"DOIs? that prove",
    r"who (has|have) published together",
    r"New on ORCID",
    r"(?<!formerly “)Collaboration graph",
    r"no server-side code",
    r"never shared",
]
# Phrases allowed only when negated or quoted as a "do not say" example just before
# (e.g. "does not prove collaboration", the launch copy's “Fully private” list).
NEGATED_ONLY = [
    r"proves? (a |the )?collaboration",
    r"proof of (a )?collaboration",
    r"verified collaboration",
    r"proof of identity",
    r"fully private",
    r"verified (researcher|team|identity)s?\b",
    r"ORCID[- ](approved|endorsed|certified)",
    r"funder[- ]approved",
]
NEGATION = re.compile(r"\b(not|no|never|nor|without|avoid)\b|n't|“", re.IGNORECASE)


def _context(text: str, start: int, width: int) -> str:
    return text[max(0, start - width):start]


@pytest.mark.parametrize("pattern", FORBIDDEN)
def test_overclaiming_phrases_do_not_return(pattern):
    hits = [f"{path.relative_to(ROOT)}: …{text[max(0, m.start() - 40):m.end() + 20]}…"
            for path in _surfaces() for text in [_read(path)]
            for m in re.finditer(pattern, text, re.IGNORECASE)]
    assert not hits, "Overclaiming wording returned (see communications/claims-privacy-audit.md):\n" + "\n".join(hits)


@pytest.mark.parametrize("pattern", NEGATED_ONLY)
def test_collaboration_and_identity_claims_are_always_negated(pattern):
    hits = []
    for path in _surfaces():
        text = _read(path)
        for match in re.finditer(pattern, text, re.IGNORECASE):
            if not NEGATION.search(_context(text, match.start(), 45)):
                hits.append(f"{path.relative_to(ROOT)}: …{text[max(0, match.start() - 60):match.end() + 20]}…")
    assert not hits, "Unnegated claim:\n" + "\n".join(hits)


def test_group_view_states_the_matching_rule_and_shows_supporting_dois():
    html = _read(ROOT / "web/playground/group.html")
    script = _read(ROOT / "web/playground/group.js")
    description = re.search(r'<meta name="description" content="([^"]+)"', html).group(1)
    assert "list the same DOI" in description and "not verified collaboration" in description
    assert html.count("list the same DOI") >= 3  # description, lede, footer
    assert "not proof of collaboration" in html
    assert "Both public records list" in script and "not verified collaboration" in script
    assert "'Supporting DOI(s)'" in script and "e.outputs.flatMap" in script
    assert "'Shared-DOI graph': graphPanel" in script


def test_graph_basis_states_the_rule_and_its_limit():
    other = json.loads(json.dumps(FIXTURE))
    other["person"]["orcid"] = "0000-0002-1825-0097"
    basis = collaboration_graph([FIXTURE, other])["basis"]
    assert "both public records list the same DOI" in basis
    assert "not verified collaboration" in basis


@pytest.mark.parametrize("template", available_templates())
def test_funder_templates_are_labelled_drafts(template):
    text = render_template(FIXTURE, template)
    assert "not an official funder form" in text and "not a funder-approved submission" in text


def test_studio_repeats_the_funder_draft_disclaimer():
    studio = _read(ROOT / "web/playground/studio.js")
    assert "Not an official funder form or a funder-approved submission" in studio


def test_feed_separates_observation_from_publication_date():
    app = _read(ROOT / "web/network/app.js")
    assert "['new', 'Newly observed']" in app
    assert "It is not the publication date" in app
    assert "First seen by your refresh" in app and "Publication date:" in app
    digest = _read(ROOT / "web/playground/digest.js")
    assert "not its publication date" in digest


def test_teams_are_not_advertised_as_available():
    """Expected to fail once Teams are live: update copy, audit and checklist together."""
    team = _read(ROOT / "web/playground/team.html")
    assert "NOT YET ENABLED ON THE PUBLIC SITE" in team and "not confirmed active" in team
    assert "When Teams are activated" in team
    assert "does not verify your affiliations or credentials" in team
    assert "not enabled on this site yet" in _read(ROOT / "web/playground/team.js")
    assert "not yet enabled on the public site" in _read(ROOT / "web/playground/index.html")
    trust = _read(ROOT / "docs/source/trust.md")
    assert "**not available** on the hosted site until a successful live test and a security review" in trust
    readme = _read(ROOT / "README.md")
    assert "Not yet confirmed active on the public site" in readme


def test_privacy_wording_names_where_data_lives():
    trust = _read(ROOT / "docs/source/trust.md")
    assert "includes Contacts notes, tags and follow-ups" in trust
    assert "**no Contacts notes**" in trust
    assert "group name and public ORCID iDs only" in trust
    readme = _read(ROOT / "README.md")
    assert "both public records list the same DOI" in readme
    assert "not independently verified credentials" in readme
    assert "Funder-format exports are drafts" in readme


def test_built_site_carries_the_exact_disclaimer_on_every_page(tmp_path):
    spec = importlib.util.spec_from_file_location("build_site", ROOT / "scripts" / "build_site.py")
    build_site = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build_site)
    disclaimer = json.loads(_read(ROOT / "config/brand.json"))["disclaimer"]
    files = build_site.build(tmp_path / "site", client_id="")
    pages = [f for f in files if f.endswith(".html")]
    assert {"index.html", "network/index.html", "group/index.html", "team/index.html", "feedback/index.html"} <= set(pages)
    for page in pages:
        text = _read(tmp_path / "site" / page)
        assert disclaimer in text, page
        assert "ORCID® is a registered trademark of ORCID, Inc." in text, page
    config = json.loads(_read(tmp_path / "site" / "config.json"))
    if not (config.get("cloud") or {}).get("exchangeUrl"):
        assert "NOT YET ENABLED" in _read(tmp_path / "site" / "team" / "index.html")


def test_audit_and_release_checklist_gate_publication():
    audit = _read(ROOT / "communications/claims-privacy-audit.md")
    checklist = _read(ROOT / "communications/release-checklist.md")
    assert "NOT cleared for public promotion" in audit
    assert "#44" in audit and "no approval exists" in audit
    for heading in ("Privacy and availability matrix", "Launch decision", "before → after"):
        assert heading in audit
    assert "**Publication status: BLOCKED.**" in checklist
    for release in ("Release A", "Release B"):
        assert f"### Sign-off — {release}" in checklist
    for field in ("Deployment URL tested", "Commit SHA", "Date (UTC)", "Recording date"):
        assert field in checklist
    assert "Sample/fictional data is labelled" in checklist and "No unsupported feature is shown" in checklist
    # Nothing in either document may claim an ORCID approval or a production verification it lacks.
    for text in (audit, checklist):
        assert not re.search(r"ORCID (has )?(approved|endorsed|granted permission)", text)
    assert checklist.count("_not signed_") >= 3
