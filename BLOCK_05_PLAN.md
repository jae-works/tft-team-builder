# Block 5 Plan - Desktop interaction, search, dynamic Trait editing and Builder polish

Target version: 0.5.0
Prepared during: 0.4.1 Block 4 polish
Status: implemented in version 0.5.0; see `BLOCK_05_REPORT.md`.

## Goal

Block 5 turns the functional Block 4 Builder into the efficient desktop interaction model intended for daily use. It should improve speed and discoverability without replacing the tested Block 2-4 domain, Trait, history or persistence layers.

Research for this plan compared current TFT team builders and the current Flet 1.0 interaction APIs. Current MetaTFT and tactics.tools builders both keep Traits visible while the unit catalog remains directly searchable, and both make adding units a low-friction interaction. Flet 1.0 provides first-class `Draggable` and `DragTarget` controls, stable-key integration testing, and keyboard/page event support, so Block 5 can implement these interactions without another UI framework or generic drag abstraction.

## Keep the Block 4 architecture

- Keep `BuilderView` as the concrete Flet composition boundary until repeated UI behavior justifies a smaller focused helper.
- Keep all Team mutations in `TeamEditor`.
- Keep Trait calculation in `trait_engine.py`.
- Keep SQLite/autosave behavior in the existing persistence package.
- Keep active List, search text, filters and hover state transient unless a later requirement explicitly asks to persist them.
- Do not introduce presenter interfaces, a command framework, an event bus or a service container.

## Interaction model

### Champion catalog search

Add one search field above the Champion library.

Requirements:
- search Champion display name;
- search Trait display names associated with each Champion;
- use the existing `normalize_search_text()` function;
- filter immediately while typing;
- keep cost groups but omit empty groups;
- show a calm empty-result state rather than a blank panel;
- `Ctrl+F` focuses this search field.

The field should use a stable key such as `builder-champion-search`.

### Click and drag coexistence

Retain the explicit add button from Block 4 as an accessible/reliable fallback. Add drag/drop as the faster desktop path rather than making drag the only way to use the Builder.

Use Flet `Draggable`/`DragTarget` directly:
- library Champion -> trailing List target: append a new instance;
- placed Champion -> trailing List target: move to the end;
- placed Champion -> occupied Champion target: swap;
- placed Champion -> another List target: cross-List move;
- modifier-assisted copy may be added only if Flet exposes the modifier state reliably in the exact pinned runtime; otherwise keep explicit copy/duplicate controls rather than inventing fragile behavior.

Drag payloads should carry only the minimum stable identity needed to resolve the domain operation. The drop handler must translate to existing `TeamEditor` methods and never mutate slots directly.

### Dense List presentation

Preserve the 0.4.1 visual rule:
- normal Builder presentation shows occupied Champion cards compactly;
- exactly one empty/drop target appears at the far right;
- internal domain gaps remain supported by the core but are not rendered as rows of empty cards;
- explicit remove deletes that slot and closes the visible sequence.

During drag, show a clear target highlight but do not create permanent empty cards between Champions.

### Dynamic Trait selection

Replace the Block 4 warning-only state with a direct editor opened from the affected Champion or warning.

The dialog should:
- derive allowed Trait choices and cardinality from the Set dynamic rule;
- support all existing selection rules already validated by the Trait engine;
- write through `TeamEditor.set_trait_selection()`;
- show current selection and validation errors before confirmation;
- use stable keys for every choice and action;
- remain usable without drag/drop.

No rule logic should be duplicated in Flet. The dialog only presents the rule and submits a `TraitSelection`.

### Trait interaction

Trait cards should become useful navigation, not just output:
- clicking a Trait filters/highlights Champions in the library that can contribute to it;
- active breakpoints stay visually stronger than inactive progress;
- invalid dynamic selections remain clearly visible but should not dominate unrelated Traits;
- maintain the two existing display toggles.

Do not implement game-specific tooltip prose that is absent from the Set data.

### List controls

Reduce header crowding as interactions mature:
- keep active/primary state immediately visible;
- keep common actions directly accessible;
- move low-frequency destructive/maintenance actions into a compact overflow menu if that produces a clearer layout in Flet 1.0;
- retain stable semantic keys regardless of whether an action is direct or in a menu.

## Keyboard behavior

Implement only shortcuts with clear desktop value:
- `Ctrl+Z`: undo;
- `Ctrl+Y` and, where appropriate, `Ctrl+Shift+Z`: redo;
- `Ctrl+F`: focus Champion search;
- `Escape`: close a currently open Builder dialog where Flet behavior permits it cleanly.

Shortcuts must call the same BuilderView methods as buttons and must never bypass `TeamEditor` or persistence.

## Visual polish

Block 5 should continue the restrained Block 4.1 cleanup rather than introducing a separate design system.

Priorities:
- consistent spacing and card radii;
- clearer hierarchy between toolbar, active List, Traits and library;
- compact Champion cards that expose image/name/cost without oversized whitespace;
- stable toolbar geometry regardless of save/history state;
- clear hover/drop states;
- avoid displaying internal/debug wording to normal users;
- responsive minimum widths so the three-column desktop layout degrades predictably on narrower windows.

Current TFT builders place the board/list and Traits near the center of the task and make the unit catalog continuously searchable. Our layout should preserve the stronger multi-List concept while adopting that low-friction catalog/search pattern instead of imitating a website pixel-for-pixel.

## Save status and errors

Keep the fixed-width icon status introduced in 0.4.1:
- saved: neutral check icon;
- pending: sync icon;
- failed: error icon;
- full detail in tooltip and logs.

For actionable persistence failures, Block 5 may add a small non-layout-shifting banner/snackbar if testing shows the icon alone is too easy to miss. Do not return to variable-width toolbar text.

## Testing

### Unit/boundary tests

Add deterministic tests for:
- Champion name search;
- Trait-name search;
- normalization and empty-result behavior;
- trait-click filtering/highlighting;
- every drag source/target translation to the expected `TeamEditor` operation;
- invalid drag payloads/no-op drops;
- dynamic Trait dialog rule/cardinality behavior;
- keyboard shortcuts;
- active List fallback after drag/delete/undo/redo;
- save and history behavior after drag/drop and dynamic Trait edits.

Maintain 100 percent production statement and branch coverage.

### Packaged Flet integration tests

Continue using stable keys. Run packaged integration tests with coverage disabled for the host driver process because application coverage is already enforced by the normal test suite and the packaged Flet app executes in a separate process:

`uv run pytest tests_flet --no-cov`

Windows desktop integration testing requires Flutter's Windows prerequisites, including Developer Mode for symlink support.

Add packaged flows for interactions exposed reliably by the pinned Tester API:
- search -> add -> remove -> one trailing target remains;
- dynamic Trait selection dialog -> valid Trait result;
- List create -> undo -> redo.

The documented Flet Tester API does not currently expose a stable drag gesture helper. Test every drag source/target translation deterministically at the Builder boundary and verify actual drag/drop manually on Windows instead of inventing a brittle private-API test.

## Out of scope

Keep these out of Block 5 unless a required interaction directly depends on them:
- Team library/start page;
- similarity search between saved Teams;
- import/export/share formats;
- real Riot/CommunityDragon acquisition pipeline;
- release packaging/signing;
- a custom component framework;
- mobile-specific gesture redesign.

## Exit criteria

Block 5 is complete when:
- Champion search by name and Trait is fast and tested;
- click-add and drag/drop both work without divergent semantics;
- occupied-slot swaps and cross-List moves use the existing core correctly;
- dynamic Trait choices can be edited in the GUI;
- keyboard shortcuts work through the same action paths as buttons;
- the dense one-trailing-slot presentation remains stable;
- normal pytest remains at 100 percent statement/branch coverage;
- Ruff lint/format, ASCII, doc mirrors, compileall and existing smokes pass;
- packaged Flet integration tests pass on Windows with Developer Mode enabled and host-driver coverage disabled, and manual Windows review confirms native drag/drop;
- manual desktop review confirms the layout remains stable at common window widths.
