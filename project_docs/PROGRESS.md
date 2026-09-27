# TFT Team Builder - Progress

Current version: 0.1.0
Current status: Block 1 implementation complete and ready for user verification.
Next planned block: Block 2 - SQLite persistence, migrations, autosave primitives, and backups.

This file records only functionality that exists in the delivered project. Detailed Block 1 verification is in `BLOCK_01_REPORT.md`.

## Completed in Block 1

- [x] Converted the repository from planning-only structure to a runnable Python project.
- [x] Added `pyproject.toml` with a Python 3.13 baseline and pinned runtime/development dependencies.
- [x] Added current Flet 1.0 desktop entry point under `src/main.py`.
- [x] Added importable `src/tft_builder/` package.
- [x] Added centralized project/runtime path handling with `pathlib` and `platformdirs`.
- [x] Added explicit writable runtime-directory creation.
- [x] Added rotating local logging configuration with safe reconfiguration when the log directory changes.
- [x] Wired non-visual application startup to path resolution, runtime-directory creation, logging, and bundled Set validation.
- [x] Added Team, TeamList, Slot, ChampionInstance, and TraitSelection domain models with tested invariants, including Team-wide Champion instance ID uniqueness.
- [x] Added strict Set manifest, Champion, Trait, dynamic Trait, Team Planner, source-spec, and source-manifest Pydantic schemas.
- [x] Added strict local Set loader and validator.
- [x] Added Set discovery and multi-Set validation helpers.
- [x] Added understandable stable validation issue codes.
- [x] Added checks for missing files, invalid JSON/UTF-8, schema errors, duplicate IDs, broken references, invalid dynamic rules, missing translations, missing assets, invalid PNG signatures, path escapes, and Team Planner inconsistencies.
- [x] Added source-manifest SHA-256 verification for generated runtime JSON/locale files and all required Champion/Trait assets.
- [x] Added deterministic offline Set generation from a committed local source spec.
- [x] Added staging-based Set generation so failed builds leave no partial output and failed overwrites preserve previous valid output.
- [x] Added source-spec/output overlap protection and source-asset symlink escape protection.
- [x] Added the generated, valid `sets/sample_set` runtime package.
- [x] Added one valid and eight deliberately invalid committed Set fixtures.
- [x] Added developer CLI commands for Set build, validation, and inspection.
- [x] Added forgiving search-text normalization.
- [x] Added repository ASCII-policy enforcement tool and tests.
- [x] Added technical decision documentation in `DECISIONS.md`.
- [x] Converted/verified project-authored technical documentation as English-only and ASCII-safe.
- [x] Updated Requirements, Development Plan, Implementation Blocks, Project Context, and Set Data Pipeline to reflect real Block 1 code.

## Verified locally in the implementation environment

- [x] `204 passed` with pytest.
- [x] Python `compileall` passed for source, tools, and tests.
- [x] Repository ASCII-policy check passed.
- [x] `sample_set` regenerated successfully from the committed local source spec.
- [x] Regenerated `sample_set` passed strict validation.
- [x] Generated Set content is deterministic across independent output directories.
- [x] Project-authored path names are ASCII-only.
- [x] Project manifest required-document checks pass.
- [x] `project_docs/` copies are byte-for-byte mirrors of the authoritative root documents.

## Environment limitation that was not marked as passed

- [!] The implementation sandbox could not download packages that were not already installed. Therefore the exact pinned Flet 1.0.1 desktop process and Ruff 0.16.9 executable were not run in that sandbox.
- [!] The user should run `uv sync`, `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, and `uv run flet run` in the normal connected Windows development environment before accepting Block 1 and starting Block 2.

No Block 2 persistence functionality is implemented in this version.
