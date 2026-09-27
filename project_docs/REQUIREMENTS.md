# TFT Team Builder - Requirements

This file is the persistent requirements checklist for the project.
It must be shipped with every project version and updated before implementation when requirements change.

Legend:
- [ ] not started
- [~] in progress
- [x] done
- [!] blocked / decision required

## Core
- [ ] Python desktop application for Windows.
- [ ] Flet GUI.
- [x] Windows desktop is the required first release target.
- [x] Browser and mobile/tablet support are deferred future targets, not removed from the long-term project direction.
- [x] Core game/build logic, Set logic and persistence boundaries must remain independent from Flet widgets so future platform/UI changes do not require a core rewrite.
- [ ] Core logic kept independent from GUI code where useful, without unnecessary abstraction layers.
- [ ] Local-first; no account or cloud required.
- [ ] Full local test suite.
- [ ] Clear, human-readable code and extensive useful comments.
- [x] Every delivered version contains this file and PROGRESS.md.
- [x] Every delivered version contains all source files, tests, set data and project metadata.

## Engineering conventions
- [x] All source code is written in English.
- [x] All project-authored README, requirements, planning, progress, handoff, decision and testing documentation is written in English.
- [x] All identifiers, module names, package names, internal schema keys, configuration keys, code comments and technical log messages are English.
- [x] Project-authored filenames and directory names use simple ASCII characters only.
- [x] Project-authored source code, technical documentation, default English UI strings and developer tooling avoid decorative or typographic Unicode characters.
- [x] Use plain alternatives such as `-`, `->`, `...`, straight quotes and normal ASCII punctuation instead of smart quotes, long dashes, Unicode arrows, decorative bullets, emoji or similar characters.
- [x] Localized external/user-facing data may contain characters required by the language, but the project does not introduce unnecessary special symbols.
- [x] Paths are never assembled with string concatenation or hardcoded path separators.
- [x] Python path handling uses `pathlib` and a small centralized path/configuration module.
- [x] Runtime writable paths do not depend on the current working directory.
- [x] Runtime user-data locations use `platformdirs` or an equivalent actively maintained platform-aware library.
- [x] No developer-machine absolute paths are committed to source, configuration, tests or generated manifests.
- [x] Source and runtime path behavior is explicitly tested on Windows-compatible path semantics where practical.
- [x] Dependencies are declared centrally in `pyproject.toml` and use maintained stable versions compatible with the selected Python/Flet toolchain.
- [x] Runtime source does not duplicate the application release version in an unused constant; `pyproject.toml` is the package-version source and release metadata synchronization is tested.
- [x] Prefer modern, actively maintained libraries when they materially improve correctness, portability or maintainability.
- [x] Prefer the Python standard library when it already provides a clear, robust solution; do not add dependencies only to appear modern.
- [x] Avoid obsolete/deprecated libraries and legacy API styles when current maintained alternatives exist.
- [x] Dependency choices are kept pragmatic; do not introduce generic frameworks, interfaces or abstractions without a concrete need.
- [x] Formatting/linting uses Ruff or an equivalent current tool configured in `pyproject.toml`.
- [x] Tests use pytest and remain easy to run locally with one documented command.
- [x] Tests include statement and branch coverage, and the project now enforces a 100 percent coverage gate.
- [x] Resource warnings are treated as test failures so leaked runtime resources cannot pass silently.
- [x] Production source does not rely on `assert` statements for required runtime validation or recovery behavior.
- [x] `uv` is constrained to a version range that includes the September 2026 Windows wheel path-traversal security fix.
- [x] A project-level automated check prevents accidental non-ASCII characters in project-authored technical files, with explicit allowlists only for localization/external data directories that legitimately require them.

## Platform and dependency strategy
- [x] Flet 1.0.1 is retained after explicit comparison with desktop-only and web-first alternatives.
- [x] Runtime uses the base `flet` package; desktop/test tooling stays in the default development group and deferred web tooling stays in a separate optional dependency group.
- [x] CPython is pinned to the 3.13 minor line for the current development cycle so Flet packaging does not silently select another Python minor version.
- [x] `platformdirs` is used only as a platform-native writable-path fallback; Flet-provided storage paths take priority inside packaged Flet applications.
- [x] `pathlib` is used for filesystem path construction and operations; `os.environ` is used only for the separate job of reading environment variables.
- [x] Static browser deployment is not assumed to be compatible with future persistence dependencies; any future browser target must be evaluated separately.
- [ ] If browser deployment is implemented, evaluate Flet dynamic web first because it preserves normal server-side Python package compatibility.
- [ ] If mobile deployment is implemented, re-run dependency, filesystem, persistence, packaging and license compatibility tests for Android/iOS before declaring support.

## Licensing and public distribution
- [x] `LICENSE_REVIEW.md` records the current direct dependency license review and release gates.
- [x] The project itself intentionally has no selected public source-code license yet.
- [ ] Select an explicit project license or proprietary distribution model before any public source release.
- [ ] Audit the exact locked transitive dependency graph and final packaged artifact before public binary distribution.
- [ ] Produce required third-party copyright/license notices for the final distributed artifact.
- [ ] Perform a separate license/artifact audit for each future browser/mobile distribution target.
- [ ] Choose final independent product branding before a public release.
- [ ] Set deliberate Flet company/organization/bundle metadata only after final release identity is known; do not ship default or invented mobile bundle identifiers.

## Riot compliance
- [ ] Unofficial third-party product presentation.
- [ ] Own application branding and UI framing.
- [ ] Only permitted Riot/TFT assets and supported data sources.
- [ ] Required Riot legal notice before public release.
- [ ] No live opponent scouting, shop reading, automatic board reading or real-time gameplay decision engine.
- [ ] No automated TFT inputs.
- [ ] Re-check current Riot rules before any public release.

## Sets
- [x] Dedicated bundled Set folder at `src/assets/sets/`.
- [x] One folder per TFT set.
- [x] Each set has a manifest and data files.
- [x] Application validates each installed set before use.
- [x] Validation checks required files, schema version, unique IDs, references, traits, champion assets and configuration completeness.
- [x] Invalid/incomplete sets fail with understandable validation errors instead of partially loading.
- [x] Runtime Set validation rejects empty Champion or Trait catalogs.
- [x] Set data contains no executable Python code.

## Set data acquisition and generation
- [x] Runtime Set packages are generated local data; the normal app has no network dependency on Riot Data Dragon or CommunityDragon.
- [ ] Riot Data Dragon is the preferred official source for supported localized TFT data and shipped visible assets.
- [ ] CommunityDragon may be used only as a pinned build-time supplemental/cross-check source for TFT metadata not exposed adequately by Data Dragon.
- [ ] Public-release compliance is rechecked for any CommunityDragon-derived fields/assets that are shipped.
- [ ] Release Set generation uses pinned/recorded source versions; unrecorded `latest` data is not accepted as a reproducible release input.
- [ ] Generated Set packages record source provenance, locale, retrieval metadata and source payload hashes.
- [ ] Source ownership is defined per field; source disagreements fail with a readable conflict instead of silently overwriting values.
- [ ] Manual Set overrides are small, explicit, version-controlled and require a human-readable reason.
- [ ] Raw downloaded source payloads are cached outside Git and are not required at runtime.
- [x] Generated Set packages contain local champion/Trait assets; runtime UI does not hotlink these assets.
- [ ] Set generation produces a source inventory/completeness report.
- [ ] Every source candidate is either included, explicitly excluded with a reason, or causes validation to fail.
- [ ] Completeness checks account for debug/summoned/alternate/legacy source records rather than assuming every raw record is a player-selectable champion.
- [x] Normal unit tests for the importer/validator run offline against committed fixtures.
- [x] Generated output from identical pinned inputs and overrides is deterministic.
- [x] Block 1 local source specs record a SHA-256 source hash plus hashes for every generated runtime JSON/locale file and every required runtime asset.
- [x] Runtime Set validation verifies required generated-file and asset hashes before accepting a Set.
- [x] Local Set generation uses a validated staging directory so a failed build does not leave partial output or destroy a previous valid output.
- [x] Set-source asset paths cannot escape the source-spec directory through path traversal, symbolic links, or Windows junctions.
- [x] Set-source roots, source-spec files, runtime Set roots and generated output roots reject symbolic-link or Windows-junction ambiguity where it could undermine reproducibility or safe replacement.
- [x] Runtime Set discovery does not follow symbolic-link or junction Set directories.

## Persistence and local data safety
- [x] User-created Team data is stored locally in SQLite using Python 3.13 `sqlite3`; no ORM is added without a demonstrated need.
- [x] Database schema changes use small explicit versioned migrations.
- [x] Critical Team writes use explicit transactions and rollback on failure.
- [x] SQLite connections enable foreign keys, WAL mode, `synchronous=FULL`, `trusted_schema=OFF` and a configured busy timeout.
- [x] The configured Database timeout controls SQLite busy timeout consistently.
- [x] Complete Team aggregates round-trip exactly, including multiple Lists, empty slots, duplicate Champion definitions, Champion instance IDs and ordered Trait selections.
- [x] Team aggregate loading uses a bounded query count instead of per-Champion Trait queries.
- [x] Team aggregate saving batches child-row writes while preserving one atomic transaction.
- [x] Team soft delete, restore, permanent delete and last-opened timestamps are persisted.
- [x] Autosave primitives support immediate structural saves and queued immutable snapshots for later GUI debounce integration.
- [x] Backups use SQLite's online backup API instead of copying a live WAL database file directly.
- [x] Program-managed backup filenames use a dedicated prefix; retention never deletes unrelated `.db` files from the backup directory.
- [x] Backup name prefixes are validated so they cannot create paths outside the configured backup directory.
- [x] Backup and restore validation checks SQLite integrity, foreign keys, supported schema versions and application-level Team/List/slot structure.
- [x] Database integrity validation also verifies required schema tables/columns and exact migration history for the stored schema version.
- [x] Application initialization rejects a structurally invalid current database instead of trusting `PRAGMA user_version` alone.
- [x] Explicit backup timestamps must be timezone-aware so generated backup names are deterministic across host time zones.
- [x] Migration of an existing database creates a pre-migration backup before schema changes are applied.
- [x] Backup restore is staged through a temporary database and only replaces the active database after validation succeeds.
- [x] Persistence tests include restart round-trips, large Team aggregates, migration, rollback, corruption detection, backup retention and restore failure cases.

## Teams and lists
- [x] A Team is the top-level saved build.
- [x] A Team belongs to exactly one TFT set.
- [x] A Team always has at least one List.
- [x] Exactly one List is the primary/starred list.
- [x] Teams and Lists use stable internal IDs; names do not need to be unique.
- [ ] Team names and List names are editable.
- [ ] Lists can be created, duplicated, reordered, cleared and deleted.
- [ ] Duplicating a List creates a new List ID and new Champion instance IDs while preserving slot/gap layout and Trait selections.
- [ ] Clearing a List removes Champions but preserves its current slot count and gaps until an explicit compact operation.
- [ ] The last remaining List cannot be deleted.
- [ ] Deleting the primary List automatically selects a deterministic adjacent replacement.
- [ ] The currently active List is separate from the primary List.

## Champion instances and slots
- [x] Lists have ordered slots and may contain gaps.
- [x] Lists have no fixed maximum number of champions.
- [x] Champion instances have their own IDs.
- [x] Champion instance IDs are unique inside a Team.
- [x] Duplicate champions are allowed.
- [ ] Duplicate champion IDs do not normally count twice for traits.
- [ ] Clearing a Champion from a slot preserves the empty slot.
- [ ] Inserting/removing a slot reindexes later slots contiguously without changing surviving Champion instance IDs.
- [ ] Moving inside a List to an empty slot moves the Champion and leaves the source slot empty.
- [ ] Moving inside a List to an occupied slot swaps both Champion instances.
- [ ] Lists can be compacted to remove gaps while preserving Champion order and instance IDs.
- [ ] Champions can be copied or moved between Lists.
- [ ] Cross-List move to an occupied slot swaps both Champion instances and preserves both instance IDs.
- [ ] Copy creates a new Champion instance ID and preserves Champion definition plus Trait selection.
- [ ] Copy to an occupied slot inserts at the target position and shifts existing slots right; it never overwrites or discards the previous target.
- [ ] A target index equal to the slot count appends; larger indexes are rejected instead of silently creating unspecified gaps.

## Champion library
- [ ] Right-side champion library.
- [ ] Champions grouped and sorted by cost.
- [ ] No hardcoded maximum champion cost.
- [ ] Only cost groups that exist in the current set are shown.
- [ ] Cost is indicated by both styling and number.
- [ ] Hover details include portrait, name, cost and traits.
- [ ] Champions can be dragged to Lists.
- [ ] Champions can also be picked up by click and placed by click.
- [ ] Escape cancels click-to-place.

## Search
- [ ] Search champions by champion name.
- [ ] Search champions by trait name.
- [x] Search normalization ignores case, spaces and punctuation and handles Unicode sensibly.
- [ ] Start page can search Teams by Team name.
- [ ] Start page can select champions to rank Teams by best matching List.
- [ ] Ranking prioritizes number of selected champion matches, then fewer extra champions.
- [ ] Duplicate selected champions are treated as separate desired instances for similarity search.

## Traits
- [ ] Left-side Trait panel reflects the active List only.
- [ ] Zero-contribution Traits are hidden.
- [ ] Trait order comes from set data.
- [ ] Breakpoints come from set data.
- [ ] Active tier color/style comes from set data.
- [ ] Optional toggle hides Traits below the first breakpoint.
- [ ] Optional toggle shows next-breakpoint progress such as 3/4.
- [ ] Trait calculation is independent from Flet widgets.
- [x] Dynamic trait selection is data-driven, not hardcoded per champion.
- [x] Supported dynamic selection rules include NONE, EXACTLY_ONE, ZERO_OR_ONE, ANY_NUMBER and EXACTLY_N.
- [ ] Required but missing dynamic choices are visibly marked and do not silently count.
- [ ] Dynamic Trait selections are validated for NONE, EXACTLY_ONE, ZERO_OR_ONE, ANY_NUMBER and EXACTLY_N before they contribute.
- [ ] PER_INSTANCE dynamic selections are evaluated independently.
- [ ] PER_CHAMPION selections must agree across duplicate instances of that Champion within one List; conflicts are reported instead of guessed.
- [ ] Trait counting supports the concrete declarative modes UNIQUE_CHAMPION and UNIQUE_INSTANCE; undefined custom counting placeholders are not accepted.
- [ ] Trait results expose current count, active breakpoint, next breakpoint/progress and invalid-dynamic-selection state in UI-independent data.

## Start page
- [ ] Set selector.
- [ ] Team creation.
- [ ] Team cards shown in the same visual language as builder Lists.
- [ ] Primary List used as the normal Team preview.
- [ ] Team name search.
- [ ] Champion-based similarity search.
- [ ] Clicking a Team opens the Builder.
- [ ] Returning from Builder preserves relevant page/search state where practical.

## Builder
- [ ] Desktop layout: Traits | Lists | Champion library.
- [ ] Independent scrolling for Trait panel, central List area and Champion library.
- [ ] Each List can horizontally scroll when required.
- [ ] Team name editable at top.
- [ ] New List button.
- [ ] Undo and Redo buttons.
- [ ] Primary List star control.
- [ ] Active List state.
- [ ] Copy/Move mode control.

## Import and export
- [ ] Each List can export a TFT-compatible Team Planner code when supported by the set codec.
- [ ] Export code can be copied to clipboard.
- [ ] If export supports at most 10 champions and the List exceeds that, show a temporary selection dialog.
- [ ] Export selection never modifies the original List.
- [ ] Team Planner code import validates and previews before overwriting a List.
- [ ] Import is one undoable operation.
- [ ] Invalid imports do not modify saved data.
- [ ] Full project-native Team export/import format exists separately from Riot Team Planner codes.
- [ ] Native format is versioned and preserves all Lists, ordering, gaps, primary List and dynamic trait choices.

## Persistence
- [x] SQLite database.
- [x] Database access is concentrated in the persistence package; UI controls and domain models do not issue SQL directly.
- [x] Persistence code stays direct and concrete; do not add repository/interface hierarchies unless a real second backend or test seam requires them.
- [ ] Autosave; no normal manual-save workflow. Block 2 provides the tested persistence/autosave primitives; GUI scheduling is deferred to the UI block.
- [ ] Structural changes saved immediately.
- [ ] Text edits use short debounce and save on focus loss.
- [ ] Do not rely on application-exit handlers for the only save.
- [x] Database schema version and migrations.
- [x] Automatic pre-migration backups plus explicit validated local backup/restore primitives.
- [x] Team deletion uses recoverable soft delete before permanent deletion at the data layer.

## Undo / Redo
- [ ] Command-based undo/redo without excessive framework abstraction.
- [ ] Undo history starts empty when a Team is opened and is not persisted across application restarts.
- [ ] Add/remove/move/swap/copy champions are undoable.
- [ ] List create/delete/reorder/duplicate/clear/compact are undoable.
- [ ] Rename Team/List is undoable.
- [ ] Primary List changes are undoable.
- [ ] Dynamic Trait changes are undoable.
- [ ] One successful user-visible edit creates one history entry; failed/no-op edits create none.
- [ ] Undo/redo restores the exact complete Team state, including IDs, gaps, ordering, timestamps and Trait selections.
- [ ] A new edit after undo clears the redo branch.
- [ ] Import is a single undoable action.
- [ ] Ctrl+Z, Ctrl+Y and Ctrl+Shift+Z supported.

## Keyboard usability
- [ ] Ctrl+F focuses champion search.
- [ ] Ctrl+N creates a List.
- [ ] Ctrl+D duplicates current List.
- [ ] Delete removes selected champion.
- [ ] Escape cancels placement/dialog where appropriate.

## Validation and failures
- [ ] Missing champion images do not crash the app.
- [ ] Missing translations have fallback behavior.
- [ ] Unknown champion/trait IDs are surfaced clearly.
- [ ] Invalid Set packages do not partially load.
- [ ] Invalid Team Planner codes do not modify data.
- [ ] Database errors are logged and surfaced appropriately in the future GUI; persistence exceptions already propagate without silent loss.
- [x] Critical writes use transactions.

## Testing
- [x] Unit tests for models.
- [x] Detailed set-package validation tests.
- [ ] Detailed trait-engine tests, including duplicate champions and dynamic choices.
- [ ] Detailed slot move/swap/copy tests.
- [ ] Detailed similarity ranking tests.
- [ ] Detailed undo/redo tests.
- [ ] Import/export round-trip tests.
- [x] Persistence and migration tests.
- [ ] App-level smoke tests where practical.

## Packaging
- [ ] Windows executable/package.
- [ ] Complete data folder behavior verified.
- [ ] Delivered ZIP always contains the complete current project.
- [x] Development handoffs use clean project replacement while preserving the existing `.git` directory.
- [x] Runtime Set data has exactly one authoritative bundled root: `src/assets/sets`.
- [x] Delivered project archives exclude caches, coverage files, bytecode caches, virtual environments, and obsolete development-only files.
- [x] Mandatory Block 1 tests do not rely on platform-specific symlink privileges and therefore have no expected OS-permission skips.
- [ ] SHA-256 checksum is calculated for every delivered ZIP.
- [ ] Release candidate is tested from a clean extracted copy.

## Explicitly out of scope for the current implementation blocks
- Browser deployment is deferred.
- Mobile/tablet deployment is deferred.
- Hex board view.
- Items.
- Trait items / emblems.
- Notes.
- In-game overlay.
- Live match analysis.
- Opponent scouting.
- Meta recommendation engine.
- Riot login.
- Cloud sync.
- Accounts / social features.


# 38. Project documentation and handoff

- [x] `PROJECT_CONTEXT.md` remains in the project root as the first handoff document.
- [x] `REQUIREMENTS.md` remains part of every delivered source version.
- [x] `PROGRESS.md` remains part of every delivered source version.
- [x] `IMPLEMENTATION_BLOCKS.md` remains part of every delivered source version.
- [x] `DEVELOPMENT_PLAN.md` remains part of every delivered source version.
- [ ] The Windows release package includes these planning/handoff files in a readable `project_docs/` directory.
- [x] `PROGRESS.md` is updated only with work that is actually implemented and locally verified.
- [x] `project_docs/` mirrors are synchronized from the root documents by a tested tool instead of manual copying.
- [x] Requirements discovered during development are added to `REQUIREMENTS.md` before or together with their implementation.
- [ ] Every delivered ZIP is complete and accompanied by a SHA-256 checksum calculated from that final ZIP.
- [x] The current implementation blocks are documented and their completion status is maintained.
- [ ] Future implementation blocks may be adjusted after completed blocks when justified by the actual code; planning changes are documented rather than silently changed.
- [x] Every delivered version includes a ready-to-copy Git add/commit/push command block.
