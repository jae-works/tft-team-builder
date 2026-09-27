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
- Runtime writable user locations are resolved by `platformdirs` unless an explicit data-root override is supplied.
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
- Reject source assets that resolve outside the source-spec directory through symlinks.

Reasoning:
- Developer tooling should never leave a directory that looks usable but contains only half a generated Set.
- `--overwrite` must not turn a bad source edit into loss of the last known-good generated package.
- The same validator at build time and runtime prevents two definitions of Set validity from drifting apart.
- Source-path containment makes committed source specs predictable and avoids accidentally packaging arbitrary local files.
