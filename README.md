# TFT Team Builder

Current version: 0.1.0
Current milestone: Block 1 complete - foundation, Set system, core models, deterministic sample Set generation, and strict Set validation.

This repository is a Windows-first desktop Team builder and personal Team library for Teamfight Tactics. The current version intentionally focuses on the foundation. The full Builder UI is scheduled for later implementation blocks.

## Project language and character policy

All project-authored source code, technical documentation, filenames, paths, comments, configuration keys, schema keys, logs, and default UI text are English. Project-authored technical text uses simple ASCII punctuation. Localized game data is the explicit exception when a language requires non-ASCII characters.

## Supported development runtime

The project currently targets CPython 3.13. Flet 1.0.1 supports Python 3.13, and the explicit Python range keeps the desktop packaging runtime stable instead of silently moving to a newer bundled Python release.

Pinned direct runtime dependencies:

- Flet 1.0.1
- Pydantic 2.13.5
- platformdirs 4.11.14

Pinned development dependencies:

- Flet CLI 1.0.1
- Flet Desktop 1.0.1
- pytest 9.1.1
- Ruff 0.16.9

## Recommended setup with uv

From the repository root on Windows:

```powershell
uv python install 3.13
uv sync
```

The first successful `uv sync` also creates or updates `uv.lock`. Keep that lockfile in Git once it has been generated in a connected environment so future environments resolve the same transitive dependency graph.

Run the desktop shell:

```powershell
uv run flet run
```

Run the complete test suite:

```powershell
uv run pytest
```

Run lint and formatting checks:

```powershell
uv run ruff check .
uv run ruff format --check .
```

Run the repository character-policy check:

```powershell
uv run python tools/check_ascii.py
```

Validate the bundled development Set:

```powershell
uv run tft-builder-dev validate-set sets/sample_set
```

Inspect it:

```powershell
uv run tft-builder-dev inspect-set sets/sample_set
```

Regenerate it deterministically from the committed local source spec:

```powershell
uv run tft-builder-dev build-set set_sources/specs/sample_set sets/sample_set --overwrite
```

## Alternative setup with pip

`uv` is the preferred project workflow because it understands the standardized development dependency group and creates the project lockfile. If `uv` cannot be used, install the same pinned packages explicitly:

```powershell
py -3.13 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e .
python -m pip install flet-cli==1.0.1 flet-desktop==1.0.1 pytest==9.1.1 ruff==0.16.9
pytest
```

## Important directories

```text
src/
    main.py
    tft_builder/

sets/
    sample_set/

set_sources/
    specs/
        sample_set/
    overrides/

tests/
    fixtures/
    ...

tools/
    check_ascii.py
    set_import/

project_docs/
```

The normal application reads only local validated Set packages. Upstream Riot and CommunityDragon acquisition is intentionally deferred until Block 7. Block 1 already defines the stable local normalization boundary and deterministic builder that those future source adapters will feed.

## Project documents

Read these in order before changing the project:

1. `PROJECT_CONTEXT.md`
2. `REQUIREMENTS.md`
3. `PROGRESS.md`
4. `IMPLEMENTATION_BLOCKS.md`
5. `DEVELOPMENT_PLAN.md`
6. `DECISIONS.md`
7. `SET_DATA_PIPELINE.md`
8. `BLOCK_01_REPORT.md`

Every delivered project ZIP must contain the complete current project and a SHA-256 checksum calculated after the final ZIP is created.
