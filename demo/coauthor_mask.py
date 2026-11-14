"""Capture-time co-author masking for the Explore & Play video (#58).

The play-campaign renderer serves a masked *copy* of the stored profile to the
browser it films (Playwright route on /generated/biosketch.json). Nothing here
edits the stored file, the Studio engine, exports for normal visitors or the
ORCID record: the input is read, deep-copied and transformed in memory.

Every author name that is not the profile owner (matched on the owner's family
name) becomes "Co-author N", numbered by first appearance across the works.
Names are keyed case-insensitively, as the Wrapped engine compares them, so
counts and "first time together" logic are unchanged. The same names are also
replaced where they occur in the biography and work titles.

    python demo/coauthor_mask.py site/generated/biosketch.json
prints {"biosketch": <masked copy>, "masked_names": <count>} as JSON.
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

PLACEHOLDER = "Co-author {n}"


def _owner_family(bio: dict[str, Any]) -> str:
    person = bio.get("person") or {}
    return str(person.get("family_name") or "").strip().lower()


def third_party_names(bio: dict[str, Any]) -> dict[str, str]:
    """Map each lower-cased third-party author name to its placeholder."""
    family = _owner_family(bio)
    mapping: dict[str, str] = {}
    for work in bio.get("works") or []:
        for author in work.get("authors") or work.get("contributors") or []:
            name = author.get("name") if isinstance(author, dict) else author
            if not isinstance(name, str) or not name.strip():
                continue
            key = name.strip().lower()
            if (family and family in key) or key in mapping:
                continue
            mapping[key] = PLACEHOLDER.format(n=len(mapping) + 1)
    return mapping


def _replace_in_text(text: str, originals: list[tuple[str, str]]) -> str:
    for original, placeholder in originals:
        text = text.replace(original, placeholder)
    return text


def mask_biosketch(bio: dict[str, Any]) -> tuple[dict[str, Any], int]:
    """Return a masked deep copy and the number of distinct names masked. ``bio`` is not modified."""
    mapping = third_party_names(bio)
    masked = copy.deepcopy(bio)
    # Exact spellings as they appear, longest first so "Benoit Petit-Demoulière" wins over "Benoit".
    spellings: dict[str, str] = {}
    for work in masked.get("works") or []:
        for i, author in enumerate(work.get("authors") or work.get("contributors") or []):
            name = author.get("name") if isinstance(author, dict) else author
            if not isinstance(name, str):
                continue
            placeholder = mapping.get(name.strip().lower())
            if not placeholder:
                continue
            spellings[name.strip()] = placeholder
            if isinstance(author, dict):
                author["name"] = placeholder
                for field in ("credit_name", "given_names", "family_name"):
                    author.pop(field, None)
            else:
                (work.get("authors") or work.get("contributors"))[i] = placeholder
    originals = sorted(spellings.items(), key=lambda kv: -len(kv[0]))
    person = masked.get("person") or {}
    if isinstance(person.get("biography"), str):
        person["biography"] = _replace_in_text(person["biography"], originals)
    for work in masked.get("works") or []:
        for field in ("title", "journal"):
            if isinstance(work.get(field), str):
                work[field] = _replace_in_text(work[field], originals)
    return masked, len(mapping)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python demo/coauthor_mask.py <biosketch.json>", file=sys.stderr)
        return 2
    bio = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    masked, count = mask_biosketch(bio)
    # Bytes, not text: a Windows console encoding would reject non-ASCII names.
    sys.stdout.buffer.write(json.dumps({"biosketch": masked, "masked_names": count}, ensure_ascii=False).encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
