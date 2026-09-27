# Block 1 Implementation Report

Status: complete.
Version: 0.1.0.

## Delivered functionality

Block 1 now contains working application foundation code rather than planning placeholders.

Implemented:

- Python 3.13 project baseline and `pyproject.toml`.
- Flet 1.0 desktop entry point and minimal startup shell.
- Centralized application path model using `pathlib` and `platformdirs`.
- Runtime directory creation that is explicit rather than a side effect of path lookup.
- Rotating application logging configuration with log-directory reconfiguration support.
- Integrated non-visual startup path for runtime directories, logging, and bundled Set validation.
- Mutable Team, TeamList, Slot, ChampionInstance, and TraitSelection models with core invariants.
- Strict Pydantic schemas for Set manifests, champions, Traits, dynamic Trait rules, Team Planner metadata, local build specs, and source manifests.
- Strict Set package loader and multi-error validator.
- Set discovery and batch validation.
- Search text normalization.
- Deterministic offline Set generation from a local source spec.
- Generated source manifest with SHA-256 values.
- Required runtime generated-data and asset hash verification.
- Transactional directory-level Set generation using validated staging output.
- Non-destructive overwrite behavior when a rebuild fails.
- Developer CLI for Set build, validation, and inspection.
- Repository ASCII-policy tool.
- Bundled `sample_set` generated from the committed source spec.
- One valid and eight deliberately invalid committed Set fixtures.
- Extensive pytest suite.
- Automated project-manifest and `project_docs/` mirror-integrity tests.

## Validator coverage

The Set validator currently checks at least:

- missing Set directories;
- missing manifest or required data files;
- invalid UTF-8 and invalid JSON;
- strict Pydantic schemas with unknown keys rejected;
- supported schema versions;
- safe relative metadata paths;
- symlink/path escapes where the platform permits testing them;
- unique Champion and Trait IDs;
- one dynamic rule per Champion;
- valid Champion-to-Trait references;
- valid dynamic-Trait Champion and Trait references;
- required champion portraits and Trait icons;
- non-empty assets;
- PNG signatures for `.png` assets;
- assets stored under the declared assets directory;
- complete default/supported locale catalogs;
- Team Planner mapping consistency;
- source-manifest generated-file and asset hash coverage;
- SHA-256 agreement for required generated files and required assets;
- deterministic ordering of reported validation issues;
- non-empty Champion/Trait catalogs.

## Local tests performed in the implementation environment

Commands run successfully:

```text
PYTHONPATH=src pytest -q
python tools/check_ascii.py
python -m compileall -q src tools tests
PYTHONPATH=src python -m tft_builder.devtools build-set set_sources/specs/sample_set sets/sample_set --overwrite
PYTHONPATH=src python -m tft_builder.devtools validate-set sets/sample_set
```

Pytest result:

```text
204 passed
```

The bundled sample Set validated successfully after deterministic regeneration. Project metadata and mirrored handoff documents also passed automated integrity checks.

## Tooling limitation of the implementation environment

The implementation sandbox does not have outbound Python package-index access. Because Flet 1.0.1 and Ruff 0.16.9 were not already installed in that sandbox, the exact pinned Flet desktop process and Ruff binary could not be executed there.

This is not treated as a passed check. Instead:

- Flet code was written against the current Flet 1.0 documentation and syntax-compiled successfully.
- Ruff configuration is present in `pyproject.toml` but must be run in the user's normal connected development environment with `uv sync`.
- The core pytest suite ran against Python 3.13 with compatible installed Pydantic/platformdirs versions.

The user should run the documented `uv` commands after extracting this version. Any issue found there belongs to Block 1 correction before Block 2 begins.
