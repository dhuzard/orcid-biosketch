"""Playful re-presentations of an ORCID record.

Every number and string emitted here is read back from the biosketch contract.
Nothing is invented, inferred, or scored: a statistic that cannot be computed
from the record is omitted rather than guessed.
"""

from __future__ import annotations

import base64
import random
import textwrap
from typing import Any

_MONTH_NAMES = (
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
)
_MONTH_ABBR = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")

_STOPWORDS = frozenset("""
about across after against among analysis approach based been before behind being
between both case cases data does during each effect effects evidence from
have having into its more most much near nested none other others over role
same some study studies such than that their them then there these this those
three through toward towards under upon used uses using very what when where
which while with within without work works your
""".split())

_AFFILIATION_KEYS = (
    "employment", "education", "employments", "educations", "fundings", "funding",
    "distinctions", "memberships", "services", "qualifications", "invited_positions",
    "research_resources",
)


# --- shared helpers -------------------------------------------------------

def _text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _esc(value: Any) -> str:
    """XML-escape any value coming from the record."""
    out = _text(value)
    for old, new in (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;"), ('"', "&quot;"), ("'", "&apos;")):
        out = out.replace(old, new)
    return out


def _ymd(date: Any) -> tuple[int | None, int | None]:
    """Parse a contract date string; tolerates ``2019``, ``2019-03``, ``2019-03-04``, ``None``."""
    if not isinstance(date, str):
        return None, None
    text = date.strip()
    if len(text) < 4 or not text[:4].isdigit():
        return None, None
    year = int(text[:4])
    month = None
    if len(text) >= 7 and text[4] in "-/" and text[5:7].isdigit():
        candidate = int(text[5:7])
        month = candidate if 1 <= candidate <= 12 else None
    return year, month


def _names(work: dict[str, Any]) -> list[str]:
    """Author names, when the record carries them; an empty list otherwise."""
    people = work.get("authors") or work.get("contributors") or []
    if not isinstance(people, list):
        return []
    names = []
    for person in people:
        if isinstance(person, str):
            name = _text(person)
        elif isinstance(person, dict):
            name = _text(person.get("name") or person.get("credit_name") or person.get("family_name"))
        else:
            name = ""
        if name:
            names.append(name)
    return names


def _outputs(bio: Any) -> list[dict[str, Any]]:
    """Normalise ``bio["works"]`` defensively; record order is preserved."""
    bio = bio if isinstance(bio, dict) else {}
    items = []
    for work in bio.get("works") or []:
        if not isinstance(work, dict):
            continue
        year, month = _ymd(work.get("publication_date"))
        identifiers = work.get("identifiers")
        identifiers = identifiers if isinstance(identifiers, dict) else {}
        items.append({
            "title": _text(work.get("title")),
            "date": _text(work.get("publication_date")) or None,
            "year": year,
            "month": month,
            "venue": _text(work.get("journal")),
            "type": _text(work.get("type")),
            "doi": _text(identifiers.get("doi")) or None,
            "url": _text(work.get("url")) or None,
            "authors": _names(work),
        })
    return items


def _order(output: dict[str, Any]) -> tuple[int, int, str]:
    return (output["year"] or 0, output["month"] or 0, output["title"])


def _person(bio: Any) -> dict[str, Any]:
    bio = bio if isinstance(bio, dict) else {}
    person = bio.get("person")
    return person if isinstance(person, dict) else {}


def _activity_years(bio: Any) -> tuple[int | None, int | None]:
    """Earliest and latest year asserted anywhere in the record."""
    bio = bio if isinstance(bio, dict) else {}
    years = [o["year"] for o in _outputs(bio) if o["year"]]
    for key in _AFFILIATION_KEYS:
        for item in bio.get(key) or []:
            if not isinstance(item, dict):
                continue
            for field in ("start_date", "end_date", "last_completed", "date"):
                year, _ = _ymd(item.get(field))
                if year:
                    years.append(year)
    return (min(years), max(years)) if years else (None, None)


def _counts(values: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return counts


def _terms(titles: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for title in titles:
        for raw in title.lower().replace("/", " ").replace("—", " ").split():
            token = "".join(ch for ch in raw if ch.isalnum() or ch == "-").strip("-")
            if len(token) < 4 or token.isdigit() or token in _STOPWORDS:
                continue
            counts[token] = counts.get(token, 0) + 1
    return counts


def _top_terms(counts: dict[str, int], limit: int = 5) -> list[str]:
    return [term for term, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]]


def _stable_index(key: str, modulo: int) -> int:
    """Deterministic across processes, unlike ``hash()``."""
    if modulo <= 0:
        return 0
    value = 2166136261
    for char in key or "-":
        value = ((value ^ ord(char)) * 16777619) & 0xFFFFFFFF
    return value % modulo


def _clip(text: str, width: int) -> str:
    text = _text(text)
    return text if len(text) <= width else text[: max(1, width - 3)].rstrip() + "..."


def _wrap(text: str, width: int, max_lines: int) -> list[str]:
    lines = textwrap.wrap(_text(text), width=width) or [""]
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = _clip(lines[-1] + " ...", width)
    return lines


# --- FUN-01: Academic Wrapped --------------------------------------------

def wrapped(bio: dict, year: int | None = None) -> dict:
    """Year-in-review statistics, every one of them read from the record.

    ``year`` defaults to the most recent year with a dated output, so the result
    never depends on the clock. Keys are omitted when the record cannot support
    them.
    """
    person = _person(bio)
    outputs = _outputs(bio)
    dated = sorted([o for o in outputs if o["year"]], key=_order)
    undated = [o for o in outputs if not o["year"]]

    if year is None:
        year = dated[-1]["year"] if dated else None
    else:
        try:
            year = int(year)
        except (TypeError, ValueError):
            year = None

    of_year = [o for o in dated if o["year"] == year] if year is not None else []
    notes: list[str] = []
    data: dict[str, Any] = {
        "person": {"name": _text(person.get("name")), "orcid": _text(person.get("orcid"))},
        "year": year,
        "output_count": len(of_year),
        "outputs": [
            {"title": o["title"], "date": o["date"], "venue": o["venue"], "type": o["type"]}
            for o in of_year
        ],
        "totals": {"outputs": len(outputs), "dated": len(dated), "undated": len(undated)},
    }

    types = _counts([o["type"] for o in of_year if o["type"]])
    if types:
        data["output_types"] = dict(sorted(types.items(), key=lambda kv: (-kv[1], kv[0])))

    venues = _counts([o["venue"] for o in of_year if o["venue"]])
    if venues:
        name, count = sorted(venues.items(), key=lambda kv: (-kv[1], kv[0]))[0]
        data["top_venue"] = {"name": name, "count": count}

    months = _counts([str(o["month"]) for o in of_year if o["month"]])
    if months:
        month, count = sorted(months.items(), key=lambda kv: (-kv[1], int(kv[0])))[0]
        data["most_prolific_month"] = {
            "month": int(month), "name": _MONTH_NAMES[int(month) - 1], "count": count,
        }
        missing = len([o for o in of_year if not o["month"]])
        if missing:
            notes.append(f"{missing} of this year's outputs record a year but no month.")

    if year is not None and of_year:
        earlier = {o["venue"] for o in dated if o["venue"] and o["year"] < year}
        first_time = sorted({o["venue"] for o in of_year if o["venue"] and o["venue"] not in earlier})
        if first_time:
            data["first_time_venues"] = first_time

    if year is not None and of_year and any(o["authors"] for o in outputs):
        own = _text(person.get("name")).lower()
        seen = {n.lower() for o in dated if o["year"] < year for n in o["authors"]}
        new = sorted({n for o in of_year for n in o["authors"] if n.lower() not in seen and n.lower() != own})
        if new:
            data["first_time_coauthors"] = new

    if len(dated) >= 2:
        gap = None
        for previous, current in zip(dated, dated[1:]):
            months_apart = (
                (current["year"] * 12 + (current["month"] or 1))
                - (previous["year"] * 12 + (previous["month"] or 1))
            )
            if gap is None or months_apart > gap["months"]:
                gap = {"months": months_apart, "from": previous["date"], "to": current["date"]}
        if gap:
            data["longest_gap"] = gap
            if any(o["month"] is None for o in dated):
                notes.append("Gaps are measured in months; year-only dates count as January.")

    if dated:
        by_year = _counts([str(o["year"]) for o in dated])
        busiest, count = sorted(by_year.items(), key=lambda kv: (-kv[1], -int(kv[0])))[0]
        data["busiest_year"] = {"year": int(busiest), "count": count}
        first_year, last_year = dated[0]["year"], dated[-1]["year"]
        data["career"] = {
            "first_output_year": first_year,
            "last_output_year": last_year,
            "span_years": last_year - first_year + 1,
        }

    if len(dated) >= 4:
        size = max(1, len(dated) // 3)
        early, recent = dated[:size], dated[-size:]
        early_terms = _top_terms(_terms([o["title"] for o in early]))
        recent_terms = _top_terms(_terms([o["title"] for o in recent]))
        if early_terms or recent_terms:
            data["keyword_drift"] = {
                "early_period": _period(early),
                "early_terms": early_terms,
                "recent_period": _period(recent),
                "recent_terms": recent_terms,
                "emerged": [t for t in recent_terms if t not in early_terms],
                "enduring": [t for t in recent_terms if t in early_terms],
            }

    if year is not None and not of_year and dated:
        nearest: dict[str, Any] = {}
        before = [o for o in dated if o["year"] < year]
        after = [o for o in dated if o["year"] > year]
        if before:
            nearest["before"] = {"title": before[-1]["title"], "date": before[-1]["date"]}
        if after:
            nearest["after"] = {"title": after[0]["title"], "date": after[0]["date"]}
        if nearest:
            data["nearest_outputs"] = nearest

    if undated:
        notes.append(f"{len(undated)} output(s) carry no publication date and are not placed on the timeline.")
    if notes:
        data["notes"] = notes
    return data


def _period(outputs: list[dict[str, Any]]) -> str:
    years = [o["year"] for o in outputs if o["year"]]
    if not years:
        return ""
    return str(years[0]) if years[0] == years[-1] else f"{years[0]}-{years[-1]}"


_CARD_WIDTH = 62


def render_wrapped(data: dict) -> str:
    """Render :func:`wrapped` output as a terminal card."""
    data = data if isinstance(data, dict) else {}
    person = data.get("person") if isinstance(data.get("person"), dict) else {}
    year = data.get("year")
    totals = data.get("totals") if isinstance(data.get("totals"), dict) else {}

    lines = [_rule("top")]
    heading = f"ORCID WRAPPED  {year}" if year is not None else "ORCID WRAPPED"
    lines.append(_row(heading))
    identity = " - ".join(x for x in (_text(person.get("name")), _text(person.get("orcid"))) if x)
    if identity:
        lines.append(_row(identity))
    lines.append(_rule("mid"))

    label = f"Outputs in {year}" if year is not None else "Outputs"
    lines.append(_pair(label, str(data.get("output_count", 0))))
    if "output_types" in data:
        kinds = ", ".join(f"{k} ({v})" for k, v in data["output_types"].items())
        lines.extend(_pair_wrapped("Kinds", kinds))
    if "top_venue" in data:
        venue = data["top_venue"]
        lines.extend(_pair_wrapped("Most-used venue", f"{venue['name']} ({venue['count']})"))
    if "most_prolific_month" in data:
        month = data["most_prolific_month"]
        lines.append(_pair("Busiest month", f"{month['name']} ({month['count']})"))
    if "first_time_venues" in data:
        lines.extend(_pair_wrapped("First time here", ", ".join(data["first_time_venues"])))
    if "first_time_coauthors" in data:
        lines.extend(_pair_wrapped("First time together", ", ".join(data["first_time_coauthors"])))
    if "nearest_outputs" in data:
        nearest = data["nearest_outputs"]
        for key, prefix in (("before", "Closest before"), ("after", "Closest after")):
            if key in nearest:
                item = nearest[key]
                lines.extend(_pair_wrapped(prefix, f"{item['date'] or ''} {item['title']}".strip()))

    career = data.get("career") if isinstance(data.get("career"), dict) else None
    gap = data.get("longest_gap") if isinstance(data.get("longest_gap"), dict) else None
    busiest = data.get("busiest_year") if isinstance(data.get("busiest_year"), dict) else None
    if career or gap or busiest:
        lines.append(_rule("mid"))
    if career:
        span = f"{career['first_output_year']}-{career['last_output_year']} ({career['span_years']} years)"
        lines.append(_pair("Dated outputs span", span))
    if busiest:
        lines.append(_pair("Year with most outputs", f"{busiest['year']} ({busiest['count']})"))
    if gap:
        between = " to ".join(x for x in (gap.get("from"), gap.get("to")) if x)
        lines.extend(_pair_wrapped("Longest gap", f"{gap['months']} months ({between})"))
    if totals.get("outputs"):
        lines.append(_pair("Outputs in the record", str(totals["outputs"])))

    drift = data.get("keyword_drift") if isinstance(data.get("keyword_drift"), dict) else None
    if drift:
        lines.append(_rule("mid"))
        lines.extend(_pair_wrapped(f"Titles {drift['early_period']}", ", ".join(drift["early_terms"]) or "-"))
        lines.extend(_pair_wrapped(f"Titles {drift['recent_period']}", ", ".join(drift["recent_terms"]) or "-"))

    outputs = data.get("outputs") or []
    if outputs:
        lines.append(_rule("mid"))
        lines.append(_row(f"Outputs of {year}" if year is not None else "Outputs"))
        for item in outputs:
            stamp = (item.get("date") or "")[:7]
            for index, chunk in enumerate(_wrap(item.get("title") or "", _CARD_WIDTH - 15, 2)):
                prefix = f"{stamp:<8}" if index == 0 else " " * 8
                lines.append(_row(f"  {prefix} {chunk}"))

    notes = [n for n in (data.get("notes") or []) if _text(n)]
    if notes:
        lines.append(_rule("mid"))
        for note in notes:
            for index, chunk in enumerate(_wrap(note, _CARD_WIDTH - 6, 3)):
                lines.append(_row(("- " if index == 0 else "  ") + chunk))
    lines.append(_rule("mid"))
    lines.append(_row("Every figure above is read from the ORCID record."))
    lines.append(_rule("bottom"))
    return "\n".join(lines) + "\n"


def _rule(kind: str) -> str:
    left, right = {"top": ("┌", "┐"), "mid": ("├", "┤"), "bottom": ("└", "┘")}[kind]
    return left + "─" * (_CARD_WIDTH - 2) + right


def _row(text: str = "") -> str:
    body = _clip(text, _CARD_WIDTH - 4) if len(text) > _CARD_WIDTH - 4 else text
    return "│ " + body.ljust(_CARD_WIDTH - 4) + " │"


def _pair(label: str, value: str) -> str:
    return _row(f"{_clip(label, 24):<24}{_clip(value, _CARD_WIDTH - 28)}")


def _pair_wrapped(label: str, value: str) -> list[str]:
    width = _CARD_WIDTH - 28
    rows = []
    for index, chunk in enumerate(_wrap(value, width, 2)):
        head = f"{_clip(label, 24):<24}" if index == 0 else " " * 24
        rows.append(_row(head + chunk))
    return rows


# --- FUN-02: trading card -------------------------------------------------

def trading_card_svg(bio: dict, qr_png: bytes | None = None) -> str:
    """A printable, self-contained trading card built only from asserted fields."""
    if qr_png is not None and not qr_png.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("The trading-card QR asset must be a PNG file")
    qr_data = base64.b64encode(qr_png).decode("ascii") if qr_png else None
    person = _person(bio)
    outputs = _outputs(bio)
    name = _text(person.get("name")) or "Unnamed record"
    orcid = _text(person.get("orcid"))
    headline = _text(person.get("headline"))
    first_year, last_year = _activity_years(bio)
    keywords = [_text(k) for k in (person.get("keywords") or []) if _text(k)]
    recent = sorted(outputs, key=_order, reverse=True)[:3]
    types = _counts([o["type"] for o in outputs if o["type"]])

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="320" height="440" viewBox="0 0 320 440" '
        'role="img" aria-label="ORCID trading card">',
        '<title>' + _esc(f"{name} - ORCID trading card") + '</title>',
        '<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#1b3b5f"/><stop offset="1" stop-color="#0d1f33"/>'
        '</linearGradient></defs>',
        '<style>'
        'text{font-family:Helvetica,Arial,sans-serif}'
        '.n{fill:#f6f4ee;font-size:17px;font-weight:bold}'
        '.h{fill:#c8d6e5;font-size:9.5px}'
        '.lbl{fill:#7b8b9c;font-size:7.5px;letter-spacing:1.2px}'
        '.val{fill:#f6f4ee;font-size:15px;font-weight:bold}'
        '.vals{fill:#f6f4ee;font-size:10.5px;font-weight:bold}'
        '.body{fill:#e7e5dd;font-size:9px}'
        '.foot{fill:#93a3b4;font-size:7.5px}'
        '.hp{fill:#ffd27d;font-size:15px;font-weight:bold}'
        '</style>',
        '<rect x="0" y="0" width="320" height="440" rx="14" fill="url(#sky)"/>',
        '<rect x="6" y="6" width="308" height="428" rx="11" fill="none" stroke="#ffd27d" stroke-width="2"/>',
    ]

    y = 40
    y_name_last = y
    for index, line in enumerate(_wrap(name, 22, 2)):
        parts.append(f'<text class="n" x="20" y="{y + index * 19}">{_esc(line)}</text>')
        y_name_last = y + index * 19
    y = y_name_last + 22
    if first_year and last_year:
        span = last_year - first_year + 1
        parts.append(f'<text class="hp" x="300" y="40" text-anchor="end">{span} HP</text>')
        parts.append(
            f'<text class="foot" x="300" y="52" text-anchor="end">'
            f'{_esc(f"years asserted {first_year}-{last_year}")}</text>'
        )
    if headline:
        for line in _wrap(headline, 46, 2):
            parts.append(f'<text class="h" x="20" y="{y}">{_esc(line)}</text>')
            y += 12
    y += 6

    parts.append(f'<rect x="20" y="{y}" width="280" height="86" rx="6" fill="#0a1826" stroke="#2b4763"/>')
    pattern_columns = 8 if qr_data else 12
    for cell in range(pattern_columns * 4):
        column, row = cell % pattern_columns, cell // pattern_columns
        digit = _stable_index(f"{orcid or name}:{cell}", 10)
        radius = 1.5 + digit * 0.32
        cx, cy = 34 + column * 23, y + 18 + row * 21
        parts.append(
            f'<circle cx="{cx}" cy="{cy}" r="{radius:.2f}" fill="#4f9ad1" opacity="{0.18 + digit * 0.07:.2f}"/>'
        )
    if qr_data:
        parts.append(f'<text class="lbl" x="32" y="{y + 33}">SCAN MY ORCID</text>')
        parts.append(f'<text class="h" x="32" y="{y + 50}">Open the public record</text>')
        parts.append(f'<rect x="214" y="{y + 4}" width="82" height="78" rx="4" fill="#fff"/>')
        parts.append(
            f'<image x="218" y="{y + 8}" width="74" height="70" preserveAspectRatio="xMidYMid meet" '
            f'style="image-rendering:pixelated" href="data:image/png;base64,{qr_data}"/>'
        )
    y += 100

    stats = [("OUTPUTS", str(len(outputs)), "val")]
    if first_year and last_year:
        stats.append(("YEARS ACTIVE", str(last_year - first_year + 1), "val"))
    if types:
        stats.append(("MOST COMMON", sorted(types.items(), key=lambda kv: (-kv[1], kv[0]))[0][0], "vals"))
    for index, (label, value, style) in enumerate(stats):
        x = 20 + index * (280 // max(1, len(stats)))
        parts.append(f'<text class="lbl" x="{x}" y="{y}">{_esc(label)}</text>')
        parts.append(f'<text class="{style}" x="{x}" y="{y + 16}">{_esc(_clip(value, 17))}</text>')
    y += 34

    if keywords:
        ability = keywords[_stable_index(orcid or name, len(keywords))]
        parts.append(f'<rect x="20" y="{y}" width="280" height="50" rx="6" fill="#12263a" stroke="#2b4763"/>')
        parts.append(f'<text class="lbl" x="32" y="{y + 16}">SPECIAL ABILITY</text>')
        parts.append(f'<text class="val" x="32" y="{y + 33}">{_esc(_clip(ability, 30))}</text>')
        parts.append(f'<text class="foot" x="32" y="{y + 44}">listed as a research keyword on this record</text>')
        y += 62

    if recent:
        parts.append(f'<text class="lbl" x="20" y="{y}">RECENT OUTPUTS</text>')
        y += 14
        for item in recent:
            stamp = (item["date"] or "")[:4] or "----"
            lines = _wrap(item["title"], 44, 2)
            head = _esc(stamp + "  " + lines[0])
            parts.append(f'<text class="body" x="20" y="{y}">{head}</text>')
            y += 11
            for extra in lines[1:]:
                parts.append(f'<text class="body" x="46" y="{y}">{_esc(extra)}</text>')
                y += 11
            y += 3

    footer = f"ORCID {orcid}" if orcid else "no ORCID iD in this record"
    parts.append(f'<text class="foot" x="20" y="422">{_esc(footer)}</text>')
    parts.append('<text class="foot" x="300" y="422" text-anchor="end">every stat is an ORCID assertion</text>')
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


# --- FUN-03: publication heatmap -----------------------------------------

_CELL = 18
_STEP = 21


def heatmap_svg(bio: dict) -> str:
    """Months as cells, years as rows, intensity by output count."""
    person = _person(bio)
    outputs = _outputs(bio)
    dated = [o for o in outputs if o["year"]]
    name = _text(person.get("name"))
    undated = len(outputs) - len(dated)
    no_month = len([o for o in dated if not o["month"]])

    grid: dict[tuple[int, int], int] = {}
    for output in dated:
        key = (output["year"], output["month"] or 0)
        grid[key] = grid.get(key, 0) + 1
    observed_years = sorted({o["year"] for o in dated})
    years = list(range(observed_years[0], observed_years[-1] + 1)) if observed_years else []
    columns = list(range(1, 13)) + ([0] if no_month else [])
    peak = max(grid.values()) if grid else 0

    left, top = 52, 62
    width = left + len(columns) * _STEP + 16 if columns else 320
    height = top + max(1, len(years)) * _STEP + (76 if no_month else 62)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="Publication activity heatmap">',
        '<title>' + _esc(f"Publication activity{' - ' + name if name else ''}") + '</title>',
        '<style>'
        'text{font-family:Helvetica,Arial,sans-serif}'
        '.bg{fill:#fbfaf7;stroke:#dedcd4}'
        '.ttl{fill:#26251f;font-size:12px;font-weight:bold}'
        '.mut{fill:#6f6e66;font-size:8.5px}'
        '.ax{fill:#4a4942;font-size:8px}'
        '.c0{fill:#e8e7e0}.c1{fill:#c9e6d3}.c2{fill:#8ed3ab}.c3{fill:#4aae7d}.c4{fill:#1d7a4f}'
        '@media (prefers-color-scheme: dark){'
        '.bg{fill:#14171a;stroke:#2c3238}'
        '.ttl{fill:#eceae3}.mut{fill:#9a9a92}.ax{fill:#c3c2ba}'
        '.c0{fill:#232830}.c1{fill:#1f4a35}.c2{fill:#2a7049}.c3{fill:#3a9a63}.c4{fill:#59c186}'
        '}'
        '</style>',
        f'<rect class="bg" x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="8"/>',
        f'<text class="ttl" x="16" y="24">{_esc("Publication activity" + (f" - {name}" if name else ""))}</text>',
    ]
    summary = f"{len(dated)} dated output(s)"
    if years:
        summary += f", {years[0]}-{years[-1]}"
    if undated:
        summary += f"; {undated} without a date"
    parts.append(f'<text class="mut" x="16" y="38">{_esc(summary)}</text>')

    if not years:
        parts.append('<text class="mut" x="16" y="62">No publication dates are recorded in this record.</text>')
        parts.append('</svg>')
        return "\n".join(parts) + "\n"

    for index, column in enumerate(columns):
        label = _MONTH_ABBR[column - 1] if column else "n/d"
        parts.append(
            f'<text class="ax" x="{left + index * _STEP + _CELL / 2}" y="{top - 6}" '
            f'text-anchor="middle">{label}</text>'
        )
    for row, year in enumerate(years):
        cy = top + row * _STEP
        parts.append(f'<text class="ax" x="{left - 8}" y="{cy + 13}" text-anchor="end">{year}</text>')
        for index, column in enumerate(columns):
            count = grid.get((year, column), 0)
            level = 0 if not count else min(4, 1 + (count * 4 - 1) // max(1, peak) if peak else 1)
            cx = left + index * _STEP
            month = _MONTH_NAMES[column - 1] if column else "no month recorded"
            parts.append(
                f'<rect class="c{level}" x="{cx}" y="{cy}" width="{_CELL}" height="{_CELL}" rx="3">'
                f'<title>{_esc(f"{year} {month}: {count} output(s)")}</title></rect>'
            )

    legend_y = top + len(years) * _STEP + 20
    parts.append(f'<text class="mut" x="16" y="{legend_y + 13}">less</text>')
    for level in range(5):
        parts.append(
            f'<rect class="c{level}" x="{48 + level * 16}" y="{legend_y + 3}" width="12" height="12" rx="2"/>'
        )
    parts.append(f'<text class="mut" x="{48 + 5 * 16 + 4}" y="{legend_y + 13}">more</text>')
    notes = [f"one cell = one month; darkest = {peak} output(s) in a month"]
    if no_month:
        notes.append('"n/d" = a year recorded without a month')
    for index, note in enumerate(notes):
        parts.append(f'<text class="mut" x="16" y="{legend_y + 30 + index * 13}">{_esc(note)}</text>')
    parts.append('</svg>')
    return "\n".join(parts) + "\n"


# --- FUN-06: fortune ------------------------------------------------------

def fortune(bio: dict, seed: int | None = None) -> str:
    """One of the researcher's own titles, formatted for a shell startup file."""
    person = _person(bio)
    titled = [o for o in _outputs(bio) if o["title"]]
    if not titled:
        return "No works are recorded in this ORCID record.\n"

    chooser = random.Random(seed) if seed is not None else random.Random()
    pick = titled[chooser.randrange(len(titled))]
    lines = textwrap.wrap(pick["title"], width=68, initial_indent="  ", subsequent_indent="  ")
    credit = [x for x in (_text(person.get("name")), (pick["date"] or "")[:4]) if x]
    trailer = "    -- " + ", ".join(credit) if credit else "    --"
    link = f"https://doi.org/{pick['doi']}" if pick["doi"] else (pick["url"] or "")
    if link:
        trailer += f"  {link}"
    return "\n".join(lines + [trailer]) + "\n"
