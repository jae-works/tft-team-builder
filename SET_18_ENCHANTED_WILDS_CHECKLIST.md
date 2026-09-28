# Set 18 - Enchanted Wilds completeness checklist

Target: live Set 18, Enchanted Wilds. The pinned client-data inputs are Data Dragon 16.19.1 and CommunityDragon 16.19. Patch 18.3 has a September 24 B-patch; structural roster/Trait membership is sourced from the pinned client data, while balance-only hotfix text must be reviewed separately before claiming exact live numeric descriptions.

## Logical Champion roster

The normalized runtime roster contains 65 logical units. CommunityDragon exposes nine Lux source variants; the importer intentionally normalizes those variants into one logical Lux with a data-driven Avatar origin choice.

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

Exact breakpoint values, display ordering, localized names/descriptions and icons are generated from the pinned sources instead of being duplicated in this checklist.

## Builder-relevant exceptional semantics

- Lux: one logical unit. Avatar plus exactly one of nine origin choices; the selected origin contributes 2 Trait points. The choices are Blossom, Coven, Elderwood, Blackthorn, Fae, Inferno, Lunar, Primal and Solar.
- Kha'Zix: Rival evolution may permanently grant zero or one of Executioner, Rapidfire, Ravager or Spellweaver. This is a PER_CHAMPION selection so duplicate copies cannot disagree.
- Elder Dragon: occupies 2 board slots and contributes 2 Riftbeast points. It must not be modeled as three Riftbeasts.
- Rival: normal activation is exact at 1 Rival. Two Rivals must not be treated as the normal active one-Rival tier merely because the count is above one; exceptional Augment behavior is outside the base Set package.
- Eclipse: derived from fielding at least 3 Solar and 3 Lunar. It is not a normal Champion-granted Trait and must not be manually selectable as a dynamic Trait.
- Rengar: has no extra Builder state. His Rival takedown rewards are gameplay/economy text, not a Champion-specific trait-count or slot rule.

## Item completeness contract

The importer does not filter Items by craftability. It starts from every Item ID declared by the Set 18 CommunityDragon ItemLists and recursively adds every referenced component. Generation fails when an expected family is absent.

Required families are:

- COMPONENT - base components, including normal component-family entries declared/referenced by the Set.
- CRAFTABLE - normal completed recipes.
- EMBLEM - craftable and non-craftable Trait emblems declared by Set 18.
- ARTIFACT - Artifact/Ornn-style special Items.
- RADIANT - Radiant variants.
- SUPPORT - Support Items.
- CONSUMABLE - Set-specific consumable/temporary potion or booster entries when declared by Set 18.
- OTHER - valid Set-declared Items that do not belong to the above semantic families.

The generated `SET_OVERVIEW.md` is the authoritative human-readable Item-name list for the pinned import. Maintaining another hand-written list of every Item name here would create a second source of truth and would drift when Riot changes the current Set inventory.

## Asset completeness contract

A complete generated package contains one current TFT PNG for every logical Champion, every Trait and every included Item. Champion images must be TFT shop portraits, not League champion art. Riot TFT Data Dragon is preferred when an exact record exists; the pinned CommunityDragon TFT path is the fallback. Every asset is hashed into `source_manifest.json` and validated before runtime use.

## Human review gate

After acquisition, inspect `src/assets/sets/enchanted_wilds/SET_OVERVIEW.md` and verify at minimum:

1. all 65 logical Champions and their Trait memberships;
2. all 36 logical Trait definitions, especially Rival and derived Eclipse;
3. Lux's nine choices, Kha'Zix's four optional evolution choices and Elder Dragon's 2-slot/+2 Riftbeast semantics;
4. every Set-declared Item family, including non-craftable Items and recursively required components;
5. current TFT portraits/icons, with no old-set or League substitutes;
6. no unexplained source candidate omissions;
7. the generated source lock and hashes match the reviewed upstream bytes.
