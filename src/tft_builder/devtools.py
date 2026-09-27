"""Small developer CLI for Set validation and deterministic local-spec builds."""

from __future__ import annotations

import argparse
from pathlib import Path

from .set_builder import build_set_from_local_spec
from .set_loader import load_set_directory, validate_set_directory


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tft-builder-dev")
    subcommands = parser.add_subparsers(dest="command", required=True)

    validate_parser = subcommands.add_parser("validate-set", help="validate one runtime Set package")
    validate_parser.add_argument("path", type=Path)

    inspect_parser = subcommands.add_parser("inspect-set", help="print a compact validated Set summary")
    inspect_parser.add_argument("path", type=Path)

    build_parser = subcommands.add_parser("build-set", help="build a Set from an offline local source spec")
    build_parser.add_argument("spec_dir", type=Path)
    build_parser.add_argument("output_dir", type=Path)
    build_parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate-set":
        report = validate_set_directory(args.path)
        if report.is_valid:
            assert report.loaded_set is not None
            print(f"VALID: {report.loaded_set.manifest.set_id}")
            return 0
        print("INVALID")
        print(report.formatted_issues())
        return 1

    if args.command == "inspect-set":
        loaded = load_set_directory(args.path)
        print(f"Set ID: {loaded.manifest.set_id}")
        print(f"Revision: {loaded.manifest.revision}")
        print(f"Champions: {len(loaded.champions)}")
        print(f"Traits: {len(loaded.traits)}")
        print(f"Dynamic rules: {len(loaded.dynamic_traits)}")
        return 0

    if args.command == "build-set":
        output = build_set_from_local_spec(args.spec_dir, args.output_dir, overwrite=args.overwrite)
        print(f"Built: {output}")
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
