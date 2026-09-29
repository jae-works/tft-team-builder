from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
from PIL import Image


def load_importer():
    path = Path(__file__).resolve().parents[1] / "tools/set_import/import_cdragon_set.py"
    spec = importlib.util.spec_from_file_location("set18_importer", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def importer():
    return load_importer()


def test_retained_item_categories_select_reviewed_families_and_keep_recipe_graph(importer) -> None:
    source_set = {
        "items": [
            "DA_Component_A",
            "DA_Normal",
            "DA_18_EmblemX",
            "DA_Radiant",
            "DA_Artifact_X",
            "legacy_artifact",
            "wisp",
        ]
    }
    all_items = {
        "DA_Component_A": {"apiName": "DA_Component_A", "tags": ["component"]},
        "DA_Normal": {"apiName": "DA_Normal", "composition": ["DA_Component_A", "DA_Component_A"]},
        "DA_18_EmblemX": {"apiName": "DA_18_EmblemX", "composition": ["DA_Component_A"]},
        "DA_Radiant": {"apiName": "DA_Radiant", "tags": ["radiant-tag"]},
        "DA_Artifact_X": {"apiName": "DA_Artifact_X"},
        "legacy_artifact": {"apiName": "legacy_artifact"},
        "wisp": {"apiName": "wisp"},
    }
    policy = {
        "component_prefix": "DA_Component_",
        "craftable_prefix": "DA_",
        "emblem_prefix": "DA_18_Emblem",
        "artifact_prefixes": ["DA_Artifact_"],
        "radiant_prefix": "DA_",
        "radiant_tag": "radiant-tag",
        "explicit_ids": {"ARTIFACT": ["legacy_artifact"]},
        "exclude_ids": [],
    }
    assert importer._retained_item_categories(source_set, all_items, policy) == {
        "DA_Component_A": "COMPONENT",
        "DA_Normal": "CRAFTABLE",
        "DA_18_EmblemX": "EMBLEM",
        "DA_Radiant": "RADIANT",
        "DA_Artifact_X": "ARTIFACT",
        "legacy_artifact": "ARTIFACT",
    }


def test_retained_item_categories_rejects_missing_or_incoherent_policy(importer) -> None:
    policy = {
        "component_prefix": "DA_Component_",
        "craftable_prefix": "DA_",
        "emblem_prefix": "DA_18_Emblem",
        "artifact_prefixes": ["DA_Artifact_"],
        "radiant_prefix": "DA_",
        "radiant_tag": "radiant-tag",
        "explicit_ids": {},
        "exclude_ids": [],
    }
    with pytest.raises(ValueError, match="missing from CommunityDragon"):
        importer._retained_item_categories({"items": ["missing"]}, {}, policy)

    all_items = {
        "DA_Normal": {"apiName": "DA_Normal", "composition": ["legacy_component"]},
        "legacy_component": {"apiName": "legacy_component"},
    }
    with pytest.raises(ValueError, match="non-retained component"):
        importer._retained_item_categories(
            {"items": list(all_items)}, all_items, policy
        )

    policy["explicit_ids"] = {"ARTIFACT": ["missing"]}
    with pytest.raises(ValueError, match="explicit retained Item IDs"):
        importer._retained_item_categories({"items": ["DA_Normal"]}, {"DA_Normal": {}}, policy)

    policy["explicit_ids"] = {}
    policy["exclude_ids"] = ["missing"]
    with pytest.raises(ValueError, match="explicit excluded Item IDs"):
        importer._retained_item_categories({"items": ["DA_Normal"]}, {"DA_Normal": {}}, policy)


def test_item_category_count_guard_detects_exact_inventory_drift(importer) -> None:
    categories = {"a": "COMPONENT", "b": "ARTIFACT", "c": "ARTIFACT"}
    importer._require_item_category_counts(categories, {"COMPONENT": 1, "ARTIFACT": 2})
    with pytest.raises(ValueError, match="category counts differ"):
        importer._require_item_category_counts(categories, {"COMPONENT": 1, "ARTIFACT": 1})


def test_expected_count_guard_accepts_exact_value_and_rejects_drift(importer) -> None:
    importer._require_expected_count("records", 3, 3)
    importer._require_expected_count("records", 3, None)
    with pytest.raises(ValueError, match="expected 4 records; got 3"):
        importer._require_expected_count("records", 3, 4)


def test_variant_records_report_all_missing_ids_and_validate_image_source(importer) -> None:
    raw = {
        "base": {"apiName": "base", "cost": 5},
        "variant": {"apiName": "variant", "cost": 5},
    }
    group = {
        "target_id": "logical",
        "source_ids": ["base", "missing_a", "missing_b"],
        "image_source_id": "base",
    }
    with pytest.raises(ValueError, match="missing_a, missing_b"):
        importer._variant_records(group, raw)

    group["source_ids"] = ["base", "variant"]
    group["image_source_id"] = "other"
    with pytest.raises(ValueError, match="image_source_id"):
        importer._variant_records(group, raw)


def test_variant_records_reject_mixed_costs(importer) -> None:
    raw = {
        "base": {"apiName": "base", "cost": 5},
        "variant": {"apiName": "variant", "cost": 4},
    }
    group = {
        "target_id": "logical",
        "source_ids": ["base", "variant"],
        "image_source_id": "base",
    }
    with pytest.raises(ValueError, match="inconsistent Champion costs"):
        importer._variant_records(group, raw)


def test_enchanted_wilds_source_config_matches_reviewed_set18_ids(project_root) -> None:
    import json

    config = json.loads(
        (project_root / "set_sources/sets/enchanted_wilds/source.json").read_text(encoding="ascii")
    )
    group = config["variant_groups"][0]

    assert config["expected_source_champions"] == 91
    assert config["expected_logical_champions"] == 65
    assert config["revision"] == "18.3b"
    assert config["localized_display_names"] == {
        "en_US": "Enchanted Wilds",
        "de_DE": "Verzauberte Wildnis",
    }
    assert config["expected_traits"] == 36
    assert config["trait_variable_override_sources"]["riot_patch_18_3"]["published"] == "2026-09-22"
    assert config["trait_variable_overrides_by_name"]["Hunter"]["breakpoints"]["5"]["HunterAD"] == 0.6
    assert config["expected_items_by_category"] == {
        "COMPONENT": 10,
        "CRAFTABLE": 39,
        "EMBLEM": 20,
        "ARTIFACT": 31,
        "RADIANT": 36,
    }
    assert config["item_retention"]["explicit_ids"]["ARTIFACT"] == [
        "TFT4_Item_OrnnDeathsDefiance"
    ]
    assert config["item_retention"]["exclude_ids"] == [
        "DA_18_EmblemFloraFatalisAugment"
    ]
    assert len(config["exclude_champions"]) == 17
    assert group["target_id"] == "DA_Lux18_Base"
    assert group["image_source_id"] == "DA_Lux18_Base"
    assert len(group["source_ids"]) == 10
    assert "DA_Lux18_Blackthorn" in group["source_ids"]
    assert "DA_18_Lux_Moonbeam" in group["source_ids"]
    assert config["dynamic_traits"][0]["champion_id"] == "DA_18_KhaZix"
    assert "DA_18_ElderDragon" in config["champion_adjustments"]




def test_dd_data_indexes_archive_records_by_stable_id_and_rejects_malformed_payloads(importer) -> None:
    payload = {
        "data": {
            "archive/path/a": {"id": "stable_a", "name": "A"},
            "archive/path/b": {"id": "stable_b", "name": "B"},
        }
    }
    assert importer._dd_data(payload) == {
        "stable_a": {"id": "stable_a", "name": "A"},
        "stable_b": {"id": "stable_b", "name": "B"},
    }

    with pytest.raises(ValueError, match="no data object"):
        importer._dd_data({"data": []})
    with pytest.raises(ValueError, match="has no stable id"):
        importer._dd_data({"data": {"bad": {}}})
    with pytest.raises(ValueError, match="has no stable id"):
        importer._dd_data({"data": {"bad": None}})
    with pytest.raises(ValueError, match="duplicate record id"):
        importer._dd_data(
            {"data": {"a": {"id": "same"}, "b": {"id": "same"}}}
        )


def test_dd_sprite_url_requires_complete_sprite_metadata(importer) -> None:
    record = {
        "id": "unit",
        "image": {
            "group": "tft-champion",
            "sprite": "tft-champion10.png",
            "x": 0,
            "y": 0,
            "w": 48,
            "h": 48,
        },
    }
    source_id, url = importer._dd_sprite_url("16.19.1", record)
    assert source_id == "ddragon_sprite_tft_champion_tft_champion10_png"
    assert url.endswith("/16.19.1/img/sprite/tft-champion10.png")

    with pytest.raises(ValueError, match="no sprite metadata"):
        importer._dd_sprite_url("16.19.1", {"id": "unit", "image": {}})
    with pytest.raises(ValueError, match="no sprite metadata"):
        importer._dd_sprite_url(
            "16.19.1", {"id": "unit", "image": {"group": "tft-champion"}}
        )


def test_append_source_once_deduplicates_identical_sources_and_rejects_collision(importer) -> None:
    record = {
        "id": "source",
        "url": "https://example.invalid/a",
        "revision": "1",
        "locale": None,
        "sha256": "0" * 64,
        "byte_length": 1,
    }
    sources = []
    importer._append_source_once(sources, record)
    importer._append_source_once(sources, dict(record))
    assert sources == [record]

    changed = dict(record)
    changed["sha256"] = "1" * 64
    with pytest.raises(ValueError, match="inconsistent metadata"):
        importer._append_source_once(sources, changed)


def test_dd_sprite_asset_crops_shared_sheet_and_records_provenance_once(
    importer, tmp_path, monkeypatch
) -> None:
    sprite = tmp_path / "sprite.png"
    image = Image.new("RGB", (96, 48))
    for x in range(48, 96):
        for y in range(48):
            image.putpixel((x, y), (255, 255, 255))
    image.save(sprite, format="PNG")

    monkeypatch.setattr(importer, "_download", lambda *_args: sprite)
    sources = []
    first = {
        "id": "first",
        "image": {
            "group": "tft-item",
            "sprite": "sheet.png",
            "x": 0,
            "y": 0,
            "w": 48,
            "h": 48,
        },
    }
    second = {
        "id": "second",
        "image": {**first["image"], "x": 48},
    }
    importer._dd_sprite_asset(
        object(), tmp_path, tmp_path, sources, "16.19.1", first, "assets/first.png"
    )
    importer._dd_sprite_asset(
        object(), tmp_path, tmp_path, sources, "16.19.1", second, "assets/second.png"
    )

    assert len(sources) == 1
    with Image.open(tmp_path / "assets/first.png") as first_output:
        assert first_output.size == (48, 48)
        assert first_output.getpixel((0, 0)) == (0, 0, 0)
    with Image.open(tmp_path / "assets/second.png") as second_output:
        assert second_output.size == (48, 48)
        assert second_output.getpixel((0, 0)) == (255, 255, 255)


def test_dd_sprite_asset_rejects_invalid_png_metadata_and_bounds(
    importer, tmp_path, monkeypatch
) -> None:
    bad = tmp_path / "bad.bin"
    bad.write_bytes(b"not a png")
    monkeypatch.setattr(importer, "_download", lambda *_args: bad)
    record = {
        "id": "unit",
        "image": {
            "group": "tft-item",
            "sprite": "sheet.png",
            "x": 0,
            "y": 0,
            "w": 48,
            "h": 48,
        },
    }
    with pytest.raises(ValueError, match="not a PNG"):
        importer._dd_sprite_asset(
            object(), tmp_path, tmp_path, [], "16.19.1", record, "asset.png"
        )

    sprite = tmp_path / "sprite.png"
    Image.new("RGB", (48, 48)).save(sprite, format="PNG")
    monkeypatch.setattr(importer, "_download", lambda *_args: sprite)

    missing_bounds = {"id": "unit", "image": {"group": "x", "sprite": "sheet.png"}}
    with pytest.raises(ValueError, match="invalid sprite bounds"):
        importer._dd_sprite_asset(
            object(), tmp_path, tmp_path, [], "16.19.1", missing_bounds, "asset.png"
        )

    for field, value in (("x", -1), ("y", -1), ("w", 0), ("h", 0)):
        invalid = {"id": "unit", "image": dict(record["image"])}
        invalid["image"][field] = value
        with pytest.raises(ValueError, match="invalid sprite bounds"):
            importer._dd_sprite_asset(
                object(), tmp_path, tmp_path, [], "16.19.1", invalid, "asset.png"
            )

    too_wide = {"id": "unit", "image": {**record["image"], "x": 1}}
    with pytest.raises(ValueError, match="exceeds sprite bounds"):
        importer._dd_sprite_asset(
            object(), tmp_path, tmp_path, [], "16.19.1", too_wide, "asset.png"
        )
    too_tall = {"id": "unit", "image": {**record["image"], "y": 1}}
    with pytest.raises(ValueError, match="exceeds sprite bounds"):
        importer._dd_sprite_asset(
            object(), tmp_path, tmp_path, [], "16.19.1", too_tall, "asset.png"
        )

def test_fnv1a_32_matches_known_communitydragon_bin_field_hashes(importer) -> None:
    assert importer._fnv1a_32("BonusDamagePercentBase") == "a9a813e7"
    assert importer._fnv1a_32("InvokerManaBonus") == "de27cb95"
    assert importer._fnv1a_32("EclipseBeamPeriod") == "53db05e8"


def test_trait_template_resolves_hashed_variables_markup_and_patch_override(importer) -> None:
    effect = {
        "variables": {
            "{641254b6}": 0.45,
            "DamageAmp": 0.1,
        }
    }
    text = importer._render_trait_template(
        "(@MinUnits@) @HunterAD*100@% %i:scaleAD% / @DamageAmp*100@%",
        effect,
        count=4,
        overrides={"HunterAD": 0.4},
    )
    assert text == "(4) 40% AD / 10%"


def test_trait_template_localizes_stat_markers_and_hides_float_noise(importer) -> None:
    text = importer._render_trait_template(
        "@Armor@ %i:scaleArmor%%i:scaleMR% / @AttackSpeed*100@% %i:scaleAS%",
        {"variables": {"Armor": 14.999998, "AttackSpeed": 0.29999995}},
        count=None,
        locale="de_DE",
    )
    assert text == "15 R\u00fcstung und Magieresistenz / 30% Angriffstempo"


def test_item_description_resolves_effect_variables_and_markup(importer) -> None:
    item = {
        "desc": (
            "@IgnorePainPercent@% over @BleedDuration@ seconds.<br>"
            "<tftitemrules>[Unique]</tftitemrules>"
        ),
        "effects": {"IgnorePainPercent": 50, "BleedDuration": 4},
    }
    assert importer._render_item_description(item, locale="en_US") == (
        "50% over 4 seconds.\n[Unique]"
    )
    assert importer._render_item_description({"desc": ""}, locale="en_US") == ""


def test_trait_display_texts_separates_summary_and_breakpoints(importer) -> None:
    trait = {
        "desc": (
            "Team summary @Shared@.<br>"
            "<row>(@MinUnits@) @Value@ %i:scaleAD%</row>"
            "<row>(@MinUnits@) @Value@ %i:scaleAD%</row>"
        ),
        "effects": [
            {"minUnits": 2, "variables": {"Shared": 5, "Value": 10}},
            {"minUnits": 4, "variables": {"Shared": 5, "Value": 20}},
        ],
    }
    summary, breakpoints = importer._trait_display_texts(
        trait,
        [{"count": 2, "style": "tier_1"}, {"count": 4, "style": "tier_2"}],
        {"4": {"Value": 25}},
    )
    assert summary == "Team summary 5."
    assert breakpoints == {2: "10 AD", 4: "25 AD"}


def test_trait_display_texts_keeps_last_duplicate_source_row_and_skips_empty_rows(importer) -> None:
    trait = {
        "desc": "<row>(@MinUnits@) old</row><row>(@MinUnits@) current</row>",
        "effects": [
            {"minUnits": 1, "variables": {}},
            {"minUnits": 1, "variables": {}},
        ],
    }
    summary, breakpoints = importer._trait_display_texts(
        trait, [{"count": 1, "style": "tier_1"}], {}
    )
    assert summary == "current"
    assert breakpoints == {1: "current"}

    empty_trait = {
        "desc": "Choose a blessing.<br><row>(@MinUnits@)</row>",
        "effects": [{"minUnits": 2, "variables": {}}],
    }
    summary, breakpoints = importer._trait_display_texts(
        empty_trait, [{"count": 2, "style": "tier_1"}], {}
    )
    assert summary == "Choose a blessing."
    assert breakpoints == {}


def test_trait_variable_overrides_require_reviewed_source_reason_and_known_breakpoint(importer) -> None:
    config = {
        "trait_variable_override_sources": {"patch": {"label": "Patch"}},
        "trait_variable_overrides_by_name": {
            "Trait": {
                "source": "patch",
                "reason": "Balance update.",
                "breakpoints": {"2": {"Value": 12}},
            }
        },
    }
    assert importer._trait_variable_overrides(config, "Trait", {"2"}) == {
        "2": {"Value": 12}
    }
    assert importer._trait_variable_overrides(config, "Other", {"2"}) == {}

    config["trait_variable_overrides_by_name"]["Trait"]["source"] = "missing"
    with pytest.raises(ValueError, match="unknown source"):
        importer._trait_variable_overrides(config, "Trait", {"2"})

    config["trait_variable_overrides_by_name"]["Trait"]["source"] = "patch"
    config["trait_variable_overrides_by_name"]["Trait"]["reason"] = " "
    with pytest.raises(ValueError, match="requires a reason"):
        importer._trait_variable_overrides(config, "Trait", {"2"})

    config["trait_variable_overrides_by_name"]["Trait"]["reason"] = "Balance update."
    with pytest.raises(ValueError, match="unknown breakpoints"):
        importer._trait_variable_overrides(config, "Trait", {"3"})
