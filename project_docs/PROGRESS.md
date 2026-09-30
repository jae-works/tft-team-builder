# TFT Team Builder - Progress

Current version: 0.7.0
Current status: Block 7 dataset correction is implemented locally. Reviewed invariants now live in each Set package instead of the Python checker, Kha'Zix supports zero through all four evolution Traits, and `SET_REVIEW.md` is generated from validated Set data. The previously reported packaged-Flet/build warnings are intentionally deferred to the next correction pass.
Next planned work: run the dedicated code/build-warning correction and full quality audit from the user's Windows `uv 0.12.19` environment. After that gate is green, proceed to Block 8; the later Block 9 hardening pass remains the place for the final broad GUI/HCI/accessibility audit.

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
- [x] 438 tests passed with 0 skips in the version 0.2.2 implementation audit.
- [x] 100.00 percent statement and branch coverage in the implementation environment.

## Version 0.2.1 Windows verification

- [x] 425 pytest tests passed with no skips.
- [x] Statement and branch coverage both reached 100.00 percent.
- [x] Ruff lint passed.
- [ ] Ruff format found exactly three formatting-only files: `src/tft_builder/persistence/team_repository.py`, `tests/test_persistence_backups.py`, and `tests/test_persistence_database.py`.
- [x] ASCII policy passed.
- [x] Project document mirror check passed.
- [x] `compileall` passed.
- [x] Bundled Set validation and inspection passed.
- [x] Database smoke round-trip and backup passed.
- [x] Flet 1.0.1/Flutter 3.44.8 started the application successfully.

## Version 0.2.2 final correction pass

- [x] Apply the three exact Ruff formatter corrections reported by the Windows 0.2.1 run.
- [x] Remove the stale unused `APP_VERSION` runtime constant so package version metadata has no redundant source-code copy.
- [x] Reject undefined `CUSTOM_SET_RULE` Trait counting because Set schema v1 has no declarative custom-rule data.
- [x] Validate required SQLite schema tables/columns and exact migration history as part of application integrity checks.
- [x] Reject malformed current databases during initialization instead of trusting `PRAGMA user_version` alone.
- [x] Require explicit backup timestamps to be timezone-aware.
- [x] Add corruption and timestamp regression tests; implementation-audit total is 438 tests at 100 percent statement/branch coverage.
- [x] Add `BLOCK_03_PLAN.md` with concrete edit, Trait and undo/redo semantics for the next block.

## Version 0.2.2 Windows verification

- [x] 438 pytest tests passed with no skips.
- [x] Statement and branch coverage both reached 100.00 percent.
- [x] `uv run ruff format .` reformatted one file; the following `ruff format --check` reported all 74 files formatted.
- [ ] Ruff lint reported one remaining `SIM300` Yoda-condition warning in `persistence/database.py`; version 0.3.0 applies the exact recommended rewrite.
- [x] ASCII policy passed.
- [x] Project document mirror check passed.
- [x] `compileall` passed.
- [x] Bundled Set validation and inspection passed.
- [x] Database smoke round-trip and backup passed.
- [x] Flet 1.0.1/Flutter 3.44.8 started the application successfully.

## Implemented in Block 3 - version 0.3.0

- [x] Added concrete `TeamEditor` operations for Team/List rename, primary List changes, List creation/duplication/deletion/reorder/clear/compact, slot insertion/removal/clear, Champion add/move/swap/copy, and Trait selection updates.
- [x] Core edits are atomic: invalid edits leave the Team and history unchanged; no-op edits create no history entry.
- [x] Successful edits update `Team.updated_at` once using timezone-aware UTC; undo/redo restores exact historical timestamps.
- [x] In-memory Team-scoped undo/redo uses exact snapshots and preserves the top-level Team object identity.
- [x] New edits after undo clear the redo branch; failed/no-op edits after undo preserve it.
- [x] Added Flet-independent Trait calculation for UNIQUE_CHAMPION and UNIQUE_INSTANCE.
- [x] Added breakpoint, next-breakpoint progress, deterministic ordering and zero-contribution hiding.
- [x] Added validation for NONE, EXACTLY_ONE, ZERO_OR_ONE, ANY_NUMBER and EXACTLY_N dynamic selections.
- [x] Added PER_INSTANCE and PER_CHAMPION handling; PER_CHAMPION compares semantic sets, not tuple order.
- [x] Invalid dynamic selections are reported explicitly and do not silently contribute.
- [x] Added `builder-smoke` developer command against the bundled sample Set.
- [x] Added large realistic List/Trait tests to catch accidental poor scaling in core loops.
- [x] Fixed the remaining Windows-reported Ruff `SIM300` condition in the Block 2 database hardening code.
- [x] 529 pytest tests pass with 0 skips in the Block 3 implementation environment.
- [x] Statement and branch coverage both remain 100.00 percent.

## Version 0.3.0 Windows verification

- [x] 529 pytest tests passed with no skips.
- [x] Statement and branch coverage both reached 100.00 percent across 1,799 production statements and 564 branches.
- [ ] `uv run ruff format .` reformatted four files, so the delivered 0.3.0 archive was not formatter-clean before the local normalization pass.
- [ ] Ruff lint then reported two test-only findings in `tests/test_trait_engine.py`: `PTH201` for `Path(".")` and `RUF043` for a regex passed to `match=` without an explicit raw string.
- [x] The following Ruff format check reported all 80 files formatted.
- [x] ASCII policy passed.
- [x] Project document mirror check passed.
- [x] `compileall` passed.
- [x] Bundled Set validation and inspection passed.
- [x] Database smoke round-trip and backup passed.
- [x] Block 3 Builder smoke passed with expected slot, Trait and undo/redo results.
- [x] Flet 1.0.1 / Flutter 3.44.8 started successfully.

## Version 0.3.1 correction and Block 4 preparation

- [x] Apply the exact Ruff `PTH201` correction: use `Path()` instead of `Path(".")`.
- [x] Apply the exact Ruff `RUF043` correction: make the regex passed to `pytest.raises(..., match=...)` explicitly raw.
- [x] Re-audit Block 3 edit/history/Trait behavior instead of relying on coverage percentage alone.
- [x] Add semantic regression tests for returned-ID stability across undo/redo, occupied-slot removal restoration, same-List copy after the source, a full multi-operation history round-trip, native/dynamic overlap counting, multiple dynamic contributors and ANY_NUMBER invalid-choice handling.
- [x] Add an integration test showing TeamEditor state can be saved, undone and saved again through AutosaveService/TeamRepository without a new adapter layer.
- [x] Remove stale pre-Block-3 wording from the application shell and project handoff documents.
- [x] Prepare Flet integration testing with pytest `asyncio_mode = "auto"` while keeping the already-pinned `flet[test]==1.0.1` dependency.
- [x] Add `BLOCK_04_PLAN.md` with concrete startup, active-List, layout, persistence, testing and error-handling rules.
- [x] Make both required Trait display toggles explicit Block 4 scope and define that transient active-List navigation is not restored by domain undo/redo.
- [x] Move independent panel/List scrolling into Block 4 planning and remove the duplicate later-block roadmap entry.
- [x] Correct stale requirement statuses for the already-implemented detailed Trait and slot tests, complete-project ZIP rule and ZIP checksum rule.
- [x] Expand the current local audit suite from 529 to 537 tests while keeping the production coverage gate at 100 percent statement and branch coverage.
- [x] Record active List state as transient GUI state and direct Flet composition/stable-key testing as explicit Block 4 decisions.
- [x] Update the machine-readable manifest and mirrored project documents for version 0.3.1 and the prepared Block 4 contract.
- [x] Remove one redundant Team invariant validation per attempted edit and reuse the existing Trait contributor map for Trait-ID membership checks; current production coverage is 1,797 statements / 564 branches at 100 percent.
- [x] Run a deterministic 30,000-operation TeamEditor stress audit with invariant/identity checks after every operation.
- [x] Run a 2,500-List independent Trait-count oracle audit covering both counting modes and native/dynamic overlap.
- [x] Audit all production functions for exact non-trivial body duplication; no merge-worthy copy/paste groups remain.
- [x] Consolidate the only exact non-trivial duplicate test helper into one parametrized two-case Set-builder regression test; no exact duplicate function-body groups remain across project Python code.

## Completed Windows verification before Block 4

- [x] Run `uv --version` and confirm the configured 0.12.x range is active.
- [x] Run `uv lock --check`.
- [x] Run `uv sync --frozen`.
- [x] Run `uv run ruff format .` once; a second/check run must report no changes.
- [x] Run `uv run ruff check .`.
- [x] Run `uv run ruff format --check .`.
- [x] Run `uv run pytest` on Windows and confirm the complete suite passes with no skips and 100 percent statement/branch coverage.
- [x] Run `uv run python tools/check_ascii.py`.
- [x] Run `uv run python tools/sync_project_docs.py --check`.
- [x] Run `uv run python -m compileall -q src tests tools`.
- [x] Run `uv run tft-builder-dev validate-set src/assets/sets/sample_set`.
- [x] Run `uv run tft-builder-dev inspect-set src/assets/sets/sample_set`.
- [x] Run `uv run tft-builder-dev database-smoke .runtime-smoke`.
- [x] Run `uv run tft-builder-dev builder-smoke src/assets/sets/sample_set`.
- [x] Run `uv run flet --version`.
- [x] Run `uv run flet run`.

## Implemented in Block 4 - version 0.4.0

- [x] Replace the placeholder shell with the real three-column Traits | Lists | Champion library Builder.
- [x] Load the most recently updated Team from SQLite or create and persist a first Team when the library is empty.
- [x] Keep active List navigation transient and separate from the persisted primary List.
- [x] Wire Team/List rename, List create/duplicate/reorder/clear/compact/delete, primary List, Champion add/remove and undo/redo to TeamEditor.
- [x] Save structural edits immediately and text edits through queued immutable snapshots with debounce plus blur/submit flush.
- [x] Surface persistence failures without silently discarding the queued snapshot.
- [x] Render active-List Trait results, invalid dynamic selections and both required Trait display toggles.
- [x] Build Champion cost groups from Set data without a hardcoded maximum cost.
- [x] Add stable Flet control keys and a packaged Flet integration smoke suite in `tests_flet/`.
- [x] Add extensive GUI-boundary unit tests while retaining the 100 percent production statement/branch coverage gate.
- [x] Restore `.github/workflows/quality.yml` to the complete handoff after the user-created Windows ZIP omitted the hidden `.github` directory.
- [x] Exclude coverage/bytecode/cache artifacts from the delivered replacement project.

## Block 4 follow-up - version 0.4.1

User Windows 0.4.0 run:
- [x] uv 0.12.19 / Python 3.13.5 environment resolved successfully.
- [x] 561 normal tests passed with 100 percent statement and branch coverage.
- [x] ASCII, document mirror, compileall, Set validation/inspection, database smoke, Builder smoke and normal Flet startup passed.
- [ ] Initial Ruff format check found five files requiring formatting.
- [ ] Ruff lint found one `I001` import-order issue in `builder_view.py`.
- [ ] Packaged Flet integration did not reach the app because Windows Developer Mode was disabled, so Flutter could not create plugin symlinks.
- [ ] The packaged Flet host pytest also inherited the normal application coverage arguments, which is inappropriate because the packaged app executes in another process.

Version 0.4.1 corrections:
- [x] Apply the Ruff import-order correction and align new source with Ruff 0.16.9 formatting style.
- [x] Normal GUI removal deletes/reindexes the slot; internal empty domain gaps are not rendered as empty cards.
- [x] Exactly one trailing empty/end position is rendered for every List.
- [x] Replace variable-width save text with a fixed-width saved/pending/error icon and tooltip.
- [x] Avoid transient blank-name warning spam while retaining final non-empty validation.
- [x] Add regression tests for dense slots, trailing target, fixed-width save state and name-edit behavior.
- [x] Separate packaged Flet driver coverage from normal application coverage; pinned Flet 1.0.1 is now invoked through `uv run pytest tests_flet --no-cov`.
- [x] Restore the hidden GitHub workflow omitted again by the manually created Windows ZIP and update its Flet command.
- [x] Prepare `BLOCK_05_PLAN.md` using current Flet drag/drop/testing APIs and current TFT team-builder interaction patterns.

Exact packaged Flet verification still requires Windows Developer Mode to be enabled.


- Split concrete List action composition out of the List card renderer so Block 5 can extend list interactions without growing one oversized GUI method.

## Implemented in Block 5 - version 0.5.0

- [x] Fixed the clipped/missing Champion remove action by separating draggable card content from a fixed compact action row; two-line names no longer push actions outside the card.
- [x] Added Champion search by name/aliases and Trait display names while preserving cost grouping.
- [x] Added Trait-click library filtering and clear-filter behavior.
- [x] Kept click-add and added native Flet Draggable/DragTarget interactions for library-to-end, instance-to-end and occupied-slot move/swap.
- [x] Added dense `TeamEditor.move_champion_to_end()` semantics with exact instance/history behavior.
- [x] Added explicit placed-Champion copy to the active List without relying on undocumented modifier state.
- [x] Added dynamic Trait selection dialogs for all existing rule/cardinality modes, with shared `validate_dynamic_selection()` logic from the Trait engine.
- [x] Added atomic PER_CHAMPION selection updates through `TeamEditor.set_champion_trait_selection()`.
- [x] Added Ctrl+Z, Ctrl+Y, Ctrl+Shift+Z, Ctrl+F and Escape handling through existing Builder actions.
- [x] Moved low-frequency List actions into a compact overflow menu while keeping active/primary/reorder controls visible.
- [x] Corrected the packaged Flet command for pinned Flet 1.0.1 to `uv run pytest tests_flet --no-cov`; the user Windows run proved its `flet test` CLI rejects the newer `--` separator form.
- [x] Expanded the normal suite to 585 tests with 2,443/2,443 production statements and 742/742 branches covered.
- [x] Added `BLOCK_05_REPORT.md` and prepared deterministic Team-library/similarity behavior in `BLOCK_06_PLAN.md`.

## Version 0.5.0 release gate still requiring the exact Windows toolchain

- [ ] `uv run ruff format --check .` and `uv run ruff check .` must pass on Ruff 0.16.9.
- [ ] `uv run pytest` must reproduce the complete 585-test 100 percent coverage result on Windows.
- [ ] `uv run pytest tests_flet --no-cov` must pass with Developer Mode enabled.
- [ ] Manual Windows review must confirm visible Remove actions and native drag/drop behavior.

## Block 5 post-Windows correction - version 0.5.1

- Real Windows 0.5.0 normal suite passed 585 tests at 100 percent statement/branch coverage.
- Ruff 0.16.9 formatted three files and then reported two E731 lambda-assignment findings in the dynamic Trait dialog. Both are replaced by one local named callback with no behavior change.
- The packaged Flet/Flutter host provisioned successfully and exited with code 0, but the app page contained no `builder-team-name` control. Exact Flet 1.0.1 source confirms device-mode tests run the packaged embedded-Python app rather than the host `main` callback.
- Root cause: `src/main.py` called `ft.run()` only under `if __name__ == "__main__"`; packaged runtime imports the configured entry module, so normal `flet run` worked while the packaged test page stayed empty. `ft.run()` now executes at module scope and a regression test runs the entry file with a non-`__main__` module name.
- Removed one unused Champion grouping helper, cached immutable Champion/Trait lookup dictionaries once per BuilderView, and consolidated repeated occupied-source-slot validation in TeamEditor.
- A proposed removal of BuilderView's pre-edit `deepcopy()` was rejected after an existing regression test demonstrated that it would couple change detection to undo-history internals and miss intentionally simulated state changes.
- Normal local suite after the correction: 586 tests, 100 percent production statement and branch coverage, zero expected skips.
- A bounded deterministic post-refactor stress audit completed 750 successful mixed add/remove/copy/dense-move edits across three Lists, validating Team invariants and Champion instance-ID uniqueness after every edit.
- `tests_flet` patches only Flet 1.0.1's leaking temporary-port probe with an equivalent context-managed socket; normal ResourceWarning handling remains strict and no broader warning suppression is added.
- Block 6 planning now explicitly follows undo-first deletion, clear empty/no-result states, visible search clear/filter state, concise task-oriented navigation, and separation of destructive actions from common actions.

## Completed in Block 6

- [x] Application startup opens the local Team Library instead of implicitly selecting one Team.
- [x] Set selector controls new-Team creation and Champion-similarity search without migrating existing Teams.
- [x] Team create/open/back navigation uses one shared repository and preserves Library session search/filter state.
- [x] Opening marks the Team opened and then reloads it before Builder construction to avoid stale last-opened timestamps.
- [x] Team-name search uses the existing normalized text rules.
- [x] Champion similarity uses deterministic multiset scoring and evaluates each List independently before selecting the Team's best List.
- [x] Duplicate desired Champions affect ranking intentionally.
- [x] Team cards show primary-List previews, Set identity, List count and updated time; missing Sets disable Open instead of rewriting data.
- [x] Normal deletion is immediate soft delete with visible Restore and a Trash view.
- [x] Deleting the final visible Team still leaves the Restore action visible next to the explicit empty-library state.
- [x] Permanent deletion is separated from routine actions and requires consequence-focused confirmation.
- [x] Empty library, empty Trash and no-results states provide explicit explanation and useful create/reset actions.
- [x] Shared Set display/search helpers remove Builder/Library presentation duplication.
- [x] Builder back navigation flushes queued text and remains in Builder when that flush fails.
- [x] Packaged Flet smoke now uses a bounded readiness wait for the library-first app rather than assuming one settle means embedded Python startup is complete.
- [x] Block 7 real TFT Set data pipeline plan prepared.

Block 6 local verification candidate:
- 617 normal tests passed with 2701 production statements and 800 branches at 100 percent coverage.
- 61 Python files passed the manual structural/duplicate-function audit.
- ASCII, project-doc mirror, compileall, sample Set validation/inspection, persistence smoke and Builder smoke passed.
- Exact Ruff 0.16.9 and packaged Flet/Flutter verification remain the Windows release gate.

## Version 0.6.1 quality and HCI audit

- [x] Add `TeamRepository.load_all()` so Team-library aggregate reads use four SELECTs independent of Team count instead of one ID query plus four queries per Team.
- [x] Cache the complete Library aggregate snapshot for the mounted LibraryView and invalidate it only after repository mutations; Team/champion search, similarity chips, Set filtering and Trash toggling no longer re-read SQLite on each keystroke.
- [x] Share exact Flet lazy-import/event/text adapters between BuilderView and LibraryView through one small UI-only helper module instead of maintaining duplicated functions.
- [x] Similarity-result cards preview the actual best-matching List; normal unfiltered cards still preview the primary List.
- [x] Add a repository policy test preventing exact non-trivial production-function copy/paste duplication from silently returning.
- [x] Remove one repeated Team List-ID set construction during invariant validation.
- [x] Correct stale requirement status for already-implemented Start-page search/similarity behavior and atomic invalid-Set rejection.
- [x] Expand HCI/accessibility requirements with non-drag operation paths, focus restoration/not-obscured behavior, semantic status announcements, hover alternatives, contrast, shortcut discoverability and explicit target-size baselines.
- [x] Expand Block 9 hardening scope to include a concrete semantics/focus/contrast/scaling audit and a post-real-data decision gate for decomposing the very large BuilderView only if it still materially improves maintainability.
- [x] Refine Block 7 acquisition requirements with HTTPS-only release sources, bounded streamed downloads and project-controlled cache names.
- [x] 623 normal tests pass with 2721 production statements and 808 branches at 100 percent coverage in the implementation environment.
- [x] A 300-Team aggregate benchmark completed through the new four-query batch path; exact performance acceptance remains a Block 9 real-library audit rather than a machine-specific timing requirement.


## Version 0.7.0 post-Windows correction and Block 7 readiness

User Windows 0.6.1 run:
- [x] 623 normal tests passed with 2721 production statements and 808 branches at 100 percent coverage.
- [x] ASCII, project-document mirror, compileall, sample Set validation/inspection, database smoke, Builder smoke and normal Flet startup passed.
- [ ] Initial Ruff format check found nine files requiring formatting; formatting was then applied.
- [ ] Ruff lint still found three unused imports after formatting.
- [ ] `git diff --check` found one trailing blank line at the end of `builder_view.py`.
- [ ] Packaged Flet/Flutter integration connected its RemoteTester but the Flutter process exited with code 79 before the Library became test-visible.
- [ ] The failed packaged run also surfaced Flet 1.0.1 dropping a RemoteTester `StreamWriter` without closing it first, which became a strict ResourceWarning.

Version 0.7.0 corrections:
- [x] Remove all three reported unused imports and the trailing EOF whitespace.
- [x] Keep all touched Python in the Ruff 0.16.9 formatting shape observed in the Windows run.
- [x] Validate bundled Sets once during application initialization and reuse the validated `LoadedSet` objects when creating the runtime instead of re-reading/hashing the complete Set tree.
- [x] Cache immutable Champion/Trait ID maps once per `LoadedSet` so Builder/Library hot paths do not rebuild dictionaries on each property access.
- [x] Render localized Set display names in the Library while retaining stable technical Set IDs internally.
- [x] Wrap selected similarity Champion controls and explicitly tell users when the candidate list is capped at 20 results.
- [x] Patch only the Flet 1.0.1 integration-test host so a disconnected RemoteTester writer is closed before the upstream cleanup drops its reference; no warning suppression and no production Flet internals are modified.
- [x] Avoid `pump_and_settle()` during the indeterminate packaged-app startup animation; readiness polling now uses single-frame `pump()` calls and keeps settled waits for completed user interactions.
- [x] Restore `.github/workflows/quality.yml`, which was again omitted by the user-created ZIP even though project tests require the complete handoff to contain it.
- [x] Refine Block 7 around concrete acquisition/build steps, immutable source cache records, offline runtime guarantees, long-name/real-asset HCI cases and one-pass startup validation.
- [x] Keep the large BuilderView decomposition as a Block 9 decision gate; the current structural/duplicate-function audit does not justify a large rewrite now.
- [x] 627 normal tests pass locally with 2736 production statements and 810 branches at 100 percent coverage.
- [ ] Exact Ruff 0.16.9 checks and the packaged Windows Flet/Flutter integration flow must be rerun on Windows before closing the v0.7.0 release gate.


## Block 7 implementation

- [x] Runtime schema v3 supports complete Set-declared Item reference data plus executable Builder-relevant exceptional semantics without a generic mechanics metadata layer.
- [x] Weighted/dynamic Trait contributions support Lux, Kha'Zix and Elder-Dragon-style data without runtime Champion branches; Elder Dragon is verified as 2 slots/+2 Riftbeast.
- [x] Developer importer is pinned to exact Data Dragon/CommunityDragon revisions and uses bounded HTTPS downloads plus local cache.
- [x] Generated packages contain source candidate accounting, provenance hashes and `SET_OVERVIEW.md`.
- [x] `inspect-set` prints Champion/Trait/Item inventories.
- [x] Adding a Set requires a valid folder only; no second activation registry exists.
- [x] Rival exact-count activation and Eclipse derived activation are modeled generically instead of being forced through ordinary >= breakpoints.
- [x] Set Item acquisition applies a reviewed canonical boundary instead of shipping all broad Set-declared engine records; the pinned Set 18 guard is 136 references across component/craftable/emblem/artifact/radiant families.
- [x] Current Part 3 normal suite passes 669 tests with 2938 production statements and 888 branches at 100 percent statement/branch coverage.
- [x] Verify the full Set 18 acquisition/build path with deterministic synthetic Data Dragon sprite sheets; 12 shared sprites produce 246 validated runtime PNGs and a 21-source lock shape.
- [x] Historical Part-3 harness corrected Data Dragon indexing to stable record IDs and tested shared sprite acquisition; post-data audit later superseded sprite acquisition for release assets.
- [x] Normalize official localized Set names and Item descriptions before packaging; generated EN/DE catalogs contain no unresolved Riot markup in the verified harness.
- [x] Run the first official networked acquisition; its sprite-bounds failure triggered the release-asset correction, and the later individual-image acquisition succeeded with a reviewed real `source_lock.json`.
- [x] Validate the generated `src/assets/sets/enchanted_wilds` package and run the Set-18 reviewed verifier; the final Windows/Flet gate remains Part 4.


## Block 7 data-completion Part 1

- [x] Reconciled the pinned Set 18 source roster instead of relying on guessed Champion IDs.
- [x] Added reviewed cardinality guards for 91 raw Champion records, 65 logical Champions and 36 Traits.
- [x] Added 17 explicit helper/encounter/pseudo-unit exclusions.
- [x] Normalized base Lux plus nine origin source records into one logical Lux.
- [x] Added optional dynamic-choice portrait assets and sample/runtime validation coverage.
- [x] Kept Kha'Zix as one logical Champion with four Trait choices and base-portrait fallback.
- [x] Corrected the Set 18 Kha'Zix and Elder Dragon source IDs.
- [x] Preserved repeated Item recipe components discovered during real-source dry normalization.
- [x] Completed Block 7 data-completion Part 2B on schema v5: Trait tooltip markup is resolved at build time, 76 of 89 breakpoints carry source-derived localized effect text, and current Patch 18.3 numeric differences are explicit source-backed overrides.

## Block 7 data completion Part 4

- Added the final Set-18 post-acquisition verifier and validated it against the complete synthetic-sprite package generated from the pinned real metadata.
- Verified 65 Champions, 36 Traits, 136 Items, exact source accounting, 246 runtime PNGs, 21 provenance sources and the reviewed Lux/Kha'Zix/Elder Dragon/Rival/Eclipse semantics.
- Added data-driven placed-slot portrait selection with safe base-image fallback and visible localized dynamic-selection text.
- Added regression coverage for choice portraits/fallbacks, dynamic text, long names, unusual costs, two-slot semantics and dense Trait memberships.
- Added `SET_18_GUI_HCI_HANDOFF.md` with the concrete keyboard, Trait-detail and layout requirements for the next GUI pass.
- The corrected official individual-image acquisition and review of the resulting `source_lock.json` now pass; final Windows/Flet and clean/warm-cache confidence work remains Part 4.

Part 4 local gate: 674 tests passed; production coverage is 2,955/2,955 statements and 892/892 branches. The Set-18 reviewed verifier passes against the complete real-metadata acquisition harness. General Ruff/Flet warning work remains intentionally deferred.


## Block 7 post-data hardening Part 1

- [x] User Windows environment verified 674 normal tests with 2,955 production statements and 892 branches at 100 percent coverage before and after the failed acquisition attempt.
- [x] Reproduced the official acquisition blocker from the user log: `DA_CrimsonRaptor18` exceeds the Data Dragon sprite bounds and no real `enchanted_wilds` package/source lock is accepted.
- [x] Rejected sprite-atlas cropping as the release source of truth after cross-checking Riot's documented individual TFT image assets and the known upstream TFT sprite/coordinate inconsistency report.
- [x] Re-audited Set 18 exceptional semantics: Kha'Zix, Rival base activation, Eclipse derivation and Elder Dragon data are structurally correct; runtime Elder board usage remains unimplemented and Lux duplicate-origin scope requires correction review.
- [x] Audited the Set-18 verifier/source-lock flow and identified full-provenance comparison, positive complete-package tests and post-build lock finalization as hardening work.
- [x] Restored `.github/workflows/quality.yml` to this replacement handoff because the user-created upload ZIP omitted hidden `.github` content even though the Windows repository test proved it existed locally.
- [ ] Part 2: implement the corrections and clear the current 13-file Ruff format drift plus four lint findings.
- [ ] Part 3: expand generic provenance verification and Set-18 semantic mutation tests.
- [ ] Part 4: perform clean/warm official acquisitions, real-package GUI/HCI checks and the full Windows/Flet release gate.

## Block 7 post-data hardening Part 1 corrections

- [x] Replaced release sprite-atlas cropping with individual Data Dragon `image.group` + `image.full` acquisition for ordinary Champion, Trait and Item assets.
- [x] Kept dynamic variant portraits data-driven: variant groups acquire each source Champion record's CommunityDragon `squareIcon`; no Lux/Kha'Zix name branches were added.
- [x] Changed Lux to `PER_CHAMPION` in Set 18 source data; Kha'Zix remains `ZERO_OR_ONE` + `PER_CHAMPION`.
- [x] Added generic board-usage calculation as the sum of each Champion definition's `board_slots`; Elder Dragon remains exactly 2 board slots and +2 Riftbeast in the dataset.
- [x] Made new/refreshed source-lock publication post-build and atomic; a failed package build cannot publish a newly accepted lock.
- [x] Removed the importer-only direct Pillow dependency because atlas cropping is gone; Flet may still install Pillow transitively.
- [x] Corrected the four reported Ruff lint findings and manually aligned all 13 previously reported formatter-drift files to the Ruff 0.16.9 changes shown by the user's Windows run. Exact Windows Ruff rerun remains the external gate.
- [x] Verified the full real-metadata acquisition path with deterministic image bytes: 65 Champions, 36 Traits, 136 Items, 2 dynamic rules, 246 runtime PNGs and 255 provenance sources; Set-18 semantic verifier reports no issues.
- [x] Local normal suite now passes 679 tests with 2,967 production statements and 898 branches at 100 percent statement/branch coverage.
- [x] User Windows verification completed official image-byte acquisition, generic/Set-18 validation and source-lock review; its remaining Ruff/test findings are corrected in Parts 2-3 and await the final Part-4 rerun.

## Version 0.7.0 Block 7 post-data hardening Parts 2-3

User Windows verification of the corrected acquisition path:
- [x] 679 tests passed before the real acquisition with 100 percent statement/branch coverage.
- [x] Official Enchanted Wilds acquisition completed from a clean output state.
- [x] Generated Set validation and inspection passed with 65 Champions, 36 Traits and 136 Items.
- [x] Set-18 reviewed verification passed with 246 runtime PNGs and 255 provenance sources.
- [x] Database and Builder smokes passed.
- [ ] Exact Ruff 0.16.9 still reported six formatter-drift files and three import-order findings in that run.
- [ ] The post-acquisition full suite reported three startup-test failures because those tests assumed only `sample_set` was installed.

Part 2 corrections:
- [x] Apply the exact reported formatter/import-block corrections.
- [x] Make startup integration tests own an isolated sample-only asset root instead of depending on the repository's installed Set inventory.

Part 3 provenance/test hardening:
- [x] Add generic source-lock verification reusable by future Sets.
- [x] Compare complete provenance records: ID inventory, URL, revision, locale, SHA-256 and byte length.
- [x] Reject duplicate source IDs in packaged `SourceManifest` data.
- [x] Add a generic provenance CLI and make the Set-18 verifier reuse it.
- [x] Use the real official Enchanted Wilds package as the positive complete Set-18 fixture.
- [x] Add mutation coverage for reviewed special semantics, Team Planner mappings, Item/source counts, locale markup, asset inventory and provenance drift.
- [x] Local normal suite passes 689 tests with 3,024 production statements and 922 branches at 100 percent statement/branch coverage.
- [ ] Part 4 remains: exact Windows Ruff rerun, clean/warm-cache reproducibility, lightweight image sanity, Flet/GUI/HCI smoke and Block 8 preparation.

### Packaged runtime correction after Parts 2-3 Windows gate

- [x] User Windows gate passed 689 normal tests at 100 percent statement/branch coverage, generic provenance verification and Set-18 review verification.
- [x] `ruff check` passed; the sole remaining Ruff formatter finding in `tests/test_set_schema.py` is corrected in this handoff.
- [x] Identified the packaged Flet failure from the built app traceback: Pydantic loads, but `pydantic_core._pydantic_core` is missing from the embedded Windows runtime.
- [x] Declare `pydantic-core==2.46.5` directly as a runtime dependency instead of rewriting schema validation or patching generated build files.
- [x] Add a small Windows bundle verifier for the Serious Python `site-packages` + `DLLs/_pydantic_core*.pyd` contract.
- [x] Local normal suite passes 692 tests with 3,041 production statements and 930 branches at 100 percent statement/branch coverage.
- [x] Second clean Windows rerun confirmed the direct dependency alone is insufficient: normal uv installs `pydantic-core==2.46.5`, but the packaged app still imports `pydantic_core/__init__.py` without `_pydantic_core`.
- [x] The same run passed 692 normal tests at 100 percent statement/branch coverage and `ruff check`; it also exposed three Ruff-format-only files and four mirrored-document EOF whitespace findings.
- [x] Disable Flet package cleanup only for Windows, preserve the native wheel through staging, and add separate staging/final native-extension diagnostics.
- [x] Make the CI Windows packaging diagnostic run even after packaged Flet failure so the failed stage is observable.
- [x] Apply the exact three formatter changes and remove the four reported EOF blank-line findings.
- [ ] Re-run the packaged Flet Windows integration from a clean `build/` directory and confirm both staging and final-bundle checks pass.
- [ ] Finish the remaining Part 4 reproducibility/image/HCI confidence gates only after packaged startup is green.

## Block 7 post-data hardening Part 4 implementation

- [x] Windows evidence now distinguishes the packaged-test harness from the application: the clean packaged run staged `_pydantic_core.cp313-win_amd64.pyd`, reached the real Library with no startup-error control, and the normal `flet run` path loaded both real Sets successfully.
- [x] Packaged Flet tests rebuild disposable Serious Python staging on every session so a prior packaging pass cannot poison a rerun.
- [x] The staging checker now validates the startup-critical native `.pyd` artifact instead of pure-Python markers that packaging may consume after the temporary app is assembled.
- [x] The Flet 1.0.1 end-to-end smoke uses visible text/tooltips for readiness/navigation while unit tests retain detailed key-based UI coverage.
- [x] Set-18 verifier adds PNG structure/dimension inventory and exact duplicate-group sanity; only the source-confirmed Spirit Visage/Radiant pair is accepted as byte-identical.
- [x] Added a generic validated Set-package comparison CLI for the final clean-cache/warm-cache reproducibility run.
- [x] Cross-platform direction is now explicit: Windows is the primary blocking target; macOS, Linux, Android, iOS and Web are long-term targets that require dedicated platform gates.
- [x] Prepared `BLOCK_08_PLAN.md` for Team Planner and native import/export work.
- [ ] User-run final Part-4 Windows gate: repeat packaged Flet test, real `flet build windows`/bundle check, clean/warm acquisition comparison and manual Set-18 HCI smoke.

## Block 7 dataset review correction - current handoff

- [x] Removed Set-18/Champion-specific constants from the reviewed package checker.
- [x] Added optional Set-owned `data/review.json` expectations for counts, exceptional semantics, Team Planner coverage, source accounting, PNG dimensions and reviewed duplicate-image groups.
- [x] Replaced the Set-specific verifier entry point with generic `tools/set_import/verify_set_review.py`.
- [x] The checker always regenerates `SET_REVIEW.md` from validated runtime data.
- [x] The generated report includes all Traits/breakpoints/effects, Champion portraits and Trait contributions, the complete component recipe matrix, non-recipe non-Radiant Items, a Radiant matrix and provenance totals.
- [x] Enchanted Wilds Kha'Zix uses `ANY_NUMBER` + `PER_CHAMPION`; all four evolution Traits can be selected simultaneously.
- [x] The reviewed Spirit Visage/Radiant duplicate-image exception moved from Python into Enchanted Wilds `review.json`.
- [x] Bundled sample data is regenerated under the new optional review-report manifest contract.
- [x] Dataset-focused regression suite: 320 passed. The four directly affected production modules (`set_builder`, `set_loader`, `set_review`, `set_schema`) reached 100 percent statement and branch coverage in that focused suite.
- [ ] Exact `uv`-driven full suite/coverage/Ruff/Windows packaged verification remains for the next pass; the implementation container has `uv 0.10.0`, below the project-required `>=0.12.18,<0.13`.
