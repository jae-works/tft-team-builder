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
9. The latest implemented block report, currently `BLOCK_06_REPORT.md`
10. `BLOCK_03_PLAN.md` for the implemented Block 3 behavior contract
11. `BLOCK_04_PLAN.md` for the implemented initial GUI behavior contract
12. `BLOCK_05_PLAN.md` for the implemented desktop interaction behavior contract
13. `BLOCK_06_PLAN.md` for the implemented Team-library behavior contract
14. `BLOCK_07_PLAN.md` for the next real-Set-data block
15. `src/assets/sets/README.md`
16. `set_sources/README.md`


## Current state

- Current version: 0.6.1.
- Blocks 1, 2 and 3 are implemented. The user Windows-verified the 0.3.0 Block 3 runtime behavior: 529 tests at 100 percent statement/branch coverage, Set and database smoke tests, Builder smoke and Flet startup all passed.
- That Windows run found only two Ruff lint findings in `tests/test_trait_engine.py` after Ruff formatted four files. Version 0.3.1 applies both exact lint corrections and expands the semantic/integration audit to 537 tests while retaining the 100 percent production coverage gate.
- Blocks 4, 5 and 6 are implemented. Version 0.6.1 is the Block 6 quality/HCI audit: Team-library aggregate loading is batched and cached, similarity cards preview the actual best-matching List, exact UI-helper duplication is consolidated and the final accessibility/hardening contract is expanded. The v0.5.1 Windows run passed 586 normal tests at 100 percent coverage and exact Ruff checks; its packaged Flet test host started successfully but queried the page before a stable Builder/Library key was visible. The Block 6 packaged smoke now waits within a bounded polling window for the library-first startup flow. Exact Ruff 0.16.9 and packaged Windows Flet verification of v0.6.1 remain release gates.

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
- `BLOCK_07_PLAN.md` is the prepared real-Set-data pipeline contract for the next block.

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

The target is a Windows desktop TFT Team Builder and local Team library.

Deferred platform targets, not current implementation scope:

- browser deployment;
- mobile/tablet deployment;

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

Windows desktop is the mandatory first release target. Browser and mobile/tablet builds remain possible future targets. They are not current deliverables. Keep core logic, persistence services and Set handling independent from Flet controls so platform work can be revisited without rewriting the domain layer.

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

Real Riot/CommunityDragon source acquisition remains Block 7 work. Do not add ad-hoc runtime downloads before then.

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

Block 6 is implemented and audited. Library search/ranking remains Flet-independent, Library aggregate reads are bounded/cached, and Block 7 is the next implementation target described in `BLOCK_07_PLAN.md`.
