# Set 18 - Enchanted Wilds completeness checklist

Target: live Set 18, Enchanted Wilds, package revision 18.3b. The pinned client-data inputs are Data Dragon 16.19.1 and CommunityDragon 16.19. Structural roster/Trait membership stays pinned; current Patch 18.3 breakpoint value differences are recorded as explicit Riot-source overrides.

## Logical Champion roster

The reviewed pinned source contains 91 raw Champion records and normalizes to 65 logical units. Seventeen helper/encounter/pseudo-unit records are explicitly excluded. CommunityDragon exposes ten Lux records (one base plus nine origin variants); the importer intentionally normalizes all ten into one logical Lux with a data-driven Avatar origin choice.

### 1-cost (14)

Akali, Camille, Cinderling, Karma, Kobuko, Leona, Ornn, Pebbles, Rakan, Rek'Sai, Varus, Veigar, Xayah, Yorick.

### 2-cost (13)

Alistar, Caitlyn, Elise, Gromp, Kayle, LeBlanc, Murkwolf, Scuttlecrab, Sejuani, Shen, Teemo, Warwick, Yunara.

### 3-cost (14)

Azir, Cassiopeia, Diana, Fiddlesticks, Hecarim, Kha'Zix, Kog'Maw, Krug, Mama Beak, Master Yi, Rammus, Rengar, Tristana, Vi.

### 4-cost (14)

Ahri, Amumu, Aphelios, Brambleback, Ezreal, Lillia, Malphite, Morgana, Nidalee, Sentinel, Sett, Sivir, Soraka, Zyra.

### 5-cost (10)

Alune, Ashe, Draven, Elder Dragon, Gnar, Ivern, Kennen, Lux, Maokai, Taric.

## Logical Trait roster

The set has 35 ordinary visible Traits plus the derived Eclipse state, for 36 logical Trait definitions in this project:

Adaptor, Apex Predator, Attuned, Avatar, Blackthorn, Blossom, Bounty Seeker, Brawler, Caustic, Coven, Defender, Eclipse, Elderwood, Emerald Aspect, Executioner, Fae, Flora Fatalis, Greenfather, Hunter, Inferno, Invoker, Juggernaut, Lunar, Monolith, Old Growth, Primal, Rapidfire, Ravager, Riftbeast, Rival, Solar, Spellweaver, Sprykin, Summoner, Thornmaiden, Vanguard.

Exact breakpoint values, display ordering, localized names/descriptions and icons are generated from the pinned sources instead of being duplicated in this checklist. Informative breakpoint rows are stored as localized plain text; unique/general-only Traits and Primal do not receive invented row text when upstream data provides none.

## Builder-relevant exceptional semantics

- Lux: one logical unit. Avatar plus exactly one of nine origin choices; the selected origin contributes 2 Trait points. The choices are Blossom, Coven, Elderwood, Blackthorn, Fae, Inferno, Lunar, Primal and Solar. Each choice has its own source-backed portrait path.
- Kha'Zix: Rival evolution may permanently grant zero or one of Executioner, Rapidfire, Ravager or Spellweaver. This is a PER_CHAMPION selection so duplicate copies cannot disagree. The pinned source has one Kha'Zix Champion portrait record, so all four choices intentionally fall back to that base portrait unless a reviewed source is added later.
- Elder Dragon: occupies 2 board slots and contributes 2 Riftbeast points. It must not be modeled as three Riftbeasts.
- Rival: normal activation is exact at 1 Rival. Two Rivals must not be treated as the normal active one-Rival tier merely because the count is above one; exceptional Augment behavior is outside the base Set package.
- Eclipse: derived from fielding at least 3 Solar and 3 Lunar. It is not a normal Champion-granted Trait and must not be manually selectable as a dynamic Trait.
- Rengar: has no extra Builder state. His Rival takedown rewards are gameplay/economy text, not a Champion-specific trait-count or slot rule.

## Item completeness contract

The current pinned source exposes 770 Set-declared Item records, but that list mixes real player-facing items with Wisps, temporary/utility engine objects and duplicate/legacy aliases. The reviewed package boundary retains exactly 136 canonical references: 10 components, 39 craftable items, 20 Set 18 emblems, 31 current artifacts and 36 radiant items. The remaining 634 source records stay explicitly excluded from the generated source inventory. Repeated recipe components remain valid and generation fails if any reviewed category count drifts.

Required families are:

- COMPONENT - base components, including normal component-family entries declared/referenced by the Set.
- CRAFTABLE - normal completed recipes.
- EMBLEM - craftable and non-craftable Trait emblems declared by Set 18.
- ARTIFACT - Artifact/Ornn-style special Items.
- RADIANT - Radiant variants.
Support, consumable/temporary, Wisp/mechanic and uncategorized engine records are intentionally outside this reviewed reference boundary. They can be added later only for a concrete feature with its own source review.

The generated `SET_OVERVIEW.md` is the authoritative human-readable Item-name list for the pinned import. Maintaining another hand-written list of every Item name here would create a second source of truth and would drift when Riot changes the current Set inventory.

## Asset completeness contract

A complete generated package contains one current TFT PNG for every logical Champion, every Trait and every included Item. Champion images must be TFT shop portraits, not League champion art. Riot TFT Data Dragon is preferred when an exact record exists; the pinned CommunityDragon TFT path is the fallback. Every asset is hashed into `source_manifest.json` and validated before runtime use.

## Human review gate

The Part 3 acquisition harness already verifies the exact generated shape before official-byte acquisition: 65 Champions, 36 Traits, 136 Items, 2 dynamic rules, 246 package PNGs, 65 Team Planner mappings and 21 provenance sources. Data Dragon supplies those PNGs through 12 shared sprite sheets. The remaining gate is to run the identical path against the official Riot sprite bytes and review the real source lock.

After acquisition, inspect `src/assets/sets/enchanted_wilds/SET_OVERVIEW.md` and verify at minimum:

1. all 65 logical Champions and their Trait memberships;
2. all 36 logical Trait definitions, especially Rival and derived Eclipse;
3. Lux's nine choices, Kha'Zix's four optional evolution choices and Elder Dragon's 2-slot/+2 Riftbeast semantics;
4. all 136 reviewed canonical Item references and their exact category counts;
5. current TFT portraits/icons, with no old-set or League substitutes;
6. no unexplained source candidate omissions;
7. the generated source lock and hashes match the reviewed upstream bytes.

## Part 4 post-acquisition verification

After the real sprite acquisition, run `tools/set_import/verify_enchanted_wilds.py` against the generated package and reviewed `source_lock.json`. This is the executable counterpart to the checklist and must pass before the package is accepted. GUI-specific stress cases and interaction expectations are recorded separately in `SET_18_GUI_HCI_HANDOFF.md` so the dataset checklist does not become a second UI specification.
