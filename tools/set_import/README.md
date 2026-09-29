# Set import tools

`import_cdragon_set.py` is the developer-only importer for pinned live TFT Set data. The runtime never imports it and never requires network access. Release acquisition uses individual Riot Data Dragon `image.group` + `image.full` files for ordinary Champion, Trait and Item assets. Dynamic variant groups use their configured CommunityDragon `squareIcon` source when Data Dragon does not expose distinct variant art. TFT sprite-atlas coordinates are not a release source of truth.

Current Set 18 command:

```text
uv run python tools/set_import/import_cdragon_set.py set_sources/sets/enchanted_wilds/source.json src/assets/sets/enchanted_wilds
```

Use `--overwrite` only when intentionally replacing an existing generated package. Use `--refresh-lock` only after reviewing a deliberate upstream refresh. A new/refreshed lock is published only after the package build and runtime validation succeed.

Generic provenance verification for any generated Set with an acquisition lock:

```text
uv run python tools/set_import/verify_source_lock.py src/assets/sets/<set_id> set_sources/sets/<set_id>/source_lock.json
```

The generic verifier compares Set ID/revision, complete provenance-ID inventory, URL, source revision, locale, SHA-256 and byte length.

Enchanted Wilds also has one intentionally Set-specific reviewed gate:

```text
uv run python tools/set_import/verify_enchanted_wilds.py src/assets/sets/enchanted_wilds --source-lock set_sources/sets/enchanted_wilds/source_lock.json
```

This adds the reviewed Set-18 roster, category/source counts and exceptional semantics such as Elder Dragon, Lux, Kha'Zix, Rival and Eclipse. It reuses the generic provenance verifier rather than duplicating lock logic.

See `SET_AUTHORING_GUIDE.md`, `SET_DATA_PIPELINE.md` and `BLOCK_07_POST_DATA_HARDENING_PLAN.md`.
