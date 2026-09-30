# TFT Team Builder - Set Data Pipeline

This document defines how TFT Set data and assets are collected, normalized, validated and shipped.

Current implementation status: schema v5 Champion/Item/Trait normalization and corrected release acquisition are implemented. Ordinary visible assets use individual Data Dragon `image.full` files, while dynamic variant portraits use each configured source record's CommunityDragon `squareIcon` when Data Dragon lacks distinct variant art. New/refreshed source locks are published only after a successful package build. The next gate is the real Windows acquisition and lock review.

## Decision

The application runtime must use only local, validated Set packages. It must not depend on Riot Data Dragon, CommunityDragon, or another remote service while the user is building Teams.

The build-time data pipeline uses three layers:

1. Riot Data Dragon as the preferred official source for supported localized TFT data and visible assets such as champion portraits and Trait icons.
2. CommunityDragon as a supplemental, build-time source and cross-check for TFT client metadata that Data Dragon does not expose conveniently or completely, including Set membership/relationships, Team Planner metadata and richer Trait metadata where needed.
3. Small, explicit project-owned overrides only for Builder semantics or mappings that cannot be derived reliably from the source data.

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
- Trait breakpoints/styles: derive from the richest pinned source that exposes them, then validate them structurally. Resolve tooltip variables at build time, including CommunityDragon BIN-field hashes (lowercase FNV-1a), and store plain localized breakpoint text so runtime UI never parses Riot markup.
- Team Planner identifiers/mappings: derive from the pinned Team Planner metadata and verify with round-trip fixtures later.
- Special selectable/dynamic Trait behavior, exact-count activation and derived Trait requirements: explicit project override unless a source exposes an unambiguous rule that we have tested.
- Current-Set Item candidates: start from the pinned CommunityDragon Set Item list, then apply the reviewed source-configured canonical boundary. For Set 18 the retained inventory is 10 components, 39 craftable items, 20 emblems, 31 current artifacts and 36 radiant items. Broad Wisp/mechanic objects, temporary utilities and duplicate/legacy aliases remain in source accounting as exclusions instead of being shipped. Riot Data Dragon may supply preferred localized fields/assets but is not used as an unfiltered Set-membership list.
- Alternate upstream Champion records that represent one player unit may normalize into one logical Champion. Source accounting remains explicit, and optional per-choice portrait paths stay in Set data rather than Champion-name GUI branches.

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
src/assets/sets/
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

The current runtime package filenames are implemented in Block 1. Later schema versions may evolve them deliberately, but the separation between raw sources, overrides, and generated runtime data must remain.

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
- dynamic Trait choices reference real Traits and any optional choice portrait is a validated Set-owned asset;
- Team Planner mappings are present when the Set declares Team Planner support;
- no source candidate disappeared without either inclusion or an explicit exclusion reason;
- no duplicate IDs are introduced during normalization;
- source conflicts have been resolved explicitly rather than silently.

## Asset policy

- Prefer Riot Data Dragon/TFT assets for shipped visible assets when available. Release acquisition must use a documented/content-verifiable individual asset path; TFT sprite atlas metadata is not trusted as the content source of truth because upstream coordinates/sheets can be inconsistent.
- Assets are copied into the generated Set package so the runtime works offline.
- Generated asset paths must be local relative paths; the GUI must not hotlink remote images.
- Missing required assets fail Set generation/validation. Runtime fallback behavior still exists for corruption after installation, but a Set should not be released in that state.
- Required asset hashes are stored in `source_manifest.json` and verified at runtime to detect accidental corruption or drift.
- Generated manifest/data/locale file hashes are also stored and verified, so hand-edited or corrupted runtime data is rejected instead of silently diverging from its generated source.

## Localization

The initial application UI and Set package use English.

The pipeline must keep localization separate from stable IDs so additional locales can be imported later without changing Team/Champion/Trait identity. Data Dragon locale data should be preferred for Riot-provided localized names when available.

## Importer and validator tools

Block 1 provides these developer entry points:

```text
tools/
    set_import/
        build_set.py
        validate_set.py
```

The current `build_set.py` command builds a deterministic runtime package from a committed local source specification, and `validate_set.py` validates an existing runtime package. The same functionality is also available through the `tft-builder-dev` command.

Implemented in Block 1:

- local source-spec parsing;
- normalization into the runtime schema;
- local asset copy;
- source-spec SHA-256 recording;
- required generated-file and asset SHA-256 recording and runtime verification;
- staging-based generation and non-destructive overwrite behavior;
- source/output overlap and source-asset symbolic-link/junction escape protection;
- schema and semantic validation;
- readable stable validation errors;
- deterministic generation tests.

Block 7 extends this boundary with the following implemented capabilities:

- pinned remote source configuration;
- download/cache with hashes;
- Riot Data Dragon and CommunityDragon source parsing;
- Set candidate filtering and reviewed source-cardinality guards;
- logical Champion variant normalization with optional per-choice portraits;
- explicit exclusion inventory/reporting;
- manual override application with reasons;
- cross-source conflict detection and review;
- source/completeness validation for real TFT Sets.

We will not create extra interfaces or generic classes solely to match this document. The source adapters should remain as small and explicit as practical.

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

The normal application reads only generated Set packages from `src/assets/sets/`. It does not download source data or attempt to repair a Set from the internet. If an installed Set fails validation, the application reports the errors and refuses to partially load it.

## Set 18 post-acquisition gate

Reviewed release Sets carry an optional `data/review.json` file. `tools/set_import/verify_set_review.py` is generic: it loads the Set-owned review policy, checks the reviewed roster/category/source counts and exceptional semantics, refreshes `SET_REVIEW.md`, and can compare `source_lock.json` with packaged provenance. Set IDs, Champion IDs, dynamic-choice rules, image-duplicate exceptions and expected inventories therefore live with the Set data rather than in Python constants.


## Post-data acquisition hardening

The generic runtime validator remains authoritative for package structure, hashes and references. Accepted source locks are finalized only after the generated package has completed its transactional build and validation. Part 3 adds reusable complete source-lock/provenance comparison around the generic loader; the Set-18 reviewed verifier reuses that comparison and adds only human-reviewed Set-specific facts.

## Generic provenance lock verification

Block 7 post-data hardening adds a reusable provenance check without adding another Set schema or verifier framework. `tft_builder.source_verification` compares a validated runtime package with a reviewed acquisition `source_lock.json` and requires exact agreement for:

- Set ID and revision;
- provenance source IDs;
- source URL;
- source revision;
- locale;
- SHA-256;
- byte length.

Malformed JSON, malformed source records, duplicate source IDs, missing sources and unexpected sources are errors. `SourceManifest` also rejects duplicate packaged provenance IDs during normal Set loading.

Use the generic developer command for future Sets:

```text
uv run python tools/set_import/verify_source_lock.py src/assets/sets/<set_id> set_sources/sets/<set_id>/source_lock.json
```

Semantic expectations are declared in the Set-owned review policy and interpreted by `verify_set_review.py`. Enchanted Wilds therefore uses the same checker implementation as future reviewed Sets; only its `review.json` contents differ.
