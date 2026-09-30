# Block 7 Report - Real TFT Set data pipeline

Version: 0.7.0

## Implemented

- Set schema v5 carries Items, Trait descriptions, optional localized breakpoint descriptions, weighted Trait contributions, board-slot costs, exact Trait activation, derived Trait requirements, source candidates and upstream source records.
- Runtime Set discovery remains folder-based; no activation registry was added.
- The Trait engine supports weighted native/dynamic contributions, exact-count activation and derived states such as Eclipse.
- Builder-relevant Champion exceptions are represented only by executable declarative fields; there are no Elder Dragon, Lux or Kha'Zix name branches in the runtime engine.
- Elder Dragon is 2 board slots and +2 Riftbeast in Set data. Lux is one logical Champion with nine PER_CHAMPION origin choices worth 2 Trait points each. Kha'Zix is one logical Champion with four ZERO_OR_ONE, PER_CHAMPION evolution choices.
- Rival uses exact-one normal activation and Eclipse is derived from at least 3 Solar plus 3 Lunar.
- The reviewed Set-18 source roster normalizes 91 raw Champion records to 65 logical units with 17 explicit exclusions and normalizes ten Lux source records to one logical Lux.
- The reviewed Item boundary retains 136 canonical references: 10 components, 39 craftables, 20 emblems, 31 artifacts and 36 radiant Items. The other 634 broad source records remain explicit exclusions.
- Item recipe multiplicity is preserved.
- Trait tooltip placeholders, including hashed BIN-field variables, are resolved at build time. Seventy-six of 89 modeled breakpoints carry source-derived localized row text; rows without reliable source text are not invented.
- The deterministic builder emits and validates Champions, Traits, Items, dynamic rules, Team Planner mappings, source inventory, locales, overview data, source manifests and local assets.
- The importer uses pinned HTTPS sources, bounded downloads, cache reuse, PNG validation, exact source hashes and atomic source-lock publication after a successful package build.
- Ordinary visible assets use individual Riot Data Dragon `image.group` + `image.full` files. Dynamic variant groups use their configured CommunityDragon `squareIcon` source when Data Dragon does not expose distinct variant art. TFT sprite coordinates are not a release source of truth.
- Placed Builder slots resolve optional dynamic portraits from Set data with base-image fallback and always expose the selected dynamic Trait text separately.
- `SET_18_GUI_HCI_HANDOFF.md` records the real-data layout and interaction cases for the later GUI pass.

## Official Set-18 acquisition result

The corrected Windows acquisition succeeded from a clean output state and generated the committed Enchanted Wilds package plus `source_lock.json`.

The generated package contains:

- 65 logical Champions;
- 36 logical Traits;
- 136 reviewed Items;
- 2 dynamic Trait rules;
- 246 runtime PNG assets;
- 65 Team Planner mappings;
- 255 pinned provenance sources.

Generic package validation and inspection passed. `verify_enchanted_wilds.py` also passed against the real package and source lock.

The earlier sprite-atlas attempt is retained only as historical evidence: its first official run failed at `DA_CrimsonRaptor18`, proving the synthetic atlas harness could not establish release asset correctness. D037 supersedes the sprite acquisition decision for release builds.

## Post-data hardening Parts 2-3

The Windows run after the acquisition correction exposed only two bounded follow-ups:

- Ruff 0.16.9 reported six formatter-drift files and three import-block ordering findings.
- Three post-acquisition startup tests assumed `sample_set` was the only installed Set and therefore failed after `enchanted_wilds` was generated.

The reported formatting/import changes are applied. Startup integration tests now create an isolated sample-only assets root, so installing additional valid Sets cannot invalidate unrelated fixture expectations.

Part 3 adds generic provenance verification in `tft_builder.source_verification` plus `tools/set_import/verify_source_lock.py`. It compares Set ID/revision, complete provenance-ID inventory and every source record's URL, source revision, locale, SHA-256 and byte length. Malformed records, duplicate IDs, missing IDs and unexpected IDs are explicit failures. `SourceManifest` now also rejects duplicate packaged provenance IDs.

`verify_enchanted_wilds.py` reuses this generic lock comparison and retains only Set-18-specific semantic checks. The official package is the positive complete fixture. Mutation tests cover Elder Dragon, Lux, Kha'Zix, Rival, Eclipse, Team Planner mapping, Item category counts, source accounting, locale markup, runtime asset inventory and all provenance fields.

## Verification status

Local verification after Parts 2-3 passes 689 tests with 3,024 production statements and 922 branches at 100 percent statement and branch coverage. The generic provenance verifier and Set-18 verifier both pass against the official package and lock in the current project tree.

Part 4 remains before closing Block 7 hardening:

- exact Ruff 0.16.9 Windows rerun on this updated handoff;
- clean-cache versus warm-cache acquisition reproducibility;
- lightweight image sanity checks;
- complete Windows/Flet and real GUI/HCI smoke;
- Block 8 Team Planner import/export preparation.

## Packaged Windows runtime correction

The Parts 2-3 Windows gate verified 689 normal tests at 100 percent statement/branch coverage and the real Set/provenance gates. The packaged Flet integration still failed before application startup: the Flutter client connected, but embedded Python exited before registering its handler. Manual launch of the built app exposed the concrete root exception: `ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'`.

The correction keeps the schema architecture unchanged and makes the required native component explicit: `pydantic-core==2.46.5` is now a direct runtime dependency. `tft_builder.package_verification.windows_bundle_issues()` plus `tools/check_windows_bundle.py` validate the documented Serious Python Windows layout and require exactly one `_pydantic_core*.pyd` in the bundle `DLLs` directory alongside the Python packages. Generated build output is never patched manually.

The one remaining Ruff 0.16.9 formatter finding in `tests/test_set_schema.py` is also applied. Local verification after this correction passes 692 normal tests with 3,041 production statements and 930 branches at 100 percent statement/branch coverage. A clean Windows Flet build/integration rerun is required before Part 4 can be closed.

## Post-data hardening Part 4 implementation

- The clean Windows packaged test proved `_pydantic_core.cp313-win_amd64.pyd` reaches Serious Python staging and the app can reach the real Team Library without the project startup-error surface.
- Packaged Flet sessions now rebuild disposable Python staging before every run; repeat tests no longer rely on a directory mutated by an earlier packaging pass.
- Flet 1.0.1 packaged smoke readiness/navigation uses visible text and tooltips instead of treating Python control keys as a device-mode release contract.
- The Set-18 verifier now checks PNG signatures, the reviewed dimension inventory and exact duplicate-image groups. The normal/Radiant Spirit Visage files are the only source-confirmed byte-identical pair.
- `compare_set_packages.py` provides the deterministic clean-cache/warm-cache comparison gate for the final networked Windows verification.
- Cross-platform direction is explicit: Windows is the current blocking release target; macOS, Linux, Android, iOS and Web are later targets requiring their own packaging/runtime verification.
- `BLOCK_08_PLAN.md` prepares Team Planner and lossless native import/export without beginning Block 8 implementation.
