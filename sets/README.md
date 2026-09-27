# sets/

This directory contains generated, runtime-ready TFT Set packages.

The normal application reads a Set only after the package passes strict local validation. Runtime Set packages contain declarative data and local assets, never executable Set-provided Python code.

`sample_set/` is the Block 1 development package. It is deliberately fictional and small. It is generated from `../set_sources/specs/sample_set/` and exists to exercise loading, validation, assets, localization, dynamic Trait schemas, Team Planner metadata, and deterministic generation. It is not a real Riot TFT Set.

Do not hand-edit generated Set files as the normal workflow. Regenerate them from a source specification or, for production TFT data later, from the pinned Set import pipeline. Project-owned source decisions belong under `set_sources/`.

Useful Block 1 commands from the repository root:

```text
tft-builder-dev validate-set sets/sample_set
tft-builder-dev inspect-set sets/sample_set
tft-builder-dev build-set set_sources/specs/sample_set sets/sample_set --overwrite
```

See `../SET_DATA_PIPELINE.md` for source ownership, provenance, completeness, asset, and future real-data import rules.
