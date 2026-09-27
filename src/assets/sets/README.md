# Runtime Set packages

This directory contains generated, runtime-ready TFT Set packages that are bundled as Flet application assets.

The application reads a Set only after the package passes strict local validation. Runtime Set packages contain declarative data and local assets, never executable Set-provided Python code.

`sample_set/` is the fictional Block 1 development package. It is generated from `set_sources/specs/sample_set/` and exists only to exercise loading, validation, assets, localization, dynamic Trait schemas, Team Planner metadata, integrity checks, and deterministic generation.

Do not hand-edit generated Set files as the normal workflow. Regenerate them from their source specification.

Useful commands from the repository root:

```text
uv run tft-builder-dev validate-set src/assets/sets/sample_set
uv run tft-builder-dev inspect-set src/assets/sets/sample_set
uv run tft-builder-dev build-set set_sources/specs/sample_set src/assets/sets/sample_set --overwrite
```

See `SET_DATA_PIPELINE.md` in the repository root for the future Riot/CommunityDragon import rules.
