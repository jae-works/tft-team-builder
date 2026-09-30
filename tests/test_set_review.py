from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

from tft_builder.models import TraitSelection
from tft_builder.set_loader import load_set_directory
from tft_builder.set_review import render_set_review, verify_review_policy, write_set_review_report
from tft_builder.set_schema import (
    DynamicSelectionRule,
    DynamicSelectionScope,
    TraitActivationMode,
)
from tft_builder.trait_engine import validate_dynamic_selection


def test_reviewed_set_accepts_complete_official_package(project_root: Path) -> None:
    loaded = load_set_directory(project_root / "src/assets/sets/enchanted_wilds")

    assert loaded.review is not None
    assert verify_review_policy(loaded) == []


def test_set18_review_policy_owns_special_semantics_and_duplicate_exception(
    project_root: Path,
) -> None:
    loaded = load_set_directory(project_root / "src/assets/sets/enchanted_wilds")
    assert loaded.review is not None

    kha = next(rule for rule in loaded.dynamic_traits if rule.champion_id == "DA_18_KhaZix")
    assert kha.selection_rule is DynamicSelectionRule.ANY_NUMBER
    assert validate_dynamic_selection(kha, TraitSelection(tuple(kha.choices))) is None
    assert loaded.review.allowed_duplicate_asset_groups == [
        [
            "assets/items/da_spiritvisage.png",
            "assets/items/da_spiritvisage_radiant.png",
        ]
    ]


def test_review_policy_detects_declared_champion_and_dynamic_drift(project_root: Path) -> None:
    loaded = load_set_directory(project_root / "src/assets/sets/enchanted_wilds")
    champions = tuple(
        champion.model_copy(update={"board_slots": 1})
        if champion.id == "DA_18_ElderDragon"
        else champion
        for champion in loaded.champions
    )
    dynamic = tuple(
        rule.model_copy(update={"selection_rule": DynamicSelectionRule.ZERO_OR_ONE})
        if rule.champion_id == "DA_18_KhaZix"
        else rule
        for rule in loaded.dynamic_traits
    )

    issues = verify_review_policy(replace(loaded, champions=champions, dynamic_traits=dynamic))

    assert any("DA_18_ElderDragon board_slots differs" in issue for issue in issues)
    assert any("DA_18_KhaZix selection_rule differs" in issue for issue in issues)


def test_review_policy_detects_unexpected_duplicate_runtime_image(
    project_root: Path, tmp_path: Path
) -> None:
    source = project_root / "src/assets/sets/enchanted_wilds"
    root = tmp_path / "enchanted_wilds"
    shutil.copytree(source, root)
    loaded = load_set_directory(root)
    assets = root / loaded.manifest.assets_dir / "items"
    (assets / "da_adaptivehelm.png").write_bytes((assets / "da_bloodthirster.png").read_bytes())

    issues = verify_review_policy(loaded)

    assert "runtime PNG duplicate groups differ from review policy" in issues


def test_review_report_contains_requested_dataset_sections(project_root: Path) -> None:
    loaded = load_set_directory(project_root / "src/assets/sets/enchanted_wilds")

    report = render_set_review(loaded)

    assert "## Traits and breakpoints" in report
    assert "## Champions" in report
    assert "## Component recipe matrix" in report
    assert "## Non-recipe items (excluding Radiant)" in report
    assert "## Radiant items" in report
    assert "DA_18_KhaZix" not in report  # Human review uses localized names rather than IDs.
    assert "Kha'Zix" in report
    assert "ANY_NUMBER / PER_CHAMPION" in report
    assert "![" in report


def test_review_report_is_recreated_at_manifest_path(project_root: Path, tmp_path: Path) -> None:
    source = project_root / "src/assets/sets/enchanted_wilds"
    root = tmp_path / "enchanted_wilds"
    shutil.copytree(source, root)
    report_path = root / "SET_REVIEW.md"
    report_path.unlink()
    loaded = load_set_directory(root)

    written = write_set_review_report(loaded)

    assert written == report_path
    assert written.read_text(encoding="utf-8") == render_set_review(loaded)


def test_review_policy_reports_all_declared_runtime_drifts(project_root: Path) -> None:
    loaded = load_set_directory(project_root / "src/assets/sets/enchanted_wilds")
    assert loaded.review is not None
    policy = loaded.review

    elder = policy.champion_expectations[0]
    rival = policy.trait_expectations[0]
    eclipse = policy.trait_expectations[1]
    lux_expectation = policy.dynamic_trait_expectations[0]
    kha_expectation = policy.dynamic_trait_expectations[1]

    review = policy.model_copy(
        update={
            "expected_set_id": "other_set",
            "expected_revision": "other-revision",
            "champion_count": 0,
            "trait_count": 0,
            "item_count": 0,
            "dynamic_trait_count": 0,
            "champion_cost_counts": [],
            "item_category_counts": [],
            "champion_expectations": [
                elder.model_copy(update={"champion_id": "missing_champion"}),
                elder.model_copy(update={"board_slots": 99, "trait_points": {}}),
            ],
            "trait_expectations": [
                rival.model_copy(update={"trait_id": "missing_trait"}),
                rival.model_copy(update={"activation_mode": TraitActivationMode.AT_LEAST}),
                eclipse.model_copy(update={"derived_requirements": {}}),
            ],
            "dynamic_trait_expectations": [
                lux_expectation.model_copy(update={"champion_id": "missing_dynamic"}),
                lux_expectation.model_copy(
                    update={
                        "selection_scope": DynamicSelectionScope.PER_INSTANCE,
                        "exact_count": 1,
                        "choices": list(reversed(lux_expectation.choices)),
                        "choice_points": {},
                    }
                ),
                kha_expectation,
            ],
            "team_planner_codec": "other_codec",
            "team_planner_champion_count": 0,
            "source_candidate_counts": [],
            "png_count": 0,
            "source_manifest_asset_count": 0,
            "provenance_source_count": 0,
            "png_dimensions": [],
            "allowed_duplicate_asset_groups": [],
            "locale_expectations": [
                policy.locale_expectations[0].model_copy(update={"value": "wrong"})
            ],
            "minimum_max_champion_traits": 99,
            "minimum_max_trait_breakpoints": 99,
        }
    )

    dynamic = tuple(
        rule.model_copy(update={"choice_images": {}})
        if rule.champion_id == lux_expectation.champion_id
        else rule.model_copy(update={"choice_images": {rule.choices[0]: "assets/fake.png"}})
        if rule.champion_id == kha_expectation.champion_id
        else rule
        for rule in loaded.dynamic_traits
    )
    locales = {locale: dict(catalog) for locale, catalog in loaded.locales.items()}
    locales[loaded.manifest.default_locale]["set.enchanted_wilds.name"] = "<b>markup</b>"

    issues = verify_review_policy(
        replace(loaded, review=review, dynamic_traits=dynamic, locales=locales)
    )
    joined = "\n".join(issues)

    for expected in (
        "Set ID differs",
        "Set revision differs",
        "Champions count differs",
        "Traits count differs",
        "Items count differs",
        "dynamic Trait rules count differs",
        "Champion cost counts differ",
        "Item category counts differ",
        "reviewed Champion is missing",
        "board_slots differs",
        "trait_points differ",
        "reviewed Trait is missing",
        "activation_mode differs",
        "derived_requirements differ",
        "reviewed dynamic Trait rule is missing",
        "selection_scope differs",
        "exact_count differs",
        "choices differ",
        "choice_points differ",
        "must define an image for every choice",
        "must not define choice images",
        "Team Planner codec differs",
        "Team Planner Champion count differs",
        "source candidate accounting differs",
        "runtime PNG count differs",
        "source-manifest asset count differs",
        "provenance source count differs",
        "runtime PNG dimension inventory differs",
        "runtime PNG duplicate groups differ",
        "still contains source markup",
        "locale value differs",
        "maximum Champion Trait count is below review minimum",
        "maximum Trait breakpoint count is below review minimum",
    ):
        assert expected in joined


def test_review_policy_handles_optional_markup_check_and_missing_policy(project_root: Path) -> None:
    official = load_set_directory(project_root / "src/assets/sets/enchanted_wilds")
    assert official.review is not None
    review = official.review.model_copy(update={"reject_locale_markup": False})
    assert verify_review_policy(replace(official, review=review)) == []

    sample = load_set_directory(project_root / "src/assets/sets/sample_set")
    assert verify_review_policy(sample) == ["Set package does not declare a review policy"]


def test_review_policy_reports_invalid_png_structures(project_root: Path, tmp_path: Path) -> None:
    source = project_root / "src/assets/sets/enchanted_wilds"
    root = tmp_path / "enchanted_wilds"
    shutil.copytree(source, root)
    loaded = load_set_directory(root)
    assets = root / loaded.manifest.assets_dir / "items"

    (assets / "directory.png").mkdir()
    (assets / "da_adaptivehelm.png").write_bytes(b"not-a-png")
    (assets / "da_bloodthirster.png").write_bytes(
        b"\x89PNG\r\n\x1a\n" + (b"\x00" * 8) + (b"\x00" * 4) + b"\x00\x00\x00\x01"
    )

    issues = verify_review_policy(loaded)
    joined = "\n".join(issues)

    assert "runtime asset is not a structurally valid PNG" in joined
    assert "runtime PNG has invalid dimensions" in joined


def test_review_report_handles_set_without_items(project_root: Path) -> None:
    loaded = load_set_directory(project_root / "src/assets/sets/sample_set")

    report = render_set_review(replace(loaded, items=()))

    assert "No components are defined for this Set." in report
    assert "No Radiant items are defined for this Set." in report


def test_review_report_covers_every_runtime_entity_and_image(project_root: Path) -> None:
    loaded = load_set_directory(project_root / "src/assets/sets/enchanted_wilds")
    catalog = loaded.locales[loaded.manifest.default_locale]

    report = render_set_review(loaded)

    for champion in loaded.champions:
        assert catalog[champion.name_key] in report
        assert champion.image in report
    for trait in loaded.traits:
        assert catalog[trait.name_key] in report
        assert trait.icon in report
    for item in loaded.items:
        assert catalog[item.name_key] in report
        assert item.icon in report
