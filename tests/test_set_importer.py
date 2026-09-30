from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


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
        importer._retained_item_categories({"items": list(all_items)}, all_items, policy)

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
    assert (
        config["trait_variable_overrides_by_name"]["Hunter"]["breakpoints"]["5"]["HunterAD"] == 0.6
    )
    assert config["expected_items_by_category"] == {
        "COMPONENT": 10,
        "CRAFTABLE": 39,
        "EMBLEM": 20,
        "ARTIFACT": 31,
        "RADIANT": 36,
    }
    assert config["item_retention"]["explicit_ids"]["ARTIFACT"] == ["TFT4_Item_OrnnDeathsDefiance"]
    assert config["item_retention"]["exclude_ids"] == ["DA_18_EmblemFloraFatalisAugment"]
    assert len(config["exclude_champions"]) == 17
    assert group["target_id"] == "DA_Lux18_Base"
    assert group["image_source_id"] == "DA_Lux18_Base"
    assert group["selection_scope"] == "PER_CHAMPION"
    assert len(group["source_ids"]) == 10
    assert "DA_Lux18_Blackthorn" in group["source_ids"]
    assert "DA_18_Lux_Moonbeam" in group["source_ids"]
    assert config["dynamic_traits"][0]["champion_id"] == "DA_18_KhaZix"
    assert config["dynamic_traits"][0]["selection_rule"] == "ANY_NUMBER"
    assert config["review"]["expected_set_id"] == "enchanted_wilds"
    assert config["review"]["dynamic_trait_expectations"][1]["selection_rule"] == "ANY_NUMBER"
    assert config["review"]["allowed_duplicate_asset_groups"] == [[
        "assets/items/da_spiritvisage.png",
        "assets/items/da_spiritvisage_radiant.png",
    ]]
    assert "DA_18_ElderDragon" in config["champion_adjustments"]


def test_dd_data_indexes_archive_records_by_stable_id_and_rejects_malformed_payloads(
    importer,
) -> None:
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
        importer._dd_data({"data": {"a": {"id": "same"}, "b": {"id": "same"}}})


def test_dd_asset_url_requires_full_image_metadata_and_uses_individual_asset(importer) -> None:
    record = {
        "id": "unit",
        "image": {
            "full": "Unit Name.TFT_Set18.png",
            "group": "tft-champion",
            "sprite": "tft-champion10.png",
            "x": 9999,
            "y": 9999,
            "w": 48,
            "h": 48,
        },
    }
    source_id, url = importer._dd_asset_url("16.19.1", record)
    assert source_id.startswith("ddragon_asset_tft_champion_unit_name_tft_set18_png_")
    assert url.endswith("/16.19.1/img/tft-champion/Unit%20Name.TFT_Set18.png")

    with pytest.raises(ValueError, match="no full image metadata"):
        importer._dd_asset_url("16.19.1", {"id": "unit", "image": {}})
    with pytest.raises(ValueError, match="no full image metadata"):
        importer._dd_asset_url("16.19.1", {"id": "unit", "image": {"group": "tft-champion"}})


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


def test_dd_full_asset_copies_individual_png_and_deduplicates_shared_source(
    importer, tmp_path, monkeypatch
) -> None:
    source = tmp_path / "source.png"
    payload = importer.PNG_SIGNATURE + b"individual-image-bytes"
    source.write_bytes(payload)
    monkeypatch.setattr(importer, "_download", lambda *_args: source)
    sources = []
    record = {
        "id": "unit",
        "image": {"group": "tft-champion", "full": "unit.png"},
    }

    importer._dd_full_asset(
        object(), tmp_path, tmp_path, sources, "16.19.1", record, "assets/first.png"
    )
    importer._dd_full_asset(
        object(), tmp_path, tmp_path, sources, "16.19.1", record, "assets/second.png"
    )

    assert len(sources) == 1
    assert (tmp_path / "assets/first.png").read_bytes() == payload
    assert (tmp_path / "assets/second.png").read_bytes() == payload


def test_dd_full_asset_rejects_non_png(importer, tmp_path, monkeypatch) -> None:
    bad = tmp_path / "bad.bin"
    bad.write_bytes(b"not a png")
    monkeypatch.setattr(importer, "_download", lambda *_args: bad)
    record = {"id": "unit", "image": {"group": "tft-item", "full": "unit.png"}}
    with pytest.raises(ValueError, match="not a PNG"):
        importer._dd_full_asset(object(), tmp_path, tmp_path, [], "16.19.1", record, "asset.png")


def test_cdragon_game_asset_converts_tex_path_and_copies_png(
    importer, tmp_path, monkeypatch
) -> None:
    source_id, url = importer._cdragon_game_asset_url(
        "16.19",
        "ASSETS/Characters/TFT18_Lux/HUD/Splashes/T_18_Lux_Coven_TeamPlanner.tex",
    )
    assert source_id.startswith("cdragon_asset_t_18_lux_coven_teamplanner_png_")
    assert url.endswith(
        "/16.19/game/assets/characters/tft18_lux/hud/splashes/t_18_lux_coven_teamplanner.png"
    )

    source = tmp_path / "variant.png"
    payload = importer.PNG_SIGNATURE + b"variant-image-bytes"
    source.write_bytes(payload)
    monkeypatch.setattr(importer, "_download", lambda *_args: source)
    sources = []
    importer._cdragon_game_asset(
        object(),
        tmp_path,
        tmp_path,
        sources,
        "16.19",
        "assets/characters/tft18_lux/hud/splashes/t_18_lux_coven_teamplanner.tex",
        "assets/variant.png",
    )
    assert (tmp_path / "assets/variant.png").read_bytes() == payload
    assert len(sources) == 1

    with pytest.raises(ValueError, match="must start with assets"):
        importer._cdragon_game_asset_url("16.19", "characters/lux.tex")
    with pytest.raises(ValueError, match="not an exported PNG"):
        importer._cdragon_game_asset_url("16.19", "assets/characters/lux.bin")


def test_source_lock_is_only_committed_after_explicit_commit(importer, tmp_path) -> None:
    config_path = tmp_path / "source.json"
    config_path.write_text("{}", encoding="ascii")
    spec_dir = tmp_path / "spec"
    spec_dir.mkdir()
    (spec_dir / "set_spec.json").write_text(
        '{"manifest":{"set_id":"set","revision":"1"},'
        '"sources":[{"id":"source","url":"https://example.invalid/a",'
        '"revision":"1","locale":null,"sha256":"' + "0" * 64 + '","byte_length":1}]}',
        encoding="ascii",
    )

    lock_path, payload = importer._prepare_source_lock(config_path, spec_dir, False)
    assert payload is not None
    assert not lock_path.exists()

    importer._commit_source_lock(lock_path, payload)
    assert lock_path.is_file()
    assert importer._prepare_source_lock(config_path, spec_dir, False) == (lock_path, None)


def test_source_lock_rejects_inventory_or_hash_drift(importer, tmp_path) -> None:
    config_path = tmp_path / "source.json"
    config_path.write_text("{}", encoding="ascii")
    spec_dir = tmp_path / "spec"
    spec_dir.mkdir()
    set_spec = spec_dir / "set_spec.json"
    set_spec.write_text(
        '{"manifest":{"set_id":"set","revision":"1"},'
        '"sources":[{"id":"source","url":"https://example.invalid/a",'
        '"revision":"1","locale":null,"sha256":"' + "0" * 64 + '","byte_length":1}]}',
        encoding="ascii",
    )
    lock_path, payload = importer._prepare_source_lock(config_path, spec_dir, False)
    importer._commit_source_lock(lock_path, payload)

    set_spec.write_text(
        '{"manifest":{"set_id":"set","revision":"1"},'
        '"sources":[{"id":"other","url":"https://example.invalid/a",'
        '"revision":"1","locale":null,"sha256":"' + "0" * 64 + '","byte_length":1}]}',
        encoding="ascii",
    )
    with pytest.raises(ValueError, match="source inventory differs"):
        importer._prepare_source_lock(config_path, spec_dir, False)

    set_spec.write_text(
        '{"manifest":{"set_id":"set","revision":"1"},'
        '"sources":[{"id":"source","url":"https://example.invalid/a",'
        '"revision":"1","locale":null,"sha256":"' + "1" * 64 + '","byte_length":1}]}',
        encoding="ascii",
    )
    with pytest.raises(ValueError, match="source hashes differ"):
        importer._prepare_source_lock(config_path, spec_dir, False)


def test_main_does_not_publish_source_lock_when_package_build_fails(
    importer, tmp_path, monkeypatch
) -> None:
    config_path = tmp_path / "source.json"
    config_path.write_text('{"set_id":"set"}', encoding="ascii")
    output = tmp_path / "output"

    def fake_build_spec(config, cache_dir, spec_dir) -> None:
        del config, cache_dir
        (spec_dir / "set_spec.json").write_text(
            '{"manifest":{"set_id":"set","revision":"1"},"sources":[]}',
            encoding="ascii",
        )

    monkeypatch.setattr(importer, "_build_spec", fake_build_spec)

    def fail_build(*args, **kwargs) -> None:
        del args, kwargs
        raise RuntimeError("build failed")

    monkeypatch.setattr(importer, "build_set_from_local_spec", fail_build)
    monkeypatch.setattr(
        "sys.argv",
        ["import_cdragon_set.py", str(config_path), str(output)],
    )

    with pytest.raises(RuntimeError, match="build failed"):
        importer.main()

    assert not config_path.with_name("source_lock.json").exists()


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


def test_trait_variable_overrides_require_reviewed_source_reason_and_known_breakpoint(
    importer,
) -> None:
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
    assert importer._trait_variable_overrides(config, "Trait", {"2"}) == {"2": {"Value": 12}}
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
