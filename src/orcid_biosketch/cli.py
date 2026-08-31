from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import exporters, fun, lint as linting
from .core import (
    API,
    SANDBOX_API,
    OrcidError,
    build_biosketch,
    fetch_orcid_record,
    load_record,
    render_markdown,
    to_jsonld,
)

COMMANDS = ("generate", "lint", "export", "wrapped", "card", "heatmap", "fortune", "badge")


def _source_parser() -> argparse.ArgumentParser:
    """Options shared by every command that needs a biosketch."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("orcid", nargs="?", help="ORCID iD, e.g. 0000-0003-4820-7951")
    parser.add_argument("--record", type=Path, help="Read a saved ORCID API record instead of fetching")
    parser.add_argument("--biosketch", type=Path, help="Read an already-generated biosketch.json")
    parser.add_argument("--config", type=Path, help="Optional JSON overrides")
    parser.add_argument("--sandbox", action="store_true", help="Use the ORCID sandbox API")
    return parser


def _biosketch(args: argparse.Namespace) -> dict[str, Any]:
    if args.biosketch:
        return json.loads(args.biosketch.read_text(encoding="utf-8"))
    override = json.loads(args.config.read_text(encoding="utf-8")) if args.config else None
    if args.record:
        return build_biosketch(load_record(args.record), override)
    if not args.orcid:
        raise OrcidError("Provide an ORCID iD, or --record / --biosketch to work offline")
    base_url = SANDBOX_API if args.sandbox else API
    return build_biosketch(fetch_orcid_record(args.orcid, base_url=base_url), override)


def _emit(text: str, destination: Path | None) -> None:
    if destination:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text, encoding="utf-8")
        print(f"Wrote {destination}", file=sys.stderr)
    else:
        sys.stdout.write(text if text.endswith("\n") else text + "\n")


def _generate(args: argparse.Namespace) -> int:
    bio = _biosketch(args)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "biosketch.json").write_text(json.dumps(bio, indent=2, ensure_ascii=False) + "\n")
    (args.output / "biosketch.jsonld").write_text(json.dumps(to_jsonld(bio), indent=2, ensure_ascii=False) + "\n")
    (args.output / "biosketch.md").write_text(render_markdown(bio, args.max_works))
    print(f"Generated biosketch for {bio['person']['name']} in {args.output}")
    return 0


def _lint(args: argparse.Namespace) -> int:
    result = linting.lint(_biosketch(args))
    _emit(json.dumps(result, indent=2, ensure_ascii=False) if args.json else linting.render_report(result), args.out)
    if args.fail_under is not None and result["percentage"] < args.fail_under:
        print(f"Record scored {result['percentage']}%, below the required {args.fail_under}%", file=sys.stderr)
        return 1
    return 0


def _export(args: argparse.Namespace) -> int:
    bio = _biosketch(args)
    if args.format == "csl":
        text = json.dumps(exporters.to_csl_json(bio), indent=2, ensure_ascii=False)
    elif args.format == "bibtex":
        text = exporters.to_bibtex(bio)
    elif args.format == "ris":
        text = exporters.to_ris(bio)
    else:
        text = exporters.render_template(bio, args.template)
    _emit(text, args.out)
    return 0


def _wrapped(args: argparse.Namespace) -> int:
    data = fun.wrapped(_biosketch(args), args.year)
    _emit(json.dumps(data, indent=2, ensure_ascii=False) if args.json else fun.render_wrapped(data), args.out)
    return 0


def _card(args: argparse.Namespace) -> int:
    _emit(fun.trading_card_svg(_biosketch(args)), args.out)
    return 0


def _heatmap(args: argparse.Namespace) -> int:
    _emit(fun.heatmap_svg(_biosketch(args)), args.out)
    return 0


def _fortune(args: argparse.Namespace) -> int:
    _emit(fun.fortune(_biosketch(args), args.seed), args.out)
    return 0


def _badge(args: argparse.Namespace) -> int:
    _emit(json.dumps(linting.to_badge(linting.lint(_biosketch(args))), indent=2), args.out)
    return 0


def build_parser() -> argparse.ArgumentParser:
    source = _source_parser()
    parser = argparse.ArgumentParser(
        prog="orcid-biosketch",
        description="Generate provenance-aware biosketches and reports from a public ORCID record",
    )
    subparsers = parser.add_subparsers(dest="command")

    generate = subparsers.add_parser("generate", parents=[source], help="Write JSON, JSON-LD and Markdown outputs")
    generate.add_argument("--output", type=Path, default=Path("generated"))
    generate.add_argument("--max-works", type=int, default=10)
    generate.set_defaults(handler=_generate)

    lint_cmd = subparsers.add_parser("lint", parents=[source], help="Report ORCID record quality and what to fix")
    lint_cmd.add_argument("--json", action="store_true", help="Emit the machine-readable report")
    lint_cmd.add_argument("--fail-under", type=int, metavar="PERCENT", help="Exit non-zero below this score")
    lint_cmd.add_argument("-o", "--out", type=Path)
    lint_cmd.set_defaults(handler=_lint)

    export = subparsers.add_parser("export", parents=[source], help="Export citations or a funder biosketch")
    export.add_argument("--format", choices=("csl", "bibtex", "ris", "template"), default="bibtex")
    export.add_argument("--template", default="nih", help=f"Funder template: {', '.join(exporters.available_templates())}")
    export.add_argument("-o", "--out", type=Path)
    export.set_defaults(handler=_export)

    wrapped = subparsers.add_parser("wrapped", parents=[source], help="A year in review, read from the record")
    wrapped.add_argument("--year", type=int)
    wrapped.add_argument("--json", action="store_true")
    wrapped.add_argument("-o", "--out", type=Path)
    wrapped.set_defaults(handler=_wrapped)

    card = subparsers.add_parser("card", parents=[source], help="Printable trading card (SVG)")
    card.add_argument("-o", "--out", type=Path)
    card.set_defaults(handler=_card)

    heatmap = subparsers.add_parser("heatmap", parents=[source], help="Publication heatmap (SVG)")
    heatmap.add_argument("-o", "--out", type=Path)
    heatmap.set_defaults(handler=_heatmap)

    fortune = subparsers.add_parser("fortune", parents=[source], help="Print one of your own titles")
    fortune.add_argument("--seed", type=int)
    fortune.add_argument("-o", "--out", type=Path)
    fortune.set_defaults(handler=_fortune)

    badge = subparsers.add_parser("badge", parents=[source], help="shields.io endpoint JSON for the lint score")
    badge.add_argument("-o", "--out", type=Path)
    badge.set_defaults(handler=_badge)
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # Back-compat: `orcid-biosketch <ORCID> ...` kept working when subcommands arrived.
    if argv and argv[0] not in COMMANDS and argv[0] not in ("-h", "--help"):
        argv.insert(0, "generate")
    args = build_parser().parse_args(argv)
    if not getattr(args, "handler", None):
        build_parser().print_help()
        return 0
    try:
        return args.handler(args)
    except OrcidError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
