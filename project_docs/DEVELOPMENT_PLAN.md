# TFT Team Builder - Development Plan

The project will be implemented in substantial, testable steps. Each coding step must deliver a complete ZIP containing the whole project, not a patch. Each step must update REQUIREMENTS.md and PROGRESS.md, run the full local test suite, and include a SHA-256 checksum for the ZIP. `PROJECT_CONTEXT.md`, `REQUIREMENTS.md`, `PROGRESS.md` and `DEVELOPMENT_PLAN.md` are permanent project files and must remain in every source delivery. The final Windows package must additionally copy them into a readable `project_docs/` directory.

## Step 1 - Foundation, reproducible Set data pipeline, validation and core models
Build the first actually runnable project foundation.

Deliverables:
- Python/Flet project bootstrapping.
- Runtime/config/path handling.
- Logging.
- Real `sets/`, `set_sources/` and `tools/set_import/` structure.
- Pinned build-time source configuration using Riot Data Dragon as the preferred official data/asset source and CommunityDragon only as a supplemental/cross-check source where needed.
- Source download/cache/provenance model with hashes; normal runtime remains offline and source-independent.
- Import normalization with per-field source ownership, conflict detection and explicit reasoned overrides.
- Source candidate inventory with INCLUDED / EXCLUDED-with-reason / ERROR completeness accounting.
- One generated development/sample Set package.
- Set manifest/data schema plus source manifest/completeness report schema.
- Set loader and exhaustive offline validator with readable errors.
- Core Team/List/Slot/ChampionInstance/TraitDefinition/ChampionDefinition models.
- Search text normalizer.
- First test suite covering model invariants, importer transforms, source conflicts, explicit exclusions, deterministic generation and Set completeness using offline fixtures.
- Minimal CLI/dev build/validation entry point so Set data can be generated and checked independently of the GUI.

Local user test target:
- Project installs/runs.
- Set build/validation command reports the bundled Set as valid.
- Deliberately broken source/Set fixtures produce understandable errors.
- Generated Set provenance/completeness report explains exactly what was included and intentionally excluded.

## Step 2 - SQLite persistence, repositories, autosave primitives and backups
Make the project capable of safely storing real Teams.

Deliverables:
- SQLite schema and schema versioning.
- Team/List/Slot/ChampionInstance/TraitSelection persistence.
- Repository/service functions kept straightforward rather than over-engineered.
- Transactions for critical writes.
- Migration mechanism.
- Backup mechanism.
- Team soft delete and restore data model.
- Persistence round-trip tests and migration tests.
- Small developer/demo script that creates, reloads and validates persisted Teams.

Local user test target:
- Create demo data, restart the process and confirm identical data reload.
- Confirm backups are created.
- Confirm deleted Teams can be restored at data level.

## Step 3 - Trait engine, dynamic traits, slot operations and command-based undo/redo
Implement the core game/build logic before the full GUI.

Deliverables:
- Trait calculation from set data.
- Unique-champion trait counting despite duplicate champion instances.
- Breakpoint and next-breakpoint state.
- Dynamic trait selection rules.
- Slot add/remove/move/swap/compact behavior.
- Cross-List Copy and Move semantics.
- Command-based undo/redo for all core edits implemented in this step.
- Full tests for trait edge cases, duplicates, dynamic selection, slots and undo/redo.

Local user test target:
- Run included demo/tests showing duplicate champion handling, swapping, copying and exact undo/redo restoration.

## Step 4 - Functional Builder GUI
Build the first genuinely usable desktop Team Builder.

Deliverables:
- Flet desktop shell.
- Builder layout: Traits | Lists | Champion library.
- Team/List name editing.
- Primary List star.
- Active List handling.
- Create/delete/duplicate/reorder/clear/compact Lists.
- Champion library grouped by cost.
- Champion hover information.
- Champion search by champion and trait.
- Drag/drop champion placement.
- Click-to-place.
- Slot move/swap behavior.
- Cross-List Copy/Move mode.
- Dynamic Trait picker.
- Trait panel and both Trait toggles.
- Keyboard shortcuts relevant to implemented features.
- Autosave wired to real user actions.
- GUI smoke tests where practical plus full existing test suite.

Local user test target:
- Build actual Teams visually and verify every edit survives restart and undo/redo works.

## Step 5 - Start page and Team library search
Turn the Builder into a usable personal build library.

Deliverables:
- Start page.
- Set selector.
- New Team flow.
- Team cards using the same List preview component/language.
- Team name search.
- Champion mini-selection search.
- Best matching List calculation per Team.
- Required ranking rules, including duplicate selected champions.
- Navigation to/from Builder while preserving useful UI state.
- Team delete/restore UI.
- Full search/ranking tests.

Local user test target:
- Create several Teams and confirm name search and champion similarity ordering manually.

## Step 6 - TFT Team Planner import/export and native full-Team exchange
Add interoperability and robust data exchange.

Deliverables:
- Team Planner codec abstraction kept small and practical.
- Implement supported Riot Team Planner code format for the chosen Set/data source.
- List export to clipboard.
- More-than-10 temporary export-selection dialog when required by the target format.
- Code import preview and validation.
- Import as one undoable action.
- Versioned native full-Team export/import preserving all internal data.
- Round-trip and failure-case tests.

Local user test target:
- Export a List and verify it in TFT/official planner if available.
- Import known codes.
- Export/import a complete Team and compare it exactly.

## Step 7 - Hardening, usability, recovery and performance
Make the desktop application robust enough for normal daily use.

Deliverables:
- Better failure screens/messages.
- Save-state feedback.
- Backup restore path.
- Missing-asset fallbacks.
- Larger data-set performance checks.
- Cache obvious reusable asset/data work without premature complexity.
- Keyboard/focus polish.
- Long-name handling.
- Logging cleanup and diagnostic information.
- End-to-end regression suite.

Local user test target:
- Use a large synthetic library, restart repeatedly, trigger selected failure cases and confirm recoverability.

## Step 8 - Windows packaging and release candidate
Produce the first complete PC version.

Deliverables:
- Windows executable/package.
- Correct writable data directory behavior.
- Bundled Set data and legal files.
- Bundle PROJECT_CONTEXT.md, REQUIREMENTS.md, PROGRESS.md and DEVELOPMENT_PLAN.md into `project_docs/` next to the released application.
- Clean-extraction/clean-install smoke test.
- Full test suite run from release source state.
- Riot-compliance checklist review against then-current rules before any public release.
- Final complete ZIP and SHA-256 checksum.

Local user test target:
- Extract/install on the target Windows PC and use the application without a Python development environment.
