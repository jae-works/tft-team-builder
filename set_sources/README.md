# Set source specifications

This directory contains project-owned inputs used to generate runtime Set packages under `src/assets/sets/`.

```text
set_sources/
    specs/
        sample_set/              # deterministic offline test/source fixture
    sets/
        enchanted_wilds/
            source.json          # pinned live source configuration
            source_lock.json     # written after the first reviewed live import
```

`specs/sample_set/` is fictional and exercises the complete schema offline. Real Sets use a small Set-specific `source.json`; downloaded Riot Data Dragon and CommunityDragon payloads are cached under `.cache/set_import/` and are not committed.

The current Set 18 importer is `tools/set_import/import_cdragon_set.py`. Special cases belong in the Set configuration as explicit data, not in Champion-specific runtime Python. See `SET_AUTHORING_GUIDE.md` and `SET_DATA_PIPELINE.md`.
