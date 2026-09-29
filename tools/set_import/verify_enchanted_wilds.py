"""Verify the reviewed Set 18 runtime package after official asset acquisition."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from tft_builder.set_loader import LoadedSet, load_set_directory
from tft_builder.set_schema import (
    CandidateKind,
    CandidateStatus,
    DynamicSelectionRule,
    DynamicSelectionScope,
    ItemCategory,
    TraitActivationMode,
)

_EXPECTED_COST_COUNTS = {1: 14, 2: 13, 3: 14, 4: 14, 5: 10}
_EXPECTED_ITEM_COUNTS = {
    ItemCategory.COMPONENT: 10,
    ItemCategory.CRAFTABLE: 39,
    ItemCategory.EMBLEM: 20,
    ItemCategory.ARTIFACT: 31,
    ItemCategory.RADIANT: 36,
}
_LUX_CHOICES = {
    "DA_18_Blackthorn",
    "DA_18_Blossom",
    "DA_18_Coven",
    "DA_18_Elderwood",
    "DA_18_Fae",
    "DA_18_Inferno",
    "DA_18_Lunar",
    "DA_18_Solar",
    "DA_Primal18",
}
_KHA_CHOICES = {
    "DA_18_Executioner",
    "DA_18_Rapidfire",
    "DA_18_Slayer",
    "DA_18_Spellweaver",
}
_MARKUP_PATTERN = re.compile(r"@[^@]+@|<[^>]+>|%i:[^%]+%")


def _add_if(issues: list[str], condition: bool, message: str) -> None:
    if condition:
        issues.append(message)


def verify_loaded_set(loaded: LoadedSet) -> list[str]:
    """Return reviewed Set-18 completeness problems for one already validated package."""

    issues: list[str] = []
    manifest = loaded.manifest
    _add_if(issues, manifest.set_id != "enchanted_wilds", "unexpected Set ID")
    _add_if(issues, manifest.revision != "18.3b", "unexpected Set revision")
    _add_if(issues, len(loaded.champions) != 65, "expected 65 logical Champions")
    _add_if(issues, len(loaded.traits) != 36, "expected 36 logical Traits")
    _add_if(issues, len(loaded.items) != 136, "expected 136 reviewed Items")
    _add_if(issues, len(loaded.dynamic_traits) != 2, "expected 2 dynamic Trait rules")

    cost_counts = Counter(champion.cost for champion in loaded.champions)
    _add_if(issues, dict(sorted(cost_counts.items())) != _EXPECTED_COST_COUNTS, "Champion cost counts drifted")
    item_counts = Counter(item.category for item in loaded.items)
    _add_if(
        issues,
        any(item_counts[category] != count for category, count in _EXPECTED_ITEM_COUNTS.items()),
        "reviewed Item category counts drifted",
    )
    _add_if(
        issues,
        sum(item_counts.values()) != sum(_EXPECTED_ITEM_COUNTS.values()),
        "unexpected Item category entered the reviewed package",
    )

    champions = loaded.champions_by_id
    traits = loaded.traits_by_id
    elder = champions.get("DA_18_ElderDragon")
    _add_if(issues, elder is None, "Elder Dragon is missing")
    if elder is not None:
        _add_if(issues, elder.board_slots != 2, "Elder Dragon must occupy 2 board slots")
        _add_if(
            issues,
            elder.trait_points.get("DA_Riftbeast18") != 2,
            "Elder Dragon must contribute 2 Riftbeast points",
        )

    rival = traits.get("DA_18_Rival")
    _add_if(issues, rival is None, "Rival Trait is missing")
    if rival is not None:
        _add_if(
            issues,
            rival.activation_mode is not TraitActivationMode.EXACT,
            "Rival must use exact-count activation",
        )

    eclipse = traits.get("DA_18_Eclipse")
    _add_if(issues, eclipse is None, "Eclipse Trait is missing")
    if eclipse is not None:
        _add_if(
            issues,
            eclipse.derived_requirements != {"DA_18_Lunar": 3, "DA_18_Solar": 3},
            "Eclipse derived requirements drifted",
        )

    dynamic = {rule.champion_id: rule for rule in loaded.dynamic_traits}
    lux = dynamic.get("DA_Lux18_Base")
    _add_if(issues, lux is None, "Lux dynamic rule is missing")
    if lux is not None:
        _add_if(
            issues,
            lux.selection_rule is not DynamicSelectionRule.EXACTLY_ONE,
            "Lux must require exactly one origin",
        )
        _add_if(
            issues,
            lux.selection_scope is not DynamicSelectionScope.PER_INSTANCE,
            "Lux origin selection must be per instance",
        )
        _add_if(issues, set(lux.choices) != _LUX_CHOICES, "Lux origin choices drifted")
        _add_if(
            issues,
            set(lux.choice_images) != _LUX_CHOICES,
            "Lux must have one source-backed portrait for every origin",
        )
        _add_if(
            issues,
            any(lux.choice_points.get(choice) != 2 for choice in _LUX_CHOICES),
            "Lux origins must each contribute 2 Trait points",
        )

    kha = dynamic.get("DA_18_KhaZix")
    _add_if(issues, kha is None, "Kha'Zix dynamic rule is missing")
    if kha is not None:
        _add_if(
            issues,
            kha.selection_rule is not DynamicSelectionRule.ZERO_OR_ONE,
            "Kha'Zix must allow zero or one evolution Trait",
        )
        _add_if(
            issues,
            kha.selection_scope is not DynamicSelectionScope.PER_CHAMPION,
            "Kha'Zix evolution selection must be shared per Champion",
        )
        _add_if(issues, set(kha.choices) != _KHA_CHOICES, "Kha'Zix choices drifted")
        _add_if(issues, bool(kha.choice_images), "Kha'Zix must use the base portrait fallback")

    _add_if(
        issues,
        manifest.team_planner_supported is not True
        or loaded.team_planner.codec != "riot_v2_12bit"
        or len(loaded.team_planner.champion_ids) != 65,
        "Team Planner mapping must cover all 65 Champions",
    )

    source_counts = Counter((item.kind, item.status) for item in loaded.source_inventory)
    expected_sources = {
        (CandidateKind.CHAMPION, CandidateStatus.INCLUDED): 74,
        (CandidateKind.CHAMPION, CandidateStatus.EXCLUDED): 17,
        (CandidateKind.TRAIT, CandidateStatus.INCLUDED): 36,
        (CandidateKind.ITEM, CandidateStatus.INCLUDED): 136,
        (CandidateKind.ITEM, CandidateStatus.EXCLUDED): 634,
    }
    _add_if(issues, source_counts != expected_sources, "source candidate accounting drifted")

    asset_root = loaded.root / manifest.assets_dir
    png_count = sum(1 for path in asset_root.rglob("*.png") if path.is_file())
    _add_if(issues, png_count != 246, "expected 246 runtime PNG assets")
    _add_if(
        issues,
        len(loaded.source_manifest.asset_sha256) != 246,
        "source manifest must hash all 246 runtime assets",
    )
    _add_if(
        issues,
        len(loaded.source_manifest.sources) != 21,
        "expected 21 pinned provenance sources",
    )

    for locale, catalog in loaded.locales.items():
        bad_keys = sorted(key for key, value in catalog.items() if _MARKUP_PATTERN.search(value))
        if bad_keys:
            issues.append(f"locale {locale} still contains Riot markup in: {', '.join(bad_keys[:5])}")

    # These are deliberate layout stress points for the GUI handoff. Do not turn them into
    # runtime limits: future Sets may exceed all of them.
    _add_if(
        issues,
        max((len(champion.traits) for champion in loaded.champions), default=0) < 3,
        "expected at least one three-Trait Champion for dense-card coverage",
    )
    _add_if(
        issues,
        max((len(trait.breakpoints) for trait in loaded.traits), default=0) < 5,
        "expected at least one five-breakpoint Trait for dense-detail coverage",
    )
    de_catalog = loaded.locales.get("de_DE", {})
    maokai_trait = traits.get("DA_18_Maokai_UniqueTrait")
    if maokai_trait is not None:
        _add_if(
            issues,
            de_catalog.get(maokai_trait.name_key) != "Wachstum der Urahnen",
            "German long-name layout fixture drifted",
        )

    return issues


def verify_source_lock(loaded: LoadedSet, source_lock: Path) -> list[str]:
    """Compare the reviewed acquisition lock with provenance embedded in the Set package."""

    payload = json.loads(source_lock.read_text(encoding="utf-8"))
    issues: list[str] = []
    _add_if(issues, payload.get("set_id") != loaded.manifest.set_id, "source lock Set ID differs")
    _add_if(
        issues,
        payload.get("revision") != loaded.manifest.revision,
        "source lock revision differs",
    )
    locked = {record["id"]: record for record in payload.get("sources", [])}
    packaged = {record.id: record for record in loaded.source_manifest.sources}
    _add_if(issues, set(locked) != set(packaged), "source lock provenance IDs differ")
    for source_id in sorted(set(locked) & set(packaged)):
        if locked[source_id].get("sha256") != packaged[source_id].sha256:
            issues.append(f"source lock hash differs for {source_id}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("set_dir", type=Path)
    parser.add_argument("--source-lock", type=Path)
    args = parser.parse_args()

    loaded = load_set_directory(args.set_dir)
    issues = verify_loaded_set(loaded)
    if args.source_lock is not None:
        issues.extend(verify_source_lock(loaded, args.source_lock))

    if issues:
        print("INVALID Set 18 review")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("VALID Set 18 review")
    print("Champions: 65 | Traits: 36 | Items: 136 | PNGs: 246 | Sources: 21")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
