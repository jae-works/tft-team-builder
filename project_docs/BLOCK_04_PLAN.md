# Block 4 Plan - First complete functional Builder GUI

Target version: 0.4.0
Status: prepared during the 0.3.1 Block 3 release audit. Implementation has not started.

## Purpose

Block 4 turns the tested non-visual Builder core into the first real desktop Builder screen. The goal is functional completeness for normal mouse-driven Team building, not final interaction polish. Block 5 remains responsible for drag/drop, search, richer hover/details behavior, dynamic Trait selection dialogs, keyboard shortcuts and the final desktop interaction pass.

The GUI must call existing domain and persistence code instead of reimplementing slot, List, Trait, undo/redo or save rules inside Flet controls.

## Scope

Block 4 implements:

- the real Flet desktop shell;
- a three-column Builder layout: Traits | Lists | Champion library;
- Team and List name editing;
- transient active-List selection separate from the persisted primary List;
- primary-List star control;
- List create, duplicate, reorder, clear, compact and delete controls;
- Champion library groups generated from Set costs without a hardcoded maximum cost;
- basic Champion add/remove behavior using explicit reliable controls rather than drag/drop;
- Trait results for the active List, including visible invalid dynamic-selection state;
- Trait display toggles for hiding below-first-breakpoint results and showing next-breakpoint progress;
- Undo/Redo buttons wired to TeamEditor;
- SQLite loading and persistence through TeamRepository and AutosaveService;
- immediate saves for structural edits;
- debounced text saves plus focus-loss flush behavior;
- stable Flet control keys for integration tests;
- focused Flet integration smoke tests in addition to the existing unit suite.

Block 4 does not implement:

- Champion drag/drop;
- click-to-pick/click-to-place mode;
- Champion/Trait search;
- Copy/Move mode UI;
- hover detail cards;
- dynamic Trait selection dialogs;
- keyboard shortcuts;
- Start page / Team library;
- real Riot Set data;
- import/export.

Those remain in later planned blocks.

## Concrete module boundary

Do not add a generic UI framework, presenter interface, service container or event bus.

The expected implementation is deliberately small:

- `app.py` remains the application composition/startup boundary.
- Add one concrete Builder UI module, initially `builder_view.py` unless implementation proves a smaller name clearer.
- `builder.py` remains the only owner of Team edit semantics and undo/redo.
- `trait_engine.py` remains the only owner of Trait calculation.
- `persistence/` remains the only code that issues SQL.
- `set_loader.py` remains the Set loading/validation boundary.

If the Builder UI module becomes too large for clear review, split only concrete rendering/helpers that have an obvious responsibility. Do not pre-create abstract base classes or interfaces.

## Runtime startup flow

Until the Start page exists in Block 6, Block 4 needs one deterministic Builder bootstrap path:

1. Run existing application initialization: paths, logging, database schema and bundled Set validation.
2. Load the validated bundled Sets.
3. Open the most recently updated non-deleted Team when one exists.
4. If no Team exists, create one Team named `Untitled Team` for the first validated bundled Set and persist it immediately.
5. Load the Team's `set_id`; if that Set cannot be loaded, show a clear blocking error rather than silently changing the Team to another Set.
6. Create a TeamEditor for the loaded Team.
7. Create an AutosaveService backed by the existing TeamRepository.
8. Initialize the transient active List to the Team's primary List.
9. Render the Builder.

This bootstrap is intentionally temporary. Block 6 replaces it with the Start page and explicit Team creation/opening.

## Active List policy

The active List and primary List are different concepts:

- `Team.primary_list_id` is persisted and used for the Team preview/library semantics.
- `active_list_id` is transient Builder-session state and is not added to Team, SQLite or undo/redo history.
- Opening a Team initializes the active List to the primary List.
- Clicking a List makes it active without changing primary status.
- Changing primary status does not force the active List to change.
- Undo/redo does not restore navigation state because active List selection is not domain history.
- If delete/undo/redo makes the active List ID invalid, the GUI falls back deterministically to the current primary List.
- Reordering Lists does not change active or primary identity.

Keep this state in the concrete Builder UI object. There is no need for a new persistent domain model.

## Layout

Use a desktop-first three-column layout inside a SafeArea:

- left: Trait panel;
- center: Team/List Builder area;
- right: Champion library.

The center column expands to consume remaining width. Left/right panels may use sensible desktop widths, but avoid layout code that assumes a fixed monitor resolution.

Scrolling rules:

- Trait panel scrolls independently vertically;
- central List area scrolls independently vertically;
- Champion library scrolls independently vertically;
- each List's Champion row can scroll horizontally when needed.

The top Builder toolbar contains:

- editable Team name;
- New List button;
- Undo button;
- Redo button;
- a compact save/error status area if required by implementation.

## List rendering and controls

Each List renders:

- active-state styling;
- editable List name;
- primary star toggle/button;
- duplicate;
- move up/down;
- clear Champions;
- compact gaps;
- delete;
- a horizontally scrollable ordered slot row.

Use the existing TeamEditor methods directly. UI code must not manually edit `team.lists`, `slots`, IDs or indexes.

For destructive List actions, use a simple confirmation only where accidental data loss would be annoying. Do not add a generic confirmation framework.

## Champion library

Build groups from Set data every render or from a small local computed structure:

- group only costs that exist in the loaded Set;
- sort cost groups numerically;
- sort Champions inside a cost group by `display_order`, then Champion ID for a deterministic tie-breaker;
- show localized Champion name, portrait and numeric cost;
- cost styling is allowed, but the number must remain visible so information is not color-only.

Block 4 placement behavior is intentionally simple and reliable:

- clicking an Add control on a Champion appends a new instance to the active List;
- removing a placed Champion uses an explicit remove control on the slot;
- empty gaps remain visible;
- append/add and remove actions call TeamEditor and then persist immediately.

Drag/drop and click-to-place are Block 5 work and must not be partially duplicated here.

## Trait panel

For the active List:

- call `calculate_traits(loaded_set, active_list)`;
- render returned Traits in their existing deterministic order;
- show current count and active breakpoint styling;
- provide a next-breakpoint-progress toggle and show progress only when it is enabled;
- provide a below-first-breakpoint toggle and hide those results when it is enabled;
- visibly mark Traits affected by invalid/missing dynamic selection;
- show a concise dynamic-selection issue message so missing choices are not silently ignored.

Block 4 only displays dynamic-selection problems. The selection dialog/editor remains Block 5.

## Persistence and autosave wiring

Structural actions are saved immediately:

- Champion add/remove;
- List create/duplicate/reorder/clear/compact/delete;
- primary List change;
- undo/redo.

For each successful structural TeamEditor action:

1. reconcile transient active-List state if needed;
2. call `AutosaveService.save_now(team)`;
3. recalculate/re-render affected UI;
4. surface persistence failures instead of pretending the action was saved.

Text editing uses short debounce plus focus-loss flush:

- Team/List name text changes must still go through TeamEditor;
- queued text state uses AutosaveService rather than direct SQL;
- focus loss or explicit submit flushes the pending Team immediately;
- do not rely on app-exit callbacks as the only save path.

During implementation, keep text-edit history usable. Do not create a complex generic history-coalescing system before an actual text-field behavior demonstrates it is needed. If debounced text produces excessive undo steps in the real UI, add the smallest concrete coalescing behavior with tests in Block 4.

## Error handling

Expected user-action validation failures should produce a readable GUI message and leave state unchanged.

Persistence or unexpected runtime failures must:

- be logged with useful context;
- be surfaced visibly;
- not be swallowed;
- never mark an unsaved state as saved.

Set-load failure is blocking for the affected Team. Do not silently use another Set.

## Flet control-key policy

Controls used by integration tests get explicit stable keys.

Prefer semantic keys such as:

- `builder-team-name`
- `builder-new-list`
- `builder-undo`
- `builder-redo`
- `champion-add-<champion_id>`
- `trait-<trait_id>`

List/slot-specific controls may include their domain UUID/index when identity matters. Tests should prefer semantic global keys and deterministic Set IDs over fragile visible-text matching. Visible text may still be asserted when the text itself is the behavior under test.

## Testing strategy

Block 4 keeps all current unit tests and the 100 percent production statement/branch coverage gate.

Add normal unit tests for any non-trivial pure GUI helper introduced, such as:

- Champion grouping/sorting by cost;
- active-List reconciliation after deletion/undo/redo;
- translation or asset-path helpers if they become real code.

Add Flet integration tests for the real screen. Flet 1.0.1 testing uses pytest and requires `asyncio_mode = "auto"`; version 0.3.1 prepares this configuration in advance.

At minimum test through the actual UI:

- application opens Builder successfully;
- initial Team/List is visible;
- Team name edit is reflected and persisted;
- New List works;
- active List can change without changing primary List;
- primary star changes persisted primary identity;
- one Champion can be added from the library and removed again;
- Trait panel reacts to an active-List change or Champion edit;
- Undo/Redo changes the rendered Team and saved state;
- restart/reopen loads the saved Team.

Use a disposable `TFT_BUILDER_DATA_DIR` for integration tests so they never touch real user data.

Do not add screenshot/golden tests unless a visual regression cannot be tested reliably through control state. Functional tests are the first priority.

## Manual Windows verification for Block 4

After the normal quality suite, manually verify at least:

- first launch with empty disposable data creates one usable Team;
- restart reopens persisted state;
- independent panel scrolling;
- List horizontal scrolling with enough Champions;
- Team/List renaming and focus-loss save;
- List create/duplicate/reorder/clear/compact/delete;
- active versus primary List behavior;
- Champion add/remove;
- Trait updates and invalid dynamic-selection marking;
- Undo/Redo followed by restart persistence;
- no console warnings/exceptions during normal interactions.

The automated `flet test` smoke should be added to the Windows verification command once the real Builder controls exist.

## Exit criteria

Block 4 is complete only when:

- the placeholder shell is replaced by the real three-column Builder;
- a Team can be built with explicit non-drag controls;
- all required Block 4 List actions work through TeamEditor;
- active and primary List states behave independently;
- Trait results reflect the active List;
- structural changes and text edits persist according to the autosave policy;
- Undo/Redo is visible and persists the restored state;
- a restart round-trip succeeds;
- Flet integration smoke tests pass;
- the full pytest suite remains at 100 percent statement and branch coverage;
- Ruff lint and format checks are clean on the pinned Windows toolchain;
- project documents and manifest are updated for the completed block.
