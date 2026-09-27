# Block 1 Implementation Report

Status: final Block 1 candidate pending one clean Windows recheck.
Version: 0.1.4.

## Purpose

Block 1 establishes the project foundation before persistence or the full Builder UI is added. It intentionally contains more validation and testing than visible product functionality.

## Delivered foundation

- CPython 3.13 development baseline.
- `src/` package layout.
- Flet 1.0.1 application entry point and minimal startup shell.
- Central application path policy using `pathlib`, Flet storage environment paths, and `platformdirs` fallback.
- Reserved `builder.db` path under the writable data root so Block 2 reuses the same path policy.
- Runtime directory creation.
- Rotating application logging.
- Startup integration for paths, logging, and bundled Set validation.
- Mutable Team/List/Slot/ChampionInstance/TraitSelection domain models.
- Strict Pydantic models for external/generated Set package data.
- Unicode-aware search normalization.
- Deterministic JSON helpers that reject duplicate object keys.
- SHA-256 file/directory integrity helpers.
- Developer CLI.

## Set system

The current Set system validates at least:

- required package files;
- UTF-8 and JSON correctness;
- duplicate JSON object keys;
- schema versions and unknown schema fields;
- portable canonical package paths;
- path traversal and Windows reserved filenames;
- metadata/assets/locales directory collisions;
- Champion and Trait ID uniqueness;
- Champion and Trait display-order uniqueness;
- native Trait references;
- dynamic Trait rules and references;
- Team Planner mapping consistency and unique external IDs;
- supported locale inventory and required translation keys;
- non-empty Champion and Trait catalogs;
- required Champion/Trait assets;
- PNG signatures;
- source-manifest generated-file hashes;
- source-manifest runtime-asset hashes;
- runtime package inventory with unexpected-file rejection;
- symbolic-link and Windows-junction rejection where containment matters;
- stable validation issue ordering.

Set generation:

- uses one committed fictional local source specification;
- generates the runtime package deterministically;
- writes into an isolated sibling staging directory;
- validates the staging output with the same runtime loader;
- promotes only a fully valid package;
- preserves an existing valid package if a rebuild fails;
- rejects overlapping source/output directories;
- rejects source paths containing symbolic links or Windows junctions;
- records source and generated payload SHA-256 values.

The bundled sample Set lives under `src/assets/sets/sample_set`. It is generated from `set_sources/specs/sample_set`.

## Cleanup performed through version 0.1.4

Version 0.1.3 started from the user's tested 0.1.2 tree and removed temporary or redundant material rather than layering more migration code on top. Version 0.1.4 keeps that clean layout and applies the final formatter corrections reported by the real Windows Ruff 0.16.9 run.

- Removed the temporary legacy-layout cleanup utility and its tests. Project handoffs now use a clean replacement model while preserving `.git`.
- Removed 116 unused duplicate fixture files. Invalid Set tests mutate temporary copies of the one canonical sample Set instead.
- Removed redundant `.gitkeep` files from directories that already contain tracked files.
- Removed duplicate Set-import wrapper scripts that repeated the existing `tft-builder-dev` CLI. `tools/set_import/` remains reserved for Block 7 adapters.
- Removed bytecode caches, pytest cache, and coverage output from the delivered tree.
- Restored the GitHub Actions workflow as an explicit part of the complete project delivery.
- Added `uv lock --check` to CI.
- Added a small cross-platform filesystem helper so symbolic links and Windows junctions follow one containment policy.
- Replaced OS-privilege-dependent symlink tests with deterministic link-behavior tests. Mandatory Block 1 tests now run without expected Windows skips.

## Windows verification history

The user's 0.1.2 Windows run confirmed:

- Python 3.13.5 and `uv sync` work;
- Flet 1.0.1 starts successfully;
- the bundled Set root resolves to `src/assets/sets`;
- sample Set validation passes;
- Ruff lint passes;
- ASCII and mirrored-document checks pass;
- 332 tests pass, with 12 tests skipped only because the environment does not permit creating symbolic links;
- Ruff formatting still reported six files.

Version 0.1.3 removed those expected skips. The user then confirmed 348 passing tests, Ruff lint, Set validation and Flet startup; Ruff format reported only three formatting-only files. Version 0.1.4 applies exactly those three corrections.

## Current implementation-environment verification

```text
349 passed
0 skipped
branch coverage: 99.63 percent
```

The implementation environment also verifies syntax compilation, ASCII policy, deterministic Set regeneration, Set validation, project metadata, and mirrored documentation.

## Why Flet remains selected

Flet remains the best current fit for the project priorities:

- Windows desktop is the mandatory first target.
- Flet also preserves an official web, Android, and iOS path if those deferred targets become worthwhile.
- Flet uses the permissive Apache-2.0 license.
- Core logic remains independent from Flet, so the UI framework can still be replaced later if a required interaction, performance target, or release constraint exposes a material limitation.

Browser and mobile/tablet support are deferred, not removed.

## Tooling note

The implementation sandbox cannot execute the exact Windows Flet desktop runtime. Final acceptance therefore still requires the user's Windows commands below. The exact Ruff binary must also pass there before Block 1 is accepted.

## Final Windows acceptance commands

```text
uv lock --check
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run python tools/check_ascii.py
uv run python tools/sync_project_docs.py --check
uv run tft-builder-dev validate-set src/assets/sets/sample_set
uv run flet run
```

Block 2 may begin after this 0.1.4 delivery passes the final Windows quality commands. No further Block 1 architecture work is planned unless that recheck exposes a concrete issue.
