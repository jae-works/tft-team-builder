# set_sources/

This directory contains project-owned inputs used to generate runtime Set packages. It is intentionally separate from `sets/`, which contains generated runtime output.

Current Block 1 layout:

```text
set_sources/
    specs/
        sample_set/
            set_spec.json
            assets/
    overrides/
```

`specs/sample_set/` is a committed, deterministic local source used by Block 1 tests and development. It is fictional and does not represent a Riot TFT Set.

`overrides/<set_id>.json` is reserved for small explicit project decisions needed by future real Set imports, such as dynamic Trait choices, a reviewed source conflict, or an exclusion that requires project knowledge. Every behavior-changing override must include a human-readable reason.

Raw downloaded Riot Data Dragon or CommunityDragon payloads do not belong here. Block 7 will cache those inputs outside Git, record exact source versions and hashes, and convert them through the same validated runtime boundary established in Block 1.

See `../SET_DATA_PIPELINE.md`.
