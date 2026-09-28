# Block 7 Plan - Real TFT Set data pipeline and production Set package

Target version: 0.7.0
Prepared during: 0.6.1 Block 6 quality audit

## Goal

Replace the fictional sample Set as the normal product data source with at least one reproducibly generated real TFT Set package while keeping the runtime completely offline from Riot/CommunityDragon services.

## Source strategy

- Prefer pinned Riot Data Dragon inputs for official visible data/assets where the required fields exist.
- Use pinned CommunityDragon inputs only for required supplemental metadata or cross-checking.
- Record source URL/revision, acquisition time where relevant, SHA-256 and project importer version.
- Never silently choose between conflicting upstream values. Surface conflicts and resolve only through a documented project override when required.
- Keep upstream parsing outside runtime Set models: adapters normalize into the existing local source/builder boundary.

## Acquisition and reproducibility

- Add a developer-only downloader using the already planned maintained HTTP client (`httpx`).
- Accept release inputs only from explicitly configured HTTPS source roots; tests may use local fixtures.
- Stream downloads to temporary files with explicit maximum-size limits instead of reading unbounded responses into memory.
- Derive cache/output names from project-controlled IDs/hashes rather than untrusted URL path text.
- Use explicit timeouts, redirect handling, status validation and bounded retries; no unbounded network retry loops.
- Cache immutable downloaded source artifacts by revision/hash so generation is reproducible and normal rebuilds do not require the network.
- Never execute remote data or source-specific Python from a downloaded Set.
- Build into staging and promote transactionally using the existing Set builder safety model.

## Candidate accounting

Every upstream Champion/Trait candidate must be one of:
- INCLUDED;
- EXCLUDED with a documented machine-readable reason;
- ERROR requiring importer/data correction.

No candidate may disappear silently during filtering. Generate an inventory/report that makes completeness review practical.

## Assets and localization

- Copy only runtime-needed local assets into the generated Set package.
- Verify image type/integrity and package hashes through the existing validator.
- Preserve stable IDs independently from localized display text.
- Generate the supported locale payloads from source data while retaining the project ASCII policy for technical files.
- Use real assets before the final UI sizing/density pass; prototype 1x1 sample images must not determine permanent card dimensions.

## Validation and testing

Add committed small source fixtures plus deterministic tests for:
- successful normalization;
- malformed/partial upstream payloads;
- duplicate IDs;
- missing assets/localization;
- source conflicts;
- candidate accounting;
- explicit overrides;
- source hash mismatch;
- cache/rebuild reproducibility;
- transactional failure behavior;
- byte-identical output from identical pinned inputs where timestamps are not part of runtime output.

The generated real Set must pass the same strict runtime validator and the normal application must still perform no network request while browsing/building Teams.

## HCI impact

- Real Champion/Trait names and portrait/icon dimensions become the basis for the later final spacing/typography pass.
- Use the real-data pass to collect long-name, unusual-cost and dense-Trait examples for Block 9 accessibility/responsive testing instead of tuning only against sample fixtures.
- Missing/corrupt real assets must use an explicit fallback rather than collapsing layout.
- Long localized names must remain readable/truncated with an accessible full-name path; final verification remains in Block 9.

## Exit criteria

Block 7 is complete when at least one real supported TFT Set can be regenerated from pinned recorded inputs, every upstream candidate is accounted for, provenance/hashes are stored, the generated package passes strict validation, tests remain at 100 percent production statement/branch coverage, and the normal application uses only the generated local package at runtime.
