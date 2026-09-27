from __future__ import annotations

import pytest
from pydantic import ValidationError

from tft_builder.set_schema import (
    ChampionDefinition,
    DynamicSelectionRule,
    DynamicTraitDefinition,
    SetManifest,
    SourceManifest,
    TeamPlannerData,
    TraitBreakpoint,
    TraitDefinition,
    validate_relative_path,
)


def valid_manifest_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "set_id": "sample_set",
        "display_name_key": "set.sample.name",
        "revision": "1.0.0",
        "default_locale": "en",
        "supported_locales": ["en"],
        "champions_file": "data/champions.json",
        "traits_file": "data/traits.json",
        "dynamic_traits_file": "data/dynamic_traits.json",
        "team_planner_file": "data/team_planner.json",
        "source_manifest_file": "source_manifest.json",
        "locales_dir": "locales",
        "assets_dir": "assets",
        "team_planner_supported": False,
    }


@pytest.mark.parametrize(
    "value",
    [
        "data/champions.json",
        "assets/champions/a.png",
        "source_manifest.json",
        "locales",
    ],
)
def test_validate_relative_path_accepts_safe_posix_paths(value: str) -> None:
    assert validate_relative_path(value) == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "/absolute/path.json",
        "../escape.json",
        "data/../escape.json",
        "data\\windows.json",
        "./data.json",
        "data//champions.json",
        "data/",
    ],
)
def test_validate_relative_path_rejects_unsafe_paths(value: str) -> None:
    with pytest.raises(ValueError):
        validate_relative_path(value)


def test_manifest_accepts_default_locale_in_supported_locales() -> None:
    manifest = SetManifest.model_validate(valid_manifest_payload())
    assert manifest.default_locale == "en"


def test_manifest_rejects_default_locale_not_supported() -> None:
    payload = valid_manifest_payload()
    payload["default_locale"] = "de"
    with pytest.raises(ValidationError, match="default_locale"):
        SetManifest.model_validate(payload)


def test_manifest_rejects_duplicate_locales() -> None:
    payload = valid_manifest_payload()
    payload["supported_locales"] = ["en", "en"]
    with pytest.raises(ValidationError, match="duplicates"):
        SetManifest.model_validate(payload)


def test_manifest_rejects_unknown_fields() -> None:
    payload = valid_manifest_payload()
    payload["unexpected"] = True
    with pytest.raises(ValidationError, match="Extra inputs"):
        SetManifest.model_validate(payload)


def test_manifest_rejects_unsupported_schema_version() -> None:
    payload = valid_manifest_payload()
    payload["schema_version"] = 2
    with pytest.raises(ValidationError):
        SetManifest.model_validate(payload)


def test_champion_cost_has_no_hardcoded_upper_limit() -> None:
    champion = ChampionDefinition(
        id="champion_10_cost",
        name_key="champion.10.name",
        cost=10,
        traits=["trait_a"],
        image="assets/champions/a.png",
        display_order=1,
    )
    assert champion.cost == 10


def test_champion_rejects_negative_cost() -> None:
    with pytest.raises(ValidationError):
        ChampionDefinition(
            id="champion_a",
            name_key="champion.a.name",
            cost=-1,
            traits=[],
            image="assets/champions/a.png",
            display_order=1,
        )


def test_champion_rejects_duplicate_native_traits() -> None:
    with pytest.raises(ValidationError, match="duplicates"):
        ChampionDefinition(
            id="champion_a",
            name_key="champion.a.name",
            cost=1,
            traits=["trait_a", "trait_a"],
            image="assets/champions/a.png",
            display_order=1,
        )


def test_champion_rejects_duplicate_search_aliases() -> None:
    with pytest.raises(ValidationError, match="duplicates"):
        ChampionDefinition(
            id="champion_a",
            name_key="champion.a.name",
            cost=1,
            traits=[],
            image="assets/champions/a.png",
            display_order=1,
            search_aliases=["a", "a"],
        )


def test_champion_rejects_blank_search_alias() -> None:
    with pytest.raises(ValidationError, match="empty"):
        ChampionDefinition(
            id="champion_a",
            name_key="champion.a.name",
            cost=1,
            traits=[],
            image="assets/champions/a.png",
            display_order=1,
            search_aliases=["  "],
        )


def test_trait_requires_at_least_one_breakpoint() -> None:
    with pytest.raises(ValidationError):
        TraitDefinition(
            id="trait_a",
            name_key="trait.a.name",
            icon="assets/traits/a.png",
            display_order=1,
            breakpoints=[],
        )


def test_trait_breakpoints_must_be_strictly_increasing() -> None:
    with pytest.raises(ValidationError, match="strictly increasing"):
        TraitDefinition(
            id="trait_a",
            name_key="trait.a.name",
            icon="assets/traits/a.png",
            display_order=1,
            breakpoints=[TraitBreakpoint(count=4, style="silver"), TraitBreakpoint(count=2, style="bronze")],
        )


def test_trait_breakpoints_reject_duplicate_count() -> None:
    with pytest.raises(ValidationError, match="strictly increasing"):
        TraitDefinition(
            id="trait_a",
            name_key="trait.a.name",
            icon="assets/traits/a.png",
            display_order=1,
            breakpoints=[TraitBreakpoint(count=2, style="bronze"), TraitBreakpoint(count=2, style="silver")],
        )


def test_dynamic_none_rejects_choices() -> None:
    with pytest.raises(ValidationError, match="must not define"):
        DynamicTraitDefinition(
            champion_id="champion_a",
            selection_rule="NONE",
            choices=["trait_a"],
        )


@pytest.mark.parametrize("rule", ["EXACTLY_ONE", "ZERO_OR_ONE", "ANY_NUMBER"])
def test_dynamic_choice_rules_require_at_least_one_choice(rule: str) -> None:
    with pytest.raises(ValidationError, match="at least one"):
        DynamicTraitDefinition(champion_id="champion_a", selection_rule=rule, choices=[])


def test_dynamic_exactly_n_requires_exact_count() -> None:
    with pytest.raises(ValidationError, match="requires exact_count"):
        DynamicTraitDefinition(
            champion_id="champion_a",
            selection_rule="EXACTLY_N",
            choices=["trait_a", "trait_b"],
        )


@pytest.mark.parametrize("exact_count", [0, 3])
def test_dynamic_exactly_n_rejects_out_of_range_count(exact_count: int) -> None:
    with pytest.raises(ValidationError, match="between 1"):
        DynamicTraitDefinition(
            champion_id="champion_a",
            selection_rule="EXACTLY_N",
            choices=["trait_a", "trait_b"],
            exact_count=exact_count,
        )


def test_dynamic_exactly_n_accepts_valid_count() -> None:
    rule = DynamicTraitDefinition(
        champion_id="champion_a",
        selection_rule="EXACTLY_N",
        choices=["trait_a", "trait_b"],
        exact_count=2,
    )
    assert rule.exact_count == 2
    assert rule.selection_rule is DynamicSelectionRule.EXACTLY_N


def test_dynamic_non_exactly_n_rejects_exact_count() -> None:
    with pytest.raises(ValidationError, match="only valid"):
        DynamicTraitDefinition(
            champion_id="champion_a",
            selection_rule="EXACTLY_ONE",
            choices=["trait_a"],
            exact_count=1,
        )


def test_dynamic_choices_must_be_unique() -> None:
    with pytest.raises(ValidationError, match="duplicates"):
        DynamicTraitDefinition(
            champion_id="champion_a",
            selection_rule="ANY_NUMBER",
            choices=["trait_a", "trait_a"],
        )


def test_team_planner_without_codec_rejects_mapping() -> None:
    with pytest.raises(ValidationError, match="require"):
        TeamPlannerData(codec=None, champion_ids={"champion_a": "123"})


def test_team_planner_with_codec_accepts_mapping() -> None:
    data = TeamPlannerData(codec="riot_v1", champion_ids={"champion_a": "123"})
    assert data.champion_ids["champion_a"] == "123"


def test_source_manifest_rejects_invalid_sha256() -> None:
    with pytest.raises(ValidationError):
        SourceManifest(
            schema_version=1,
            source_type="local_spec",
            source_sha256="abc",
            generated_file_sha256={},
            asset_sha256={},
        )
