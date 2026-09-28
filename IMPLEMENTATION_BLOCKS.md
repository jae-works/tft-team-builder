# TFT Team Builder - Implementation Blocks

This file is the current high-level implementation roadmap.

The roadmap is intentionally not immutable. After a block has been implemented and locally tested, later blocks may be split, merged, reordered or clarified if the actual code shows that this is the cleaner path. Any such change must be documented here, in `DEVELOPMENT_PLAN.md` when relevant, and in `PROGRESS.md`.

A block is only considered completed after:
- its intended functionality exists,
- the complete local test suite passes,
- the user receives a complete project ZIP,
- the final ZIP is integrity-checked,
- a SHA-256 checksum is generated from that final ZIP,
- `REQUIREMENTS.md` and `PROGRESS.md` are updated.

## Block 1 - Foundation, Set system and core models - final candidate v0.1.4

- [x] Create the runnable Python/Flet project foundation and central `pyproject.toml`.
- [x] Select and pin a current supported Python/Flet/dependency toolchain after compatibility verification.
- [x] Add configuration, centralized `pathlib`/`platformdirs` paths and logging.
- [x] Add Ruff configuration and a one-command pytest workflow.
- [x] Add an automated check that project-authored technical files remain within the agreed ASCII-safe character policy.
- [x] Implement the core models: Set, ChampionDefinition, TraitDefinition, Team, TeamList, Slot, ChampionInstance and TraitSelection.
- [x] Implement the Set package schema, loader and strict validator.
- [x] Add the developer-side Set import/build skeleton described in `SET_DATA_PIPELINE.md`.
- [x] Add one canonical valid offline Set fixture and deliberately invalid temporary test cases derived from it.
- [x] Add search-text normalization.
- [x] Add extensive tests for model invariants, Set validation and deterministic Set generation behavior that exists at this stage.
- [x] Provide a small developer command/entry point for building or validating Set packages without the GUI.

User-test goal:
- The project has a runnable Flet entry point and locally verified core/tooling code.
- A bundled development/sample Set validates successfully.
- Broken fixture Sets produce understandable errors.


Verification summary:
- 349 pytest tests pass in the current Block 1 implementation environment with no skipped tests.
- Branch-aware coverage is 99.63 percent, above the required 95 percent threshold.
- ASCII policy and Python compileall checks pass.
- Bundled `sample_set` regenerates deterministically and validates successfully.
- Set generation uses isolated staging and non-destructive overwrite behavior.
- Symbolic links and Windows junctions are treated as link-like filesystem redirects where containment matters.
- The user already verified 348 tests, Ruff lint, Set validation and Flet startup on Windows for v0.1.3. Version 0.1.4 applies the exact remaining Ruff formatter corrections and needs one final clean Windows recheck. See `BLOCK_01_REPORT.md`.

## Block 2 - SQLite persistence, migrations, autosave primitives and backups - implemented and Windows-verified v0.2.2

- [x] Select direct Python 3.13 `sqlite3` after comparing it with an ORM for this local aggregate-oriented store.
- [x] Store Teams, Lists, Slots, ChampionInstances and TraitSelections.
- [x] Add schema versioning and explicit migrations.
- [x] Add direct persistence services without repository/interface boilerplate beyond the concrete Team repository.
- [x] Use explicit transactions for critical writes.
- [x] Add backup creation, validation, retention and restore.
- [x] Add Team soft delete and restore.
- [x] Add autosave primitives for immediate saves and queued immutable snapshots.
- [x] Add persistence round-trip, restart, migration, rollback, corruption, large-Team and backup tests.
- [x] Add a developer database smoke command.
- [x] Keep browser/mobile persistence as a deferred target-specific evaluation rather than constraining the Windows store prematurely.

Verification summary:
- The v0.2.2 implementation audit and the user's Windows run both reached 438 pytest tests with no skips and 100 percent statement/branch coverage.
- The Team repository uses bounded aggregate queries and batched writes rather than per-Champion Trait queries.
- Backups are namespaced, path-safe, application-integrity checked and retained without touching unrelated database files.
- The Windows v0.2.2 run also passed formatter-check, ASCII policy, document mirrors, compileall, Set validation/inspection, database smoke and Flet startup. Ruff lint found one SIM300 equivalent-expression style issue; v0.3.0 applies Ruff's recommended form before the Block 3 implementation.

User-test goal:
- Data survives process restart exactly.
- Backups are generated and can be restored safely.
- Deleted Teams can be restored at data level.
- Ruff lint and format checks are completely clean.

## Block 3 - Core builder logic: slots, move/copy/swap, Trait engine and undo/redo - implemented v0.3.0

The concrete behavior contract remains documented in `BLOCK_03_PLAN.md`; implementation evidence is in `BLOCK_03_REPORT.md`.

- [x] Implement direct UI-independent editing operations for Lists, Slots, Champion instances, names and primary List changes.
- [x] Implement clear/insert/remove/compact semantics without losing surviving instance identity.
- [x] Implement same-List and cross-List Move semantics: empty targets move, occupied targets swap, and instance IDs are preserved.
- [x] Implement Copy semantics with a new instance ID; occupied targets insert and shift instead of overwriting data.
- [x] Implement List create/duplicate/reorder/clear/delete behavior, including deterministic primary-List replacement and last-List protection.
- [x] Implement Trait calculation from validated Set data for UNIQUE_CHAMPION and UNIQUE_INSTANCE counting.
- [x] Implement Trait breakpoints, next-breakpoint progress and deterministic Trait ordering.
- [x] Validate every dynamic Trait selection rule and both PER_INSTANCE/PER_CHAMPION scopes; invalid required choices are reported and do not silently count.
- [x] Treat PER_CHAMPION choices as semantic sets so selection ordering cannot create a false conflict.
- [x] Implement small Team-scoped undo/redo history using exact reversible snapshots, not a generic command framework.
- [x] Ensure successful edits update `Team.updated_at`; undo/redo restores historical timestamps exactly.
- [x] Make failed edits atomic and keep failed/no-op edits out of history.
- [x] Add a `builder-smoke` developer command that exercises editing, Trait calculation and undo/redo against the bundled sample Set.
- [x] Add extensive edge-case and large-realistic-input tests while keeping the 100 percent statement/branch coverage gate.

Verification summary:
- The 0.3.0 Windows run passed all 529 tests with no skips and 100 percent statement/branch coverage across 1,799 production statements and 564 branches.
- ASCII policy, project-document mirror, compileall, sample Set validation/inspection, persistence smoke, Builder smoke and Flet startup all passed on Windows.
- Ruff formatted four files and then reported two test-only lint findings (`PTH201` and `RUF043`); version 0.3.1 fixes both exact findings and adds extra semantic regression coverage.
- The 0.3.1 audit suite expands to 537 tests while retaining 100 percent production statement/branch coverage; one pinned Windows rerun remains the final quality gate.
- The user completed the pinned Windows 0.3.1 gate: Ruff lint/format, 537 tests at 100 percent coverage, all smokes and Flet startup passed.

User-test goal:
- The Windows verification run demonstrates exact slot behavior, duplicate counting, dynamic Trait validation, moves, swaps, copies, List operations, Trait results and full-state undo/redo restoration.

## Block 4 - First complete functional Builder GUI - implemented v0.4.0, polished v0.4.1

Detailed behavior, persistence wiring and Flet integration-test scope are defined in `BLOCK_04_PLAN.md`.

- Build the desktop Flet shell.
- Build the three-column Builder layout: Traits | Lists | Champion library.
- Add Team/List name editing.
- Add primary List star and active List handling.
- Add List create/delete/duplicate/reorder/clear/compact controls.
- Add Champion library grouped by cost.
- Add basic reliable Champion placement/removal interaction.
- Wire Trait display to the active List.
- Wire real persistence/autosave and undo/redo to GUI actions.
- Add independent vertical panel scrolling and horizontal List scrolling.
- Add stable control keys and practical Flet integration smoke tests in addition to the full existing suite.

User-test goal:
- A real Team can be built visually and survives restart.
- Core Builder operations work from the GUI.

## Block 5 - Full desktop interaction, Drag & Drop, search and Builder polish - implemented v0.5.0

- [x] Add Champion drag/drop from the library while retaining explicit click-add.
- [x] Add dense same-/cross-List moves to a List end.
- [x] Add occupied-slot move/swap behavior.
- [x] Keep explicit copy-to-active behavior without undocumented drag modifiers.
- [x] Add Champion and Trait search using the normalizer.
- [x] Add compact Champion details/tooltips and stable interaction keys.
- [x] Add dynamic Trait selection dialogs for existing rule/scope modes.
- [x] Add relevant keyboard shortcuts and focus behavior.
- [x] Reduce List-header clutter with a maintenance overflow menu.
- [x] Add exhaustive boundary tests and packaged-Flet smoke coverage for supported Tester interactions.

User-test goal:
- The Builder behaves like the intended desktop product rather than a technical prototype.

## Block 6 - Start page and Team library - planned v0.6

- Build the Start page.
- Add Set selection.
- Add Team creation/opening/deletion/restoration flow.
- Show Team cards using the primary List preview.
- Add Team-name search.
- Add Champion mini-selection for similarity search.
- Implement best-matching List calculation per Team.
- Implement the required ranking rules, including duplicate selected Champions.
- Preserve useful navigation/search state when returning from the Builder.
- Add exhaustive similarity-search tests.

User-test goal:
- Multiple Teams can be managed as a useful local library and found by name or Champion similarity.

## Block 7 - Real TFT Set data pipeline and production Set package - planned v0.7

- Finish the reproducible Set import pipeline using the maintained HTTP/download tooling selected for the project (planned `httpx`).
- Use pinned/recorded Riot Data Dragon inputs as the preferred official visible-data/asset source.
- Use pinned CommunityDragon inputs only as supplemental/cross-check metadata where required.
- Record provenance and source hashes.
- Implement source conflict reporting.
- Implement candidate inventory with INCLUDED / EXCLUDED-with-reason / ERROR accounting.
- Apply explicit project-owned overrides only where required.
- Extract/copy local runtime assets.
- Generate and validate at least one real usable TFT Set package.
- Keep the normal application fully offline from these sources.
- Add importer/source-fixture tests and reproducibility checks.

User-test goal:
- The Builder uses real TFT Champions, Traits, costs and local images from a validated Set package.

## Block 8 - TFT Team Planner codes and complete native import/export - planned v0.8

- Implement the supported TFT Team Planner code codec for the chosen Set/data format.
- Export a List and copy the code to the clipboard.
- Add the temporary >10-unit export-selection dialog when required by the target format.
- Add code import preview and validation.
- Make code import a single undoable action.
- Implement a versioned native full-Team export/import format.
- Preserve all internal Team/List/Slot/Trait-selection data in the native format.
- Add round-trip and failure-case tests.

User-test goal:
- Lists can be exchanged with TFT's Team Planner where supported.
- Complete Teams can be exported and re-imported exactly.

## Deferred platform work after desktop v1.0

Browser and mobile/tablet support are not part of the current nine-block desktop release plan, but they remain valid future directions. Any future platform block must re-evaluate persistence, filesystem behavior, UI layout, packaging, dependency compatibility, security and licensing for that target. Flet is retained partly because it provides official web, Android and iOS build paths.

## Block 9 - Hardening, recovery, performance, Windows packaging and v1.0 release candidate

- Improve error messages and failure screens.
- Finish save-state feedback and backup restore behavior.
- Add missing-asset fallbacks.
- Test large synthetic libraries and large Lists.
- Optimize obvious bottlenecks without unnecessary architectural complexity.
- Polish keyboard/focus/long-name behavior.
- Finalize logging and diagnostics.
- Run the full end-to-end regression suite.
- Build the Windows executable/package.
- Verify the writable data directory behavior.
- Bundle validated Set data and required legal/project documents.
- Test a clean extracted/installed copy without a Python development environment.
- Re-check then-current Riot rules before any public release.
- Produce the final complete release ZIP and SHA-256 checksum.

User-test goal:
- The application can be used as a normal Windows desktop program from a clean installation/extraction.

## Current block status

- [x] Block 1 - Foundation, Set system and core models
- [x] Block 2 - SQLite persistence, migrations, autosave primitives and backups
- [x] Block 3 - Core builder logic, Trait engine and undo/redo
- [x] Block 4 - First complete functional Builder GUI
- [x] Block 5 - Full desktop interaction, search and Builder polish
- [ ] Block 6 - Start page and Team library
- [ ] Block 7 - Real TFT Set data pipeline and production Set package
- [ ] Block 8 - TFT Team Planner codes and native import/export
- [ ] Block 9 - Hardening, Windows packaging and v1.0 release candidate
