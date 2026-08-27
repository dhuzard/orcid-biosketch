from __future__ import annotations

import json
import os
import urllib.request
from datetime import datetime, timezone
from typing import Any

API = "https://pub.orcid.org/v3.0"


def fetch_orcid_record(orcid: str, token: str | None = None) -> dict[str, Any]:
    """Fetch the public ORCID 3.0 record as JSON."""
    headers = {"Accept": "application/json", "User-Agent": "orcid-biosketch/0.1"}
    token = token or os.getenv("ORCID_ACCESS_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(f"{API}/{orcid}/record", headers=headers)
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def _value(node: Any, default: str = "") -> str:
    return node.get("value", default) if isinstance(node, dict) else default


def _date(node: dict[str, Any] | None) -> str | None:
    if not node:
        return None
    parts = [_value(node.get(k)) for k in ("year", "month", "day")]
    parts = [p for p in parts if p]
    return "-".join(parts) or None


def _affiliations(groups: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    items = []
    for group in groups or []:
        for wrapped in group.get("summaries", []):
            summary = wrapped.get(f"{kind}-summary", {})
            org = summary.get("organization", {})
            items.append({
                "organization": org.get("name"),
                "role": summary.get("role-title"),
                "department": summary.get("department-name"),
                "start_date": _date(summary.get("start-date")),
                "end_date": _date(summary.get("end-date")),
                "source": _source(summary),
                "orcid_put_code": summary.get("put-code"),
            })
    return items


def _source(node: dict[str, Any]) -> dict[str, Any]:
    source = node.get("source") or {}
    origin = source.get("source-orcid") or source.get("source-client-id") or {}
    return {"name": _value(source.get("source-name")), "id": origin.get("path")}


def _works(groups: list[dict[str, Any]]) -> list[dict[str, Any]]:
    works = []
    for group in groups or []:
        summaries = group.get("work-summary", [])
        if not summaries:
            continue
        work = summaries[0]
        external_ids = work.get("external-ids", {}).get("external-id", [])
        identifiers = {
            item.get("external-id-type", "unknown"): item.get("external-id-value")
            for item in external_ids if item.get("external-id-value")
        }
        works.append({
            "title": _value((work.get("title") or {}).get("title")),
            "type": work.get("type"),
            "publication_date": _date(work.get("publication-date")),
            "journal": _value(work.get("journal-title")),
            "url": _value(work.get("url")),
            "identifiers": identifiers,
            "source": _source(work),
            "orcid_put_code": work.get("put-code"),
        })
    return sorted(works, key=lambda x: x.get("publication_date") or "", reverse=True)


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def build_biosketch(record: dict[str, Any], override: dict[str, Any] | None = None) -> dict[str, Any]:
    """Normalize an ORCID record into the stable biosketch contract."""
    person = record.get("person", {})
    name = person.get("name") or {}
    activities = record.get("activities-summary", {})
    orcid = record.get("orcid-identifier", {}).get("path", "")
    urls = {
        item.get("url-name") or "website": _value(item.get("url"))
        for item in person.get("researcher-urls", {}).get("researcher-url", [])
    }
    modified_ms = (record.get("history", {}).get("last-modified-date") or {}).get("value")
    generated_at = (
        datetime.fromtimestamp(modified_ms / 1000, timezone.utc).isoformat()
        if modified_ms else None
    )
    result = {
        "schema_version": "0.1.0",
        "person": {
            "name": " ".join(filter(None, [_value(name.get("given-names")), _value(name.get("family-name"))])),
            "given_names": _value(name.get("given-names")),
            "family_name": _value(name.get("family-name")),
            "credit_name": _value(name.get("credit-name")) or None,
            "orcid": orcid,
            "orcid_url": f"https://orcid.org/{orcid}",
            "biography": (person.get("biography") or {}).get("content", ""),
            "country": _value((person.get("addresses", {}).get("address") or [{}])[0].get("country")),
            "keywords": [x.get("content") for x in person.get("keywords", {}).get("keyword", [])],
            "urls": urls,
        },
        "employment": _affiliations(activities.get("employments", {}).get("affiliation-group", []), "employment"),
        "education": _affiliations(activities.get("educations", {}).get("affiliation-group", []), "education"),
        "works": _works(activities.get("works", {}).get("group", [])),
        "provenance": {
            "primary_source": f"https://orcid.org/{orcid}",
            "orcid_api_version": "3.0",
            "orcid_last_modified": modified_ms,
            "generated_at": generated_at,
            "override_applied": bool(override),
        },
    }
    return _deep_merge(result, override or {})


def to_jsonld(bio: dict[str, Any]) -> dict[str, Any]:
    person = bio["person"]
    return {
        "@context": "https://schema.org",
        "@type": "Person",
        "@id": person["orcid_url"],
        "name": person["name"],
        "givenName": person["given_names"],
        "familyName": person["family_name"],
        "description": person["biography"],
        "sameAs": [person["orcid_url"], *[v for v in person["urls"].values() if v]],
        "knowsAbout": person["keywords"],
        "alumniOf": [x["organization"] for x in bio["education"] if x["organization"]],
    }


def render_markdown(bio: dict[str, Any], max_works: int = 10) -> str:
    p = bio["person"]
    lines = [f"# {p['name']}", "", f"[ORCID: {p['orcid']}]({p['orcid_url']})", ""]
    if p["biography"]:
        lines.extend([p["biography"], ""])
    if bio["employment"]:
        lines.extend(["## Employment", ""])
        for item in bio["employment"]:
            period = "–".join(filter(None, [item["start_date"], item["end_date"] or "present"]))
            lines.append(f"- **{item['role'] or 'Position'}**, {item['organization']} ({period})")
        lines.append("")
    if bio["works"]:
        lines.extend(["## Selected works", ""])
        for work in bio["works"][:max_works]:
            doi = work["identifiers"].get("doi")
            target = f"https://doi.org/{doi}" if doi else work["url"]
            title = f"[{work['title']}]({target})" if target else work["title"]
            lines.append(f"- {title} ({(work['publication_date'] or '')[:4]})")
        lines.append("")
    lines.append(f"_Generated from ORCID; synchronized {bio['provenance']['generated_at']}._")
    return "\n".join(lines) + "\n"
