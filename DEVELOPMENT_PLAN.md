# TFT Team Builder - Development Plan

The project is implemented in substantial, user-testable blocks rather than many tiny coding steps.

The authoritative current block roadmap is `IMPLEMENTATION_BLOCKS.md`.

## Delivery rule for every coding block

- Implement a meaningful amount of working functionality.
- Update `REQUIREMENTS.md` if requirements changed or were clarified.
- Update `PROGRESS.md` only with functionality that actually exists and was locally verified.
- Update `IMPLEMENTATION_BLOCKS.md` and this document when later planning changes.
- Run the complete local test suite.
- Do not claim tests that were not actually run.
- Build a complete project ZIP, never a patch-only delivery.
- Verify the final archive for corruption and required files.
- Generate SHA-256 from the final ZIP after packaging.
- Give the user the full ZIP, checksum and a ready-to-copy Git add/commit/push block.

## Planning is allowed to evolve

The nine currently planned blocks are a roadmap, not an artificial architecture constraint.

After a completed block, later blocks may be:
- clarified,
- reordered,
- split,
- merged,
- reduced,
- expanded when a newly discovered required behavior belongs there.

Changes must be documented before or together with implementation. Completed history must not be rewritten to make the project appear more complete than it was at the time.

## Current implementation order

1. Foundation, Set system and core models.
2. SQLite persistence, migrations, autosave primitives and backups.
3. Core builder logic: slots, move/copy/swap, Trait engine and undo/redo.
4. First complete functional Builder GUI.
5. Full desktop interaction, Drag & Drop, search and Builder polish.
6. Start page and Team library.
7. Real TFT Set data pipeline and production Set package.
8. TFT Team Planner codes and complete native import/export.
9. Hardening, recovery, performance, Windows packaging and v1.0 release candidate.

See `IMPLEMENTATION_BLOCKS.md` for scope and user-test targets for each block.

## Coding approach

The code should remain practical, modern and human-readable.

- Code, identifiers, comments, internal configuration/schema keys and technical logs are English.
- Project-authored technical text uses simple ASCII punctuation and avoids decorative Unicode.
- Use simple ASCII filenames/directories for project-owned paths.
- Use `pathlib` and one centralized application-path module; never base runtime correctness on the current working directory.
- Use a platform-aware maintained library such as `platformdirs` for writable user-data directories.
- Declare runtime/dev dependencies and tool configuration in `pyproject.toml`.
- Prefer currently maintained stable libraries when they improve correctness or portability.
- Prefer a clear standard-library solution over an unnecessary dependency.

- Do not create interfaces, abstract base classes or generic frameworks merely to match a preconceived architecture diagram.
- Introduce abstractions only when they remove real duplication, isolate correctness-sensitive behavior or make testing materially better.
- Keep UI logic separate from core game/build logic where that protects correctness.
- Keep persistence separate from Flet widgets.
- Keep Set data declarative; runtime Set packages must not contain executable Set-specific Python.
- Add detailed comments around non-obvious invariants and important tradeoffs.
- Prefer explicit code over clever code.
- Tests are expected to be extensive even when production code stays simple.
- Before consequential implementation choices, compare the practical alternatives and their failure modes. Record the chosen approach and concise rationale in project documentation when it materially affects architecture, persistence, compatibility or future maintenance.

### Planned library policy

Block 1 selected and pinned the current baseline after compatibility research:

- Flet 1.0.1 for the Windows-first GUI while preserving the long-term Windows/macOS/Linux/Android/iOS/Web target. Windows remains the blocking development gate; target-specific tooling stays optional until that platform is actively verified.
- Pydantic 2.13.5 for strict external Set/manifest/schema validation.
- `platformdirs` 4.11.15 for writable platform-specific application paths when Flet-specific storage paths are not available.
- Persistence uses Python 3.13 `sqlite3` directly with explicit migrations. SQLAlchemy/Alembic remain unnecessary unless a later concrete requirement makes the direct layer materially worse.
- `httpx` for developer-side Set source downloads in Block 7.
- pytest 9.1.1 for tests.
- Ruff 0.16.9 for formatting/linting/import checks.

These are implementation tools, not goals by themselves. If a dependency does not provide a concrete benefit, the standard library is preferred.

## Set data plan

`SET_DATA_PIPELINE.md` is the binding detailed plan for TFT source data and assets.

The short version:
- runtime uses local validated Set packages,
- Riot Data Dragon is the preferred official source for supported visible data/assets,
- CommunityDragon may supplement/cross-check build-time metadata,
- exact source revisions/hashes are recorded,
- conflicts are surfaced rather than silently overwritten,
- manual overrides are explicit and reasoned,
- source candidates must be included, explicitly excluded with a reason, or reported as an error.

## Documentation shipped with the project

Every source delivery includes at least:
- `PROJECT_CONTEXT.md`
- `REQUIREMENTS.md`
- `PROGRESS.md`
- `IMPLEMENTATION_BLOCKS.md`
- `DEVELOPMENT_PLAN.md`
- `DECISIONS.md`
- `LICENSE_REVIEW.md`
- `SET_DATA_PIPELINE.md`
- the current completed block report, currently `BLOCK_03_REPORT.md`
- the implemented Block 3 behavior contract, `BLOCK_03_PLAN.md`

The final Windows package also ships readable copies of the relevant project documentation in `project_docs/` so another developer or AI instance can understand what was built and why.

## Current implementation position

Blocks 1 through 6 are implemented. Version 0.6.0 adds the local Team Library and keeps ranking/search logic Flet- and SQLite-independent. The v0.5.1 Windows run passed 586 normal tests at 100 percent coverage and exact Ruff checks; the packaged Flet host built and exited cleanly but did not expose a stable application key after one settle. The Block 6 packaged smoke now uses bounded polling for the library-first startup flow instead of treating one settle as a readiness contract. `BLOCK_07_PLAN.md` is the next-block handoff for reproducible real TFT Set acquisition and generation.


## Block 2 persistence decision

Block 2 uses Python 3.13 `sqlite3` directly. SQLAlchemy and Alembic were intentionally not added because the current local-only schema is small, explicit, aggregate-oriented, and fully covered by tests. The persistence package is isolated so a later backend decision does not leak SQL into the UI or domain models.
