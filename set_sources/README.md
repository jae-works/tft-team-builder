# set_sources/

Project-owned inputs that cannot or should not be generated directly from upstream TFT data live here.

`overrides/<set_id>.json` is intended for small explicit decisions such as dynamic Trait choices, known source conflicts, exclusions that require project knowledge, or mappings that cannot be derived reliably.

Every override that changes source-derived behavior must include a human-readable reason. Raw downloaded Riot/CommunityDragon payloads do not belong here; they are cached locally under `.cache/set_import/` and are not committed.

See `../SET_DATA_PIPELINE.md`.
