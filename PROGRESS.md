# TFT Team Builder - Progress

This is the implementation log. REQUIREMENTS.md describes what the project must do; this file records what has actually been implemented and verified.

Legend:
- [ ] pending
- [~] in progress
- [x] implemented/planning artifact created and locally verified
- [!] blocked / needs correction

## Current version
v0.0.3-planning

## Completed planning/handoff work
- [x] Requirements checklist established.
- [x] Development workflow established.
- [x] Project divided into larger implementation steps.
- [x] `PROJECT_CONTEXT.md` established as the first handoff document.
- [x] Dedicated `sets/`, `set_sources/`, `tools/set_import/`, `src/` and `tests/` paths are represented in the planning package.
- [x] Requirement established that each delivered build contains complete source, tests, set data, project documents and metadata.
- [x] Requirement established that each delivered ZIP receives a SHA-256 checksum after final packaging.
- [x] Pragmatic coding style documented: detailed tests/comments without unnecessary interface/generic-class proliferation.
- [x] Set-data source strategy reviewed against current Riot TFT/Data Dragon documentation and current CommunityDragon TFT listings.
- [x] Added `SET_DATA_PIPELINE.md` defining build-time source roles, pinned provenance, source conflict handling, local assets, manual overrides and offline runtime behavior.
- [x] Corrected completeness design so debug/summoned/alternate/legacy source records require explicit classification rather than naive source-record counting.
- [x] Added the rule that every source candidate must be INCLUDED, EXCLUDED with a reason, or ERROR.
- [x] Added reproducibility requirement: exact source revisions and hashes are recorded; unrecorded `latest` is not a release input.
- [x] Added `.gitignore` rules for Python/build output and local source-download caches.

- [x] Added `IMPLEMENTATION_BLOCKS.md` as the persistent nine-block high-level roadmap.
- [x] Documented that future blocks may be adjusted after completed blocks when implementation findings justify it.
- [x] Split the planned Builder work into a functional GUI block and a separate full desktop-interaction/polish block.
- [x] Moved completion of the real production TFT Set pipeline into its own planned Block 7, while Block 1 establishes the schemas, validator, fixtures and tooling foundation.
- [x] Documented the standard Git delivery command-block requirement.

## Not yet implemented
- [ ] Application source code.
- [ ] Set importer/downloader.
- [ ] Generated real Set package.
- [ ] Set loader and validator code.
- [ ] Database.
- [ ] Trait engine.
- [ ] Undo/redo.
- [ ] GUI.
- [ ] Import/export.
- [ ] Windows packaging.

## Verification for v0.0.3-planning
- [x] Required root planning documents exist.
- [x] `IMPLEMENTATION_BLOCKS.md` exists and documents all nine current implementation blocks.
- [x] `DEVELOPMENT_PLAN.md` points to the block roadmap and documents how the roadmap may evolve.
- [x] `SET_DATA_PIPELINE.md` exists.
- [x] `sets/README.md` exists.
- [x] `set_sources/README.md` exists.
- [x] `tools/set_import/README.md` exists.
- [x] `src/`, `tests/`, `sets/`, `set_sources/overrides/` and `tools/set_import/` are represented in the ZIP via tracked placeholder/readme files.
- [x] Project documentation copies are generated into `project_docs/` before packaging.
- [x] Planning archive integrity and required-file verification performed after packaging.

No application tests are claimed in this planning-only version because application code does not exist yet.
