# TFT Team Builder - Project Context and Handoff

This is the first document another developer or AI instance should read before changing the project.

## Mandatory reading order

1. `PROJECT_CONTEXT.md`
2. `REQUIREMENTS.md`
3. `PROGRESS.md`
4. `IMPLEMENTATION_BLOCKS.md`
5. `DEVELOPMENT_PLAN.md`
6. `DECISIONS.md`
7. `LICENSE_REVIEW.md`
8. `SET_DATA_PIPELINE.md`
9. The latest implemented block report, currently `BLOCK_07_REPORT.md`
10. `BLOCK_03_PLAN.md` for the implemented Block 3 behavior contract
11. `BLOCK_04_PLAN.md` for the implemented initial GUI behavior contract
12. `BLOCK_05_PLAN.md` for the implemented desktop interaction behavior contract
13. `BLOCK_06_PLAN.md` for the implemented Team-library behavior contract
14. `BLOCK_07_PLAN.md`, `BLOCK_07_DATA_COMPLETION_PLAN.md` and `BLOCK_07_POST_DATA_HARDENING_PLAN.md` for the active real-Set-data work
15. `src/assets/sets/README.md`
16. `set_sources/README.md`


## Current state

- Current version: 0.7.0.
- Blocks 1, 2 and 3 are implemented. The user Windows-verified the 0.3.0 Block 3 runtime behavior: 529 tests at 100 percent statement/branch coverage, Set and database smoke tests, Builder smoke and Flet startup all passed.
- That Windows run found only two Ruff lint findings in `tests/test_trait_engine.py` after Ruff formatted four files. Version 0.3.1 applies both exact lint corrections and expands the semantic/integration audit to 537 tests while retaining the 100 percent production coverage gate.
- Block 7 post-data hardening Part 1 now includes the audit corrections and is ready for Windows verification: production acquisition uses individual Data Dragon `image.full` assets for ordinary records plus generic CommunityDragon `squareIcon` assets for distinct dynamic variants; board usage sums Set-declared `board_slots`; Lux is PER_CHAMPION; new/refreshed source locks publish only after a successful package build. The local suite is 679 tests at 100 percent statement/branch coverage.
- Blocks 4, 5 and 6 are implemented. Version 0.7.0 is the post-Windows Block 6 correction: the v0.6.1 Windows run passed 623 normal tests at 100 percent coverage but exposed three Ruff F401 findings, formatter/EOF drift, and a packaged Flet/Flutter exit-code-79 failure. The correction removes those source hygiene findings, validates Sets once at startup, caches immutable `LoadedSet` ID maps, improves real-data Library naming/result-density behavior, and closes Flet 1.0.1 RemoteTester writers in the integration-test compatibility shim before upstream cleanup drops them. The normal local suite is 627 tests at 100 percent statement/branch coverage. Exact Ruff 0.16.9 and packaged Windows Flet verification of v0.7.0 remain release gates.

## Source of truth

- `REQUIREMENTS.md` contains what the application is required to do and status checkboxes.
- `PROGRESS.md` contains work that actually exists in the current delivered version.
- `IMPLEMENTATION_BLOCKS.md` contains the high-level roadmap and block status.
- `DEVELOPMENT_PLAN.md` contains delivery rules and development order.
- `DECISIONS.md` records consequential technical choices and rationale.
- `LICENSE_REVIEW.md` records dependency-license findings and public-release license gates.
- `SET_DATA_PIPELINE.md` defines source/provenance/completeness rules for TFT Set generation.
- `BLOCK_01_REPORT.md` records detailed implementation and test evidence for Block 1.
- `BLOCK_02_REPORT.md` records persistence implementation and hardening evidence for Block 2.
- `BLOCK_03_PLAN.md` is the concrete behavior contract implemented by Block 3.
- `BLOCK_03_REPORT.md` records Block 3 implementation and test evidence.
- `BLOCK_04_PLAN.md` is the implemented Block 4 GUI behavior contract.
- `BLOCK_05_PLAN.md` is the implemented interaction-focused contract for Block 5.
- `BLOCK_05_REPORT.md` records Block 5 implementation/test evidence.
- `BLOCK_06_PLAN.md` is the implemented Team-library behavior contract.
- `BLOCK_06_REPORT.md` records Block 6 implementation/test evidence.
- `BLOCK_07_PLAN.md` defines the original real-Set-data pipeline contract; `BLOCK_07_POST_DATA_HARDENING_PLAN.md` is the active correction plan after the first official Windows acquisition audit.

These files are part of the project. They are not chat-only notes.

## Language and character rules

- All project-authored source code is English.
- All project-authored README, requirements, planning, progress, handoff, decision, test, and technical documentation is English.
- Identifiers, module/package names, schema/config keys, comments, default UI strings, and technical logs are English.
- Project-authored technical text uses normal ASCII punctuation only.
- Project-owned filenames and directory names are ASCII-only.
- Localized game data is the explicit exception when a language requires non-ASCII characters.
- `tools/check_ascii.py` and repository tests enforce the technical character policy.

## Development workflow

For every coding block:

- Research current external APIs/libraries before consequential choices.
- Implement substantial working functionality, not placeholder architecture.
- Keep code direct and human-readable. Do not create interfaces or generic base classes without a concrete need.
- Add detailed comments around non-obvious invariants and failure modes.
- Add extensive tests.
- Update requirements before or together with requirement changes.
- Update progress only for implemented and verified work.
- Update decisions when architecture, persisted data, compatibility, or maintenance choices materially change.
- Run the complete available local test suite.
- Deliver the complete current project, not a patch.
- Generate SHA-256 only after creating the final ZIP.
- Provide a ready-to-copy Git add/commit/push command block.
- Wait for the user's local verification before starting the next block.

## Current technical baseline

- CPython 3.13 (`>=3.13,<3.14`).
- Flet 1.0.1.
- Pydantic 2.13.5.
- platformdirs 4.11.15.
- pytest 9.1.1.
- Ruff 0.16.9.
- Hatchling 1.32.4.
- `src/` package layout.
- `pyproject.toml` is the central packaging/tool configuration file.

See `DECISIONS.md` before changing this baseline.

## Current product scope

The current blocking target is the Windows desktop TFT Team Builder and local Team library. The long-term product target also includes macOS, Linux, Android, iOS and Web once each target passes its own packaging/runtime verification. Non-Windows work is currently secondary and non-blocking.

Explicitly out of scope unless Requirements are changed later:
- hex board view;
- items and Trait items;
- notes;
- in-game overlay;
- live match analysis;
- opponent scouting;
- match-state meta recommendations;
- Riot login;
- cloud synchronization;
- user accounts;
- social/online Team library features.

## Platform direction

Windows desktop is the mandatory first release target and primary development gate. macOS, Linux, Android, iOS and Web are explicit later targets, but they are not current blocking deliverables. Keep core logic, persistence services and Set handling independent from Flet controls so platform work can be revisited without rewriting the domain layer.

Flet remains the selected UI framework after Block 1 review because it supports Windows today and has official web, Android and iOS build paths. Future browser work should evaluate dynamic web before static Pyodide deployment when persistence or native Python packages are involved. Pydantic uses the native `pydantic-core` package, so exact Flet mobile wheel compatibility must be rechecked before Android/iOS support is declared.

Before public distribution, read `LICENSE_REVIEW.md` and perform the target-specific dependency/artifact audit described there.

## Important model rules

- Team and TeamList are different objects.
- A Team always has at least one TeamList and exactly one primary List reference.
- ChampionInstance identity is independent from Champion definition identity.
- Duplicate Champions are allowed.
- Lists use real ordered slots and may contain empty slots.
- Dynamic Trait behavior is declarative Set data, not Champion-specific Python code.
- Set packages contain data/assets only, never executable Set-provided Python.
- The internal Team model may eventually contain more information than Riot Team Planner export can represent.

## Set package rule

Runtime Set packages must validate completely before use. Block 1 currently validates structure, references, localizations, assets, source-manifest asset hashes, and relevant Team Planner metadata. A broken Set is rejected rather than partially loaded.

The committed `sample_set` is generated from `set_sources/specs/sample_set` and is not intended to represent a real Riot TFT Set.

Block 7 implements pinned developer-only Riot Data Dragon/CommunityDragon acquisition. Runtime downloads remain prohibited; the app consumes only validated local packages.

## Riot compliance rule

The project must remain within current Riot/TFT third-party application rules. Re-check the then-current policy before public release and before adding any Riot-sensitive feature. Do not add live match decision assistance, opponent scouting, automatic gameplay inputs, or unsupported client automation merely because it is technically possible.


## Block 2 and Block 3 handoff notes

Persistence is implemented under `src/tft_builder/persistence/` using direct Python `sqlite3`. Do not introduce an ORM or generic repository hierarchy without a concrete requirement that outweighs the current simpler design. `TeamRepository.save()` persists one complete Team aggregate transactionally. `BackupManager` owns SQLite online backup/restore behavior. `AutosaveService` is intentionally timer-free; later UI code may debounce calls into it without moving persistence logic into Flet controls.

Version 0.2.2 also validates required schema tables/columns and migration history before treating an existing database as healthy.

Block 3 adds `TeamEditor` in `builder.py` and the Flet-independent calculation engine in `trait_engine.py`. GUI code should call these concrete core operations rather than reimplementing slot/move/copy/history/Trait semantics in controls. `TeamEditor` owns in-memory history only; Block 4 connects successful edits to `AutosaveService`. The active List is transient GUI-session state and is deliberately not added to the persisted Team model.

## Block 4 handoff

Version 0.4.0 introduced the first functional Builder GUI; version 0.4.1 polishes that boundary without changing its architecture. `src/tft_builder/builder_view.py` is the concrete Flet composition boundary; it must continue to delegate domain changes to `TeamEditor`, Trait calculation to `trait_engine`, and persistence to the existing persistence package. The active List and Trait display toggles are transient UI state. Structural edits save immediately. Text edits queue immutable snapshots and use a short async debounce, with explicit blur/submit flush.

`tests_flet/` contains the packaged Flet smoke flow. With the pinned Flet 1.0.1 CLI, run the plugin directly as `uv run pytest tests_flet --no-cov`; the user Windows run proved that `flet test ... -- --no-cov` is not supported by this pinned CLI. Normal `uv run pytest` remains the 100 percent application coverage gate. Windows Developer Mode is required for Flutter plugin symlink support.

## Block 5 handoff

Version 0.5.0 added Champion/Trait search, Trait-click filtering, native Flet drag/drop translation, dynamic Trait editing and desktop keyboard shortcuts while keeping all mutations in TeamEditor. Version 0.5.1 is the post-Windows correction/audit: the packaged entry module now starts Flet when imported by device-mode tests, the two real Ruff E731 findings are removed, repeated Set lookup dictionaries are cached once per BuilderView, and one unused catalog helper was removed. `move_champion_to_end()` remains the dense trailing-drop primitive, `set_champion_trait_selection()` is the PER_CHAMPION dynamic edit primitive, and `validate_dynamic_selection()` is the shared rule validator.

Block 6 is implemented and audited. Library search/ranking remains Flet-independent and Library aggregate reads are bounded/cached. Block 7 is implemented through the data-completion handoff, and the active post-data corrections are tracked in `BLOCK_07_POST_DATA_HARDENING_PLAN.md`.

## Block 7 corrected Set 18 semantics

The Set 18 pipeline uses schema v5. Elder Dragon consumes 2 board slots and contributes 2 Riftbeast points. Lux uses a data-driven +2 selected-origin rule; Kha'Zix can independently select zero through all four reviewed evolution Traits; Rengar has no separate Builder state. Rival uses exact-count activation at one unit, and Eclipse is derived from 3 Solar plus 3 Lunar instead of fake Champion membership. The importer retains the reviewed 136-reference user-facing Item boundary, preserves recipe components, and source-accounts the remaining broad CommunityDragon records as explicit exclusions. See `SET_18_ENCHANTED_WILDS_CHECKLIST.md`.


## Block 7 data-completion handoff

Part 1 reconciles the pinned Set 18 payload before live asset acquisition. The importer expects 91 raw Champion records, normalizes them to 65 logical Champions, and explicitly excludes 17 helper/encounter/pseudo-unit records. Lux is one logical Champion backed by ten upstream records (base plus nine origins); `dynamic_traits.choice_images` maps each origin Trait to its reviewed Set-owned portrait. Kha'Zix stays one logical Champion with four independently selectable evolution Traits and base-portrait fallback; all four may be selected together. Repeated Item recipe components are valid and preserved. Part 2 fixes the 136-reference Item boundary and localized breakpoint text. Release acquisition now uses individual Riot Data Dragon images for ordinary assets and configured CommunityDragon variant portraits rather than untrusted TFT sprite coordinates. See `BLOCK_07_DATA_COMPLETION_PLAN.md`.

## Current Set-data handoff

Block 7 data-completion Parts 1-4 are implemented and the corrected Windows acquisition has generated the real `enchanted_wilds` package plus source lock. The reviewed Set-18 shape and GUI edge assumptions are frozen in `SET_18_ENCHANTED_WILDS_CHECKLIST.md` and `SET_18_GUI_HCI_HANDOFF.md`. Generic package validation and the generic Set-owned review-policy checker pass on the official-byte package. The reviewed invariants now live in `data/review.json`, and every checker run refreshes `SET_REVIEW.md`.


## Block 7 post-data hardening audit

The first networked Windows acquisition proved that the synthetic atlas harness was insufficient: the run stopped at `DA_CrimsonRaptor18` before a runtime package existed. The corrected acquisition uses individual Riot TFT `image.full` assets for ordinary records and source-record CommunityDragon `squareIcon` paths for distinct dynamic variant portraits; atlas rectangles are no longer a production dependency. The subsequent official-byte Windows acquisition completed successfully and produced the current real package plus source lock.

Special-rule audit: Elder Dragon data correctly declares 2 board slots and +2 Riftbeast, and the Builder calculates board usage generically by summing `board_slots`; one Champion card remains one logical instance. Kha'Zix ANY_NUMBER + PER_CHAMPION evolution, Rival exact-one base activation and Eclipse 3 Solar + 3 Lunar derivation remain sound. Lux remains one logical Avatar with a +2 chosen origin and now uses PER_CHAMPION scope so duplicate copies in one List cannot disagree.

`load_set_directory()` remains the generic package validator. `tft_builder.source_verification` provides reusable complete provenance/source-lock comparison, while `verify_set_review.py` interprets Set-owned `review.json` expectations and regenerates the manual inspection report. See `BLOCK_07_POST_DATA_HARDENING_PLAN.md`.

## Current Block 7 packaged-runtime gate

The real Enchanted Wilds dataset and source lock are committed and Windows-verified. The former Set-specific verifier has been replaced by one generic reviewed-Set checker whose expectations are read from the Set package itself. Two clean packaged Flet runs now isolate the remaining release blocker: embedded Pydantic reaches `pydantic_core/__init__.py` from `build/site-packages`, but `_pydantic_core` is missing before application startup. Making `pydantic-core==2.46.5` a direct dependency did not change that packaging outcome. The clean Windows rerun proved `_pydantic_core.cp313-win_amd64.pyd` is staged, and the packaged process reached the real Library without the application startup error. Repeat runs exposed two test-harness issues rather than a Set/runtime defect: Serious Python staging is disposable after packaging, and Flet 1.0.1 packaged tests do not reliably expose the expected Python TextField key. Part 4 now rebuilds staging per Flet test session, uses visible user-facing semantics for the packaged smoke, retains a separate final Windows `DLLs` bundle gate, and adds image/reproducibility checks. The latest Windows normal suite passed 694 tests at 100 percent statement/branch coverage; the final external Windows packaged/release gate remains pending.
