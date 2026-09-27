# TFT Team Builder - Set Data Pipeline

This document defines how TFT Set data and assets are collected, normalized, validated and shipped.
It is a planning/architecture document until the importer is implemented.

## Decision

The application runtime must use only local, validated Set packages. It must not depend on Riot Data Dragon, CommunityDragon, or another remote service while the user is building Teams.

The build-time data pipeline uses three layers:

1. Riot Data Dragon as the preferred official source for supported localized TFT data and visible assets such as champion portraits and Trait icons.
2. CommunityDragon as a supplemental, build-time source and cross-check for TFT client metadata that Data Dragon does not expose conveniently or completely, including Set membership/relationships, Team Planner metadata and richer Trait metadata where needed.
3. Small, explicit project-owned overrides for mechanics or mappings that cannot be derived reliably from the source data.

CommunityDragon is a community project and is not a Riot-supported API. It must never become a runtime dependency. Before a public release, any CommunityDragon-derived fields or assets that are shipped must be reviewed against the then-current Riot rules. Prefer Riot-hosted assets whenever they are available.

## Reproducibility

Generated Set packages must be reproducible from pinned inputs.

- Do not build a release Set package against an unrecorded `latest` endpoint.
- An importer may use `latest` for discovery, but it must resolve and record the exact source version/revision used for generation.
- Store source URLs/identifiers, locale, retrieval timestamp and SHA-256 hashes of downloaded source payloads in the generated source report/manifest.
- Record the Data Dragon version separately from the CommunityDragon version because they may update at different times.
- Do not silently upgrade an existing Set package when the application starts.

## Field/source policy

The importer must define source ownership per field rather than applying one global precedence rule.

Examples of intended ownership:

- Localized display names and Riot-hosted champion/Trait assets: prefer Riot Data Dragon when available.
- Champion cost/tier: compare available sources; a disagreement is a validation/review error rather than a silent overwrite.
- Set membership and champion-to-Trait relationships when not adequately represented by Data Dragon: derive from the pinned supplemental TFT client metadata.
- Trait breakpoints/styles: derive from the richest pinned source that exposes them, then validate them structurally.
- Team Planner identifiers/mappings: derive from the pinned Team Planner metadata and verify with round-trip fixtures later.
- Special selectable/dynamic Trait behavior: explicit project override unless a source exposes an unambiguous rule that we have tested.

If two trusted inputs disagree on a field that should agree, generation must stop with a readable conflict report. Overrides may resolve a conflict only when the override contains a human-readable reason.

## Raw input and generated output

Downloaded raw payloads belong in a local cache such as:

```text
.cache/
    set_import/
```

The cache is not committed to Git and is not required by the application runtime.

Project-owned manual decisions live in:

```text
set_sources/
    overrides/
        <set_id>.json
```

Generated runtime Set packages live in:

```text
sets/
    <set_id>/
        manifest.json
        source_manifest.json
        data/
            champions.json
            traits.json
            dynamic_traits.json
            team_planner.json
        locales/
            en.json
        assets/
            champions/
            traits/
```

The exact filenames may evolve when implementation starts, but the separation between raw sources, overrides and generated runtime data must remain.

## Completeness model

A Set is not considered complete merely because every local JSON file parses.

The importer must produce a source inventory and a completeness report. Client/source data can include summoned units, debug entries, alternate forms, legacy records or other entities that are not intended to appear in the Team Builder, so a simple raw record count is insufficient.

Every source candidate must end in one of these states:

- INCLUDED: present in the generated Set package.
- EXCLUDED: deliberately omitted with an explicit machine-readable reason.
- ERROR: unresolved; generation/validation fails.

Examples of legitimate exclusions can include source records that are verified summoned-only entities, debug/test units, non-player Team Planner entries, or records belonging to a different Set. The exact exclusion reason must be preserved so another developer/AI instance can audit the decision.

The completeness report must verify at minimum:

- expected player-selectable champions are all represented;
- every included champion has a valid cost, display name, asset and valid Trait references;
- every included Trait has a valid ID, display name, icon and structurally valid breakpoints;
- dynamic Trait choices reference real Traits;
- Team Planner mappings are present when the Set declares Team Planner support;
- no source candidate disappeared without either inclusion or an explicit exclusion reason;
- no duplicate IDs are introduced during normalization;
- source conflicts have been resolved explicitly rather than silently.

## Asset policy

- Prefer Riot Data Dragon/TFT assets for shipped visible assets when available.
- Assets are copied into the generated Set package so the runtime works offline.
- Generated asset paths must be local relative paths; the GUI must not hotlink remote images.
- Missing required assets fail Set generation/validation. Runtime fallback behavior still exists for corruption after installation, but a Set should not be released in that state.
- Asset file hashes may be stored in `source_manifest.json` to detect accidental corruption or drift.

## Localization

The initial application UI and Set package use English.

The pipeline must keep localization separate from stable IDs so additional locales can be imported later without changing Team/Champion/Trait identity. Data Dragon locale data should be preferred for Riot-provided localized names when available.

## Importer and validator tools

Planned developer tools:

```text
tools/
    set_import/
        build_set.py
        validate_set.py
```

The exact split may change if a smaller implementation is clearer. We will not create extra interfaces/classes solely to match this sketch.

The tools must support:

- pinned source configuration;
- download/cache with hashes;
- source parsing;
- Set candidate filtering;
- explicit exclusion reporting;
- manual overrides;
- normalization into the runtime schema;
- local asset extraction/copy;
- schema validation;
- source/completeness validation;
- readable errors suitable for both humans and tests.

## Tests

Network availability must not be required for the normal unit test suite.

Tests will use committed small fixtures representing source payloads and generated Set packages. Coverage must include:

- a valid minimal import;
- malformed source data;
- missing required files;
- duplicate champion/Trait IDs;
- unresolved champion-to-Trait references;
- missing required assets;
- invalid Trait breakpoint order/ranges;
- conflicting source values;
- valid and invalid manual overrides;
- source candidates missing from both INCLUDED and EXCLUDED sets;
- explicit exclusions with reasons;
- deterministic generation from the same pinned inputs;
- source manifest/hash generation.

Optional/manual network integration checks may be provided later, but they must not make the normal local test suite flaky.

## Runtime rule

The normal application reads only generated Set packages from `sets/`. It does not download source data or attempt to repair a Set from the internet. If an installed Set fails validation, the application reports the errors and refuses to partially load it.
