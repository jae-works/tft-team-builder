# Block 3 Plan - Core builder logic, Trait engine and undo/redo

Target version: 0.3.x
Status: prepared after the Block 2 hardening pass. Implementation starts only after version 0.2.2 passes the final Windows recheck.

## Purpose

Block 3 builds the complete non-visual editing core that the Flet Builder will call later. The code remains concrete and small: normal functions/classes around the existing Team models, no generic command framework, service interface hierarchy, event bus, or UI abstraction layer.

## Planned module boundaries

The exact filenames may change if implementation shows a simpler split, but the intended responsibilities are:

- builder editing operations for Lists, Slots, Champion instances, names and primary List changes;
- Trait calculation from one validated LoadedSet plus one TeamList;
- a small undo/redo history that records complete reversible edit state without depending on Flet or SQLite.

Persistence remains outside these operations. Block 4 will connect successful edits to AutosaveService.

## Slot and Champion semantics

The following behavior is the implementation contract for Block 3:

- Clearing a slot removes its Champion but keeps the slot and therefore keeps the gap.
- Inserting a slot shifts the selected slot and all later slots one position right and reindexes them contiguously.
- Removing a slot removes that position completely and shifts later slots left.
- Compacting removes empty slots only, preserves Champion order, preserves Champion instance IDs, and reindexes remaining slots from zero.
- A move preserves Champion instance identity.
- Moving to an empty slot moves the Champion and leaves the source slot empty.
- Moving to an occupied slot swaps the two Champion instances. This rule applies inside one List and across two Lists.
- A copy preserves the source Champion definition and Trait selection but creates a new Champion instance ID.
- Copying to an empty existing slot fills that slot.
- Copying to an occupied slot inserts a new slot at the target position and shifts the previous target and later slots right. Copy never overwrites or discards the previous target.
- A target index equal to the current slot count is an append position. Larger indexes are rejected instead of silently creating unspecified gaps.
- Duplicate Champion definitions are valid. Champion instance IDs remain unique across the whole Team after every operation.

## List semantics

Block 3 implements List creation, duplication, reordering, clearing, compacting and deletion as core operations.

- Duplicating a List creates a new List ID and new Champion instance IDs while preserving names, slot/gap layout, Champion definitions and Trait selections.
- Deleting the final remaining List is rejected.
- Deleting the primary List selects a deterministic replacement: the List that occupies the deleted List's resulting position, or the previous final List when the deleted List was last.
- Reordering Lists does not change List IDs or primary List identity.
- Clearing a List removes Champions but preserves its current number of slots. Compacting that cleared List may then reduce it to zero slots.

## Trait counting

Trait calculation uses validated Set data only and is independent from Flet.

- Native Champion Traits come from ChampionDefinition.traits.
- UNIQUE_CHAMPION counts at most one contribution from each Champion definition ID in one List.
- UNIQUE_INSTANCE counts every placed Champion instance carrying that Trait.
- No undefined custom counting mode is accepted in Set schema v1. A future special counting rule must first gain concrete declarative Set data and tests.
- Dynamic selected Traits are validated against the Champion's DynamicTraitDefinition before they count.
- NONE accepts no selected Trait.
- EXACTLY_ONE requires exactly one allowed choice.
- ZERO_OR_ONE accepts zero or one allowed choice.
- ANY_NUMBER accepts any unique subset of allowed choices.
- EXACTLY_N requires exactly exact_count allowed choices.
- Invalid or incomplete required selections are reported in the calculation result and contribute no dynamic Traits until corrected.
- PER_INSTANCE selections are evaluated independently for each Champion instance.
- PER_CHAMPION selections are shared within one List: duplicate instances of the same Champion must resolve to the same selected Trait set. Conflicting stored selections are reported as invalid rather than guessed.
- Dynamic Trait contributions use the selected Trait's own counting_mode when totals are aggregated.

## Trait result state

For each Trait with a positive contribution, the engine exposes enough immutable result data for the later GUI without leaking UI concepts into core logic:

- Trait ID;
- current contribution count;
- active breakpoint, or none when below the first breakpoint;
- next breakpoint, or none when the highest breakpoint is active;
- progress count needed by displays such as 3/4;
- whether one or more required dynamic selections are invalid or missing.

Trait results follow TraitDefinition.display_order and then Trait ID for deterministic ties. Zero-contribution Traits remain absent from the normal result list.

## Undo and redo

Undo/redo is Team-scoped and starts empty when a Team is opened.

- Every successful user-visible core edit is one history entry.
- One undo restores the complete Team state from immediately before that edit, including IDs, slot gaps, order, names, primary List, timestamps and Trait selections.
- Redo restores the corresponding post-edit state exactly.
- A new edit after undo clears the redo branch.
- Failed/no-op edits do not create history entries.
- History snapshots are in memory only and are not persisted across application restarts.
- The implementation may use deep immutable snapshots because Team objects are small; do not build a generic command object hierarchy unless tests demonstrate a concrete need.

## Timestamp policy

Successful edits update Team.updated_at with one timezone-aware UTC timestamp supplied by the editor operation or generated at execution time. Undo/redo restores the exact stored timestamp from the target snapshot instead of manufacturing a new historical value.

## Test scope

Block 3 tests must cover at least:

- every empty/occupied source and target combination for move, swap and copy;
- same-List and cross-List behavior;
- append positions, invalid indexes and gap preservation;
- duplicate Champions and instance identity rules;
- List duplication/deletion/reordering/primary replacement;
- every dynamic selection rule and both selection scopes;
- UNIQUE_CHAMPION versus UNIQUE_INSTANCE counting;
- breakpoint and next-breakpoint behavior at zero, below, exactly on and above thresholds;
- deterministic Trait ordering;
- invalid dynamic selection reporting;
- multi-step undo/redo, redo invalidation after a new edit, no-op history behavior and exact full-state restoration;
- large but realistic Lists to catch accidental quadratic behavior where practical.

The project keeps the 100 percent statement and branch coverage gate.
