# Block 7 post-data hardening plan

This document records the post-acquisition hardening requested after the first real Windows Set 18 run. The work is split into four small parts so corrections can be verified between handoffs. This remains Block 7 hardening and does not replace roadmap Block 8.

## Part 1 - Audit plus justified corrections

Status: complete.

### Confirmed data semantics

- Set 18 remains 91 raw Champion records -> 65 logical Champions, 36 logical Traits and 136 retained Item references.
- Elder Dragon declares exactly 2 board slots and exactly +2 Riftbeast in Set data.
- Kha'Zix remains one logical Champion with a ZERO_OR_ONE, PER_CHAMPION evolution choice and base-portrait fallback.
- Lux remains one logical Champion, the chosen Avatar origin contributes 2 Trait points, and Set 18 uses PER_CHAMPION scope so duplicate Lux copies in one List cannot disagree.
- Rival's ordinary base-Set state is exact at one Rival; the two-Rival state is Augment-gated and is not a normal base breakpoint.
- Eclipse remains a derived state requiring at least 3 Solar and 3 Lunar.

### Corrections implemented

- Replaced release sprite-atlas cropping with individual Riot Data Dragon `image.group` + `image.full` acquisition for ordinary Champion, Trait and Item assets.
- Dynamic variant portraits use each configured variant source record's CommunityDragon `squareIcon` generically. This is necessary because Set-18 Lux variants share one Data Dragon `image.full` portrait even though CommunityDragon exposes distinct variant records.
- Added generic board usage as the sum of Set-declared `board_slots`; no Elder Dragon branch exists in runtime code.
- Changed only Set-18 Lux data to PER_CHAMPION; the generic engine still supports PER_INSTANCE for future Sets that require it.
- A new/refreshed `source_lock.json` is prepared before package construction but atomically published only after `build_set_from_local_spec()` succeeds.
- Removed the importer-only direct Pillow dependency because production atlas cropping no longer exists.

## Part 2 - Windows correction verification and bug closure

Status: complete; exact final Ruff rerun is part of Part 4.

The user's real Windows run proved the corrected acquisition path works with official bytes:

- 679 tests passed before acquisition at 100 percent statement/branch coverage.
- Official Set-18 acquisition completed and wrote a validated package plus `source_lock.json`.
- Generic validation and inspection found 65 Champions, 36 Traits and 136 Items.
- The Set-18 reviewed verifier passed with 246 runtime PNGs and 255 provenance sources.
- Database and Builder smokes passed.

Two small follow-up classes were found and corrected locally:

- Ruff 0.16.9 reported six formatter-drift files and three import-block ordering findings; the exact reported formatting/import changes are applied in this handoff.
- Three post-acquisition startup tests assumed `sample_set` was the only installed Set. They now build an isolated sample-only assets root, so installing the real Set cannot invalidate an unrelated startup fixture.

## Part 3 - Generic provenance verifier and deeper tests

Status: implemented and locally verified.

- `tft_builder.source_verification` compares any validated Set package with a reviewed acquisition lock without introducing another Set schema/framework.
- The comparison validates Set ID/revision, exact provenance-ID inventory and every source record's URL, revision, locale, SHA-256 and byte length.
- Malformed JSON, malformed source records, duplicate lock IDs, missing IDs and unexpected IDs are reported explicitly.
- `SourceManifest` now rejects duplicate packaged provenance IDs during normal Set validation.
- `tools/set_import/verify_source_lock.py` exposes the generic comparison as a small developer CLI for future Sets.
- `verify_enchanted_wilds.py` reuses the generic source-lock verifier and keeps only Set-18-specific semantic expectations.
- The real official Set-18 package is the positive complete verifier fixture.
- Mutation tests cover Elder Dragon, Lux, Kha'Zix, Rival, Eclipse, Team Planner mapping, Item category drift, source accounting, locale markup, runtime asset inventory and complete provenance-field drift.
- Official individual-image URL construction, CommunityDragon variant-image acquisition and failed-build lock atomicity remain explicitly tested.
- Local normal suite: 689 tests; 3,024 production statements and 922 branches at 100 percent statement/branch coverage.

## Part 4 - Final confidence and next-block preparation

Status: planned.

- Compare one clean-cache official acquisition with one warm-cache rerun for deterministic package/provenance output.
- Add lightweight image sanity checks for missing, blank or obviously duplicated required icons without pretending to perform semantic computer vision.
- Run the complete Windows gate: exact Ruff 0.16.9, compileall, normal tests, generic provenance verifier, Set-18 verifier, database/builder smokes, normal Flet startup and packaged Flet integration.
- Exercise Lux choice portraits, Kha'Zix evolution text/base portrait, Elder Dragon board usage, Rival, Eclipse and long localized labels in the real GUI.
- Close Block 7 hardening and prepare roadmap Block 8 Team Planner import/export.
