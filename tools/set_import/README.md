# Set import tools

`import_cdragon_set.py` is the concrete developer-only importer for pinned live TFT Set data. It combines Riot TFT Data Dragon with CommunityDragon Set metadata, downloads each required Riot Data Dragon sprite sheet once, crops the declared icon rectangles into the offline Set package, emits provenance/candidate accounting, and then delegates to the normal deterministic Set builder. Set 18 currently needs 12 shared sprite sheets for all 246 runtime PNGs instead of roughly 240 independent image requests.

Current Set 18 command:

```text
uv run python tools/set_import/import_cdragon_set.py set_sources/sets/enchanted_wilds/source.json src/assets/sets/enchanted_wilds
```

Use `--overwrite` when intentionally replacing an existing generated package. Use `--refresh-lock` only after reviewing a deliberate upstream refresh. Runtime code never imports this module and never requires network access.

See `SET_AUTHORING_GUIDE.md` and `SET_DATA_PIPELINE.md`.

After acquiring Enchanted Wilds with official Riot sprite bytes, run the Set-specific reviewed gate:

```text
uv run python tools/set_import/verify_enchanted_wilds.py src/assets/sets/enchanted_wilds --source-lock set_sources/sets/enchanted_wilds/source_lock.json
```

This complements generic Set validation with the reviewed Set-18 roster, special semantics, source-accounting and asset-count expectations.
