# Block 7 data completion plan

This plan splits the remaining Set-data work into four bounded parts so each handoff stays reviewable and does not mix data acquisition work with the later general code/build correction pass.

## Part 1 - Source roster and Champion variants

Status: implemented in the current handoff; final local verification is recorded in `PROGRESS.md`.

- Reconcile the pinned Set 18 source configuration against the downloaded CommunityDragon payload instead of relying on guessed Champion IDs.
- Account explicitly for all 91 raw Set 18 Champion records: 65 logical player units, 17 excluded helper/encounter/pseudo-unit records, and 10 Lux source records normalized into one logical Lux.
- Keep one logical Lux and one logical Kha'Zix. Do not duplicate Champions in the runtime catalog merely to represent a selected dynamic Trait.
- Add optional per-choice Champion portrait paths to `dynamic_traits`, so Lux can switch portraits from Set data without Champion-name branches in GUI code.
- Preserve Kha'Zix as one logical Champion. The pinned Set payload contains no separate Kha'Zix Champion portrait records for the four Rival evolution choices, so no synthetic images are invented.
- Fail early when pinned raw/logical Champion counts or Trait counts drift.
- Preserve repeated recipe components; two copies of one component are valid Item composition data.

## Part 2 - Trait breakpoint and Item normalization

Status: implemented.

- [x] Store human-readable, localized breakpoint-specific effect text so the GUI can explain what each breakpoint does without parsing Riot markup at runtime.
- [x] Keep the general Trait description as context, but avoid making it the only place where breakpoint-specific values live.
- [x] Resolve readable and FNV-1a-hashed upstream placeholder names automatically. Current-patch numeric differences use a small hand-editable override record with a reviewed source ID and human-readable reason.
- [x] Audit the current 770 Set-declared Item records. The reviewed boundary retains 136 canonical references: 10 components, 39 craftable items, 20 Set 18 emblems, 31 current artifacts and 36 radiant items; 634 engine/alias/temporary records are excluded from packaging.
- [x] Preserve recipe multiplicity and validate all retained Item references/categories deterministically with exact category-count guards.
- [x] Normalize Trait breakpoint display text and add only the minimal reviewed override data needed for current patch values (Part 2B).

## Part 3 - Real Set package acquisition

Status: acquisition implementation verified; official binary acquisition still needs a networked run.

- [x] Run the corrected pinned import through a complete synthetic sprite-backed acquisition harness using the reviewed source configuration.
- [x] Resolve Riot Data Dragon records by stable public `id` and crop all runtime icons from 12 pinned Riot sprite sheets instead of issuing roughly 240 independent image downloads.
- [x] Verify the complete generated shape: 65 Champions, 36 Traits, 136 Items, 2 dynamic rules, 246 PNG assets, 65 Team Planner mappings and 21 provenance sources.
- [x] Normalize localized Set names and Item descriptions so generated locale files/`SET_OVERVIEW.md` contain no Riot HTML/placeholder markup.
- [ ] Perform the same build with the official sprite bytes in a networked environment, write/review the real `source_lock.json`, and commit the validated `src/assets/sets/enchanted_wilds` package.

## Part 4 - Dataset verification and GUI/HCI handoff fixtures

Status: implemented; official Riot sprite-byte acquisition remains the external final gate.

- [x] Perform the complete dataset completeness review against the 65-Champion/36-Trait checklist.
- [x] Add focused regression fixtures for long names, dense Trait memberships, unusual cost/slot cases and dynamic portraits.
- [x] Record the final GUI requirements for accessible Lux/Kha'Zix selection, portrait fallback behavior, full Trait/breakpoint explanations and keyboard operation.
- [x] Add a Set-18-specific post-acquisition verifier for reviewed counts, special semantics, source accounting, assets and locale markup.
- [x] Wire data-driven dynamic portrait selection plus textual selected-Trait display into placed Builder slots.
- Only after this data block is accepted, continue with the separate general code/build/warning correction block requested by the project owner.
