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
9. The latest block report, currently `BLOCK_02_REPORT.md`
10. `src/assets/sets/README.md`
11. `set_sources/README.md`

## Current state

- Current version: 0.2.1.
- Block 1 is hardened and pending final user verification.
- Block 2 is implemented. Version 0.2.1 is the hardened persistence release candidate and must receive the final Windows quality recheck before Block 3 begins.
- The current application shell is intentionally minimal. The complete Builder GUI begins in Block 4.

## Source of truth

- `REQUIREMENTS.md` contains what the application is required to do and status checkboxes.
- `PROGRESS.md` contains work that actually exists in the current delivered version.
- `IMPLEMENTATION_BLOCKS.md` contains the high-level roadmap and block status.
- `DEVELOPMENT_PLAN.md` contains delivery rules and development order.
- `DECISIONS.md` records consequential technical choices and rationale.
- `LICENSE_REVIEW.md` records dependency-license findings and public-release license gates.
- `SET_DATA_PIPELINE.md` defines source/provenance/completeness rules for TFT Set generation.
- `BLOCK_01_REPORT.md` records detailed implementation and test evidence for Block 1.

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


## Block 2 handoff note

Persistence is implemented under `src/tft_builder/persistence/` using direct Python `sqlite3`. Do not introduce an ORM or generic repository hierarchy without a concrete requirement that outweighs the current simpler design. `TeamRepository.save()` persists one complete Team aggregate transactionally. `BackupManager` owns SQLite online backup/restore behavior. `AutosaveService` is intentionally timer-free; later UI code may debounce calls into it without moving persistence logic into Flet controls.
