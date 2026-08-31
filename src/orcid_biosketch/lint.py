"""ORCID record quality report.

Scores a biosketch contract (see ``core.build_biosketch``) against a fixed,
weighted rubric and returns findings that tell the researcher what to change in
the ORCID user interface. Nothing here fetches, infers or rewrites a
credential: every finding is a statement about what the record does or does not
already assert.

Rubric
------

Fourteen independent checks, 100 points in total. A check that cannot be
assessed (its input section is absent from the contract) is *not applicable*:
it scores nothing and is removed from ``max_score`` as well, so the percentage
always reflects only what the record could be judged on.

| check                     | weight | scoring                                     |
|---------------------------|--------|---------------------------------------------|
| `works.identifiers`       | 15     | proportional to works with any external id  |
| `works.publication_date`  | 10     | proportional to works with a date           |
| `works.self_asserted`     |  8     | proportional to works asserted by others    |
| `works.duplicates`        |  7     | proportional to works outside duplicate sets|
| `works.venue`             |  5     | proportional to venue-bearing works with one|
| `works.title`             |  5     | proportional to works with a title          |
| `person.biography`        | 10     | 300+ chars full, 120+ half, 1+ quarter, 0   |
| `person.keywords`         |  6     | 3+ full, 1-2 half, 0                        |
| `person.urls`             |  4     | 1+ full, 0                                  |
| `affiliations.employment` |  8     | 1+ full, 0                                  |
| `affiliations.education`  |  5     | 1+ full, 0                                  |
| `affiliations.org_ids`    |  5     | proportional to affiliations with a ROR/id  |
| `fundings`                |  8     | 1+ full, 0                                  |
| `provenance.freshness`    |  4     | <12 months full, <24 months half, older 0   |

Proportional checks award ``weight * passing / assessed``. Per-check points are
rounded to two decimals, then ``score`` and ``percentage`` are the totals
rounded to the nearest integer. The same contract therefore always produces the
same numbers, and ``result["checks"]`` shows each check's contribution.

Grades are cut from the percentage: A+ >= 95, A >= 90, B >= 80, C >= 70,
D >= 60, F below 60.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}

GRADE_THRESHOLDS: list[tuple[int, str]] = [(95, "A+"), (90, "A"), (80, "B"), (70, "C"), (60, "D"), (0, "F")]
GRADE_COLORS = {
    "A+": "brightgreen",
    "A": "brightgreen",
    "B": "green",
    "C": "yellowgreen",
    "D": "yellow",
    "F": "red",
}

# Affiliation-shaped sections of the contract. Sections added later (KF-01)
# are picked up automatically by the organisation-identifier check.
AFFILIATION_SECTIONS = (
    "employment",
    "education",
    "distinctions",
    "memberships",
    "services",
    "qualifications",
    "invited_positions",
)

# Keys under which a disambiguated organisation identifier may appear.
ORG_ID_KEYS = (
    "ror",
    "organization_id",
    "organization_identifier",
    "disambiguated_organization",
    "disambiguated_id",
)

# Work types for which a journal / venue is expected. Works with no recorded
# type are assumed venue-bearing; datasets, software and similar are not.
VENUE_TYPES = {
    "journal-article",
    "conference-paper",
    "conference-abstract",
    "book",
    "book-chapter",
    "book-review",
    "review",
    "magazine-article",
    "newspaper-article",
    "dissertation-thesis",
    "translation",
    "",
}

BIOGRAPHY_FULL = 300
BIOGRAPHY_SHORT = 120
KEYWORDS_FULL = 3
STALE_DAYS = 365
VERY_STALE_DAYS = 730
EXAMPLE_LIMIT = 3


def _works(bio: dict[str, Any]) -> list[dict[str, Any]]:
    works = bio.get("works")
    return [w for w in works if isinstance(w, dict)] if isinstance(works, list) else []


def _section(bio: dict[str, Any], name: str) -> list[dict[str, Any]]:
    items = bio.get(name)
    return [x for x in items if isinstance(x, dict)] if isinstance(items, list) else []


def _person(bio: dict[str, Any]) -> dict[str, Any]:
    person = bio.get("person")
    return person if isinstance(person, dict) else {}


def _text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _identifiers(work: dict[str, Any]) -> dict[str, Any]:
    identifiers = work.get("identifiers")
    return identifiers if isinstance(identifiers, dict) else {}


def _doi(work: dict[str, Any]) -> str:
    return _text(_identifiers(work).get("doi")).lower()


def _source_id(node: dict[str, Any]) -> str:
    source = node.get("source")
    return _text(source.get("id")) if isinstance(source, dict) else ""


def _label(work: dict[str, Any]) -> str:
    title = _text(work.get("title")) or "(untitled)"
    put_code = work.get("orcid_put_code")
    return f"{title} [{put_code}]" if put_code else title


def _examples(works: list[dict[str, Any]]) -> list[str]:
    return [_label(w) for w in works[:EXAMPLE_LIMIT]]


def _normalized_title(work: dict[str, Any]) -> str:
    return re.sub(r"[^a-z0-9]+", " ", _text(work.get("title")).lower()).strip()


def _org_identifier(item: dict[str, Any]) -> tuple[bool, bool]:
    """Return (identifier field present, identifier has a value)."""
    candidates: list[tuple[str, Any]] = [(k, v) for k, v in item.items() if k in ORG_ID_KEYS]
    org = item.get("organization")
    if isinstance(org, dict):
        candidates.extend((k, v) for k, v in org.items() if k in ORG_ID_KEYS)
    return bool(candidates), any(_text(v) if not isinstance(v, dict) else v for _, v in candidates)


def _affiliations(bio: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for name in AFFILIATION_SECTIONS for item in _section(bio, name)]


def _record_age(bio: dict[str, Any], now: datetime) -> timedelta | None:
    provenance = bio.get("provenance")
    provenance = provenance if isinstance(provenance, dict) else {}
    stamp = provenance.get("orcid_last_modified")
    moment: datetime | None = None
    if isinstance(stamp, (int, float)) and stamp > 0:
        moment = datetime.fromtimestamp(stamp / 1000, timezone.utc)
    else:
        generated = _text(provenance.get("generated_at"))
        if generated:
            try:
                moment = datetime.fromisoformat(generated.replace("Z", "+00:00"))
            except ValueError:
                moment = None
    if moment is None:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return now - moment


def _finding(
    check: str,
    severity: str,
    message: str,
    fix: str,
    count: int,
    examples: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "check": check,
        "severity": severity,
        "message": message,
        "fix": fix,
        "count": count,
        "examples": list(examples or []),
    }


def _result(
    weight: float,
    ratio: float | None,
    finding: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """A check outcome. ``ratio`` of None marks the check not applicable."""
    if ratio is None:
        return {"applicable": False, "points": 0.0, "max_points": 0.0, "finding": finding}
    ratio = max(0.0, min(1.0, ratio))
    return {
        "applicable": True,
        "points": round(weight * ratio, 2),
        "max_points": float(weight),
        "finding": finding if ratio < 1.0 else None,
    }


def _check_identifiers(bio: dict[str, Any], now: datetime) -> dict[str, Any]:
    works = _works(bio)
    if not works:
        return _result(15, None)
    failing = [w for w in works if not any(_text(v) for v in _identifiers(w).values())]
    return _result(
        15,
        1 - len(failing) / len(works),
        _finding(
            "works.identifiers",
            "error",
            f"{len(failing)} of {len(works)} works carry no DOI or other external identifier, "
            "so they cannot be matched to the published literature.",
            "In ORCID, open each work and add an external identifier (DOI preferred, else "
            "PMID, arXiv, ISBN or Handle). Easier still: delete the manual entry and re-import "
            "the work from Crossref Metadata Search or Europe PMC via Add works > Search & link, "
            "which fills the identifier in for you.",
            len(failing),
            _examples(failing),
        ),
    )


def _check_publication_date(bio: dict[str, Any], now: datetime) -> dict[str, Any]:
    works = _works(bio)
    if not works:
        return _result(10, None)
    failing = [w for w in works if not _text(w.get("publication_date"))]
    return _result(
        10,
        1 - len(failing) / len(works),
        _finding(
            "works.publication_date",
            "warning",
            f"{len(failing)} of {len(works)} works have no publication date, so they sort last "
            "in every chronological output and are invisible to any date filter.",
            "In ORCID, edit each work and set at least the publication year under "
            "Publication date. Year alone is enough; month and day are optional.",
            len(failing),
            _examples(failing),
        ),
    )


def _check_venue(bio: dict[str, Any], now: datetime) -> dict[str, Any]:
    works = [w for w in _works(bio) if _text(w.get("type")).lower() in VENUE_TYPES]
    if not works:
        return _result(5, None)
    failing = [w for w in works if not _text(w.get("journal"))]
    return _result(
        5,
        1 - len(failing) / len(works),
        _finding(
            "works.venue",
            "warning",
            f"{len(failing)} of {len(works)} works that should name a venue have no journal, "
            "conference or publisher recorded.",
            "In ORCID, edit each work and fill Journal title with the journal, conference "
            "proceedings or book in which it appeared.",
            len(failing),
            _examples(failing),
        ),
    )


def _check_title(bio: dict[str, Any], now: datetime) -> dict[str, Any]:
    works = _works(bio)
    if not works:
        return _result(5, None)
    failing = [w for w in works if not _text(w.get("title"))]
    return _result(
        5,
        1 - len(failing) / len(works),
        _finding(
            "works.title",
            "error",
            f"{len(failing)} of {len(works)} works have an empty title and are unusable in any "
            "citation, export or web listing.",
            "In ORCID, find each work by its put-code under Works and either type the correct "
            "title or delete the entry and re-import it from a search-and-link wizard.",
            len(failing),
            _examples(failing),
        ),
    )


def _check_self_asserted(bio: dict[str, Any], now: datetime) -> dict[str, Any]:
    works = _works(bio)
    orcid = _text(_person(bio).get("orcid"))
    if not works or not orcid:
        return _result(8, None)
    failing = [w for w in works if _source_id(w) == orcid]
    return _result(
        8,
        1 - len(failing) / len(works),
        _finding(
            "works.self_asserted",
            "info",
            f"{len(failing)} of {len(works)} works are asserted only by you, not by a publisher "
            "or an institution, so a reader has nothing but your own word for them.",
            "In ORCID, grant permission to a trusted party under Account settings > Trusted "
            "organizations, then use Add works > Search & link (Crossref, DataCite, Scopus, "
            "Europe PMC) so the same works arrive again asserted by the source. Third-party "
            "assertions do not replace yours, they sit alongside them in the same work group.",
            len(failing),
            _examples(failing),
        ),
    )


def _duplicate_groups(works: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """Group works that share a DOI or a normalised title.

    Union rather than bucketing, so the common case — a manual entry plus a
    publisher import of the same paper, only one of which carries the DOI —
    lands in a single group.
    """
    parent = list(range(len(works)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    seen: dict[str, int] = {}
    for index, work in enumerate(works):
        keys = [f"doi:{_doi(work)}"] if _doi(work) else []
        if _normalized_title(work):
            keys.append(f"title:{_normalized_title(work)}")
        for key in keys:
            roots = sorted({find(seen.setdefault(key, index)), find(index)})
            parent[roots[-1]] = roots[0]
    groups: dict[int, list[dict[str, Any]]] = {}
    for index, work in enumerate(works):
        groups.setdefault(find(index), []).append(work)
    return [items for _, items in sorted(groups.items()) if len(items) > 1]


def _check_duplicates(bio: dict[str, Any], now: datetime) -> dict[str, Any]:
    works = _works(bio)
    if not works:
        return _result(7, None)
    groups = _duplicate_groups(works)
    redundant = sum(len(items) - 1 for items in groups)
    examples = [f"{_label(items[0])} x{len(items)}" for items in groups[:EXAMPLE_LIMIT]]
    return _result(
        7,
        1 - redundant / len(works),
        _finding(
            "works.duplicates",
            "warning",
            f"{len(groups)} probable duplicate work groups ({redundant} redundant entries): the "
            "same DOI or the same title appears more than once.",
            "In ORCID, open Works, select the duplicated entries and use Combine works to merge "
            "them into a single group; only delete a copy when it is genuinely the same output "
            "recorded twice.",
            redundant,
            examples,
        ),
    )


def _check_biography(bio: dict[str, Any], now: datetime) -> dict[str, Any]:
    text = _text(_person(bio).get("biography"))
    ratio = 1.0 if len(text) >= BIOGRAPHY_FULL else 0.5 if len(text) >= BIOGRAPHY_SHORT else 0.25 if text else 0.0
    message = (
        f"The biography is {len(text)} characters, too short to say what you work on."
        if text
        else "The record has no biography, so every generated profile starts with a blank space."
    )
    return _result(
        10,
        ratio,
        _finding(
            "person.biography",
            "warning" if text else "error",
            message,
            "In ORCID, open Biography on your record and write a few sentences (aim for 300 "
            "characters or more) covering your field, your current focus and your affiliation. "
            "Set its visibility to Everyone or it will not appear in public outputs.",
            1,
        ),
    )


def _check_keywords(bio: dict[str, Any], now: datetime) -> dict[str, Any]:
    keywords = [k for k in (_person(bio).get("keywords") or []) if _text(k)]
    ratio = 1.0 if len(keywords) >= KEYWORDS_FULL else 0.5 if keywords else 0.0
    return _result(
        6,
        ratio,
        _finding(
            "person.keywords",
            "warning",
            f"Only {len(keywords)} keyword(s) recorded; keywords are how reviewers, editors and "
            "search tools find you by expertise.",
            "In ORCID, use Keywords > Add keyword and add at least three terms describing your "
            "field, methods and organisms or systems. Keep them the words a colleague would "
            "actually search for.",
            1,
            keywords[:EXAMPLE_LIMIT],
        ),
    )


def _check_urls(bio: dict[str, Any], now: datetime) -> dict[str, Any]:
    urls = _person(bio).get("urls")
    count = len([v for v in urls.values() if _text(v)]) if isinstance(urls, dict) else 0
    return _result(
        4,
        1.0 if count else 0.0,
        _finding(
            "person.urls",
            "info",
            "No researcher URLs, so the record does not link to your lab page, personal site or "
            "other profiles.",
            "In ORCID, use Websites & social links > Add link to add your institutional page, "
            "personal website, or Google Scholar / GitHub profile, each with a short label.",
            1,
        ),
    )


def _affiliation_check(section: str, weight: int, severity: str, label: str, fix: str) -> Callable[..., dict[str, Any]]:
    def check(bio: dict[str, Any], now: datetime) -> dict[str, Any]:
        items = _section(bio, section)
        return _result(
            weight,
            1.0 if items else 0.0,
            _finding(
                f"affiliations.{section}",
                severity,
                f"No {label} entries: the record cannot show where you work or trained.",
                fix,
                1,
            ),
        )

    return check


_check_employment = _affiliation_check(
    "employment",
    8,
    "error",
    "employment",
    "In ORCID, use Employment > Add employment and enter your current position, picking the "
    "organisation from the suggestion list so it links to a ROR/Ringgold identifier.",
)

_check_education = _affiliation_check(
    "education",
    5,
    "warning",
    "education or qualification",
    "In ORCID, use Education and qualifications > Add education and add at least your highest "
    "degree, again picking the institution from the suggestion list.",
)


def _check_fundings(bio: dict[str, Any], now: datetime) -> dict[str, Any]:
    items = _section(bio, "fundings")
    return _result(
        8,
        1.0 if items else 0.0,
        _finding(
            "fundings",
            "warning",
            "No funding recorded. Grants are the part of a record funders and hiring panels "
            "look for first, and an ORCID record without them reads as a bare publication list.",
            "In ORCID, use Funding > Add funding > Search & link to import awards through the "
            "DimensionsWizard funding registry, or add them manually with funder, grant number, "
            "amount and dates.",
            1,
        ),
    )


def _check_org_ids(bio: dict[str, Any], now: datetime) -> dict[str, Any]:
    items = _affiliations(bio)
    assessable = [item for item in items if _org_identifier(item)[0]]
    if not assessable:
        return _result(5, None)
    failing = [item for item in assessable if not _org_identifier(item)[1]]
    examples = [_text(item.get("organization")) or "(unnamed organisation)" for item in failing[:EXAMPLE_LIMIT]]
    return _result(
        5,
        1 - len(failing) / len(assessable),
        _finding(
            "affiliations.org_ids",
            "warning",
            f"{len(failing)} of {len(assessable)} affiliations name an organisation with no ROR "
            "or other disambiguated identifier, so they cannot be resolved automatically.",
            "In ORCID, edit each affiliation and retype the organisation name, choosing an entry "
            "from the drop-down suggestions rather than free text; the suggestion carries the "
            "ROR / Ringgold / GRID identifier with it.",
            len(failing),
            examples,
        ),
    )


def _check_freshness(bio: dict[str, Any], now: datetime) -> dict[str, Any]:
    age = _record_age(bio, now)
    if age is None:
        return _result(
            4,
            0.0,
            _finding(
                "provenance.freshness",
                "info",
                "The record carries no last-modified timestamp, so its freshness cannot be "
                "established.",
                "Re-generate the biosketch from a live ORCID fetch so provenance carries "
                "orcid_last_modified; if the record itself is stale, update it in ORCID first.",
                1,
            ),
        )
    days = age.days
    ratio = 1.0 if days < STALE_DAYS else 0.5 if days < VERY_STALE_DAYS else 0.0
    return _result(
        4,
        ratio,
        _finding(
            "provenance.freshness",
            "warning",
            f"The record was last modified {days} days ago; anything published since is missing.",
            "Sign in to ORCID and add the outputs, positions and grants from the past year. "
            "Turning on Add works > Search & link permissions for Crossref and DataCite keeps "
            "this current without further effort.",
            1,
        ),
    )


# Declaration order fixes the order of the per-check breakdown.
CHECKS: tuple[tuple[str, int, Callable[[dict[str, Any], datetime], dict[str, Any]]], ...] = (
    ("works.identifiers", 15, _check_identifiers),
    ("works.publication_date", 10, _check_publication_date),
    ("works.venue", 5, _check_venue),
    ("works.title", 5, _check_title),
    ("works.self_asserted", 8, _check_self_asserted),
    ("works.duplicates", 7, _check_duplicates),
    ("person.biography", 10, _check_biography),
    ("person.keywords", 6, _check_keywords),
    ("person.urls", 4, _check_urls),
    ("affiliations.employment", 8, _check_employment),
    ("affiliations.education", 5, _check_education),
    ("affiliations.org_ids", 5, _check_org_ids),
    ("fundings", 8, _check_fundings),
    ("provenance.freshness", 4, _check_freshness),
)

TOTAL_WEIGHT = sum(weight for _, weight, _ in CHECKS)


def _grade(percentage: int) -> str:
    for threshold, grade in GRADE_THRESHOLDS:
        if percentage >= threshold:
            return grade
    return "F"


def lint(bio: dict[str, Any], *, now: datetime | None = None) -> dict[str, Any]:
    """Score a biosketch contract and report what to fix.

    Returns ``{"score", "max_score", "percentage", "grade", "findings",
    "checks", "subject"}``. Every field of ``bio`` is read defensively, so a
    partial or empty contract yields findings rather than an exception.
    """
    moment = now or datetime.now(timezone.utc)
    breakdown: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    earned = 0.0
    available = 0.0
    for name, weight, check in CHECKS:
        outcome = check(bio, moment)
        earned += outcome["points"]
        available += outcome["max_points"]
        breakdown.append({
            "check": name,
            "weight": weight,
            "points": outcome["points"],
            "max_points": outcome["max_points"],
            "applicable": outcome["applicable"],
        })
        if outcome["finding"] is not None:
            finding = dict(outcome["finding"])
            finding["weight"] = weight
            finding["points_lost"] = round(outcome["max_points"] - outcome["points"], 2)
            findings.append(finding)

    if not _works(bio):
        findings.append(_finding(
            "works.missing",
            "error",
            "The record contains no works at all, so every work-level check was skipped.",
            "In ORCID, use Add works > Search & link and import your outputs from Crossref, "
            "DataCite, Scopus or Europe PMC. Manual entry is the last resort.",
            0,
        ) | {"weight": 0, "points_lost": 0.0})

    findings.sort(key=lambda f: (-f["points_lost"], SEVERITY_ORDER.get(f["severity"], 9), f["check"]))
    percentage = int(round(100 * earned / available)) if available else 0
    person = _person(bio)
    return {
        "score": int(round(earned)),
        "max_score": int(round(available)),
        "percentage": percentage,
        "grade": _grade(percentage),
        "findings": findings,
        "checks": breakdown,
        "subject": {
            "name": _text(person.get("name")),
            "orcid": _text(person.get("orcid")),
        },
    }


def _bar(points: float, maximum: float, width: int = 12) -> str:
    if maximum <= 0:
        return "-" * width
    filled = int(round(width * points / maximum))
    return "#" * filled + "." * (width - filled)


def _wrap(text: str, width: int, indent: str) -> list[str]:
    lines: list[str] = []
    current = ""
    for word in text.split():
        candidate = f"{current} {word}".strip()
        if len(candidate) > width and current:
            lines.append(indent + current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(indent + current)
    return lines


def _clip(text: str, width: int) -> str:
    return text if len(text) <= width else text[: width - 1].rstrip() + "\u2026"


def render_report(result: dict[str, Any]) -> str:
    """Render a lint result as a plain-text terminal report."""
    subject = result.get("subject") or {}
    header = " — ".join(filter(None, [subject.get("name"), subject.get("orcid")]))
    out: list[str] = ["ORCID record quality report"]
    if header:
        out.append(header)
    out.append("=" * 72)
    out.append(
        f"Score {result.get('score', 0)}/{result.get('max_score', 0)} "
        f"({result.get('percentage', 0)}%)   Grade {result.get('grade', 'F')}"
    )
    out.append("")
    out.append("Rubric")
    out.append("-" * 72)
    for entry in result.get("checks", []):
        if entry.get("applicable"):
            score = f"{entry['points']:5.2f} / {entry['max_points']:5.2f}"
            bar = _bar(entry["points"], entry["max_points"])
        else:
            score = "  n/a         "
            bar = "-" * 12
        out.append(f"  {entry['check']:<26} {score}  {bar}")
    out.append("")

    findings = result.get("findings", [])
    out.append(f"Findings ({len(findings)})")
    out.append("-" * 72)
    if not findings:
        out.append("  Nothing to fix. This record is complete against every check.")
    for finding in findings:
        lost = finding.get("points_lost", 0)
        cost = f" (-{lost:g} pts)" if lost else ""
        out.append(f"  [{finding['severity']}] {finding['check']}  x{finding['count']}{cost}")
        out.extend(_wrap(finding["message"], 66, "    "))
        out.extend(_wrap(f"Fix: {finding['fix']}", 66, "    "))
        for example in finding.get("examples", []):
            out.append(f"      - {_clip(example, 64)}")
        out.append("")
    out.append("Scoring rubric and thresholds: orcid_biosketch/lint.py")
    return "\n".join(out).rstrip() + "\n"


def to_badge(result: dict[str, Any], label: str = "ORCID record") -> dict[str, Any]:
    """Shields.io endpoint JSON, coloured by grade."""
    grade = result.get("grade", "F")
    return {
        "schemaVersion": 1,
        "label": label,
        "message": f"{result.get('percentage', 0)}% ({grade})",
        "color": GRADE_COLORS.get(grade, "lightgrey"),
    }
