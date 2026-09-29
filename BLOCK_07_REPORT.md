# Block 7 Report - Real TFT Set data pipeline

Version: 0.7.0

## Implemented

- Set schema v5 carries Items, Trait descriptions, optional localized breakpoint descriptions, weighted Trait contributions, board-slot costs, exact Trait activation, derived Trait requirements, source candidates and upstream source records.
- Runtime Set discovery remains folder-based; no activation registry was added.
- The Trait engine supports weighted native/dynamic contributions, exact-count activation and derived states such as Eclipse.
- Builder-relevant Champion exceptions are represented only by executable declarative fields. The redundant generic `mechanics.json` layer was removed.
- Elder Dragon is corrected to 2 board slots and +2 Riftbeast; Lux and Kha'Zix remain data-driven; Rengar has no Champion-specific Builder state.
- Data-completion Part 1 reconciles Set 18 against the pinned payload: 91 raw Champion records become 65 logical units, 17 source records are explicitly excluded, and ten Lux records normalize to one Lux with nine source-backed choice portraits.
- Data-completion Part 2A cross-checks the broad Item list against current external Set references and retains exactly 136 canonical user-facing Item records (10 component, 39 craftable, 20 emblem, 31 artifact, 36 radiant) instead of 770 mixed engine records. Death's Defiance is the explicit legacy-ID artifact retained by current-source verification; Corrupt Vampiric Scepter and the duplicate Flora Fatalis augment emblem record are excluded.
- Dynamic Trait definitions may carry optional per-choice portrait paths. Kha'Zix deliberately has no synthetic choice portraits because the pinned payload exposes only one Kha'Zix Champion portrait record.
- Item recipe multiplicity is preserved. Part 2B now resolves Riot tooltip placeholders, including hashed BIN-field variables, into localized plain text and stores informative breakpoint effects through optional `description_key` values.
- The deterministic builder emits `items.json`, `source_inventory.json` and `SET_OVERVIEW.md` and hashes them with the rest of the package.
- The Set importer retains only the reviewed canonical Set-18 Item boundary and source-accounts the remaining broad CommunityDragon records as exclusions.
- `inspect-set` prints complete Champion, Trait and Item inventories for developer review.
- The pinned Riot Data Dragon + CommunityDragon importer uses HTTPS-only bounded downloads, cache, retries, PNG validation, source hashes and a source lock.
- The committed sample Set uses schema v5 and exercises localized breakpoint descriptions offline.
- `SET_18_ENCHANTED_WILDS_CHECKLIST.md` documents the 65 logical Champion roster, 36 logical Trait definitions and the manual completion gate.

## Verification status

Part 3 now fixes Data Dragon record indexing to stable public IDs and switches visible asset acquisition to shared sprite sheets. A complete offline acquisition harness builds and runtime-validates 65 Champions, 36 Traits, 136 Items, 2 dynamic rules, 246 PNG assets, 65 Team Planner mappings and 21 provenance sources from 12 synthetic Data Dragon sprite sheets. The same code path must still be run once with official Riot sprite bytes in a networked environment before the real `source_lock.json` and `src/assets/sets/enchanted_wilds` package are committed. No placeholder/old-set art is shipped.

The final normal Python suite for this handoff passes 669 tests with 2938 production statements and 888 branches at 100 percent statement/branch coverage. ASCII policy, project-document mirror checks and Python compilation also pass.

Block 7 remains official-source-package-pending. Parts 1-2 are implemented and the Part 3 acquisition/build path is verified end-to-end; only the official sprite-byte/source-lock run remains before Part 4 final dataset/GUI-HCI handoff and the later normal Windows/Flet correction gates.

## Data completion Part 4 - verification and GUI/HCI handoff

Part 4 adds the final reviewed Set-18 verification gate and records the GUI assumptions without introducing Champion-name-specific UI logic. `tools/set_import/verify_enchanted_wilds.py` validates the complete post-acquisition package: 65 logical Champions, 36 Traits, 136 reviewed Items, exact cost/category/source counts, Lux/Kha'Zix/Elder Dragon/Rival/Eclipse semantics, 65 Team Planner mappings, 246 runtime PNGs, 21 provenance sources and markup-free locales. It also optionally compares the acquisition `source_lock.json` hashes with the provenance embedded in the package.

Placed Builder slots now resolve an optional dynamic portrait from Set data only when exactly one selected Trait has a `choice_images` entry. Missing/multiple choices use the base portrait. The selected dynamic Trait text is rendered separately, so Lux's portrait is never the only state indicator and Kha'Zix remains understandable despite intentionally having no choice portraits.

`SET_18_GUI_HCI_HANDOFF.md` records the next GUI pass requirements and real layout stress points: the cost distribution, Elder Dragon's two slots, three-native-Trait Champions, five-breakpoint Traits and long German labels. The official Riot sprite-byte/source-lock run remains the only external Set-package gate before the generated real package can be committed.

Part 4 final local verification passes 674 tests with 2,955 production statements and 892 branches at 100 percent statement and branch coverage. The Set-18 verifier also passes against the full real-metadata/synthetic-sprite acquisition package, including source-lock comparison. ASCII policy, project-document mirror checks and Python compilation pass. General Ruff/Flet corrections remain intentionally deferred to the separate correction block.
