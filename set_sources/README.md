# Set source specifications

This directory contains project-owned inputs used to generate runtime Set packages under `src/assets/sets/`.

Current Block 1 layout:

```text
set_sources/
    specs/
        sample_set/
            set_spec.json
            assets/
    overrides/
```

`specs/sample_set/` is a committed deterministic local source used by Block 1 tests and development. It is fictional and does not represent a Riot TFT Set.

`overrides/<set_id>.json` is reserved for small explicit project decisions needed by future real Set imports, such as dynamic Trait choices, reviewed source conflicts, or exclusions that require project knowledge. Every behavior-changing override must include a human-readable reason.

Raw downloaded Riot Data Dragon or CommunityDragon payloads do not belong in Git. Block 7 will cache those inputs outside the repository, record exact source versions and hashes, and normalize them into the same validated runtime boundary established in Block 1.

See `SET_DATA_PIPELINE.md` in the repository root.
