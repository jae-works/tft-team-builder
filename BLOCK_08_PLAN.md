# Block 8 plan - Team Planner and native import/export

Block 8 adds exchange formats without weakening the existing local Team model. Riot Team Planner codes are a constrained external representation; the native project format remains the lossless round-trip format.

## Part 1 - Codec contract and fixtures

- Freeze reviewed Team Planner codec fixtures against the Set-owned `team_planner.json` mapping.
- Implement decode/encode as Flet-independent pure functions with explicit validation errors.
- Preserve duplicate Champions and reject unknown/mismatched Set mappings deterministically.
- Document every external-format limit before connecting it to the GUI.

## Part 2 - List import/export core

- Export one List to a Team Planner code.
- When the external format cannot represent every placed Champion, require an explicit selection instead of silently dropping units.
- Decode to a preview object first; importing becomes one validated, undoable TeamEditor action.
- Add round-trip, malformed-input, wrong-Set, duplicate and boundary tests.

## Part 3 - Native full-Team format

- Add a small versioned native JSON format for complete Team/List/slot/dynamic-Trait state.
- Preserve data the Riot format cannot represent, including multiple Lists, primary-List identity, slot ordering and dynamic Trait selections.
- Validate before mutation and import atomically.
- Add deterministic round-trip and migration/version-rejection tests.

## Part 4 - GUI, clipboard and HCI

- Add import preview and explicit confirmation/cancel paths.
- Add copy/export actions with clear success/error feedback.
- Provide a >10-unit selection dialog only when the external codec requires it.
- Keep all import/export operations usable without drag-and-drop and restore focus after dialogs.
- Extend packaged Flet smoke coverage only for stable user-visible contracts; keep codec correctness in normal unit tests.

## Cross-platform constraint

Block 8 core codecs and native files must remain platform-neutral. Windows is the current verification priority, but clipboard/file-picker UI must use Flet/platform-aware APIs so later macOS, Linux, Android, iOS and Web support does not require a codec or persistence rewrite.
