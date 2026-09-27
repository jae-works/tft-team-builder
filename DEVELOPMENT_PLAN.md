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

The code should remain practical and human-readable.

- Do not create interfaces, abstract base classes or generic frameworks merely to match a preconceived architecture diagram.
- Introduce abstractions only when they remove real duplication, isolate correctness-sensitive behavior or make testing materially better.
- Keep UI logic separate from core game/build logic where that protects correctness.
- Keep persistence separate from Flet widgets.
- Keep Set data declarative; runtime Set packages must not contain executable Set-specific Python.
- Add detailed comments around non-obvious invariants and important tradeoffs.
- Prefer explicit code over clever code.
- Tests are expected to be extensive even when production code stays simple.

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
- `SET_DATA_PIPELINE.md`

The final Windows package also ships readable copies of the relevant project documentation in `project_docs/` so another developer or AI instance can understand what was built and why.
