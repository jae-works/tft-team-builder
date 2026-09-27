# TFT Team Builder - Project Context / Handoff

This file is the first document another developer or AI instance should read before changing the project.

## Mandatory reading order

1. `PROJECT_CONTEXT.md`
2. `REQUIREMENTS.md`
3. `PROGRESS.md`
4. `DEVELOPMENT_PLAN.md`
5. `sets/README.md`

## Source of truth

- `REQUIREMENTS.md` contains what the application is required to do.
- `PROGRESS.md` contains only work that has actually been implemented and locally verified in the current delivered version.
- `DEVELOPMENT_PLAN.md` contains the current development steps and order.
- These files are part of the project itself. They must not be treated as chat-only notes.
- Every delivered project ZIP must contain the latest versions of all of these files.
- The Windows release package must also ship these project documents in a readable `project_docs/` directory next to the application files.

## Development workflow

For every coding step:

- Implement a substantial, testable piece of functionality. Do not submit a code-only placeholder step.
- Update `REQUIREMENTS.md` when requirements are clarified, added or deliberately changed.
- Update `PROGRESS.md` with what was actually implemented and what tests were actually run.
- Update `DEVELOPMENT_PLAN.md` when the planned order or scope changes.
- Keep per-Set data inside `sets/` and validate it instead of assuming it is complete.
- Run the complete local test suite before delivery.
- Deliver the complete current project, not a patch or a partial folder.
- Create a SHA-256 checksum for the final ZIP after the ZIP has been created.
- Do not mark a requirement complete merely because code exists; it should be locally verified.

## Coding style

- Prefer clear, direct Python over architecture for architecture's sake.
- Do not create large numbers of interfaces, generic base classes or abstraction layers without a concrete need.
- Separate areas where the separation protects correctness: UI vs. game logic, persistence vs. UI, and executable code vs. Set data.
- Write detailed comments for non-obvious behavior and important invariants.
- Keep the code human-readable and explicit while still being precise and well-tested.
- Tests should be thorough, especially for Set validation, traits, duplicate champions, slots, move/copy/swap semantics, undo/redo, persistence and import/export.

## Current product scope

The current target is a Windows desktop TFT Team Builder and personal Team library.

Explicitly outside the current scope unless `REQUIREMENTS.md` is changed later:

- Mobile or tablet applications
- Board/hex positioning view
- Items
- Notes
- In-game overlay
- Live match analysis
- Opponent scouting
- Meta recommendations based on the current match state
- Riot login
- Cloud synchronization
- User accounts
- Social/online Team library features

## Important model rules

- A Team and a List are different objects.
- A Team has one or more Lists and exactly one primary List.
- A Champion on a List is a Champion instance with its own stable ID.
- Duplicate champions are allowed on a List.
- Duplicate copies of the same champion do not normally count the same native Trait more than once.
- Lists use real slots and may contain gaps.
- Moving onto an occupied slot swaps where the move semantics call for a swap.
- Copy and Move are different operations.
- Traits and Set-specific behavior are data-driven.
- Set packages contain data/assets, not executable Python supplied by the Set.
- The internal Team model may contain more information than Riot's Team Planner export format can represent.

## Set completeness rule

The application must never simply assume a Set directory is complete. A Set loader/validator must report understandable errors for missing required files, invalid schemas, duplicate IDs, unresolved Trait references, invalid dynamic-Trait rules, invalid breakpoints, missing required assets and other structural inconsistencies defined by the Set schema.

## Riot compliance rule

The project should stay within the current Riot/TFT third-party application rules. Any public release and any future Riot-sensitive feature must be checked against the then-current Riot policies before release. Do not add live match decision assistance, opponent scouting, automatic gameplay inputs or unsupported client automation merely because they are technically possible.
