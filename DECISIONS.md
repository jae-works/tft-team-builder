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
- Riot Data Dragon and CommunityDragon acquisition are deferred to Block 7.
- Future upstream adapters must normalize into this stable builder boundary instead of being coupled directly to runtime models.

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

Revisit when:
- Block 2 introduces persistence/service interfaces, or `ty` reaches a stable release suitable for a hard CI gate.

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
