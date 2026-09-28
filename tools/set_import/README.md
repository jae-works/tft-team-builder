# Set import tools

`import_cdragon_set.py` is the concrete developer-only importer for pinned live TFT Set data. It combines Riot TFT Data Dragon with CommunityDragon Set metadata, downloads TFT PNG assets into an offline Set package, emits provenance/candidate accounting, and then delegates to the normal deterministic Set builder.

Current Set 18 command:

```text
uv run python tools/set_import/import_cdragon_set.py set_sources/sets/enchanted_wilds/source.json src/assets/sets/enchanted_wilds
```

Use `--overwrite` when intentionally replacing an existing generated package. Use `--refresh-lock` only after reviewing a deliberate upstream refresh. Runtime code never imports this module and never requires network access.

See `SET_AUTHORING_GUIDE.md` and `SET_DATA_PIPELINE.md`.
