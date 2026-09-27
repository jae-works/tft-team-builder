"""Small developer CLI for Set validation and deterministic local-spec builds."""

from __future__ import annotations

import argparse
from pathlib import Path

from .models import ChampionInstance, Slot, Team, TraitSelection
from .persistence import BackupManager, Database, TeamRepository
from .set_builder import build_set_from_local_spec
from .set_loader import load_set_directory, validate_set_directory


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tft-builder-dev")
    subcommands = parser.add_subparsers(dest="command", required=True)

    validate_parser = subcommands.add_parser(
        "validate-set", help="validate one runtime Set package"
    )
    validate_parser.add_argument("path", type=Path)

    inspect_parser = subcommands.add_parser(
        "inspect-set", help="print a compact validated Set summary"
    )
    inspect_parser.add_argument("path", type=Path)

    build_parser = subcommands.add_parser(
        "build-set", help="build a Set from an offline local source spec"
    )
    build_parser.add_argument("spec_dir", type=Path)
    build_parser.add_argument("output_dir", type=Path)
    build_parser.add_argument("--overwrite", action="store_true")

    smoke_parser = subcommands.add_parser(
        "database-smoke", help="exercise SQLite persistence in an explicit directory"
    )
    smoke_parser.add_argument("directory", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "validate-set":
        report = validate_set_directory(args.path)
        if report.is_valid and report.loaded_set is not None:
            print(f"VALID: {report.loaded_set.manifest.set_id}")
            return 0
        print("INVALID")
        print(report.formatted_issues())
        return 1

    if args.command == "database-smoke":
        directory = args.directory.expanduser().resolve()
        database = Database(directory / "builder.db", backups_dir=directory / "backups")
        database.initialize()
        repository = TeamRepository(database)
        team = Team.create(set_id="sample_set", name="Persistence smoke")
        team.primary_list.slots.extend(
            [
                Slot(0, ChampionInstance("sample_guardian")),
                Slot(1),
                Slot(
                    2,
                    ChampionInstance(
                        "sample_mage",
                        trait_selection=TraitSelection(("sample_arcane",)),
                    ),
                ),
            ]
        )
        team.validate_invariants()
        repository.save(team)
        loaded = repository.load(team.team_id)
        if loaded != team:
            raise RuntimeError("persistence smoke round-trip mismatch")
        backup = BackupManager(database, directory / "backups").create_backup(prefix="smoke")
        print(f"Database schema: {database.schema_version()}")
        print(f"Round-trip Team: {loaded.team_id}")
        print(f"Backup: {backup}")
        return 0

    if args.command == "inspect-set":
        loaded = load_set_directory(args.path)
        print(f"Set ID: {loaded.manifest.set_id}")
        print(f"Revision: {loaded.manifest.revision}")
        print(f"Champions: {len(loaded.champions)}")
        print(f"Traits: {len(loaded.traits)}")
        print(f"Dynamic rules: {len(loaded.dynamic_traits)}")
        return 0

    # The subparser is required and only defines the known commands above. Reaching this
    # point therefore means the validated command is ``build-set``; keeping that guarantee
    # in argparse avoids a redundant defensive branch that can never occur in normal use.
    output = build_set_from_local_spec(args.spec_dir, args.output_dir, overwrite=args.overwrite)
    print(f"Built: {output}")
    return 0
