# sets/

This directory contains generated, runtime-ready TFT Set packages.

The normal application reads from this directory only after a Set package passes local validation. Set packages contain data and local assets, never executable Set-provided Python code.

Do not hand-edit generated Set files as the normal workflow. Source-specific/manual decisions belong under `set_sources/overrides/`, and the Set importer regenerates the runtime package.

See `../SET_DATA_PIPELINE.md` for source ownership, provenance, completeness rules and the planned importer/validator workflow.
