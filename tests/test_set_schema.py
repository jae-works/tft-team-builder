from __future__ import annotations

import pytest
from pydantic import ValidationError

from tft_builder.set_schema import (
    ChampionDefinition,
    DynamicSelectionRule,
    DynamicTraitDefinition,
    LocalSetSpec,
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
            breakpoints=[
                TraitBreakpoint(count=4, style="silver"),
                TraitBreakpoint(count=2, style="bronze"),
            ],
        )


def test_trait_breakpoints_reject_duplicate_count() -> None:
    with pytest.raises(ValidationError, match="strictly increasing"):
        TraitDefinition(
            id="trait_a",
            name_key="trait.a.name",
            icon="assets/traits/a.png",
            display_order=1,
            breakpoints=[
                TraitBreakpoint(count=2, style="bronze"),
                TraitBreakpoint(count=2, style="silver"),
            ],
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


def test_champion_cost_rejects_numeric_string_coercion() -> None:
    with pytest.raises(ValidationError):
        ChampionDefinition.model_validate(
            {
                "id": "champion_a",
                "name_key": "champion.a.name",
                "cost": "1",
                "traits": [],
                "image": "assets/champions/a.png",
                "display_order": 1,
            }
        )


def test_trait_breakpoint_count_rejects_numeric_string_coercion() -> None:
    with pytest.raises(ValidationError):
        TraitBreakpoint.model_validate({"count": "2", "style": "bronze"})


def test_manifest_boolean_rejects_string_coercion() -> None:
    payload = valid_manifest_payload()
    payload["team_planner_supported"] = "false"
    with pytest.raises(ValidationError):
        SetManifest.model_validate(payload)


def test_display_order_rejects_numeric_string_coercion() -> None:
    with pytest.raises(ValidationError):
        TraitDefinition.model_validate(
            {
                "id": "trait_a",
                "name_key": "trait.a.name",
                "icon": "assets/traits/a.png",
                "display_order": "1",
                "breakpoints": [{"count": 2, "style": "bronze"}],
            }
        )


def test_manifest_rejects_duplicate_metadata_file_paths() -> None:
    payload = valid_manifest_payload()
    payload["traits_file"] = payload["champions_file"]
    with pytest.raises(ValidationError, match="metadata file paths must not overlap"):
        SetManifest.model_validate(payload)


def test_manifest_rejects_overlapping_assets_and_locales_directories() -> None:
    payload = valid_manifest_payload()
    payload["locales_dir"] = "assets/locales"
    with pytest.raises(ValidationError, match="must not overlap"):
        SetManifest.model_validate(payload)


def test_manifest_rejects_metadata_file_inside_assets_directory() -> None:
    payload = valid_manifest_payload()
    payload["champions_file"] = "assets/champions.json"
    with pytest.raises(ValidationError, match="must not overlap assets_dir"):
        SetManifest.model_validate(payload)


def test_local_set_spec_requires_exact_supported_locale_inventory() -> None:
    payload = {
        "schema_version": 1,
        "manifest": valid_manifest_payload(),
        "champions": [],
        "traits": [],
        "locales": {},
        "assets": {},
    }
    with pytest.raises(ValidationError, match="locale inventory"):
        LocalSetSpec.model_validate(payload)


def test_dynamic_none_without_choices_is_valid() -> None:
    rule = DynamicTraitDefinition(champion_id="champion_a", selection_rule="NONE")
    assert rule.selection_rule is DynamicSelectionRule.NONE
    assert rule.choices == []


def test_team_planner_rejects_blank_mapping_value() -> None:
    with pytest.raises(ValidationError, match="at least 1 character"):
        TeamPlannerData(codec="riot_v1", champion_ids={"champion_a": "   "})


def test_manifest_rejects_metadata_file_inside_locales_directory() -> None:
    payload = valid_manifest_payload()
    payload["champions_file"] = "locales/champions.json"
    with pytest.raises(ValidationError, match="must not overlap locales_dir"):
        SetManifest.model_validate(payload)


def valid_local_spec_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "manifest": valid_manifest_payload(),
        "champions": [
            {
                "id": "champion_a",
                "name_key": "champion.a.name",
                "cost": 1,
                "traits": ["trait_a"],
                "image": "assets/champions/a.png",
                "display_order": 0,
            }
        ],
        "traits": [
            {
                "id": "trait_a",
                "name_key": "trait.a.name",
                "icon": "assets/traits/a.png",
                "display_order": 0,
                "breakpoints": [{"count": 1, "style": "bronze"}],
            }
        ],
        "locales": {
            "en": {
                "set.sample.name": "Sample",
                "champion.a.name": "A",
                "trait.a.name": "Trait A",
            }
        },
        "assets": {
            "assets/champions/a.png": "assets/champions/a.png",
            "assets/traits/a.png": "assets/traits/a.png",
        },
    }


def test_champion_rejects_negative_display_order() -> None:
    with pytest.raises(ValidationError):
        ChampionDefinition(
            id="champion_a",
            name_key="champion.a.name",
            cost=1,
            traits=[],
            image="assets/champions/a.png",
            display_order=-1,
        )


def test_trait_rejects_negative_display_order() -> None:
    with pytest.raises(ValidationError):
        TraitDefinition(
            id="trait_a",
            name_key="trait.a.name",
            icon="assets/traits/a.png",
            display_order=-1,
            breakpoints=[TraitBreakpoint(count=1, style="bronze")],
        )


def test_manifest_rejects_metadata_file_that_is_parent_of_another_metadata_file() -> None:
    payload = valid_manifest_payload()
    payload["champions_file"] = "data"
    with pytest.raises(ValidationError, match="metadata file paths must not overlap"):
        SetManifest.model_validate(payload)


def test_manifest_rejects_configured_file_colliding_with_fixed_manifest() -> None:
    payload = valid_manifest_payload()
    payload["champions_file"] = "manifest.json"
    with pytest.raises(ValidationError, match="metadata file paths must not overlap"):
        SetManifest.model_validate(payload)


def test_manifest_rejects_assets_directory_below_metadata_file_path() -> None:
    payload = valid_manifest_payload()
    payload["assets_dir"] = "manifest.json/assets"
    with pytest.raises(ValidationError, match="must not overlap assets_dir"):
        SetManifest.model_validate(payload)


def test_local_set_spec_requires_asset_targets_under_assets_directory() -> None:
    payload = valid_local_spec_payload()
    payload["assets"]["outside.png"] = payload["assets"].pop("assets/champions/a.png")
    with pytest.raises(ValidationError, match="stored under assets_dir"):
        LocalSetSpec.model_validate(payload)


def test_local_set_spec_rejects_overlapping_asset_file_paths() -> None:
    payload = valid_local_spec_payload()
    payload["assets"]["assets/nested"] = "assets/champions/a.png"
    payload["assets"]["assets/nested/file.png"] = "assets/traits/a.png"
    with pytest.raises(ValidationError, match="asset file paths must not overlap"):
        LocalSetSpec.model_validate(payload)


def test_local_set_spec_requires_mapping_for_every_referenced_asset() -> None:
    payload = valid_local_spec_payload()
    payload["assets"].pop("assets/champions/a.png")
    with pytest.raises(ValidationError, match="no asset mapping"):
        LocalSetSpec.model_validate(payload)


def test_local_set_spec_rejects_unreferenced_asset_mapping() -> None:
    payload = valid_local_spec_payload()
    payload["assets"]["assets/extra/background.png"] = "assets/traits/a.png"
    with pytest.raises(ValidationError, match="unreferenced runtime assets"):
        LocalSetSpec.model_validate(payload)


@pytest.mark.parametrize(
    "value",
    [
        "data/file name.json",
        "data/file:name.json",
        "data/.hidden.json",
        "data/CON.json",
        "data/con.txt",
        "data/COM1.bin",
        "data/Lpt9.dat",
        "data/uber.json",
    ],
)
def test_validate_relative_path_rejects_nonportable_components(value: str) -> None:
    if value == "data/uber.json":
        value = "data/\N{LATIN SMALL LETTER U WITH DIAERESIS}ber.json"
    with pytest.raises(ValueError):
        validate_relative_path(value)


def test_validate_relative_path_accepts_portable_filename_characters() -> None:
    value = "assets/champions/unit_name-v2.1.png"
    assert validate_relative_path(value) == value


def test_team_planner_rejects_duplicate_external_ids() -> None:
    with pytest.raises(ValidationError, match="must be unique"):
        TeamPlannerData(
            codec="riot_v1",
            champion_ids={"champion_a": "123", "champion_b": "123"},
        )


def test_local_set_spec_rejects_missing_required_translation() -> None:
    payload = valid_local_spec_payload()
    del payload["locales"]["en"]["champion.a.name"]
    with pytest.raises(ValidationError, match="missing required translation keys"):
        LocalSetSpec.model_validate(payload)


def test_local_set_spec_rejects_unexpected_locale() -> None:
    payload = valid_local_spec_payload()
    payload["locales"]["de"] = dict(payload["locales"]["en"])
    with pytest.raises(ValidationError, match="locale inventory"):
        LocalSetSpec.model_validate(payload)
