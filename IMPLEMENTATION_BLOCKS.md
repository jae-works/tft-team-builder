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

## Block 1 - Foundation, Set system and core models - complete v0.1.0

- [x] Create the runnable Python/Flet project foundation and central `pyproject.toml`.
- [x] Select and pin a current supported Python/Flet/dependency toolchain after compatibility verification.
- [x] Add configuration, centralized `pathlib`/`platformdirs` paths and logging.
- [x] Add Ruff configuration and a one-command pytest workflow.
- [x] Add an automated check that project-authored technical files remain within the agreed ASCII-safe character policy.
- [x] Implement the core models: Set, ChampionDefinition, TraitDefinition, Team, TeamList, Slot, ChampionInstance and TraitSelection.
- [x] Implement the Set package schema, loader and strict validator.
- [x] Add the developer-side Set import/build skeleton described in `SET_DATA_PIPELINE.md`.
- [x] Add small valid and deliberately invalid offline Set fixtures.
- [x] Add search-text normalization.
- [x] Add extensive tests for model invariants, Set validation and deterministic Set generation behavior that exists at this stage.
- [x] Provide a small developer command/entry point for building or validating Set packages without the GUI.

User-test goal:
- The project has a runnable Flet entry point and locally verified core/tooling code.
- A bundled development/sample Set validates successfully.
- Broken fixture Sets produce understandable errors.


Verification summary:
- 204 pytest tests passed in the implementation environment.
- ASCII policy check passed.
- Python compileall passed for source, tools and tests.
- Bundled `sample_set` was regenerated deterministically and validated successfully.
- Set generation uses isolated staging and non-destructive overwrite behavior.
- Source manifests verify both generated data files and required assets.
- Exact Flet/Ruff executable checks remain for the user environment because the implementation sandbox cannot download missing packages. See `BLOCK_01_REPORT.md`.

## Block 2 - SQLite persistence, migrations, autosave primitives and backups - planned v0.2

- Add SQLite persistence using the current maintained persistence stack chosen for the project (planned SQLAlchemy 2.x).
- Store Teams, Lists, Slots, ChampionInstances and TraitSelections.
- Add schema versioning and explicit migrations (planned Alembic).
- Add straightforward repository/service functions without unnecessary abstraction layers.
- Use transactions for critical writes.
- Add backup creation and restore foundations.
- Add Team soft delete/restore data model.
- Add persistence round-trip and migration tests.
- Add a developer/demo path that creates data, reloads it and verifies equality.

User-test goal:
- Data survives process restart exactly.
- Backups are generated.
- Deleted Teams can be restored at data level.

## Block 3 - Core builder logic: slots, move/copy/swap, Trait engine and undo/redo - planned v0.3

- Implement slot add/remove/move/swap/compact behavior.
- Implement cross-List Copy and Move semantics.
- Implement duplicate-champion behavior.
- Implement Trait calculation from Set data.
- Ensure duplicate Champion IDs do not normally double-count native Traits.
- Implement Trait breakpoints and next-breakpoint state.
- Implement dynamic Trait selection rules.
- Implement command-based undo/redo for the core edit operations.
- Add extensive edge-case tests.

User-test goal:
- Included tests/demos show correct duplicate counting, moves, swaps, copies and exact undo/redo restoration.

## Block 4 - First complete functional Builder GUI - planned v0.4

- Build the desktop Flet shell.
- Build the three-column Builder layout: Traits | Lists | Champion library.
- Add Team/List name editing.
- Add primary List star and active List handling.
- Add List create/delete/duplicate/reorder/clear/compact controls.
- Add Champion library grouped by cost.
- Add basic reliable Champion placement/removal interaction.
- Wire Trait display to the active List.
- Wire real persistence/autosave and undo/redo to GUI actions.
- Add practical smoke tests in addition to the full existing suite.

User-test goal:
- A real Team can be built visually and survives restart.
- Core Builder operations work from the GUI.

## Block 5 - Full desktop interaction, Drag & Drop, search and Builder polish - planned v0.5

- Add Champion drag/drop from the library.
- Add moving/reordering within Lists.
- Add occupied-slot swaps.
- Add cross-List Copy/Move mode.
- Add click-to-place interaction.
- Add Champion and Trait search using the normalizer.
- Add hover/details information.
- Add dynamic Trait selection dialogs.
- Add independent panel/list scrolling behavior.
- Add relevant keyboard shortcuts and focus behavior.
- Add tests for the new interaction logic where it can be tested below the GUI layer.

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
- [ ] Block 2 - SQLite persistence, migrations, autosave primitives and backups
- [ ] Block 3 - Core builder logic, Trait engine and undo/redo
- [ ] Block 4 - First complete functional Builder GUI
- [ ] Block 5 - Full desktop interaction, search and Builder polish
- [ ] Block 6 - Start page and Team library
- [ ] Block 7 - Real TFT Set data pipeline and production Set package
- [ ] Block 8 - TFT Team Planner codes and native import/export
- [ ] Block 9 - Hardening, Windows packaging and v1.0 release candidate
