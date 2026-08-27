from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import build_biosketch, fetch_orcid_record, render_markdown, to_jsonld


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a biosketch from a public ORCID record")
    parser.add_argument("orcid", help="ORCID iD, e.g. 0000-0003-4820-7951")
    parser.add_argument("--config", type=Path, help="Optional JSON overrides")
    parser.add_argument("--output", type=Path, default=Path("generated"))
    parser.add_argument("--max-works", type=int, default=10)
    args = parser.parse_args()

    override = json.loads(args.config.read_text()) if args.config else None
    bio = build_biosketch(fetch_orcid_record(args.orcid), override)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "biosketch.json").write_text(json.dumps(bio, indent=2, ensure_ascii=False) + "\n")
    (args.output / "biosketch.jsonld").write_text(json.dumps(to_jsonld(bio), indent=2, ensure_ascii=False) + "\n")
    (args.output / "biosketch.md").write_text(render_markdown(bio, args.max_works))
    print(f"Generated biosketch for {bio['person']['name']} in {args.output}")


if __name__ == "__main__":
    main()

