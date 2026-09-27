# TFT Team Builder - Progress

Current version: 0.2.1
Current status: Block 2 implemented in the implementation environment; final Windows verification pending.
Next planned block: Block 3 - core builder logic, Trait engine, and undo/redo.

This file records implemented work. Detailed Block 1 evidence is in `BLOCK_01_REPORT.md`.

## Completed in Block 1

- [x] Python 3.13 project with `src/` layout and `pyproject.toml`.
- [x] Flet 1.0.1 desktop entry point and minimal startup shell.
- [x] Flet kept at the UI boundary; core modules do not depend on Flet widgets.
- [x] Central `pathlib` path handling with Flet storage paths and `platformdirs` fallback.
- [x] Stable `builder.db` path reserved under the writable application data root for Block 2 without creating a database in Block 1.
- [x] Runtime directory creation independent from the current working directory.
- [x] Rotating local logging with safe idempotent reconfiguration.
- [x] Team, TeamList, Slot, ChampionInstance, and TraitSelection models with tested invariants.
- [x] Strict Pydantic schemas for generated Set data and local Set source specifications.
- [x] Strict local Set loader and validator with deterministic multi-error reporting.
- [x] Champion/Trait ID and display-order validation.
- [x] Trait, dynamic-Trait, locale, asset, and Team Planner reference validation.
- [x] UTF-8, JSON, duplicate-key, PNG, hash, and package-inventory validation.
- [x] Runtime Set packages reject unexpected files and link-like filesystem entries.
- [x] Symbolic links and Windows junctions are handled as link-like redirects where containment matters.
- [x] Runtime Set discovery does not follow link-like Set directories.
- [x] Deterministic offline Set generation from one committed fictional sample specification.
- [x] Transactional staging and non-destructive overwrite behavior for Set generation.
- [x] Source assets reject path traversal and link-like path components.
- [x] SHA-256 verification for generated data/locale files and required runtime assets.
- [x] One canonical bundled `sample_set`; invalid test cases are created from temporary mutations instead of committed duplicate fixture trees.
- [x] Developer CLI for Set build, validation, and inspection.
- [x] Unicode-aware search normalization while project-authored technical files remain ASCII-safe.
- [x] Repository ASCII-policy and project-path checks.
- [x] Architecture checks preventing Flet leakage into core modules and legacy `os.path` use.
- [x] GitHub Actions quality workflow for Windows and Linux on Python 3.13.
- [x] Dependency and release-license review document.
- [x] Browser and mobile/tablet remain deferred possibilities rather than removed targets.
- [x] Pytest uses importlib mode and the installed-project boundary created by `uv sync`.
- [x] Project documentation is English and mirrored into `project_docs/`.
- [x] Project handoffs use a clean replacement model while preserving the existing `.git` directory.
- [x] Temporary legacy-cleanup tooling and unused duplicate fixtures were removed from the clean 0.1.3 tree.

## Windows verification history

Version 0.1.0:
- [x] `uv` environment creation worked.
- [x] Flet 1.0.1 installed and the application shell started.
- [x] The sample Set was found and validated.
- [x] Windows-specific test assumptions and initial Ruff drift were identified and fixed afterward.

Version 0.1.2 user run:
- [x] `uv sync` succeeded with Python 3.13.5.
- [x] 332 tests passed.
- [x] 12 link tests were skipped only because the Windows environment did not permit symlink creation.
- [x] Ruff lint check passed.
- [x] ASCII policy passed.
- [x] Project document mirror check passed.
- [x] Bundled sample Set validation passed.
- [x] Flet application startup passed and used `src/assets/sets`.
- [ ] Ruff format check reported six files requiring formatting.

Version 0.1.3 removes the platform-permission skip design. Link-related security behavior is now tested deterministically without requiring Windows symlink privileges.


Version 0.1.3 user run:
- [x] 348 tests passed with no skips.
- [x] Ruff lint check passed.
- [x] ASCII policy passed.
- [x] Project document mirror check passed.
- [x] Bundled sample Set validation passed.
- [x] Flet startup passed and resolved the bundled Set root correctly.
- [ ] Ruff format check identified exactly three formatting-only files. Version 0.1.4 applies those exact formatter changes.

## Verified in the implementation environment for version 0.1.4

- [x] 349 pytest tests passed.
- [x] 0 tests skipped.
- [x] Branch-aware coverage reached 99.63 percent.
- [x] Required statement and branch coverage threshold is now 100 percent.
- [x] Python source/test/tool syntax compilation passed during the clean delivery audit.
- [x] Repository ASCII-policy check passed during the clean delivery audit.
- [x] Bundled `sample_set` validates successfully.
- [x] Set generation remains deterministic and transactional.
- [x] Project document mirror and manifest checks pass after synchronization.
- [x] Unused duplicate fixture trees, bytecode caches, coverage output, and temporary legacy tooling are absent from the clean project tree.

## Final Windows verification required before Block 2

- [ ] Run `uv lock --check`.
- [ ] Run `uv sync`.
- [ ] Run `uv run pytest` and confirm no failures and no skips.
- [ ] Run `uv run ruff check .`.
- [ ] Run `uv run ruff format --check .`.
- [ ] Run `uv run python tools/check_ascii.py`.
- [ ] Run `uv run python tools/sync_project_docs.py --check`.
- [ ] Run `uv run tft-builder-dev validate-set src/assets/sets/sample_set`.
- [ ] Run `uv run flet run`.

No Block 2 persistence implementation is included in version 0.1.4.


## Completed in Block 2

- [x] Standard-library SQLite persistence with no new runtime ORM dependency.
- [x] WAL, foreign keys, `synchronous=FULL`, busy timeout, and trusted-schema hardening.
- [x] Explicit schema migrations and migration history.
- [x] Automatic pre-migration backups for existing databases.
- [x] Complete Team/List/Slot/ChampionInstance/TraitSelection round-trip persistence.
- [x] Empty slots and duplicate Champion definitions persist exactly.
- [x] Soft delete, restore, permanent delete, and last-opened metadata.
- [x] Online backup creation, validation, pruning, and atomic restore.
- [x] Autosave primitives for immediate saves and queued immutable snapshots.
- [x] Application startup initializes the database through the central path layer.
- [x] Developer database smoke command.
- [x] 425 tests passed with 0 skips in the implementation environment.
- [x] 100.00 percent statement and branch coverage in the implementation environment.

## Final Windows verification required before Block 3

- [ ] Run `uv lock --check`.
- [ ] Run `uv sync --frozen`.
- [ ] Run `uv run pytest` on Windows and confirm 425 passed with no skips.
- [ ] Run `uv run ruff check .`.
- [ ] Run `uv run ruff format --check .`.
- [ ] Run `uv run python tools/check_ascii.py`.
- [ ] Run `uv run python tools/sync_project_docs.py --check`.
- [ ] Run `uv run tft-builder-dev validate-set src/assets/sets/sample_set`.
- [ ] Run `uv run tft-builder-dev database-smoke .runtime-smoke`.
- [ ] Run `uv run flet run`.
