# Block 5 Report - Desktop interaction, search and Builder polish

Version: 0.5.0
Status: implemented locally; exact Ruff 0.16.9 and packaged Windows Flet verification pending user release gate.

## Implemented

- Champion library search by Champion display name, aliases and associated Trait display names.
- Trait cards can filter/unfilter the Champion library without replacing the text search.
- Existing click-add remains available while native Flet Draggable/DragTarget controls add the desktop drag path.
- Library Champion -> List end appends a new instance.
- Placed Champion -> List end performs a dense move and preserves the instance ID.
- Placed Champion -> occupied Champion target uses the existing TeamEditor move/swap semantics.
- Cross-List end moves are atomic and close the source sequence instead of leaving a visible gap.
- Explicit placed-Champion copy remains available without depending on undocumented modifier state.
- Dynamic Trait selection is editable from the invalid-selection warning or the affected Champion.
- Dynamic dialogs reuse `validate_dynamic_selection()` from the Trait engine instead of reimplementing rule logic in Flet.
- PER_INSTANCE and PER_CHAMPION edit scopes are supported. PER_CHAMPION edits update matching instances atomically through TeamEditor.
- Ctrl+Z, Ctrl+Y, Ctrl+Shift+Z, Ctrl+F and Escape are wired through the same Builder actions used by visible controls.
- Low-frequency List maintenance actions are grouped in an overflow menu while active/primary/reorder controls remain visible.
- Champion cards expose compact name/cost/Trait details and stable semantic keys.

## Block 4.1 desktop bug fixes folded into this release

The real Windows review exposed a clipped/missing Champion remove action. This was a presentation bug, not a Trait or first-added-Champion bug: a fixed 122-pixel card contained a portrait, up to two name lines, padding and a normal-size IconButton, so the action could extend below the clipped card. Two-line names such as Sample Guardian hid it completely.

Version 0.5.0 gives the card a defined content/action split: portrait/name are the draggable content and a fixed compact action row stays inside the card. A regression test checks the action geometry and removal behavior independently of Champion identity.

The user Windows 0.4.1 verification also confirmed that Ruff lint passed after two formatter changes and that 564 tests passed with 100 percent statement/branch coverage. The documented `flet test ... -- --no-cov` invocation was incorrect for pinned Flet 1.0.1: that CLI rejects the `--` separator for `flet test`. The project now runs the packaged Flet pytest plugin directly with `uv run pytest tests_flet --no-cov` on Windows.

## Core additions

`TeamEditor.move_champion_to_end()` provides one atomic dense move operation for the GUI trailing drop target. It preserves the Champion instance ID, removes the source slot, reindexes the source List and appends to the destination. Moving the already-last Champion to the same List is a no-op.

`TeamEditor.set_champion_trait_selection()` provides the concrete PER_CHAMPION update needed by dynamic Trait editing. It updates all matching Champion instances in one edit/history entry without exposing a generic bulk-edit abstraction.

`validate_dynamic_selection()` is public Trait-engine validation used by both calculation and the GUI dialog. Rule/cardinality logic therefore has one implementation.

## Verification in the implementation environment

The current normal suite passes 585 tests with 2,443/2,443 production statements and 742/742 branches covered (100 percent statement and branch coverage). No skips are expected.

A deterministic extra editor stress pass executed 1,231 successful mixed add/remove/copy/dense-move operations across three Lists, validating Team invariants and unique Champion instance IDs after every successful edit.

The implementation environment cannot install the pinned Ruff 0.16.9 binary or Flet 1.0.1 because external package access is unavailable. Exact formatter/linter and packaged-Flet verification therefore remain Windows release gates. The source is based on the user's post-Ruff 0.4.1 ZIP and the exact previously reported formatter changes were preserved before Block 5 changes.

## Packaged Flet testing

For pinned Flet 1.0.1 use:

`uv run pytest tests_flet --no-cov`

Do not use `uv run flet test --tests-dir tests_flet -- --no-cov` with this pinned CLI; the user's real Windows run proved that 1.0.1 rejects that separator for `flet test`.

The packaged smoke covers stable-key startup, add/remove regression, search, dynamic Trait dialog and List history. Drag source/target translation is exhaustively covered below the packaged boundary because the documented Tester API does not currently expose a stable drag gesture helper; real drag is part of the manual Windows review.

## Architecture review

Block 5 does not add presenter interfaces, a command hierarchy, an event bus or a custom drag framework. `BuilderView` remains the concrete Flet boundary; mutations stay in TeamEditor; Trait semantics stay in trait_engine; persistence stays in the persistence package.

The file is larger because the Builder now owns real desktop interactions. Concrete render/action helpers are separated by responsibility, but further splitting is deferred until there is a repeated independent component with a cleaner boundary than passing most Builder state/callbacks through another layer.
