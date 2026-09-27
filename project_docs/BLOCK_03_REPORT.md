# Block 3 Report - Core builder logic, Trait engine and undo/redo

Version: 0.3.0
Status: implemented; complete implementation-environment test suite passes. Final pinned Windows Ruff/Flet verification is required before Block 4.

## Scope delivered

Block 3 adds the complete non-visual Builder editing core planned in `BLOCK_03_PLAN.md`. The implementation remains deliberately concrete and small: one Team editor, one Trait calculation module, standard-library snapshots, and no generic command hierarchy, service interface layer, event bus, or Flet dependency.

New production modules:

- `src/tft_builder/builder.py`
  - Team/List rename operations;
  - primary List changes;
  - List create/duplicate/delete/reorder/clear/compact;
  - slot insert/remove/clear;
  - Champion add/move/swap/copy;
  - dynamic Trait selection edits;
  - exact Team-scoped undo/redo history.
- `src/tft_builder/trait_engine.py`
  - native and dynamic Trait contributions;
  - UNIQUE_CHAMPION and UNIQUE_INSTANCE counting;
  - breakpoint and next-breakpoint calculation;
  - deterministic Trait result ordering;
  - validation/reporting for all schema-v1 dynamic selection rules and both selection scopes.

The developer CLI now also provides `builder-smoke` for an integrated manual Block 3 check against the bundled sample Set.

## Editing behavior

`TeamEditor` applies every edit to a deep working copy and commits only after Team invariants pass. This gives atomic failure behavior without transaction/interface machinery in the domain layer.

Implemented rules include:

- clearing a slot keeps the gap;
- inserting/removing slots reindexes later slots contiguously;
- compacting removes gaps while preserving Champion order and surviving instance IDs;
- moves to empty slots leave a source gap;
- moves to occupied slots swap both instances, including across Lists;
- a target index equal to slot count appends and larger indexes fail;
- copies always receive a new Champion instance ID;
- copies into occupied slots insert and shift rather than overwrite;
- duplicate Lists receive a new List ID and new Champion instance IDs while preserving gaps and Trait selections;
- the final List cannot be deleted;
- deleting the primary List chooses the deterministic adjacent replacement defined in the plan.

## Undo/redo behavior

History is intentionally in memory only and starts empty for each `TeamEditor`.

- One successful edit creates one undo entry.
- Failed edits are atomic and create no history entry.
- No-op edits create no history entry.
- A new successful edit after undo clears the redo branch.
- Failed/no-op edits after undo do not destroy the redo branch.
- Undo/redo restores the exact complete Team state, including IDs, gaps, ordering, primary List, timestamps and Trait selections.
- The editor preserves the caller's top-level `Team` object identity while restoring fields from isolated snapshots.
- Successful edits update `Team.updated_at` once with a timezone-aware UTC timestamp; undo/redo restores stored historical timestamps rather than generating new ones.

## Trait engine behavior

Trait calculation consumes one validated `LoadedSet` and one `TeamList` and has no Flet or persistence dependency.

- Native Champion Traits come from Set data.
- UNIQUE_CHAMPION deduplicates contributions by Champion definition ID.
- UNIQUE_INSTANCE counts every contributing placed instance.
- Zero-contribution Traits are absent from the normal result list.
- Results follow `display_order` and then Trait ID for a deterministic tie-breaker.
- Results include current count, active breakpoint, next breakpoint, amount needed for the next breakpoint, and invalid-dynamic-selection state.
- Unknown Champion IDs in a List fail clearly instead of silently disappearing from calculations.

Dynamic Trait handling covers:

- NONE;
- EXACTLY_ONE;
- ZERO_OR_ONE;
- ANY_NUMBER;
- EXACTLY_N;
- PER_INSTANCE;
- PER_CHAMPION.

Invalid or incomplete selections produce explicit `DynamicSelectionIssue` values and contribute no dynamic Traits for the affected invalid selection. PER_CHAMPION compares semantic Trait sets rather than tuple ordering, so the same choices in different stored order do not produce a false conflict.

## Tests added

Block 3 adds dedicated `test_builder.py` and `test_trait_engine.py` coverage plus developer-command integration tests.

The test matrix covers, among other cases:

- empty/occupied move targets inside and across Lists;
- swap identity preservation;
- append targets and invalid indexes;
- copy to empty/occupied/append targets;
- duplicate Champion definitions and instance identity;
- List duplication/deletion/reordering/primary replacement;
- slot insertion/removal/clear/compact;
- Team/List rename and primary changes;
- atomic invalid edits and no-op history behavior;
- multi-step undo/redo and redo invalidation;
- exact full-state/timestamp restoration;
- all dynamic selection rules;
- PER_INSTANCE and PER_CHAMPION behavior;
- selection-order-insensitive PER_CHAMPION equality;
- UNIQUE_CHAMPION versus UNIQUE_INSTANCE;
- below/exact/above breakpoint states;
- invalid dynamic selection reporting;
- deterministic Trait ordering;
- integrated bundled `sample_set` calculation;
- 300-slot edit and 500-instance Trait calculations as realistic scaling guards.

## Verification evidence

Implementation environment:

- Python 3.13.5.
- 529 pytest tests pass with no skips.
- Statement coverage: 100.00 percent.
- Branch coverage: 100.00 percent.
- Production coverage total at this stage: 1,799 statements and 564 branches.
- ASCII policy check passes.
- Project document mirror check passes.
- `compileall` passes for `src`, `tests`, and `tools`.
- Bundled Set validation and inspection pass.
- Persistence database smoke passes.
- Block 3 `builder-smoke` passes with the expected three-slot, Trait-count, and undo/redo results.

The implementation environment does not have network access and does not contain the exact locked Ruff 0.16.9/Flet development toolchain, so the normal pinned Windows quality sequence remains the release gate for this candidate. The user's previous v0.2.2 Windows run already verified 438 tests at 100 percent, ASCII/document checks, compileall, Set validation/inspection, database smoke and Flet startup; it found one remaining Ruff SIM300 warning, which v0.3.0 fixes exactly.

## Block 4 handoff

Block 4 should build the first complete Flet Builder GUI on top of these existing core operations rather than reimplementing their rules in controls.

- Use `TeamEditor` as the mutation/history boundary for Builder actions.
- Calculate the active List's Trait panel through `calculate_traits()`.
- Connect successful structural edits to Block 2 persistence/autosave primitives.
- Keep transient active-List and interaction state in the UI layer; do not confuse it with the persistent primary List.
- Keep GUI work focused on presentation, input handling, autosave scheduling and integration because slot/move/copy/Trait/history semantics are now core-owned and tested.
