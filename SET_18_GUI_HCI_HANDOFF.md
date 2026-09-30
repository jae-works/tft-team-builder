# Set 18 GUI and HCI handoff

This document freezes the reviewed Set-data assumptions that the next GUI pass may rely on. It is intentionally about observable data and interaction requirements, not a new UI architecture.

## Verified Set 18 layout stress points

- 65 logical Champions use costs 1 through 5 with distribution 14 / 13 / 14 / 14 / 10. The GUI must still remain data-driven; the development sample keeps a cost-7 Champion specifically to catch hardcoded five-cost assumptions.
- Elder Dragon is the only current 2-slot Champion and contributes 2 Riftbeast points. Slot rendering and placement must not infer board usage from Champion cost or card size.
- Thirteen reviewed Champions have three native Traits. The GUI must not assume that two Trait labels are enough, and dynamic choices can add further visible context.
- Blossom and Elderwood each expose five breakpoints. Trait-detail presentation must support arbitrary Set-defined breakpoint counts rather than fixed tier slots.
- German is a stronger text-layout stress case than English. `Wachstum der Urahnen` is a reviewed 20-character Trait name, while `Mama Schnabel` and `Kluftkrabbler` are 13-character Champion names. Cards may truncate visually where necessary, but full text must remain reachable by focus/click-accessible details.

## Dynamic Champion presentation

- Lux remains one logical Champion. Her exactly-one origin selection changes the placed-slot portrait when that choice has a `choice_images` entry. The selected origin must also remain visible as text; the portrait is never the only state indicator.
- Kha'Zix remains one logical Champion. His zero-or-one evolution choice has no reviewed per-choice portraits, so every choice intentionally uses the base portrait while the selected Trait remains visible textually.
- A missing optional choice image, an empty selection or a multi-choice/otherwise invalid selection must use the logical Champion's base portrait without changing card geometry.
- The runtime must never branch on Champion names to choose portraits. Set data is authoritative.

## Dynamic choice control

For single-choice rules, the next GUI refinement should visually communicate single-selection semantics rather than presenting the control like an arbitrary multi-select list.

- `EXACTLY_ONE`: prefer a radio-style single-choice control.
- `ZERO_OR_ONE`: prefer the same model plus an explicit `None` / `No evolution Trait` choice.
- Choice text is mandatory even when portraits differ.
- Enter/Space must activate the focused choice, Escape must cancel/close, and closing the editor should restore focus to its trigger.
- Validation/status text must be exposed without stealing keyboard focus.

## Trait details

A click/focus-accessible Trait-details surface should show:

1. localized Trait name and icon;
2. general localized description when present;
3. every Set-defined breakpoint in source order;
4. breakpoint-specific localized effect text when present;
5. current count and active breakpoint;
6. next-breakpoint progress when another breakpoint exists;
7. derived activation requirements for derived states such as Eclipse.

Essential explanations must not be hover-only. Traits whose source only provides a general description must display that description without inventing missing breakpoint prose.

## Regression gates

The final GUI verification should explicitly cover:

- Lux base portrait -> selected origin portrait -> base fallback;
- Kha'Zix selection with unchanged base portrait and visible selected Trait text;
- Elder Dragon 2-slot placement and +2 Riftbeast contribution;
- a three-native-Trait Champion such as Xayah or Sentinel;
- a five-breakpoint Trait such as Elderwood or Blossom;
- long German Champion/Trait labels;
- the development sample's cost-7 Champion;
- keyboard-only open/select/apply/cancel for dynamic choices;
- focus return after closing the dynamic editor and Trait details.

`tools/set_import/verify_set_review.py` is the final post-acquisition dataset gate. It reads Enchanted Wilds expectations from `data/review.json`, verifies reviewed counts/special semantics/source accounting/asset inventory/locale markup, and regenerates `SET_REVIEW.md`.


## Post-data hardening clarification

Elder Dragon should render as one Champion card/instance. Its special rule affects board-capacity usage, not visual/list identity: board usage must sum each placed Champion definition's `board_slots` value, so Elder Dragon contributes 2 while ordinary units contribute 1. Do not represent this by inserting a duplicate hidden/visible Slot.

Lux duplicate-origin behavior is under final Part 2 review. The UI must follow the eventual Set-level selection scope and must never allow two duplicate Lux instances to display conflicting origins if the reviewed mechanic requires one shared Avatar origin.

## Part-4 real GUI smoke

Before leaving Block 7, verify the real Enchanted Wilds package on Windows with these data-driven cases: Lux changes portrait and contributes two points to one selected origin; duplicate Lux copies share the PER_CHAMPION selection; Kha'Zix can remain unevolved or select any combination up to all four evolution Traits while keeping the base portrait; Elder Dragon remains one visual Champion while board usage increases by two and Riftbeast increases by exactly two; Rival activates only at the reviewed exact-one base state; Eclipse appears only after the derived 3 Lunar plus 3 Solar condition. Repeat the check with the German locale stress labels and a dense five-breakpoint Trait. These are smoke cases, not Champion-name branches to add to the UI.
