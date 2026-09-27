# TFT Team Builder - Project Context and Handoff

This is the first document another developer or AI instance should read before changing the project.

## Mandatory reading order

1. `PROJECT_CONTEXT.md`
2. `REQUIREMENTS.md`
3. `PROGRESS.md`
4. `IMPLEMENTATION_BLOCKS.md`
5. `DEVELOPMENT_PLAN.md`
6. `DECISIONS.md`
7. `SET_DATA_PIPELINE.md`
8. The latest block report, currently `BLOCK_01_REPORT.md`
9. `sets/README.md`
10. `set_sources/README.md`

## Current state

- Current version: 0.1.0.
- Block 1 is implemented.
- Block 2 is next, but should not begin until the user has tested version 0.1.0 locally and either approved it or reported corrections.
- The current application shell is intentionally minimal. The complete Builder GUI begins in Block 4.

## Source of truth

- `REQUIREMENTS.md` contains what the application is required to do and status checkboxes.
- `PROGRESS.md` contains work that actually exists in the current delivered version.
- `IMPLEMENTATION_BLOCKS.md` contains the high-level roadmap and block status.
- `DEVELOPMENT_PLAN.md` contains delivery rules and development order.
- `DECISIONS.md` records consequential technical choices and rationale.
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
- platformdirs 4.11.14.
- pytest 9.1.1.
- Ruff 0.16.9.
- Hatchling 1.32.4.
- `src/` package layout.
- `pyproject.toml` is the central packaging/tool configuration file.

See `DECISIONS.md` before changing this baseline.

## Current product scope

The target is a Windows desktop TFT Team Builder and local Team library.

Explicitly out of scope unless Requirements are changed later:

- mobile/tablet application;
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
