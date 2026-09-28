# TFT Team Builder

Current version: 0.6.1
Current milestone: Block 6 Team Library is implemented and quality-audited in v0.6.1. The Library now uses bounded batch aggregate reads, in-view search/filter caching and best-match List previews; HCI/accessibility requirements are refined for final hardening. Exact v0.6.1 Windows Ruff/Flet verification remains pending.

TFT Team Builder is a local-first Team builder and personal Team library for Teamfight Tactics. Windows desktop is the required first platform. Browser and mobile/tablet targets are deliberately deferred, not removed from the long-term project direction.

## Platform strategy

Immediate target:
- Windows desktop: required.

Deferred targets:
- Browser: possible later, with Flet dynamic web as the most practical first web option if this becomes a real requirement.
- Android/iOS: possible later if the desktop product proves useful enough to justify mobile UI and packaging work.

The core models, Set validation, search, persistence boundaries, and future game logic must not depend on Flet widgets. This keeps the project portable and leaves an escape route if the UI framework ever needs to change.

Flet 1.0.1 remains the selected UI framework after a Block 1 re-evaluation. It supports Windows, web, Android, and iOS from one Python-oriented UI stack, uses a permissive Apache-2.0 license, and is a better strategic fit here than a desktop-only choice. Desktop remains the only committed release target today.

## Project language and character policy

All project-authored source code, technical documentation, filenames, paths, comments, configuration keys, schema keys, logs, and default UI text are English. Project-authored technical text uses simple ASCII punctuation. Localized game data is the explicit exception when a language requires non-ASCII characters.

## Supported development runtime

The current development line is CPython 3.13.

`requires-python` is intentionally `>=3.13,<3.14`. Flet can select a Python runtime from that range during builds, so this prevents a silent move to another Python minor version before we explicitly test and approve it.

Pinned direct runtime dependencies:
- Flet 1.0.1
- Pydantic 2.13.5
- platformdirs 4.11.15

Pinned development dependencies:
- Flet CLI 1.0.1
- Flet Desktop 1.0.1
- Flet Web 1.0.1 in the optional `web` dependency group
- Flet test extras 1.0.1
- pytest 9.1.1
- pytest-cov 7.1.0
- Ruff 0.16.9
- Hatchling 1.32.4 as the build backend

## Setup with uv

From the repository root in Git CMD or another normal terminal:

```text
uv python install 3.13
uv sync
```

The default sync installs the Windows desktop development/test toolchain. A future web experiment can add the deferred web group with `uv sync --group web`.

`uv sync` creates or updates `uv.lock`. Keep `uv.lock` in Git. The committed lockfile is part of the reproducible development environment.

Project handoffs are clean replacements rather than ZIP overlays. When replacing a local checkout, keep the hidden `.git` directory, remove the other project files, and copy in the complete delivered project. Do not delete `.git` unless you intentionally want to destroy the local Git repository.

The pinned Flet 1.0.1 integration plugin runs the app in packaged device mode. The configured `src/main.py` therefore starts Flet at module import time as required by the packaged runtime; guarding `ft.run()` behind `if __name__ == "__main__"` would make the packaged test app render an empty page even though normal `flet run` works.

Run the current quality checks:

```text
uv lock --check
uv sync --frozen
uv run ruff format .
uv run ruff check .
uv run ruff format --check .
uv run pytest
uv run python tools/check_ascii.py
uv run python tools/sync_project_docs.py --check
uv run python -m compileall -q src tests tests_flet tools
uv run tft-builder-dev validate-set src/assets/sets/sample_set
uv run tft-builder-dev inspect-set src/assets/sets/sample_set
uv run tft-builder-dev database-smoke .runtime-smoke
uv run tft-builder-dev builder-smoke src/assets/sets/sample_set
uv run pytest tests_flet --no-cov
uv run flet --version
uv run flet run
```


Windows note: packaged Flet desktop integration tests build a Flutter Windows host. Windows Developer Mode must be enabled so Flutter can create plugin symlinks. The packaged Flet app runs in a separate process, so this integration-driver test intentionally disables pytest-cov with `--no-cov`; the normal `uv run pytest` suite remains the mandatory 100 percent statement/branch coverage gate.

## Persistence development command

Run a complete persistence round-trip and backup smoke test in an explicit disposable directory:

```text
uv run tft-builder-dev database-smoke .runtime-smoke
```

The command creates `.runtime-smoke/builder.db` and a validated SQLite backup. Remove the disposable directory after the check. Normal application data uses the centralized platform-aware writable data path instead.

## Block 3 core smoke command

Exercise the non-visual Builder editor, dynamic Trait calculation and undo/redo against the bundled sample Set:

```text
uv run tft-builder-dev builder-smoke src/assets/sets/sample_set
```

The command is intentionally small and deterministic. It complements, rather than replaces, the exhaustive pytest suite.

## Set development commands

Validate the bundled sample Set:

```text
uv run tft-builder-dev validate-set src/assets/sets/sample_set
```

Inspect it:

```text
uv run tft-builder-dev inspect-set src/assets/sets/sample_set
```

Regenerate it from the committed local source specification:

```text
uv run tft-builder-dev build-set set_sources/specs/sample_set src/assets/sets/sample_set --overwrite
```

The normal application reads only local validated Set packages. Real Riot Data Dragon and CommunityDragon acquisition is deferred until Block 7.

## Important directories

```text
src/
    main.py
    assets/
        sets/
    tft_builder/

set_sources/
    specs/
        sample_set/
    overrides/

tests/

tools/
    check_ascii.py
    set_import/

project_docs/
```

The bundled `sample_set` is fictional. It exists only to exercise validation, generation, assets, localization, dynamic Trait schemas, and Team Planner metadata.

## Licensing and public release

The application itself does not yet have a selected public source-code license. That choice must be made deliberately before a public source release.

Third-party software and Riot/TFT asset/data obligations are separate concerns. `LICENSE_REVIEW.md` records the current dependency-license review and the release gates that must be completed before distributing a public build.

## Project documents

Read these in order before changing the project:

1. `PROJECT_CONTEXT.md`
2. `REQUIREMENTS.md`
3. `PROGRESS.md`
4. `IMPLEMENTATION_BLOCKS.md`
5. `DEVELOPMENT_PLAN.md`
6. `DECISIONS.md`
7. `LICENSE_REVIEW.md`
8. `SET_DATA_PIPELINE.md`
9. `BLOCK_01_REPORT.md`
10. `BLOCK_02_REPORT.md`
11. `BLOCK_03_PLAN.md`
12. `BLOCK_04_PLAN.md`
13. `BLOCK_04_REPORT.md`
14. `BLOCK_05_PLAN.md`
15. `BLOCK_05_REPORT.md`
16. `BLOCK_06_PLAN.md`
17. `BLOCK_06_REPORT.md`
18. `BLOCK_07_PLAN.md`

Every delivered project ZIP must contain the complete current project and a SHA-256 checksum calculated after the final ZIP is created.
