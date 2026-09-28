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


@pytest.mark.parametrize(
    ("item", "expected"),
    [
        ({"apiName": "base", "tags": ["component"]}, "COMPONENT"),
        ({"apiName": "radiant_item", "tags": []}, "RADIANT"),
        ({"apiName": "ornn_item", "tags": []}, "ARTIFACT"),
        ({"apiName": "support_item", "tags": []}, "SUPPORT"),
        ({"apiName": "emblem", "associatedTraits": ["Trait"]}, "EMBLEM"),
        ({"apiName": "crafted", "composition": ["a", "b"]}, "CRAFTABLE"),
        ({"apiName": "consumable_item", "tags": []}, "CONSUMABLE"),
        ({"apiName": "TFT18_BlastPotion", "tags": []}, "CONSUMABLE"),
        ({"apiName": "TFT18_AttackSpeedBooster", "tags": []}, "CONSUMABLE"),
        ({"apiName": "special_reward", "tags": []}, "OTHER"),
    ],
)
def test_item_category_keeps_non_craftable_families(importer, item, expected) -> None:
    assert importer._category(item) == expected


def test_collect_set_items_keeps_every_declared_item_and_recursive_components(importer) -> None:
    source_set = {
        "items": ["artifact", "radiant", "support", "emblem", "other", "crafted"]
    }
    all_items = {
        "artifact": {"apiName": "artifact"},
        "radiant": {"apiName": "radiant"},
        "support": {"apiName": "support"},
        "emblem": {"apiName": "emblem"},
        "other": {"apiName": "other"},
        "crafted": {"apiName": "crafted", "composition": ["sword", "rod"]},
        "sword": {"apiName": "sword"},
        "rod": {"apiName": "rod"},
    }
    assert importer._collect_set_item_ids(source_set, all_items) == set(all_items)


def test_collect_set_items_rejects_missing_component_record(importer) -> None:
    source_set = {"items": ["crafted"]}
    all_items = {"crafted": {"apiName": "crafted", "composition": ["missing"]}}
    with pytest.raises(ValueError, match="missing from CommunityDragon"):
        importer._collect_set_item_ids(source_set, all_items)


def test_required_item_categories_detect_upstream_inventory_regressions(importer) -> None:
    rows = [{"category": "COMPONENT"}, {"category": "ARTIFACT"}]
    importer._require_item_categories(rows, ["COMPONENT", "ARTIFACT"])
    with pytest.raises(ValueError, match="SUPPORT"):
        importer._require_item_categories(rows, ["COMPONENT", "SUPPORT"])
