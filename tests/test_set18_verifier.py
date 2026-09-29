from __future__ import annotations

import importlib.util
from dataclasses import replace
from pathlib import Path

import pytest

from tft_builder.set_loader import load_set_directory
from tft_builder.set_schema import (
    DynamicSelectionRule,
    DynamicSelectionScope,
    ItemCategory,
    TraitActivationMode,
)


def load_verifier():
    path = Path(__file__).resolve().parents[1] / "tools/set_import/verify_enchanted_wilds.py"
    spec = importlib.util.spec_from_file_location("set18_verifier", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def verifier():
    return load_verifier()


@pytest.fixture(scope="module")
def set18(project_root: Path):
    return load_set_directory(project_root / "src/assets/sets/enchanted_wilds")


def replace_champion(loaded, champion_id: str, **updates):
    champions = tuple(
        champion.model_copy(update=updates) if champion.id == champion_id else champion
        for champion in loaded.champions
    )
    return replace(loaded, champions=champions)


def replace_trait(loaded, trait_id: str, **updates):
    traits = tuple(
        trait.model_copy(update=updates) if trait.id == trait_id else trait
        for trait in loaded.traits
    )
    return replace(loaded, traits=traits)


def replace_dynamic_rule(loaded, champion_id: str, **updates):
    rules = tuple(
        rule.model_copy(update=updates) if rule.champion_id == champion_id else rule
        for rule in loaded.dynamic_traits
    )
    return replace(loaded, dynamic_traits=rules)


def test_set18_verifier_accepts_complete_official_package(verifier, set18) -> None:
    assert verifier.verify_loaded_set(set18) == []


def test_set18_verifier_rejects_the_small_development_sample(verifier, valid_set_dir) -> None:
    issues = verifier.verify_loaded_set(load_set_directory(valid_set_dir))

    assert "unexpected Set ID" in issues
    assert "expected 65 logical Champions" in issues
    assert "expected 136 reviewed Items" in issues
    assert "Elder Dragon is missing" in issues
    assert "Lux dynamic rule is missing" in issues
    assert "expected 246 runtime PNG assets" in issues


def test_set18_verifier_catches_elder_dragon_semantic_drift(verifier, set18) -> None:
    changed = replace_champion(
        set18,
        "DA_18_ElderDragon",
        board_slots=1,
        trait_points={"DA_Riftbeast18": 3},
    )
    issues = verifier.verify_loaded_set(changed)

    assert "Elder Dragon must occupy 2 board slots" in issues
    assert "Elder Dragon must contribute 2 Riftbeast points" in issues


def test_set18_verifier_catches_lux_and_khazix_dynamic_rule_drift(verifier, set18) -> None:
    lux = next(rule for rule in set18.dynamic_traits if rule.champion_id == "DA_Lux18_Base")
    lux_points = dict(lux.choice_points)
    lux_points[lux.choices[0]] = 1
    lux_images = dict(lux.choice_images)
    lux_images.pop(lux.choices[0])
    changed = replace_dynamic_rule(
        set18,
        "DA_Lux18_Base",
        selection_rule=DynamicSelectionRule.ZERO_OR_ONE,
        selection_scope=DynamicSelectionScope.PER_INSTANCE,
        choices=lux.choices[:-1],
        choice_points=lux_points,
        choice_images=lux_images,
    )
    kha = next(rule for rule in changed.dynamic_traits if rule.champion_id == "DA_18_KhaZix")
    changed = replace_dynamic_rule(
        changed,
        "DA_18_KhaZix",
        selection_rule=DynamicSelectionRule.EXACTLY_ONE,
        selection_scope=DynamicSelectionScope.PER_INSTANCE,
        choices=kha.choices[:-1],
        choice_images={"DA_18_Executioner": "assets/champions/fake.png"},
    )
    issues = verifier.verify_loaded_set(changed)

    assert "Lux must require exactly one origin" in issues
    assert "Lux origin selection must be shared per Champion" in issues
    assert "Lux origin choices drifted" in issues
    assert "Lux must have one source-backed portrait for every origin" in issues
    assert "Lux origins must each contribute 2 Trait points" in issues
    assert "Kha'Zix must allow zero or one evolution Trait" in issues
    assert "Kha'Zix evolution selection must be shared per Champion" in issues
    assert "Kha'Zix choices drifted" in issues
    assert "Kha'Zix must use the base portrait fallback" in issues


def test_set18_verifier_catches_rival_eclipse_and_team_planner_drift(verifier, set18) -> None:
    changed = replace_trait(
        set18,
        "DA_18_Rival",
        activation_mode=TraitActivationMode.AT_LEAST,
    )
    changed = replace_trait(
        changed,
        "DA_18_Eclipse",
        derived_requirements={"DA_18_Lunar": 2, "DA_18_Solar": 3},
    )
    planner_ids = dict(changed.team_planner.champion_ids)
    planner_ids.pop(next(iter(planner_ids)))
    changed = replace(
        changed,
        team_planner=changed.team_planner.model_copy(update={"champion_ids": planner_ids}),
    )
    issues = verifier.verify_loaded_set(changed)

    assert "Rival must use exact-count activation" in issues
    assert "Eclipse derived requirements drifted" in issues
    assert "Team Planner mapping must cover all 65 Champions" in issues


def test_set18_verifier_catches_item_source_locale_and_asset_drift(
    verifier, set18, tmp_path: Path
) -> None:
    first_item = set18.items[0]
    items = (
        first_item.model_copy(update={"category": ItemCategory.OTHER}),
        *set18.items[1:],
    )
    locales = {locale: dict(catalog) for locale, catalog in set18.locales.items()}
    first_key = next(iter(locales[set18.manifest.default_locale]))
    locales[set18.manifest.default_locale][first_key] = "<b>markup</b>"
    source_manifest = set18.source_manifest.model_copy(
        update={
            "asset_sha256": dict(list(set18.source_manifest.asset_sha256.items())[1:]),
            "sources": set18.source_manifest.sources[:-1],
        }
    )
    changed = replace(
        set18,
        root=tmp_path,
        items=items,
        source_inventory=set18.source_inventory[:-1],
        locales=locales,
        source_manifest=source_manifest,
    )
    issues = verifier.verify_loaded_set(changed)

    assert "reviewed Item category counts drifted" in issues
    assert "source candidate accounting drifted" in issues
    assert "expected 246 runtime PNG assets" in issues
    assert "source manifest must hash all 246 runtime assets" in issues
    assert "expected 255 pinned provenance sources" in issues
    assert any(issue.startswith("locale en_US still contains Riot markup in:") for issue in issues)
