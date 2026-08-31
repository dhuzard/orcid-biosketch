"""Citation and funder-format exporters.

Every exporter is a pure function of the biosketch contract: no network, no
file IO except reading the template files shipped as package data. Output is
deterministic — the same biosketch always renders byte-identical text.

Template syntax (see ``templates/``), deliberately tiny so that a new funder
format is a contributed data file rather than a code change:

* ``{{ person.name }}``      — dotted lookup, missing values render empty
* ``{{ title | upper }}``    — filters: ``upper``, ``lower``, ``title``,
  ``trim``, ``year``
* ``{{?works}}…{{/?works}}``  — render the body once, only if the section exists
  and is non-empty (use it to hide a heading whose section is empty)
* ``{{#works limit=5}}…{{/works}}`` — repeat the block for each item of a list
  section of the contract; inside, keys resolve against the item first, then
  the root. Every item also gets ``index``, ``index0`` and ``period``; works
  additionally get ``year``, ``doi``, ``doi_url``, ``venue``, ``authors_text``
  and ``citation``. Unknown or empty sections render nothing.
"""

from __future__ import annotations

import re
import unicodedata
from importlib import resources
from pathlib import Path
from typing import Any

CSL_TYPES = {
    "book": "book",
    "book-chapter": "chapter",
    "book-review": "review-book",
    "conference-abstract": "paper-conference",
    "conference-paper": "paper-conference",
    "conference-poster": "speech",
    "data-set": "dataset",
    "dataset": "dataset",
    "dictionary-entry": "entry-dictionary",
    "dissertation": "thesis",
    "dissertation-thesis": "thesis",
    "edited-book": "book",
    "encyclopedia-entry": "entry-encyclopedia",
    "journal-article": "article-journal",
    "journal-issue": "periodical",
    "lecture-speech": "speech",
    "magazine-article": "article-magazine",
    "manual": "book",
    "newsletter-article": "article-newspaper",
    "newspaper-article": "article-newspaper",
    "online-resource": "webpage",
    "patent": "patent",
    "preprint": "article",
    "report": "report",
    "research-tool": "software",
    "software": "software",
    "standards-and-policy": "standard",
    "supervised-student-publication": "article-journal",
    "technical-standard": "standard",
    "translation": "book",
    "website": "webpage",
    "working-paper": "manuscript",
}
CSL_FALLBACK = "document"

BIBTEX_TYPES = {
    "article-journal": "article",
    "article-magazine": "article",
    "article-newspaper": "article",
    "article": "misc",
    "book": "book",
    "chapter": "incollection",
    "entry-dictionary": "incollection",
    "entry-encyclopedia": "incollection",
    "manuscript": "unpublished",
    "paper-conference": "inproceedings",
    "patent": "misc",
    "periodical": "article",
    "report": "techreport",
    "review-book": "article",
    "thesis": "phdthesis",
}
BIBTEX_FALLBACK = "misc"

RIS_TYPES = {
    "article-journal": "JOUR",
    "article-magazine": "MGZN",
    "article-newspaper": "NEWS",
    "article": "UNPB",
    "book": "BOOK",
    "chapter": "CHAP",
    "dataset": "DATA",
    "entry-dictionary": "CHAP",
    "entry-encyclopedia": "CHAP",
    "manuscript": "UNPB",
    "paper-conference": "CPAPER",
    "patent": "PAT",
    "periodical": "JOUR",
    "report": "RPRT",
    "software": "COMP",
    "speech": "CONF",
    "standard": "STAND",
    "thesis": "THES",
    "webpage": "ELEC",
}
RIS_FALLBACK = "GEN"

_BIBTEX_ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}
_KEY_STOPWORDS = {
    "a", "an", "and", "as", "at", "by", "for", "from", "in", "of", "on", "or",
    "the", "to", "with",
}


def _text(value: Any) -> str:
    return " ".join(str(value).split()) if value not in (None, "") else ""


def _works(bio: dict[str, Any]) -> list[dict[str, Any]]:
    return [w for w in bio.get("works") or [] if isinstance(w, dict)]


def _identifier(work: dict[str, Any], *names: str) -> str:
    identifiers = work.get("identifiers") or {}
    if not isinstance(identifiers, dict):
        return ""
    for name in names:
        for key, value in identifiers.items():
            if str(key).lower() == name and value:
                return _text(value)
    return ""


def _split_name(name: str) -> tuple[str, str]:
    name = _text(name)
    if "," in name:
        family, _, given = name.partition(",")
        return _text(family), _text(given)
    parts = name.split(" ")
    return (parts[-1], " ".join(parts[:-1])) if len(parts) > 1 else (name, "")


def _person(entry: Any) -> dict[str, str] | None:
    """Normalize one author/contributor entry; shape is not yet in the contract."""
    if isinstance(entry, str):
        family, given = _split_name(entry)
    elif isinstance(entry, dict):
        family = _text(entry.get("family") or entry.get("family_name") or entry.get("surname"))
        given = _text(entry.get("given") or entry.get("given_names") or entry.get("first_name"))
        if not family:
            family, given = _split_name(
                entry.get("name") or entry.get("credit_name") or entry.get("credit-name") or ""
            )
    else:
        return None
    if not family and not given:
        return None
    role = ""
    if isinstance(entry, dict):
        role = _text(entry.get("role") or entry.get("contributor_role")).lower()
    return {"family": family, "given": given, "role": role}


def _contributors(work: dict[str, Any]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """(authors, editors) — empty until the contract carries contributor lists."""
    raw = work.get("authors") or work.get("contributors") or []
    if not isinstance(raw, list):
        return [], []
    people = [p for p in (_person(entry) for entry in raw) if p]
    editors = [p for p in people if "editor" in p["role"]]
    authors = [p for p in people if "editor" not in p["role"]]
    return authors, editors


def _name_text(person: dict[str, str]) -> str:
    return f"{person['family']}, {person['given']}" if person["given"] else person["family"]


def _date_parts(work: dict[str, Any]) -> list[int]:
    parts: list[int] = []
    for chunk in _text(work.get("publication_date")).split("-"):
        if not chunk.isdigit():
            break
        parts.append(int(chunk))
    return parts[:3]


def _year(work: dict[str, Any]) -> str:
    parts = _date_parts(work)
    return str(parts[0]) if parts else ""


def _venue(work: dict[str, Any]) -> str:
    return _text(work.get("journal") or work.get("container_title") or work.get("venue"))


def _ascii(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]", "", folded.lower())


def _key_stem(bio: dict[str, Any], work: dict[str, Any]) -> str:
    authors, _ = _contributors(work)
    family = authors[0]["family"] if authors else _text((bio.get("person") or {}).get("family_name"))
    words = [w for w in re.split(r"\W+", _text(work.get("title"))) if w]
    first = next((w for w in words if w.lower() not in _KEY_STOPWORDS), words[0] if words else "")
    stem = "_".join(filter(None, [_ascii(family) or "anon", _ascii(first) or "untitled", _year(work) or "nodate"]))
    return stem


def _citation_keys(bio: dict[str, Any]) -> list[str]:
    """Stable keys in contract order; collisions get a deterministic suffix."""
    keys: list[str] = []
    seen: dict[str, int] = {}
    for work in _works(bio):
        stem = _key_stem(bio, work)
        seen[stem] = seen.get(stem, 0) + 1
        keys.append(stem if seen[stem] == 1 else f"{stem}_{seen[stem]}")
    return keys


def to_csl_json(bio: dict[str, Any]) -> list[dict[str, Any]]:
    """Render the works of a biosketch as CSL-JSON items."""
    items = []
    for key, work in zip(_citation_keys(bio), _works(bio)):
        authors, editors = _contributors(work)
        item: dict[str, Any] = {
            "id": key,
            "type": CSL_TYPES.get(_text(work.get("type")), CSL_FALLBACK),
        }
        if _text(work.get("title")):
            item["title"] = _text(work.get("title"))
        if authors:
            item["author"] = [{"family": a["family"], "given": a["given"]} for a in authors]
        if editors:
            item["editor"] = [{"family": e["family"], "given": e["given"]} for e in editors]
        if _venue(work):
            item["container-title"] = _venue(work)
        parts = _date_parts(work)
        if parts:
            item["issued"] = {"date-parts": [parts]}
        doi = _identifier(work, "doi")
        if doi:
            item["DOI"] = doi
        for name, field in (("isbn", "ISBN"), ("issn", "ISSN"), ("pmid", "PMID"), ("pmc", "PMCID")):
            value = _identifier(work, name)
            if value:
                item[field] = value
        url = _text(work.get("url")) or (f"https://doi.org/{doi}" if doi else "")
        if url:
            item["URL"] = url
        note = _text((work.get("source") or {}).get("name")) if isinstance(work.get("source"), dict) else ""
        if note:
            item["source"] = note
        items.append(item)
    return items


def _bibtex_escape(text: Any) -> str:
    return "".join(_BIBTEX_ESCAPES.get(char, char) for char in _text(text))


def _bibtex_title(title: Any) -> str:
    """Escape, and brace-protect tokens whose capitalisation must survive."""
    out = []
    for token in _text(title).split(" "):
        core = token.strip(".,;:()[]?!\"'")
        escaped = _bibtex_escape(token)
        if len(core) > 1 and any(char.isupper() for char in core[1:]):
            escaped = "{" + escaped + "}"
        out.append(escaped)
    return " ".join(out)


def to_bibtex(bio: dict[str, Any]) -> str:
    """Render the works of a biosketch as a BibTeX database."""
    entries = []
    for key, work in zip(_citation_keys(bio), _works(bio)):
        csl_type = CSL_TYPES.get(_text(work.get("type")), CSL_FALLBACK)
        doi = _identifier(work, "doi")
        authors, editors = _contributors(work)
        fields: list[tuple[str, str]] = []
        if authors:
            fields.append(("author", " and ".join(_bibtex_escape(_name_text(a)) for a in authors)))
        if editors:
            fields.append(("editor", " and ".join(_bibtex_escape(_name_text(e)) for e in editors)))
        if _text(work.get("title")):
            fields.append(("title", _bibtex_title(work.get("title"))))
        venue = _venue(work)
        if venue:
            field = "journal" if csl_type in ("article-journal", "article-magazine", "periodical") else "booktitle"
            fields.append((field, _bibtex_escape(venue)))
        if _year(work):
            fields.append(("year", _year(work)))
        parts = _date_parts(work)
        if len(parts) > 1:
            fields.append(("month", f"{parts[1]:d}"))
        if doi:
            fields.append(("doi", _bibtex_escape(doi)))
        for name, field in (("isbn", "isbn"), ("issn", "issn")):
            value = _identifier(work, name)
            if value:
                fields.append((field, _bibtex_escape(value)))
        url = _text(work.get("url")) or (f"https://doi.org/{doi}" if doi else "")
        if url:
            fields.append(("url", _bibtex_escape(url)))
        if not fields:
            fields.append(("note", _bibtex_escape("No metadata available")))
        width = max(len(name) for name, _ in fields)
        body = ",\n".join(f"  {name.ljust(width)} = {{{value}}}" for name, value in fields)
        entries.append(f"@{BIBTEX_TYPES.get(csl_type, BIBTEX_FALLBACK)}{{{key},\n{body}\n}}\n")
    return "\n".join(entries)


def _ris_line(tag: str, value: Any) -> str:
    return f"{tag}  - {_text(value)}\n"


def to_ris(bio: dict[str, Any]) -> str:
    """Render the works of a biosketch as an RIS database."""
    records = []
    for key, work in zip(_citation_keys(bio), _works(bio)):
        csl_type = CSL_TYPES.get(_text(work.get("type")), CSL_FALLBACK)
        authors, editors = _contributors(work)
        doi = _identifier(work, "doi")
        lines = [_ris_line("TY", RIS_TYPES.get(csl_type, RIS_FALLBACK)), _ris_line("ID", key)]
        lines += [_ris_line("AU", _name_text(a)) for a in authors]
        lines += [_ris_line("A2", _name_text(e)) for e in editors]
        if _text(work.get("title")):
            lines.append(_ris_line("TI", work.get("title")))
        if _venue(work):
            lines.append(_ris_line("T2", _venue(work)))
        parts = _date_parts(work)
        if parts:
            lines.append(_ris_line("PY", parts[0]))
            lines.append(_ris_line("DA", "/".join([str(p) for p in parts] + [""] * (4 - len(parts)))))
        if doi:
            lines.append(_ris_line("DO", doi))
        for name, tag in (("isbn", "SN"), ("issn", "SN")):
            value = _identifier(work, name)
            if value:
                lines.append(_ris_line("SN", value))
                break
        url = _text(work.get("url")) or (f"https://doi.org/{doi}" if doi else "")
        if url:
            lines.append(_ris_line("UR", url))
        lines.append("ER  - \n")
        records.append("".join(lines))
    return "\n".join(records)


def _period(item: dict[str, Any]) -> str:
    start = _text(item.get("start_date"))
    end = _text(item.get("end_date"))
    if not start and not end:
        return ""
    return f"{start or '?'}–{end or 'present'}"


def _citation(work: dict[str, Any]) -> str:
    authors, _ = _contributors(work)
    names = "; ".join(_name_text(a) for a in authors)
    doi = _identifier(work, "doi")
    bits = [names, _text(work.get("title")), _venue(work), _year(work)]
    bits.append(f"https://doi.org/{doi}" if doi else _text(work.get("url")))
    return ". ".join(bit for bit in bits if bit)


def _work_scope(work: dict[str, Any]) -> dict[str, Any]:
    doi = _identifier(work, "doi")
    return {
        "year": _year(work),
        "doi": doi,
        "doi_url": f"https://doi.org/{doi}" if doi else "",
        "venue": _venue(work),
        "authors_text": "; ".join(_name_text(a) for a in _contributors(work)[0]),
        "citation": _citation(work),
    }


def _item_scope(section: str, item: dict[str, Any], index: int) -> dict[str, Any]:
    scope: dict[str, Any] = {k: v for k, v in item.items()}
    scope.update({"index": index + 1, "index0": index, "period": _period(item)})
    identifiers = item.get("identifiers")
    if isinstance(identifiers, dict):
        scope.setdefault("grant_number", _identifier(item, "grant_number", "grant-number", "grant"))
    if section == "works":
        scope.update(_work_scope(item))
    return scope


def _sections(bio: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Every list-of-dict section of the contract, so new sections need no code."""
    out = {}
    for name, value in bio.items():
        if isinstance(value, list) and all(isinstance(x, dict) for x in value):
            out[name] = [_item_scope(name, item, i) for i, item in enumerate(value)]
    return out


def _root(bio: dict[str, Any]) -> dict[str, Any]:
    person = bio.get("person") or {}
    root: dict[str, Any] = {k: v for k, v in bio.items()}
    root.update(_sections(bio))
    root["person"] = person
    root["keywords_text"] = ", ".join(_text(k) for k in person.get("keywords") or [])
    root["generated_at"] = _text((bio.get("provenance") or {}).get("generated_at"))
    current = next((e for e in bio.get("employment") or [] if isinstance(e, dict) and not e.get("end_date")), None)
    root["current_position"] = _item_scope("employment", current, 0) if current else {}
    return root


def _lookup(path: str, scopes: list[dict[str, Any]]) -> Any:
    keys = path.split(".")
    for scope in scopes:
        node: Any = scope
        for key in keys:
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                node = None
                break
        if node is not None:
            return node
    return ""


_FILTERS = {
    "upper": lambda v: v.upper(),
    "lower": lambda v: v.lower(),
    "title": lambda v: v.title(),
    "trim": lambda v: v.strip(),
    "year": lambda v: v[:4],
}
_PLACEHOLDER = re.compile(r"\{\{\s*([\w.]+)((?:\s*\|\s*\w+)*)\s*\}\}")
_BLOCK = re.compile(
    r"^[ \t]*\{\{#\s*(\w+)\s*(?:limit=(\d+))?\s*\}\}[ \t]*\n(.*?)^[ \t]*\{\{/\s*\1\s*\}\}[ \t]*\n",
    re.DOTALL | re.MULTILINE,
)
_CONDITION = re.compile(
    r"^[ \t]*\{\{\?\s*(\w+)\s*\}\}[ \t]*\n(.*?)^[ \t]*\{\{/\?\s*\1\s*\}\}[ \t]*\n",
    re.DOTALL | re.MULTILINE,
)


def _substitute(text: str, scopes: list[dict[str, Any]]) -> str:
    def replace(match: re.Match[str]) -> str:
        value = _lookup(match.group(1), scopes)
        rendered = _text(value) if not isinstance(value, (list, dict)) else ""
        for name in re.findall(r"\w+", match.group(2) or ""):
            rendered = _FILTERS.get(name, lambda v: v)(rendered)
        return rendered

    return _PLACEHOLDER.sub(replace, text)


def _render(text: str, scopes: list[dict[str, Any]]) -> str:
    def expand(match: re.Match[str]) -> str:
        section, limit, body = match.group(1), match.group(2), match.group(3)
        items = _lookup(section, scopes)
        items = items if isinstance(items, list) else []
        items = items[: int(limit)] if limit else items
        return "".join(_render(body, [item if isinstance(item, dict) else {}, *scopes]) for item in items)

    def keep(match: re.Match[str]) -> str:
        return _render(match.group(2), scopes) if _lookup(match.group(1), scopes) else ""

    return _substitute(_BLOCK.sub(expand, _CONDITION.sub(keep, text)), scopes)


def _template_dir():
    return resources.files(__package__).joinpath("templates")


def available_templates() -> list[str]:
    """Names of the funder templates shipped as package data."""
    return sorted(
        entry.name[:-3] for entry in _template_dir().iterdir()
        if entry.name.endswith(".md") and not entry.name.startswith("_")
    )


def _template_text(template: str) -> str:
    name = template[:-3] if template.endswith(".md") else template
    if name in available_templates():
        return _template_dir().joinpath(f"{name}.md").read_text(encoding="utf-8")
    path = Path(template)
    if path.is_file():
        return path.read_text(encoding="utf-8")
    raise ValueError(f"Unknown template {template!r}; available: {', '.join(available_templates())}")


def render_template(bio: dict[str, Any], template: str) -> str:
    """Render a funder template — a shipped name, or a path to a contributed file."""
    text = _render(_template_text(template), [_root(bio)])
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
