# Block 4 Report - Functional Builder GUI

Version: 0.4.1
Status: implemented; exact pinned Windows/Flet integration release gate pending.

## Implemented

- Real three-column Flet Builder: Traits | Lists | Champion library.
- SQLite startup loads the most recently updated Team or creates/persists an initial Team.
- Team/List rename, List management, primary/active List handling, Champion add/remove, Trait rendering and undo/redo.
- Immediate structural persistence plus debounced text persistence with blur/submit flush.
- Visible save failures with queued retry snapshot rather than silent loss.
- Set-driven Champion cost groups and local Set assets.
- Active-List Trait calculation, invalid dynamic-selection indication, hide-below-breakpoint and next-breakpoint toggles.
- Stable Flet control keys and packaged integration smoke coverage in `tests_flet/`.

## Architecture

Flet remains confined to `app.py` and `builder_view.py`. Domain mutations stay in `TeamEditor`; Trait rules stay in `trait_engine`; SQLite stays in the persistence package. No presenter hierarchy, generic command framework, service interfaces or event bus were added.

## Verification in the implementation environment

The current 0.4.1 normal suite passes 564 tests with 2,149/2,149 production statements and 636/636 branches covered (100 percent for both). The exact pinned Flet 1.0.1 integration suite cannot be executed in the implementation sandbox because Flet is not installed there and network package installation is unavailable. The current local Set, database and Builder smokes, ASCII policy, document mirror and compile checks pass. The final Windows gate therefore runs Ruff, pytest, all existing smokes, Flet integration tests and the real application.

## User Windows baseline used for Block 4

The user-provided 0.3.1 run passed Ruff lint after normalization, 537 tests at 100 percent statement/branch coverage, ASCII/doc/compile checks, Set validation/inspection, persistence smoke, Builder smoke and Flet 1.0.1 startup.

## 0.4.1 corrective polish after first real desktop review

The first Windows 0.4.0 run confirmed 561 normal tests at 100 percent statement/branch coverage and a working desktop GUI. It also exposed five formatter-drift files, one Ruff import-order finding, a packaged-Flet coverage mismatch, and the Windows Developer Mode prerequisite before the Flutter test host could start.

Version 0.4.1 therefore:
- adopts the exact Ruff-compatible import/format direction from the user run;
- changes explicit Champion removal to delete/reindex the slot in the normal GUI;
- hides internal empty domain gaps from the normal List presentation and renders exactly one trailing empty/end target;
- replaces variable-width save text with a fixed-width saved/pending/error icon and tooltip;
- prevents transient blank name edits from producing warning-log spam while still rejecting blank completed names;
- gives packaged Flet tests the documented `--no-cov` driver invocation because the application runs in a separate packaged process;
- documents Windows Developer Mode as a prerequisite for Flutter plugin symlink support;
- prepares `BLOCK_05_PLAN.md` from current Flet drag/drop/testing APIs and current TFT-builder interaction patterns.

- List header actions are composed by a dedicated concrete helper, keeping List content rendering easier to extend without introducing a generic UI framework.

## User Windows 0.4.1 verification used by Block 5

The user subsequently verified 0.4.1 with uv 0.12.19, 564 normal tests at 100 percent statement/branch coverage, Set/database/Builder smokes and a successful Flet 1.0.1 GUI startup. Ruff lint passed; Ruff formatted two files before the final clean format check. The packaged integration command itself did not start because pinned Flet 1.0.1 rejects the newer `--` separator for `flet test`, so 0.5.0 changes the Windows packaged smoke command to direct pytest plugin execution: `uv run pytest tests_flet --no-cov`.
