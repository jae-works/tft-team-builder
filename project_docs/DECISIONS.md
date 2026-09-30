# Technical Decisions

This document records consequential implementation choices that should remain understandable to another developer or AI instance. It is not intended to record every small coding choice.

## D001 - CPython 3.13 for the current Windows development baseline

Status: accepted in Block 1.

Decision:
- `requires-python` is `>=3.13,<3.14`.

Reasoning:
- Flet 1.0 supports Python 3.13 as a stable bundled runtime.
- Flet can otherwise select a newer supported Python automatically from `requires-python`.
- Pinning the minor Python line avoids silently changing the Windows packaging runtime while the project is still being built.
- Python 3.13 is modern, supported by the selected dependencies, and matches the local test interpreter used for Block 1.

Revisit when:
- a future dependency requires another Python line;
- the Windows release block establishes that Python 3.14 or later is equally safe and materially beneficial.

## D002 - Flet 1.0.1 and current Flet 1.0 APIs

Status: accepted in Block 1.

Decision:
- Use Flet 1.0.1.
- Use `ft.run(main)` and current Flet 1.0 APIs rather than compatibility code for pre-1.0 examples.

Reasoning:
- Flet 1.0 is now the stable major release.
- Carrying compatibility code for APIs removed in Flet 1.0 would add complexity without helping this new project.

## D003 - `src/` package layout plus Flet `src/main.py` entry point

Status: accepted in Block 1.

Decision:
- Importable application code lives under `src/tft_builder/`.
- Flet starts from `src/main.py` configured in `pyproject.toml`.

Reasoning:
- A `src/` layout helps tests exercise the intended installed package rather than accidentally importing arbitrary repository-root modules.
- Flet directly supports an application path under `src`.
- This keeps the Flet entry point small while the actual logic remains importable and testable.

## D004 - Pydantic for external Set schemas, dataclasses for mutable user domain state

Status: accepted in Block 1.

Decision:
- Use Pydantic 2.13.5 for JSON-facing Set, manifest, source-spec, and source-manifest schemas.
- Use standard-library dataclasses for mutable Team, TeamList, Slot, ChampionInstance, and TraitSelection domain models.

Reasoning:
- External generated/imported data benefits from strict type validation, `extra="forbid"`, and structured validation errors.
- Mutable internal Team state does not need another framework layer and remains clearer as direct Python dataclasses.
- This deliberately avoids building generic model interfaces or repositories before they are needed.

## D005 - Centralized `pathlib` plus platformdirs path policy

Status: accepted in Block 1.

Decision:
- All path construction uses `pathlib`.
- Packaged Flet storage environment paths are preferred for writable runtime data/cache locations; `platformdirs` is the non-Flet fallback unless an explicit data-root override is supplied.
- The process current working directory is not used to locate project resources.

Reasoning:
- Packaged desktop application files may be read-only.
- Windows user data belongs in a writable per-user location.
- Centralizing the rules makes normal, portable, and test paths predictable and testable.

## D006 - Runtime Set packages are local and strictly validated

Status: accepted in Block 1.

Decision:
- The runtime consumes local Set directories only.
- A Set either validates completely or is rejected; it is never partially loaded.
- Validation collects multiple independent issues in one pass when practical.

Reasoning:
- Builders should remain usable offline.
- Partial Set loading creates hard-to-debug game-data errors.
- Multiple error reporting makes manual Set development substantially faster.

## D007 - Stable local Set builder boundary before upstream source adapters

Status: accepted in Block 1.

Decision:
- Block 1 implements deterministic generation from a committed offline local source spec.
- Block 7 implements Riot Data Dragon and CommunityDragon acquisition as developer-only tooling.
- Upstream importers normalize into this stable builder boundary instead of coupling remote formats to runtime models.

Reasoning:
- Core application development should not be blocked by changing remote source formats.
- Offline fixtures make tests deterministic and fast.
- The same generated runtime schema can be validated regardless of where the upstream data came from.

## D008 - Source manifest hashes are enforced for generated files and required assets

Status: accepted in Block 1.

Decision:
- Every generated manifest/data/locale file except `source_manifest.json` itself has a SHA-256 entry in `source_manifest.json`.
- Every champion portrait and Trait icon referenced by a generated Set has a SHA-256 entry as well.
- The runtime Set validator verifies both groups and rejects missing, unexpected, or mismatched hashes.

Reasoning:
- File existence alone does not detect corruption or accidental edits.
- Hashing generated JSON/locale files catches silent manual changes to costs, Traits, mappings, or manifest configuration.
- The source manifest already records provenance information, so integrity verification remains simple and explicit.

## D009 - Hatchling build backend and pyproject-centered tool configuration

Status: accepted in Block 1.

Decision:
- Use Hatchling 1.32.4 as the Python build backend.
- Keep direct dependencies, the standardized PEP 735 `dev` dependency group, and pytest, Ruff, Hatchling, and Flet configuration in `pyproject.toml`.

Reasoning:
- `pyproject.toml` is the current Python packaging configuration standard.
- Hatchling supports the simple `src/` package without requiring legacy `setup.py` or `setup.cfg` files.
- Development-only tools belong in `dependency-groups.dev` rather than a published optional runtime extra; this matches current `uv` project guidance and keeps release dependency metadata clean.
- Central configuration avoids drift between multiple requirements/configuration files.

## D010 - Set generation is staged and non-destructive

Status: accepted in Block 1.

Decision:
- Build a candidate Set in a sibling temporary staging directory.
- Validate the staging package with the same runtime loader before promotion.
- Reject source/output directory overlap before modifying the filesystem.
- Preserve an existing valid output when generation fails before promotion.
- Reject source assets that escape or redirect source-spec containment through path traversal, symbolic links, or Windows junctions.

Reasoning:
- Developer tooling should never leave a directory that looks usable but contains only half a generated Set.
- `--overwrite` must not turn a bad source edit into loss of the last known-good generated package.
- The same validator at build time and runtime prevents two definitions of Set validity from drifting apart.
- Source-path containment makes committed source specs predictable and avoids accidentally packaging arbitrary local files.

## D011 - Flet remains the UI framework after cross-platform and license review

Status: accepted during Block 1 hardening.

Decision:
- Keep Flet 1.0.1 as the UI framework.
- Windows desktop remains the only committed first-release target.
- Keep browser and Android/iOS as deferred possibilities rather than current deliverables.
- Keep core logic free of Flet dependencies except at the application/UI boundary.

Reasoning:
- Flet has official desktop, web, Android, and iOS build paths.
- Its Apache-2.0 license is permissive for the intended distribution model.
- PySide6 is excellent for desktop but adds Qt LGPL/commercial-license considerations and does not offer the same direct web path.
- Toga is attractive for native multi-platform applications, but its web backend is not mature enough for this project's optional web direction today.
- NiceGUI is strong for web-oriented Python applications and desktop WebView packaging, but it is a weaker fit for the combination of native desktop priority and possible mobile packaging.
- Flet 1.0 is a recent major line, so exact version pinning and UI/core separation are deliberate risk controls.

Revisit when:
- Flet prevents a required Builder interaction or performance target;
- a future browser/mobile target reveals a material packaging or persistence limitation;
- Flet licensing or maintenance status changes materially.

## D012 - Bare Flet runtime package plus explicit development platform packages

Status: accepted during Block 1 hardening.

Decision:
- Runtime dependency is `flet==1.0.1`.
- Default development dependencies include the matching Flet CLI, Desktop, and test packages.
- Flet Web is kept in a separate optional `web` dependency group.
- Do not encode a `desktop_flavor = "full"` setting when the application does not use media features that require it.

Reasoning:
- Current Flet guidance separates the base runtime from platform/development tooling.
- Keeping platform packages out of published runtime metadata avoids declaring unnecessary runtime requirements.
- Isolating web tooling preserves an easy future web experiment without installing an unused platform package during normal Windows desktop development.

## D013 - Windows-first now, browser/mobile deferred but architecturally preserved

Status: accepted during Block 1 hardening.

Decision:
- Desktop Windows functionality has priority over speculative cross-platform compromises.
- Browser and mobile/tablet support remain future possibilities.
- Future browser work should evaluate dynamic Flet web first when normal Python persistence packages are required.
- Static Pyodide web deployment must not be assumed compatible with every desktop dependency.
- Pydantic depends on the native `pydantic-core` package. Flet publishes mobile wheels for `pydantic-core`, but exact version availability must be checked again before Android/iOS support is declared.

Reasoning:
- Flet dynamic web runs Python server-side and therefore preserves normal Python package compatibility.
- Static web runs Python through Pyodide and has a different package/filesystem environment.
- Mobile packaging also changes filesystem, persistence, signing, and dependency constraints.
- Treating those targets as future compatibility goals rather than current requirements avoids weakening the desktop product while still protecting the architecture from unnecessary lock-in.

## D014 - `pathlib` for paths, `os.environ` only for environment access

Status: accepted during Block 1 hardening.

Decision:
- Use `pathlib.Path` for filesystem paths and operations.
- Do not use legacy `os.path` APIs in application source.
- Reading process environment variables through `os.environ` remains appropriate and is centralized in `paths.py`.
- Prefer Flet-provided asset/data/cache environment paths when present, then use `platformdirs` as the non-Flet fallback.

Reasoning:
- `pathlib` provides clearer cross-platform path semantics.
- Environment-variable lookup is not a filesystem-path operation, so replacing `os.environ` with another library would not improve correctness.
- Centralizing both concerns keeps Windows packaging, tests, and future platform adaptations localized.

## D015 - Test the installed project and defer release identity metadata

Status: accepted during Block 1 hardening.

Decision:
- Keep the `src/` layout, but do not add `src` to pytest's configured Python path.
- Use pytest's `importlib` import mode and let `uv sync` install the project in editable mode for local development and CI.
- Do not invent `company`, `org`, or `bundle_id` metadata before the project has a final independent brand and release identity.

Reasoning:
- `uv sync` installs packaged projects with a declared build system, so tests should exercise that installed project boundary rather than bypass it through a permanent `pythonpath = ["src"]` setting.
- Pytest recommends `importlib` import mode for new projects because it avoids test-import side effects on `sys.path`.
- Flet defaults organization metadata when none is provided. A public or mobile release must replace defaults with deliberate identity metadata, but a placeholder company or organization would create misleading release metadata today.

Revisit when:
- a public Windows build is prepared and final product/company metadata exists;
- Android, iOS, macOS, or Linux packaging is implemented and requires a stable organization and bundle identifier.


## D016 - Keep Hatchling after reviewing uv_build

Status: accepted during Block 1 final hardening.

Decision:
- Keep Hatchling 1.32.4 as the build backend for the current project.
- Do not switch build backends only because uv also provides `uv_build`.

Reasoning:
- `uv_build` is a strong modern default for many pure-Python packages.
- Astral explicitly recommends considering Hatchling when a project needs more flexible layout/build behavior.
- This application uses a Flet `src/main.py` app entry, bundled assets and a package whose import name differs from the normalized project distribution name. Hatchling already handles this layout cleanly with minimal configuration.
- Switching now would add migration risk without improving runtime behavior, testability, portability or licensing.

Revisit when:
- the packaging layout becomes simpler or uv_build adds a concrete capability that reduces real project complexity.

## D017 - Do not add a second static type checker during Block 1

Status: accepted during Block 1 final hardening.

Decision:
- Keep extensive type annotations, strict Pydantic boundaries, Ruff and branch-aware pytest coverage.
- Do not make `ty`, basedpyright or another static checker a Block 1 dependency.

Reasoning:
- Astral `ty` is still classified as beta.
- basedpyright is mature enough to consider, but it would add another substantial development dependency and a new quality gate that cannot be executed in the implementation sandbox used for this handoff.
- The current domain layer is small, heavily runtime-validated and highly covered. The value of a dedicated checker increases materially once persistence repositories, command services and GUI state introduce larger typed interfaces.
- Adding an unverified quality tool would conflict with the project rule that claimed checks must actually be runnable and tested.

Revisited after Block 2:
- The direct persistence layer remains small, fully annotated where useful, and covered at 100 percent statement/branch coverage. No second static checker was added during Block 2.

Revisit when:
- Block 3 introduces enough editing/history/trait-engine surface that a stable static checker would catch concrete issues not already covered by Ruff, Pydantic boundaries and tests; or `ty` reaches a stable release suitable for a hard CI gate.

## D018 - Separate deferred web tooling from the default desktop dev environment

Status: accepted during Block 1 final hardening.

Decision:
- `uv sync` installs the Windows-first development/test stack.
- `flet-web==1.0.1` lives in a separate `web` dependency group and is installed only for a web experiment with `uv sync --group web`.

Reasoning:
- Browser support remains desirable but deferred.
- Keeping unused platform tooling out of the normal desktop environment reduces dependency surface and local setup work without sacrificing the future Flet web path.

## D019 - Security floor for uv and reproducible Set roots

Status: accepted during Block 1 final hardening.

Decision:
- Require `uv>=0.12.18,<0.13`; CI currently pins 0.12.19.
- Reject symbolic-link or junction source-spec roots/files, generated output roots and runtime Set roots where following redirects could make validation, hashing, or replacement depend on external filesystem state.
- Ignore symbolic-link and junction Set directories during automatic discovery.

Reasoning:
- uv 0.12.18 fixed a Windows wheel-install path-traversal vulnerability.
- This project is Windows-first, so the fixed floor is a meaningful security requirement rather than routine version churn.
- Set generation and runtime validation are intended to be reproducible and self-contained. Symlink roots weaken that guarantee and complicate safe overwrite/rollback behavior.

## D020 - Treat Windows junctions as link-like filesystem redirects

Status: accepted in Block 1 cleanup.

Decision:
- Treat both symbolic links and Windows directory junctions as link-like entries anywhere Set containment, hashing, discovery, or transactional generation depends on a self-contained directory tree.
- Use Python 3.13 `Path.is_junction()` together with `Path.is_symlink()`.
- Use `Path.walk()` for controlled tree scanning so link-like directories can be pruned before descent.

Reasoning:
- Windows is the mandatory first platform.
- A junction can redirect directory traversal even though `Path.is_symlink()` returns false for it.
- A reproducible Set package must not silently depend on files outside its apparent root.
- Python 3.13 already provides the required standard-library APIs, so no additional filesystem dependency is justified.

## D021 - Clean project replacement instead of development migration cleanup

Status: accepted in Block 1 cleanup.

Decision:
- Complete project handoffs replace the project files in the local checkout while preserving the hidden `.git` directory.
- Do not retain temporary cleanup utilities for obsolete development layouts once the user has moved to clean replacement.
- Keep runtime migration logic separate from source-tree handoff convenience. Real user-data/database migrations will be handled explicitly when persistence exists.

Reasoning:
- ZIP overlay updates cannot remove obsolete files and therefore created avoidable test and maintenance complexity.
- The user explicitly prefers replacing the current project contents with the new complete delivery.
- Development-only cleanup code has no value in the final product and should not become permanent maintenance surface.

## D022 - One canonical valid Set fixture plus mutation-based invalid cases

Status: accepted in Block 1 cleanup.

Decision:
- Keep one canonical generated `sample_set` as the valid integration fixture.
- Build invalid test cases by copying it into pytest temporary directories and applying the minimum mutation needed for each test.
- Do not commit full duplicate invalid fixture trees unless a future binary/file-system case cannot be expressed safely by mutation.

Reasoning:
- The removed invalid fixture directories duplicated more than one hundred files and were no longer referenced by the tests.
- Mutation-based fixtures make each failing condition explicit and prevent fixture copies from drifting independently.
- This reduces repository size and maintenance work without reducing coverage.

## D023 - Block 2 persistence stack is a decision gate, not a preselected ORM

Status: accepted as Block 2 preparation.

Decision:
- Keep SQLite as the required local persistence format.
- Do not add SQLAlchemy, Alembic, or another database framework in Block 1.
- At the start of Block 2, prototype the required transactions, migrations, ordered slots, soft delete, backups, and round-trip tests with direct `sqlite3` and compare that result with SQLAlchemy 2.0.x.
- Prefer direct `sqlite3` if it remains clear and testable. Select SQLAlchemy only if it materially reduces persistence complexity rather than merely adding abstraction.
- Use Alembic only if SQLAlchemy is selected and migration complexity justifies it.

Reasoning:
- The project has one local database and a deliberately small domain model, so the standard library may be sufficient and maximizes portability with zero additional runtime dependency.
- Flet currently publishes mobile wheels for selected SQLAlchemy 2.0.x versions, but not every current SQLAlchemy release. Choosing the newest desktop ORM release today could unnecessarily narrow a future mobile path.
- Static Flet web uses Pyodide and has different filesystem/persistence constraints from native desktop. Dynamic web is the more natural future path if the desktop persistence stack must remain unchanged.
- Browser and mobile are deferred compatibility goals, not reasons to weaken the Windows desktop implementation.

Revisit when:
- Block 2 begins and both persistence prototypes can be compared against the actual schema and migration tests;
- a future web/mobile implementation requires a different storage adapter.


## Block 2 - direct sqlite3 persistence

Decision: use Python 3.13 standard-library `sqlite3` rather than SQLAlchemy/Alembic for the current local database.

Reasons:
- one embedded local database with no server/backend abstraction requirement;
- small explicit schema and migrations are easier to audit directly;
- no added runtime dependency or mobile packaging surface;
- complete Team aggregates are naturally saved in one transaction;
- SQLite online backup API is directly available;
- 100 percent branch coverage is practical with the direct layer.

Connection policy: application-controlled explicit transactions in SQLite autocommit mode, `foreign_keys=ON`, WAL journal mode, `synchronous=FULL`, busy timeout, and `trusted_schema=OFF`.

## Block 2 hardening decisions - v0.2.1

- Keep direct Python `sqlite3`. The local Team aggregate store does not currently justify an ORM or migration framework dependency.
- Treat the complete Team as the transaction boundary. Saving a Team replaces its persisted child graph atomically.
- Batch List, Slot, ChampionInstance and TraitSelection writes with `executemany()` and load a Team with a bounded number of aggregate queries. This avoids per-Champion query growth while keeping the SQL explicit.
- Bind SQLite `busy_timeout` to the configured `Database.timeout` value so configuration has one meaning.
- Program-generated backup files use the `tft-builder-` filename namespace. Retention operates only on that namespace and never deletes unrelated `.db` files.
- Validate backup prefixes as one ASCII-safe filename token before constructing a backup path.
- Validate SQLite integrity, foreign keys, supported schema versions and Team/List/slot structural invariants before accepting restored data.
- Keep browser/mobile persistence deferred. Windows desktop uses SQLite now; a future web/mobile target must re-evaluate storage/runtime constraints instead of forcing a weaker cross-platform abstraction into the desktop core today.
- Raise the enforced statement and branch coverage gate from 95 percent to 100 percent while the project remains small enough to maintain that standard without artificial tests.


## D024 - Block 3 uses concrete edit semantics and snapshot undo/redo

Status: accepted during the version 0.2.2 pre-Block-3 audit and implemented in version 0.3.0.

Decision:
- Define slot, move, copy, List, Trait and undo/redo behavior in `BLOCK_03_PLAN.md` before implementation.
- Moving onto an occupied slot swaps Champion instances and preserves their IDs.
- Copying creates a new Champion instance ID. If the target slot is occupied, insert a new slot at that position and shift existing slots right rather than overwriting data.
- Use Team-scoped in-memory before/after snapshots for undo/redo while Team objects remain small. Do not create a generic command class hierarchy merely to implement history.
- Set schema v1 accepts only concrete Trait counting modes that the engine can implement from existing declarative data: `UNIQUE_CHAMPION` and `UNIQUE_INSTANCE`.
- Do not accept a placeholder custom counting mode until a real Set requirement defines the additional declarative fields and tests needed to evaluate it.

Reasoning:
- Block 3 behavior must be deterministic before GUI interactions depend on it.
- Snapshot history gives exact restoration of IDs, gaps, ordering, timestamps and dynamic Trait selections with less code and lower correctness risk than a large inverse-command hierarchy.
- The current Team sizes are small enough that snapshot memory cost is negligible compared with the simplicity and auditability benefit.
- An undefined custom counting branch would either be dead code or force Champion/Set-specific Python behavior, both of which conflict with the project's direct-code and declarative-Set rules.

Revisit when:
- profiling shows snapshot history has a real memory/performance problem;
- a real TFT Set requires a counting rule that cannot be represented by `UNIQUE_CHAMPION` or `UNIQUE_INSTANCE`.

## D025 - Active List is transient Builder session state

Status: accepted during version 0.3.1 Block 4 preparation.

Decision:
- Keep the currently displayed/edited List as transient Builder UI state.
- Do not persist the active List in `Team`, SQLite, or undo/redo history.
- Initialize the active List from `Team.primary_list_id`.
- If the active List disappears after delete, undo, redo, or reload, fall back to the current primary List.
- Reordering Lists does not change which List is active because identity is ID-based rather than index-based.

Reasoning:
- `primary_list_id` is persistent Team/library meaning, while the active List is navigation state for one UI session.
- Persisting navigation state would mix presentation concerns into the domain model and require a schema migration with no user-data benefit.
- Keeping this distinction explicit prevents GUI actions from accidentally changing the Team's primary List.

Revisit when:
- a future product requirement explicitly asks to restore the last viewed List across application sessions.

## D026 - Block 4 uses direct Flet composition with stable test keys

Status: accepted during version 0.3.1 Block 4 preparation.

Decision:
- Start the Builder GUI with one concrete Flet composition module and small local helper functions where they remove real duplication.
- Do not introduce presenter interfaces, a service container, an event bus, or a generic component framework before a concrete need exists.
- Use `TeamEditor` for domain mutations/history, `calculate_traits()` for Trait results, and Block 2 persistence/autosave primitives directly from the GUI composition layer.
- Give interactive controls stable explicit keys so integration tests do not depend on visible labels or localized text.
- Configure pytest with `asyncio_mode = "auto"` before Flet integration tests are added; the existing `flet[test]` development dependency remains the test dependency.

Reasoning:
- Block 3 already owns editing semantics; Block 4 should adapt those operations to controls instead of creating a parallel application architecture.
- Stable keys make GUI tests resilient to text and layout changes.
- A small direct UI is easier to inspect and change while the first real Builder workflow is still being discovered.

Revisit when:
- the concrete GUI grows enough repeated interaction/state code that extracting a focused helper clearly reduces complexity.

## D027 - Dense Builder slots and fixed-width save state

Status: accepted during version 0.4.1 after first real desktop review.

Decision:
- Keep gap-capable slots in the domain model and persistence layer.
- In the normal Builder presentation, render only occupied Champion cards plus exactly one trailing empty/end position.
- The explicit GUI remove action calls `TeamEditor.remove_slot()` so remaining positions close immediately.
- Do not show a row of internal empty domain slots in the normal Builder UI.
- Represent save state with a fixed-width icon and tooltip instead of variable-width toolbar text.
- Treat transient blank text while editing Team/List names as an input state, not as a domain failure on every keystroke; enforce non-empty names when the edit is finished.

Reasoning:
- The user's first real desktop run showed that visible internal gaps read as accidental empty cards and made the central List unnecessarily wide.
- Keeping core gap semantics preserves exact move/import/history behavior while presenting the common Builder workflow densely.
- A fixed-width status indicator prevents Undo/Redo and adjacent toolbar controls from moving when save text changes.
- Text fields naturally pass through an empty value while replacing text; logging a warning for that transient state creates noise without improving validation.

Revisit when:
- a future positional/board view intentionally needs visible empty cells as first-class placement targets.

## D028 - Block 5 keeps click-add and adds direct Flet drag/search behavior

Status: accepted during version 0.4.1 Block 5 preparation.

Decision:
- Keep the explicit add button as an accessible fallback while adding Flet `Draggable`/`DragTarget` interactions for desktop speed.
- Add Champion search by Champion and Trait display names using the existing normalizer.
- Use stable keys for drag targets, search and dynamic Trait controls.
- Implement dynamic Trait selection as a focused Builder dialog that submits `TraitSelection` through `TeamEditor`.
- Keep all domain mutation, Trait calculation and persistence in their existing layers.
- Run packaged Flet tests with `--no-cov`; the normal pytest suite remains the 100 percent application coverage gate.

Reasoning:
- Current MetaTFT and tactics.tools builders keep Traits visible and make the unit catalog searchable with click/drag as the fast path.
- Current Flet 1.0 provides native `Draggable` and `DragTarget` controls, so a custom drag framework is unnecessary.
- The packaged Flet app executes separately from the host pytest driver, so applying host-process source coverage to that test produces a false zero-percent failure.

Revisit when:
- packaged test architecture changes so application-process coverage can be collected reliably without weakening the normal coverage gate.

## D029 - Block 5 uses native drag identities and shared dynamic-Trait validation

Status: accepted and implemented in version 0.5.0.

Decision:
- Use native Flet `Draggable` and `DragTarget` controls with minimal stable source keys instead of a custom drag framework.
- Keep click-add as the reliable accessible path alongside drag/drop.
- Translate every drop into a concrete TeamEditor operation; controls never mutate slots directly.
- Add one concrete dense `move_champion_to_end()` operation because trailing-target moves should not create source gaps in the normal Builder workflow.
- Expose Trait-engine dynamic-selection validation for GUI reuse rather than duplicating rule/cardinality logic in the dialog.
- Use an explicit copy control rather than depending on modifier state that is not part of the documented pinned drag event contract.
- Run packaged Flet tests for pinned 1.0.1 through `pytest tests_flet --no-cov`; keep native drag gesture verification manual until the documented Tester API provides a stable drag helper.

Reasoning:
- Current TFT builders make unit search and click/drag placement low-friction, but our multi-List/domain semantics are already stronger than a web-board clone.
- Stable keys carry only identity; all correctness remains in the covered domain layer.
- One shared validator prevents GUI and Trait calculation from accepting different dynamic selections.
- Avoiding undocumented drag/test modifier APIs keeps the pinned desktop runtime deterministic.

Revisit when:
- Flet exposes a documented drag gesture in its Tester API or reliable modifier state in drag events;
- repeated independent Builder components justify extracting a smaller concrete UI component boundary.

## D030 - Packaged Flet entry modules start at import time

Status: accepted during version 0.5.1 after the real 0.5.0 Windows packaged-test run.

Decision:
- Keep the configured Flet entry file (`src/main.py`) minimal and call `ft.run(...)` at module scope.
- Do not guard the packaged Flet entry call behind `if __name__ == "__main__"`.
- Keep application bootstrap logic in `tft_builder.app.main`; the entry file only delegates to it.
- Maintain a regression test that loads the entry file with a non-`__main__` module name and verifies that Flet is started.

Reasoning:
- Pinned Flet 1.0.1 device-mode integration tests execute the packaged embedded-Python app, not the host-side test callback.
- The real Windows 0.5.0 packaged host started successfully but rendered no Builder controls because `src/main.py` only called `ft.run()` when executed as `__main__`.
- Normal `flet run` still worked, so this distinction must be tested explicitly rather than inferred from manual startup.

Revisit when:
- Flet packaging semantics change in a future pinned version and the replacement behavior is verified on Windows.

## D031 - Block 6 uses undo-first soft delete and explicit empty states

Status: accepted during version 0.5.1 Block 6 preparation.

Decision:
- Normal Team deletion from the Start page is an immediate recoverable soft delete and does not show a routine confirmation dialog.
- Surface Restore/Undo after soft delete and keep a discoverable Deleted/Trash view for later recovery.
- If permanent deletion is exposed, separate it visually from common actions and require a specific consequence-focused confirmation with descriptive action labels rather than Yes/No.
- Team search, Champion-similarity selection and Deleted/Trash mode must expose their active state and clear/reset affordances.
- Empty library, empty Trash and zero-result states must explain what happened and provide the next useful action.

Reasoning:
- Undoable routine actions should stay fast and reversible; repeated confirmations train users to dismiss dialogs without reading them.
- Destructive irreversible actions need stronger separation and explicit consequences.
- Blank result surfaces are ambiguous because users cannot tell zero results from loading or failure.
- The Team library is a navigation/search surface, so visible state and clear recovery paths matter more than dense controls.

Revisit when:
- user testing shows that soft-delete feedback is not discoverable enough or the library gains genuinely irreversible batch operations.

## D032 - Block 6 similarity ranking is pure, deterministic and List-aware

Status: accepted in Block 6.

Decision:
- Team-name filtering and Champion-similarity ranking live in a small Flet/SQLite-independent module.
- Similarity uses Champion multisets and scores each List independently; a Team adopts its best List score.
- Library search/filter state is session state, not persisted Team state.

Reasoning:
- Multi-List Teams are the product model, so flattening all Lists would produce misleading similarity rankings.
- Pure deterministic ranking is easier to reason about and exhaustively test than database- or UI-coupled scoring.
- Search/navigation state is transient preference, not Team content.
- Recoverable deletion behavior is already defined by D031 and is not duplicated here.

## D033 - Block 6 navigation reloads after marking a Team opened

Status: accepted in Block 6.

Decision:
- Opening a Team performs `mark_opened(team_id)` and then loads a fresh Team aggregate before creating TeamEditor.
- Returning from Builder flushes queued text before leaving; a failed flush keeps the Builder open.

Reasoning:
- Saving an aggregate loaded before `mark_opened()` could overwrite the newer database-only timestamp with stale state.
- Navigation must not silently abandon debounced text changes when persistence fails.

## D034 - Team Library reads are batched and cached between repository mutations

Status: accepted during version 0.6.1 quality audit.

Decision:
- `TeamRepository.load_all()` reconstructs all visible Team aggregates with four SELECTs regardless of Team count.
- `LibraryView` keeps one in-memory aggregate snapshot for the lifetime of the current Library screen.
- Search text, similarity selections, Set filtering and Trash toggling operate on that snapshot without re-reading SQLite.
- Repository mutations performed by the Library explicitly reload the snapshot; returning from Builder creates a fresh LibraryView and therefore a fresh snapshot.

Reasoning:
- The original Library path performed one ID query plus four aggregate queries per Team on every UI refresh, including every search keystroke.
- Library search/filter state is transient read-only state, so re-reading unchanged aggregates adds latency and disk work without improving correctness.
- A concrete batch method keeps persistence direct and avoids introducing a cache/service framework.

Revisit when:
- another process or background task can mutate the same database while one LibraryView remains mounted; that would require an explicit invalidation mechanism rather than implicit polling.

## D035 - Accessibility hardening requires non-drag operation paths and explicit semantics

Status: accepted during version 0.6.1 HCI audit; implementation remains a pre-v1.0 requirement.

Decision:
- Dragging is an accelerator, never the sole path for a core Builder edit; move/swap placement must also be operable by click/keyboard.
- Focus must remain visible, return to a logical trigger after temporary UI closes and not be obscured by application-owned overlays.
- Important status changes must have semantic/assistive-technology exposure without stealing focus.
- Essential Champion/Trait information must have a focus/click-accessible path and must not exist only on hover.
- Final visual verification includes contrast, high contrast, dark theme, scaling and target-size audits using real Set data.

Reasoning:
- WCAG 2.2 adds explicit guidance for dragging alternatives, minimum target size and unobscured/visible focus.
- Microsoft Fluent/Windows guidance emphasizes logical focus management, keyboard navigation, contrast, responsive scaling and framework semantics.
- Flet exposes `Semantics`, tooltip-derived button semantics and a semantics debugger, so these requirements can be verified without building a custom accessibility framework.

Revisit when:
- the pinned Flet version changes or platform-specific accessibility behavior requires a different control strategy.


## D0B - Runtime Set discovery uses the filesystem as the registry

Status: accepted in Block 7.

Decision:
- A valid direct child under `src/assets/sets/` is an installed Set; there is no second Python activation list.
- Set packages carry complete Set-declared Item reference data, source provenance and review inventory even when the current Builder UI does not expose Item equipping. Builder-relevant special semantics use executable fields (`trait_points`, `board_slots`, dynamic Trait rules, exact activation and derived requirements) rather than a generic mechanics metadata layer.
- Special Champion behavior is represented through generic weighted Trait contributions, board-slot costs, dynamic Trait selections and mechanic metadata rather than Champion-specific engine branches.

Reasoning:
- One authoritative installation mechanism avoids registry/folder drift.
- Complete reference data makes Set review and future features possible without forcing those features into the current UI.
- Data-driven mechanics keep future unusual Champions addable without rewriting the core Trait engine.


## D036 - Set 18 visible assets use pinned Data Dragon sprite sheets

Status: accepted during Block 7 data-completion Part 3.

Decision:
- Data Dragon TFT records are normalized by their stable `id` field rather than archive-path dictionary keys.
- Champion, Lux-variant, Trait and retained Item icons are cropped from the pinned `image.sprite` sheets and coordinates supplied by Data Dragon.
- Each shared sprite sheet is downloaded and source-hashed once; generated cropped PNGs are still individually hashed in the runtime package.
- CommunityDragon remains the supplemental source for Set relationships and richer metadata, not the preferred visible-asset host when Riot Data Dragon already exposes the exact record.

Reasoning:
- Set 18 needs only 12 sprite downloads for 246 runtime PNGs, avoiding hundreds of redundant network requests and provenance records.
- Stable Data Dragon IDs fix the previous archive-key lookup bug and cover all reviewed Set 18 Champions, Lux variants, Traits and Items.
- Cropping declared rectangles is deterministic and keeps the runtime package fully local while preserving a compact, auditable source lock.


## D037 - Release Set assets use individual Data Dragon TFT image files

Status: implemented during Block 7 post-data hardening Part 1. This supersedes D036 for release acquisition.

Decision:
- Keep Data Dragon as the preferred official visible-asset source and keep stable record-ID normalization.
- Use each ordinary reviewed record's documented `image.group` + `image.full` asset as the release image source of truth.
- Do not trust TFT `image.sprite` atlas coordinates as sufficient content proof for shipped Champion/Trait/Item images.
- Keep bounded HTTPS downloads, local cache reuse, PNG checks and SHA-256 provenance. The larger source-lock inventory is acceptable because acquisition is developer-only and correctness is more important than minimizing request count.
- For dynamic variant portraits, use the configured variant source record's CommunityDragon `squareIcon` when Data Dragon does not expose distinct `image.full` content. This stays generic to variant groups and does not branch on Champion names.

Reasoning:
- The user's first official Windows Set 18 acquisition fails because `DA_CrimsonRaptor18` exceeds the downloaded sprite bounds.
- Riot documents individual TFT icon directories and `image.full` metadata.
- Riot's developer-relations tracker has an open report for TFT Data Dragon missing sprite sheets and wrong Champion sprite coordinates, including wrong in-bounds mappings that simple bounds checks cannot detect.
- The previous 12-sprite synthetic harness verified our crop code, not the correctness of Riot's live atlas metadata.

Revisit when:
- Riot explicitly guarantees TFT atlas correctness and we can verify atlas crops against an independent official content identity without re-downloading each individual icon.

## D038 - Source locks use one generic complete-provenance verifier

Status: accepted during Block 7 post-data hardening Part 3.

Decision:
- Keep `load_set_directory()` as the authoritative generic runtime-package validator.
- Add one small generic source-lock comparison around an already validated `LoadedSet`; do not introduce another Set schema, adapter hierarchy or verifier framework.
- Compare exact source ID inventory plus URL, source revision, locale, SHA-256 and byte length, not only content hashes.
- Reject duplicate packaged provenance IDs during normal schema validation.
- Set-specific review tools may add domain expectations but must reuse the generic lock comparison.

Reasoning:
- A matching hash alone does not prove that the reviewed source identity, revision or locale is still the one intended by the acquisition configuration.
- Future Sets need the same provenance gate, while roster counts and exceptional semantics remain Set-specific review facts.
- Keeping the generic layer as two small functions plus a CLI matches the project's no-framework/no-unnecessary-abstraction rule.

Revisit when:
- the acquisition-lock format gains a deliberate versioned schema or a second independent acquisition system requires materially different provenance semantics.

## D039 - Native Pydantic core is an explicit packaged runtime dependency

Status: implemented during Block 7 post-data hardening packaged-runtime correction.

Decision:
- Keep Pydantic as the Set-schema implementation; do not rewrite the validated schema layer only to avoid a packaging defect.
- Declare `pydantic-core==2.46.5` directly beside `pydantic==2.13.5` in runtime dependencies.
- Treat `_pydantic_core*.pyd` in the final Windows bundle `DLLs` directory as a release invariant and provide a small verifier for it.
- Do not vendor a Windows `.pyd`, copy files manually into generated build output, or switch packaging systems before the supported Flet/Serious Python path is re-tested.

Reasoning:
- The packaged app reached Pydantic's Python package but failed before Flet startup because its compiled `pydantic_core` extension was absent.
- Serious Python documents Windows native extensions as files in `<exe-dir>/DLLs`; the application should verify that supported layout instead of patching generated output.
- Pydantic provides useful strict validation throughout the Set pipeline, and replacing it would be a much larger, riskier change than making its required native runtime component explicit.

Revisit when:
- the pinned Flet/Serious Python toolchain still omits the extension after a clean Windows build with the direct dependency, or Pydantic is otherwise removed from runtime Set loading.

## D040 - Disable package cleanup only for the Windows Flet build and verify both packaging stages

Status: implemented after the second clean packaged-runtime Windows failure.

Decision:
- Keep Pydantic and the explicit `pydantic-core==2.46.5` runtime dependency.
- Disable Flet package cleanup only for Windows with `[tool.flet.windows.cleanup] packages = false`; do not disable app cleanup or change other target platforms.
- Verify `build/site-packages` after Serious Python dependency staging for the packaged integration test. Verify a real `flet build windows` release bundle separately; do not treat the integration-test Debug runner as if it were the deployable bundle.
- Make the CI packaging diagnostic run with `always()` after the packaged Flet test so a failed app startup still leaves actionable staging/final evidence.
- Do not upgrade Flet in the same correction. Flet 1.0.2/Serious Python 5.0.0 is a separate candidate upgrade and should not be mixed into diagnosis of the pinned 1.0.1 failure.

Reasoning:
- The second Windows run proved that making `pydantic-core` direct was not sufficient: it was installed in the normal uv environment, while the packaged app still reached `pydantic_core/__init__.py` without its compiled `_pydantic_core` module.
- Flet documents package cleanup as enabled by default, and historical Flet Windows evidence shows cleanup removing `pydantic_core/_pydantic_core*.pyd` together with other native extension files. Preserving package files is therefore the smallest supported configuration change that directly targets the observed loss.
- The packaged integration traceback proves its embedded Python process imports dependencies directly from project `build/site-packages`. Serious Python documents `DLLs` for deployable Windows native extensions, but that final layout belongs to a real Windows release build. Separate checks prevent a false failure caused by inspecting the integration-test Debug runner as a release bundle.
- Changing the packaging toolchain and cleanup behavior simultaneously would make a successful rerun ambiguous and would add unnecessary migration risk.

Revisit when:
- a clean Windows rerun still lacks the staged `_pydantic_core*.pyd`; then inspect the exact verbose pip/Serious Python install command and consider the separately tested Flet 1.0.2 upgrade.
- staging contains the native extension but the final bundle does not; then the defect is in Serious Python's Windows relocation/copy stage rather than dependency cleanup.


## D041 - Treat Flet packaged-test staging as disposable and keep cross-platform support explicit

Status: accepted in Block 7 Part 4.

Decision:
- Rebuild Serious Python dependency staging before every packaged Flet test session; do not rely on `build/site-packages` surviving a previous packaging pass unchanged.
- Use visible text/tooltips for the Flet 1.0.1 packaged smoke. Python control keys remain useful unit-test hooks but are not a release-readiness contract for that device-mode runner.
- Keep the final Windows bundle `DLLs` verification separate from the temporary integration-test staging check.
- Keep Windows as the current blocking release platform while treating macOS, Linux, Android, iOS and Web as explicit long-term targets that must each earn support through a dedicated platform gate.

Reasoning:
- The clean Windows test staged `_pydantic_core.cp313-win_amd64.pyd` successfully, while a repeat packaged test reused a staging tree that had already been consumed and regressed to the Flet error surface.
- The same clean run reached the real Library without the Python startup error but did not expose the expected Python-side TextField key through the Flet 1.0.1 packaged tester. Visible user-facing semantics are the correct end-to-end contract at this pinned version.
- Flet and Serious Python provide target-specific desktop/mobile/web packaging layouts, so portability should be preserved by design without making unverified platforms block the Windows-first milestone.

Revisit when:
- Flet is upgraded to a release with a verified semantics identifier contract for packaged tests; then migrate the smoke from visible text/tooltips to native semantics identifiers where useful.
- a non-Windows platform becomes an active release target; add its platform-specific package/runtime gate before declaring support.
