# Block 6 Plan - Start page and Team library

Target version: 0.6.0
Prepared during: 0.5.0 Block 5 completion

## Goal

Block 6 turns the application from a single-Builder program into the intended local Team library. The Start page should make saved Teams easy to create, find, open, soft-delete and restore without weakening the existing Team aggregate or Builder workflow.

The distinguishing project behavior is that one Team may contain multiple Lists. Start-page previews and similarity ranking therefore operate on Lists deliberately instead of flattening a Team into one Champion bag.

## Product research applied

Current TFT builders such as MetaTFT and tactics.tools emphasize a continuously searchable unit catalog and quick team construction. MetaTFT also exposes saved teams from the builder. Block 6 should keep our local-first multi-List model as the differentiator instead of copying a web layout pixel-for-pixel.

The Start page should use a familiar local-library pattern: clear create/open actions, search at the top, compact cards, recoverable deletion, and persistent navigation state for the current session.

## Navigation

- Application startup opens the Start page once more than one Team/library workflow matters; a first-run empty state can create the first Team directly.
- Opening a Team constructs the existing BuilderView for that Team.
- Returning to the Start page preserves Team-name search and Champion-similarity selection for the current session.
- Builder active-List state remains Builder-session state and is not added to SQLite.
- Do not add a router framework unless direct page composition becomes genuinely repetitive.

## Set selection

- Add a Set selector backed only by validated bundled Set packages.
- New Teams use the selected Set ID/revision.
- Existing Teams always open against their own stored Set identity; the selector does not silently migrate them.
- If the required Set is missing or incompatible, show a clear disabled/error card rather than corrupting or rewriting the Team.

## Team cards

Each Team card should show:
- Team name;
- Set identity/revision where useful;
- primary List as the normal Champion preview;
- List count;
- last-updated information in a compact form;
- explicit Open action;
- recoverable Delete action.

Do not render every List on the Start page. The primary List is the summary by design; the full multi-List structure belongs in the Builder.

## Create, delete and restore

- Create a Team with one List and make that List primary.
- Persist creation before opening the Builder.
- Normal delete uses the existing soft-delete persistence behavior.
- Provide a small Deleted/Trash view or restore affordance rather than immediate permanent deletion.
- Permanent deletion, if exposed at all in Block 6, requires explicit confirmation and must use existing persistence primitives.

## Team-name search

- Search normalized Team names with the existing search normalization rules.
- Filter locally and deterministically.
- Empty query restores the normal ordering.
- Preserve search text when entering and returning from the Builder during the session.

## Champion similarity search

The Start page can select zero or more desired Champion definitions, including duplicates. For every saved Team:

1. Score every List in that Team independently.
2. Build multisets (Champion ID -> count) for the selected Champions and List Champions.
3. `matches = sum(min(selected_count[id], list_count[id]))`.
4. `extras = max(0, total_list_champions - matches)`.
5. The Team's score is its best List score.
6. Rank higher match count first.
7. For equal match count, rank fewer extras first.
8. Keep a deterministic final tie-breaker (updated time, then Team ID or name as documented by implementation).

Duplicate desired Champions therefore matter. Selecting Guardian twice should prefer a List containing two Guardians over one containing one Guardian.

A zero-Champion similarity selection does not invent a ranking signal; normal library ordering remains in effect.

## Similarity implementation boundary

Implement ranking as a small Flet-independent function/module with immutable/result data that is easy to test. It reads Teams/Lists/Champion IDs and knows nothing about controls or SQLite queries.

Do not add vector databases, fuzzy-search libraries, generic scoring interfaces or machine-learning dependencies. The requirement is deterministic multiset matching.

## Performance

The first implementation may load normal local Team aggregates and rank them in memory. Add database search/index complexity only if realistic-library benchmarks show a need. Block 9 remains the performance-hardening block.

## Testing

Add exhaustive deterministic tests for:
- name normalization/filtering;
- one/multiple Lists per Team;
- primary List preview selection;
- exact matches;
- partial matches;
- duplicate desired Champions;
- duplicate List Champions;
- fewer-extra tie-break;
- best-List selection per Team;
- deterministic final ties;
- empty desired selection;
- soft delete/restore visibility;
- missing Set behavior;
- navigation/search-state preservation;
- create -> persist -> open -> return flows.

Maintain the 100 percent production statement and branch coverage gates.

## Flet integration scope

Use stable keys for Start-page search, Team cards, create/open/delete/restore controls and Builder-back navigation. Add one packaged Windows smoke covering create/open/return/search/delete/restore if the pinned Flet Tester API supports each step reliably. Keep logic-level similarity tests independent of Flet.

## Out of scope

- Riot Team Planner import/export (Block 8).
- Real Riot/CommunityDragon Set acquisition (Block 7).
- Cloud/account sync.
- Meta recommendations.
- Custom database-search infrastructure without measured need.

## Exit criteria

Block 6 is complete when multiple saved Teams can be managed as a useful local library, Team-name search works, Champion multiset similarity ranking follows the specified rules, soft delete/restore works, Builder navigation preserves relevant session filters, tests remain at 100 percent statement/branch coverage, and the Windows GUI release gate is clean.
