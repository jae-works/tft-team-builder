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
- [ ] Core logic kept independent from GUI code where useful, without unnecessary abstraction layers.
- [ ] Local-first; no account or cloud required.
- [ ] Full local test suite.
- [ ] Clear, human-readable code and extensive useful comments.
- [ ] Every delivered version contains this file and PROGRESS.md.
- [ ] Every delivered version contains all source files, tests, set data and project metadata.

## Riot compliance
- [ ] Unofficial third-party product presentation.
- [ ] Own application branding and UI framing.
- [ ] Only permitted Riot/TFT assets and supported data sources.
- [ ] Required Riot legal notice before public release.
- [ ] No live opponent scouting, shop reading, automatic board reading or real-time gameplay decision engine.
- [ ] No automated TFT inputs.
- [ ] Re-check current Riot rules before any public release.

## Sets
- [ ] Dedicated sets/ folder.
- [ ] One folder per TFT set.
- [ ] Each set has a manifest and data files.
- [ ] Application validates each installed set before use.
- [ ] Validation checks required files, schema version, unique IDs, references, traits, champion assets and configuration completeness.
- [ ] Invalid/incomplete sets fail with understandable validation errors instead of partially loading.
- [ ] Set data contains no executable Python code.

## Set data acquisition and generation
- [ ] Runtime Set packages are generated local data; the normal app has no network dependency on Riot Data Dragon or CommunityDragon.
- [ ] Riot Data Dragon is the preferred official source for supported localized TFT data and shipped visible assets.
- [ ] CommunityDragon may be used only as a pinned build-time supplemental/cross-check source for TFT metadata not exposed adequately by Data Dragon.
- [ ] Public-release compliance is rechecked for any CommunityDragon-derived fields/assets that are shipped.
- [ ] Release Set generation uses pinned/recorded source versions; unrecorded `latest` data is not accepted as a reproducible release input.
- [ ] Generated Set packages record source provenance, locale, retrieval metadata and source payload hashes.
- [ ] Source ownership is defined per field; source disagreements fail with a readable conflict instead of silently overwriting values.
- [ ] Manual Set overrides are small, explicit, version-controlled and require a human-readable reason.
- [ ] Raw downloaded source payloads are cached outside Git and are not required at runtime.
- [ ] Generated Set packages contain local champion/Trait assets; runtime UI does not hotlink these assets.
- [ ] Set generation produces a source inventory/completeness report.
- [ ] Every source candidate is either included, explicitly excluded with a reason, or causes validation to fail.
- [ ] Completeness checks account for debug/summoned/alternate/legacy source records rather than assuming every raw record is a player-selectable champion.
- [ ] Normal unit tests for the importer/validator run offline against committed fixtures.
- [ ] Generated output from identical pinned inputs and overrides is deterministic.

## Teams and lists
- [ ] A Team is the top-level saved build.
- [ ] A Team belongs to exactly one TFT set.
- [ ] A Team always has at least one List.
- [ ] Exactly one List is the primary/starred list.
- [ ] Teams and Lists use stable internal IDs; names do not need to be unique.
- [ ] Team names and List names are editable.
- [ ] Lists can be created, duplicated, reordered, cleared and deleted.
- [ ] The last remaining List cannot be deleted.
- [ ] Deleting the primary List automatically selects another primary List.
- [ ] The currently active List is separate from the primary List.

## Champion instances and slots
- [ ] Lists have ordered slots and may contain gaps.
- [ ] Lists have no fixed maximum number of champions.
- [ ] Champion instances have their own IDs.
- [ ] Duplicate champions are allowed.
- [ ] Duplicate champion IDs do not normally count twice for traits.
- [ ] Moving inside a List to an empty slot moves the champion.
- [ ] Moving inside a List to an occupied slot swaps both champions.
- [ ] Lists can be compacted to remove gaps.
- [ ] Champions can be copied or moved between Lists.
- [ ] Move to occupied slot swaps.
- [ ] Copy preserves the original and inserts the copy safely without overwriting data.

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
- [ ] Search normalization ignores case, spaces and punctuation and handles Unicode sensibly.
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
- [ ] Dynamic trait selection is data-driven, not hardcoded per champion.
- [ ] Supported dynamic selection rules include NONE, EXACTLY_ONE, ZERO_OR_ONE, ANY_NUMBER and EXACTLY_N.
- [ ] Required but missing dynamic choices are visibly marked and do not silently count.

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
- [ ] SQLite database.
- [ ] Autosave; no normal manual-save workflow.
- [ ] Structural changes saved immediately.
- [ ] Text edits use short debounce and save on focus loss.
- [ ] Do not rely on application-exit handlers for the only save.
- [ ] Database schema version and migrations.
- [ ] Automatic local backups.
- [ ] Team deletion uses recoverable soft delete before permanent deletion.

## Undo / Redo
- [ ] Command-based undo/redo without excessive framework abstraction.
- [ ] Undo history starts when a Team is opened.
- [ ] Add/remove/move/swap/copy champions are undoable.
- [ ] List create/delete/reorder/duplicate/clear/compact are undoable.
- [ ] Rename Team/List is undoable.
- [ ] Primary List changes are undoable.
- [ ] Dynamic Trait changes are undoable.
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
- [ ] Database errors are logged and surfaced appropriately.
- [ ] Critical writes use transactions.

## Testing
- [ ] Unit tests for models.
- [ ] Detailed set-package validation tests.
- [ ] Detailed trait-engine tests, including duplicate champions and dynamic choices.
- [ ] Detailed slot move/swap/copy tests.
- [ ] Detailed similarity ranking tests.
- [ ] Detailed undo/redo tests.
- [ ] Import/export round-trip tests.
- [ ] Persistence and migration tests.
- [ ] App-level smoke tests where practical.

## Packaging
- [ ] Windows executable/package.
- [ ] Complete data folder behavior verified.
- [ ] Delivered ZIP always contains the complete current project.
- [ ] SHA-256 checksum is calculated for every delivered ZIP.
- [ ] Release candidate is tested from a clean extracted copy.

## Explicitly out of scope for the current project
- Mobile/tablet app.
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

- [ ] `PROJECT_CONTEXT.md` remains in the project root as the first handoff document.
- [ ] `REQUIREMENTS.md` remains part of every delivered source version.
- [ ] `PROGRESS.md` remains part of every delivered source version.
- [ ] `IMPLEMENTATION_BLOCKS.md` remains part of every delivered source version.
- [ ] `DEVELOPMENT_PLAN.md` remains part of every delivered source version.
- [ ] The Windows release package includes these planning/handoff files in a readable `project_docs/` directory.
- [ ] `PROGRESS.md` is updated only with work that is actually implemented and locally verified.
- [ ] Requirements discovered during development are added to `REQUIREMENTS.md` before or together with their implementation.
- [ ] Every delivered ZIP is complete and accompanied by a SHA-256 checksum calculated from that final ZIP.
- [ ] The current implementation blocks are documented and their completion status is maintained.
- [ ] Future implementation blocks may be adjusted after completed blocks when justified by the actual code; planning changes are documented rather than silently changed.
- [ ] Every delivered version includes a ready-to-copy Git add/commit/push command block.
