# Set Authoring Guide

This guide defines the supported way to add or refresh TFT Sets.

## Design

The runtime has one authoritative Set root: `src/assets/sets/`. Every direct child that contains a valid `manifest.json` is discovered automatically. There is deliberately no Python registry or active-Set list: adding a second authoritative switch would create drift. A Set is usable only when the normal validator accepts the complete package.

Remote acquisition is developer-only. The app never downloads or repairs Set data while running.

## Runtime Set package

A generated Set folder contains:

```text
src/assets/sets/<set_id>/
    manifest.json
    source_manifest.json
    SET_OVERVIEW.md
    data/
        champions.json
        items.json
        traits.json
        dynamic_traits.json
        team_planner.json
    locales/
        <locale>.json
    reports/
        source_inventory.json
    assets/
        champions/*.png
        items/*.png
        traits/*.png
```

`SET_OVERVIEW.md` is generated from normalized data for human review. `source_inventory.json` accounts for imported Set candidates. `source_manifest.json` records generated-file, asset and upstream-source hashes.

## Data rules

Stable IDs are never localized. Localized names/descriptions live only in locale catalogs.

Champion data stores only Builder-relevant facts: ID, display key, cost, Traits, weighted Trait points, board-slot cost, portrait and search aliases. Combat stats and ability numbers are intentionally excluded.

Items store ID, localized name/description keys, PNG icon, category, component IDs, associated Trait IDs and source tags. Item equipping is not currently a Builder feature, but Set packages retain the complete Set-declared Item reference inventory.

Traits store ID, localized name/description keys, PNG icon, display order, breakpoints, counting mode, activation mode and optional derived requirements.

Builder-relevant exceptional behavior must use executable declarative fields rather than Champion-name branches or descriptive metadata files:

- use `trait_points` when one unit contributes more than one point to a native Trait;
- use `board_slots` when one logical unit consumes more than one board slot;
- use `dynamic_traits` for player-selected Trait membership such as Lux or Kha'Zix;
- use Trait `activation_mode=EXACT` when a Trait is active only at an exact count;
- use Trait `derived_requirements` for states such as Eclipse that are activated by other Trait counts.

Do not add a generic mechanic record merely to store gameplay prose the Builder does not execute. Put gameplay explanation in the normal Trait description unless it changes Builder state.

## Items

Current-Set Item membership comes from the pinned CommunityDragon Set ItemLists. The importer keeps every Set-declared Item regardless of craftability and recursively adds every referenced component. Riot Data Dragon is used as a preferred localization/asset source where an exact record exists, but its global current-item catalog is not treated as Set membership because it can cover multiple active Sets/modes.

The current Set source config defines expected Item families. Acquisition fails rather than silently producing an incomplete package when one disappears unexpectedly. Set 18 requires component, craftable, emblem, artifact, radiant, support, consumable and other families.

## Images

Keep source-quality TFT PNGs as PNG. Do not substitute League of Legends champion art for TFT shop portraits. The importer prefers Riot TFT Data Dragon assets where available and falls back to the pinned CommunityDragon TFT asset path. Validation checks file presence, PNG signature, package location and hashes; it does not pretend to recognize image content.

## Adding a new Set

Copy `set_sources/sets/enchanted_wilds/source.json` to a new Set-specific source folder and change the pinned Set/source versions plus only the explicit normalization rules that the new Set actually needs. Then run:

```text
uv run python tools/set_import/import_cdragon_set.py set_sources/sets/<set_id>/source.json src/assets/sets/<set_id>
```

The first reviewed import writes `source_lock.json` beside `source.json`. Subsequent imports must match the recorded source hashes. Use `--refresh-lock` only after intentionally reviewing an upstream refresh.

Then run:

```text
uv run tft-builder-dev validate-set src/assets/sets/<set_id>
uv run tft-builder-dev inspect-set src/assets/sets/<set_id>
```

`validate-set` is the non-mutating structural/integrity checker. `inspect-set` prints the complete Champion/Trait/Item inventory with IDs, references and asset paths. `SET_OVERVIEW.md` provides the corresponding review artifact inside the generated Set folder.

No code list needs editing after a valid package is copied into `src/assets/sets/`.

## Current Set 18 source config

`set_sources/sets/enchanted_wilds/source.json` targets Set 18, Enchanted Wilds, pinned client-data revision 18.3 / Data Dragon 16.19.1 / CommunityDragon 16.19, with English and German locale imports. Patch 18.3 received a September 24 B-patch; structural Set membership remains pinned and reproducible, while balance-only tooltip numbers must be reviewed when claiming exact live numeric descriptions.

The only Builder-semantic normalizations are Lux's Avatar origin choice, Kha'Zix's Rival evolution choice, Elder Dragon's 2-slot/+2 Riftbeast contribution, exact one-Rival base activation and derived Eclipse activation from 3 Solar plus 3 Lunar. Rengar has no Champion-specific Builder state.

See `SET_18_ENCHANTED_WILDS_CHECKLIST.md` for the review roster and completeness gates.

## Review rule

A generated package is not accepted merely because JSON parses. It must pass structural validation, source-candidate accounting, source-lock/hash checks, the normal test suite, and manual inspection of `SET_OVERVIEW.md`. The validator verifies structure and internal consistency; current gameplay truth still requires source review, especially after server-side B-patches.
