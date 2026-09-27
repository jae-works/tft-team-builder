from __future__ import annotations

import shutil
from pathlib import Path

import pytest

import tft_builder.set_loader as set_loader
from tft_builder.set_loader import (
    SetValidationError,
    discover_set_directories,
    load_set_directory,
    validate_all_sets,
    validate_set_directory,
)


def issue_codes(path: Path) -> set[str]:
    return {issue.code for issue in validate_set_directory(path).issues}


def test_valid_committed_fixture_loads(valid_set_dir: Path) -> None:
    report = validate_set_directory(valid_set_dir)
    assert report.is_valid
    assert report.issues == ()
    assert report.loaded_set is not None
    assert report.loaded_set.manifest.set_id == "sample_set"


def test_loaded_set_exposes_id_maps(valid_set_dir: Path) -> None:
    loaded = load_set_directory(valid_set_dir)
    assert set(loaded.champions_by_id) == {"sample_guardian", "sample_mage", "sample_flex"}
    assert set(loaded.traits_by_id) == {"sample_guard", "sample_arcane", "sample_wildcard"}


def test_loaded_set_is_sorted_by_display_order(valid_set_dir: Path) -> None:
    loaded = load_set_directory(valid_set_dir)
    assert [champion.id for champion in loaded.champions] == [
        "sample_guardian",
        "sample_mage",
        "sample_flex",
    ]
    assert [trait.id for trait in loaded.traits] == [
        "sample_guard",
        "sample_arcane",
        "sample_wildcard",
    ]


def test_load_set_directory_raises_detailed_error_for_invalid_set(
    copied_valid_set: Path,
) -> None:
    (copied_valid_set / "assets/champions/sample_guardian.png").unlink()
    with pytest.raises(SetValidationError) as exc_info:
        load_set_directory(copied_valid_set)
    assert "missing_asset" in str(exc_info.value)
    assert exc_info.value.report.is_valid is False


def test_duplicate_champion_id_is_reported(copied_valid_set: Path, load_json, save_json) -> None:
    path = copied_valid_set / "data/champions.json"
    payload = load_json(path)
    payload.append(dict(payload[0]))
    save_json(path, payload)
    assert "duplicate_id" in issue_codes(copied_valid_set)


def test_champion_unknown_trait_is_reported(copied_valid_set: Path, load_json, save_json) -> None:
    path = copied_valid_set / "data/champions.json"
    payload = load_json(path)
    payload[0]["traits"] = ["missing_trait"]
    save_json(path, payload)
    assert "unknown_trait" in issue_codes(copied_valid_set)


def test_invalid_trait_breakpoint_order_is_schema_error(
    copied_valid_set: Path, load_json, save_json
) -> None:
    path = copied_valid_set / "data/traits.json"
    payload = load_json(path)
    payload[0]["breakpoints"] = [
        {"count": 4, "style": "silver"},
        {"count": 2, "style": "bronze"},
    ]
    save_json(path, payload)
    assert "schema_error" in issue_codes(copied_valid_set)


def test_dynamic_rule_unknown_trait_is_reported(
    copied_valid_set: Path, load_json, save_json
) -> None:
    path = copied_valid_set / "data/dynamic_traits.json"
    payload = load_json(path)
    payload[0]["choices"] = ["missing_trait"]
    save_json(path, payload)
    assert "unknown_trait" in issue_codes(copied_valid_set)


def test_missing_required_translation_is_reported(
    copied_valid_set: Path, load_json, save_json
) -> None:
    path = copied_valid_set / "locales/en.json"
    payload = load_json(path)
    payload.pop("champion.sample_guardian.name")
    save_json(path, payload)
    assert "missing_translation" in issue_codes(copied_valid_set)


def test_invalid_png_signature_is_reported(copied_valid_set: Path) -> None:
    path = copied_valid_set / "assets/champions/sample_guardian.png"
    path.write_bytes(b"not a png")
    assert "invalid_png" in issue_codes(copied_valid_set)


def test_team_planner_support_requires_codec(copied_valid_set: Path, load_json, save_json) -> None:
    manifest_path = copied_valid_set / "manifest.json"
    manifest = load_json(manifest_path)
    manifest["team_planner_supported"] = True
    save_json(manifest_path, manifest)
    save_json(copied_valid_set / "data/team_planner.json", {"codec": None, "champion_ids": {}})
    assert "missing_team_planner_codec" in issue_codes(copied_valid_set)


def test_missing_set_directory_reports_missing_set(tmp_path: Path) -> None:
    report = validate_set_directory(tmp_path / "missing")
    assert not report.is_valid
    assert [issue.code for issue in report.issues] == ["missing_set"]


def test_missing_manifest_reports_missing_file(tmp_path: Path) -> None:
    root = tmp_path / "set"
    root.mkdir()
    assert issue_codes(root) == {"missing_file"}


def test_invalid_manifest_json_reports_invalid_json(tmp_path: Path) -> None:
    root = tmp_path / "set"
    root.mkdir()
    (root / "manifest.json").write_text("{broken", encoding="utf-8")
    assert "invalid_json" in issue_codes(root)


def test_manifest_schema_error_stops_semantic_loading(
    copied_valid_set: Path, load_json, save_json
) -> None:
    path = copied_valid_set / "manifest.json"
    payload = load_json(path)
    payload["schema_version"] = 999
    save_json(path, payload)
    report = validate_set_directory(copied_valid_set)
    assert "schema_error" in {issue.code for issue in report.issues}
    assert report.loaded_set is None


def test_missing_champions_file_is_reported(copied_valid_set: Path) -> None:
    (copied_valid_set / "data/champions.json").unlink()
    assert "missing_file" in issue_codes(copied_valid_set)


def test_missing_traits_file_is_reported(copied_valid_set: Path) -> None:
    (copied_valid_set / "data/traits.json").unlink()
    assert "missing_file" in issue_codes(copied_valid_set)


def test_missing_dynamic_traits_file_is_reported(copied_valid_set: Path) -> None:
    (copied_valid_set / "data/dynamic_traits.json").unlink()
    assert "missing_file" in issue_codes(copied_valid_set)


def test_missing_source_manifest_is_reported(copied_valid_set: Path) -> None:
    (copied_valid_set / "source_manifest.json").unlink()
    assert "missing_file" in issue_codes(copied_valid_set)


def test_invalid_utf8_file_is_reported(copied_valid_set: Path) -> None:
    (copied_valid_set / "data/champions.json").write_bytes(b"\xff\xfe")
    assert "invalid_utf8" in issue_codes(copied_valid_set)


def test_champions_must_be_json_array(copied_valid_set: Path) -> None:
    (copied_valid_set / "data/champions.json").write_text("{}\n", encoding="utf-8")
    assert "schema_error" in issue_codes(copied_valid_set)


def test_traits_must_be_json_array(copied_valid_set: Path) -> None:
    (copied_valid_set / "data/traits.json").write_text("{}\n", encoding="utf-8")
    assert "schema_error" in issue_codes(copied_valid_set)


def test_duplicate_trait_id_is_reported(copied_valid_set: Path, load_json, save_json) -> None:
    path = copied_valid_set / "data/traits.json"
    payload = load_json(path)
    payload.append(dict(payload[0]))
    save_json(path, payload)
    assert "duplicate_id" in issue_codes(copied_valid_set)


def test_duplicate_dynamic_rule_is_reported(copied_valid_set: Path, load_json, save_json) -> None:
    path = copied_valid_set / "data/dynamic_traits.json"
    payload = load_json(path)
    payload.append(dict(payload[0]))
    save_json(path, payload)
    assert "duplicate_dynamic_rule" in issue_codes(copied_valid_set)


def test_dynamic_rule_unknown_champion_is_reported(
    copied_valid_set: Path, load_json, save_json
) -> None:
    path = copied_valid_set / "data/dynamic_traits.json"
    payload = load_json(path)
    payload[0]["champion_id"] = "missing_champion"
    save_json(path, payload)
    assert "unknown_champion" in issue_codes(copied_valid_set)


def test_team_planner_unknown_champion_mapping_is_reported(
    copied_valid_set: Path, save_json
) -> None:
    path = copied_valid_set / "data/team_planner.json"
    save_json(path, {"codec": "riot_v1", "champion_ids": {"missing_champion": "123"}})
    assert "unknown_champion" in issue_codes(copied_valid_set)


def test_team_planner_supported_requires_every_champion_mapping(
    copied_valid_set: Path, load_json, save_json
) -> None:
    manifest_path = copied_valid_set / "manifest.json"
    manifest = load_json(manifest_path)
    manifest["team_planner_supported"] = True
    save_json(manifest_path, manifest)
    planner_path = copied_valid_set / "data/team_planner.json"
    save_json(planner_path, {"codec": "riot_v1", "champion_ids": {"sample_guardian": "1"}})
    codes = issue_codes(copied_valid_set)
    assert "missing_team_planner_mapping" in codes


def test_valid_team_planner_supported_set_loads(
    copied_valid_set: Path, load_json, save_json, refresh_generated_hashes
) -> None:
    manifest_path = copied_valid_set / "manifest.json"
    manifest = load_json(manifest_path)
    manifest["team_planner_supported"] = True
    save_json(manifest_path, manifest)
    save_json(
        copied_valid_set / "data/team_planner.json",
        {
            "codec": "riot_v1",
            "champion_ids": {
                "sample_guardian": "1",
                "sample_mage": "2",
                "sample_flex": "3",
            },
        },
    )
    refresh_generated_hashes(copied_valid_set)
    assert validate_set_directory(copied_valid_set).is_valid


def test_locale_non_string_value_is_rejected(copied_valid_set: Path, load_json, save_json) -> None:
    path = copied_valid_set / "locales/en.json"
    payload = load_json(path)
    payload["set.sample_set.name"] = 123
    save_json(path, payload)
    assert "invalid_locale" in issue_codes(copied_valid_set)


def test_empty_locale_value_is_rejected(copied_valid_set: Path, load_json, save_json) -> None:
    path = copied_valid_set / "locales/en.json"
    payload = load_json(path)
    payload["set.sample_set.name"] = "   "
    save_json(path, payload)
    assert "invalid_locale" in issue_codes(copied_valid_set)


def test_missing_supported_locale_file_is_reported(
    copied_valid_set: Path, load_json, save_json
) -> None:
    path = copied_valid_set / "manifest.json"
    payload = load_json(path)
    payload["supported_locales"] = ["en", "de"]
    save_json(path, payload)
    assert "missing_file" in issue_codes(copied_valid_set)


def test_zero_byte_asset_is_rejected(copied_valid_set: Path) -> None:
    (copied_valid_set / "assets/champions/sample_guardian.png").write_bytes(b"")
    assert "empty_asset" in issue_codes(copied_valid_set)


def test_manifest_path_traversal_is_rejected_by_schema(
    copied_valid_set: Path, load_json, save_json
) -> None:
    path = copied_valid_set / "manifest.json"
    payload = load_json(path)
    payload["champions_file"] = "../outside.json"
    save_json(path, payload)
    assert "schema_error" in issue_codes(copied_valid_set)


def test_asset_link_like_path_is_rejected(
    copied_valid_set: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = copied_valid_set / "assets/champions/sample_guardian.png"
    original = set_loader.is_link_like
    monkeypatch.setattr(
        set_loader,
        "is_link_like",
        lambda path: path == target or original(path),
    )

    assert "unexpected_symlink" in issue_codes(copied_valid_set)


def test_validation_collects_multiple_independent_issues(
    copied_valid_set: Path, load_json, save_json
) -> None:
    (copied_valid_set / "assets/champions/sample_guardian.png").unlink()
    path = copied_valid_set / "data/champions.json"
    payload = load_json(path)
    payload[1]["traits"] = ["missing_trait"]
    save_json(path, payload)
    codes = [issue.code for issue in validate_set_directory(copied_valid_set).issues]
    assert "missing_asset" in codes
    assert "unknown_trait" in codes
    assert len(codes) >= 2


def test_validation_issue_order_is_deterministic(
    copied_valid_set: Path, load_json, save_json
) -> None:
    (copied_valid_set / "assets/champions/sample_guardian.png").unlink()
    path = copied_valid_set / "data/champions.json"
    payload = load_json(path)
    payload[1]["traits"] = ["missing_trait"]
    save_json(path, payload)
    first = validate_set_directory(copied_valid_set).issues
    second = validate_set_directory(copied_valid_set).issues
    assert first == second


def test_discover_set_directories_ignores_non_set_folders(
    tmp_path: Path, valid_set_dir: Path
) -> None:
    parent = tmp_path / "sets"
    parent.mkdir()
    (parent / "not_a_set").mkdir()
    destination = parent / "valid"
    shutil.copytree(valid_set_dir, destination)
    assert discover_set_directories(parent) == (destination,)


def test_discover_set_directories_returns_empty_when_parent_missing(tmp_path: Path) -> None:
    assert discover_set_directories(tmp_path / "missing") == ()


def test_validate_all_sets_returns_one_report_per_discovered_set(
    tmp_path: Path, valid_set_dir: Path
) -> None:
    parent = tmp_path / "sets"
    parent.mkdir()
    shutil.copytree(valid_set_dir, parent / "a")
    shutil.copytree(valid_set_dir, parent / "b")
    reports = validate_all_sets(parent)
    assert len(reports) == 2
    assert all(report.is_valid for report in reports)


def test_required_asset_hash_must_be_present(copied_valid_set: Path, load_json, save_json) -> None:
    path = copied_valid_set / "source_manifest.json"
    payload = load_json(path)
    payload["asset_sha256"].pop("assets/champions/sample_guardian.png")
    save_json(path, payload)
    assert "missing_asset_hash" in issue_codes(copied_valid_set)


def test_unexpected_asset_hash_is_rejected(copied_valid_set: Path, load_json, save_json) -> None:
    path = copied_valid_set / "source_manifest.json"
    payload = load_json(path)
    payload["asset_sha256"]["assets/unused.png"] = "0" * 64
    save_json(path, payload)
    assert "unexpected_asset_hash" in issue_codes(copied_valid_set)


def test_modified_asset_fails_hash_validation(copied_valid_set: Path) -> None:
    path = copied_valid_set / "assets/champions/sample_guardian.png"
    path.write_bytes(path.read_bytes() + b"modified")
    assert "asset_hash_mismatch" in issue_codes(copied_valid_set)


def test_champion_asset_must_live_under_manifest_assets_dir(
    copied_valid_set: Path, load_json, save_json
) -> None:
    source = copied_valid_set / "assets/champions/sample_guardian.png"
    destination = copied_valid_set / "outside.png"
    destination.write_bytes(source.read_bytes())
    champion_path = copied_valid_set / "data/champions.json"
    champions = load_json(champion_path)
    champions[0]["image"] = "outside.png"
    save_json(champion_path, champions)
    report = validate_set_directory(copied_valid_set)
    assert "asset_outside_assets_dir" in {issue.code for issue in report.issues}


def test_trait_asset_must_live_under_manifest_assets_dir(
    copied_valid_set: Path, load_json, save_json
) -> None:
    source = copied_valid_set / "assets/traits/sample_guard.png"
    destination = copied_valid_set / "outside.png"
    destination.write_bytes(source.read_bytes())
    trait_path = copied_valid_set / "data/traits.json"
    traits = load_json(trait_path)
    traits[0]["icon"] = "outside.png"
    save_json(trait_path, traits)
    report = validate_set_directory(copied_valid_set)
    assert "asset_outside_assets_dir" in {issue.code for issue in report.issues}


def test_missing_generated_file_hash_is_rejected(
    copied_valid_set: Path, load_json, save_json
) -> None:
    path = copied_valid_set / "source_manifest.json"
    payload = load_json(path)
    payload["generated_file_sha256"].pop("data/champions.json")
    save_json(path, payload)
    assert "missing_generated_file_hash" in issue_codes(copied_valid_set)


def test_unexpected_generated_file_hash_is_rejected(
    copied_valid_set: Path, load_json, save_json
) -> None:
    path = copied_valid_set / "source_manifest.json"
    payload = load_json(path)
    payload["generated_file_sha256"]["data/unused.json"] = "0" * 64
    save_json(path, payload)
    assert "unexpected_generated_file_hash" in issue_codes(copied_valid_set)


def test_modified_generated_file_fails_hash_validation(
    copied_valid_set: Path, load_json, save_json
) -> None:
    path = copied_valid_set / "data/champions.json"
    payload = load_json(path)
    payload[0]["cost"] = payload[0]["cost"] + 1
    save_json(path, payload)
    assert "generated_file_hash_mismatch" in issue_codes(copied_valid_set)


def test_empty_champion_catalog_is_rejected(copied_valid_set: Path, save_json) -> None:
    save_json(copied_valid_set / "data/champions.json", [])
    assert "empty_champions" in issue_codes(copied_valid_set)


def test_empty_trait_catalog_is_rejected(copied_valid_set: Path, save_json) -> None:
    save_json(copied_valid_set / "data/traits.json", [])
    assert "empty_traits" in issue_codes(copied_valid_set)


def test_duplicate_json_object_key_is_reported(copied_valid_set: Path) -> None:
    path = copied_valid_set / "manifest.json"
    path.write_text('{"schema_version": 1, "schema_version": 1}\n', encoding="utf-8")
    assert "duplicate_json_key" in issue_codes(copied_valid_set)


def test_validation_issue_without_location_formats_compactly() -> None:
    from tft_builder.set_loader import ValidationIssue

    issue = ValidationIssue("code", "message")
    assert issue.format() == "[code] message"


def test_duplicate_champion_display_order_is_reported(
    copied_valid_set: Path, load_json, save_json
) -> None:
    path = copied_valid_set / "data/champions.json"
    payload = load_json(path)
    payload[1]["display_order"] = payload[0]["display_order"]
    save_json(path, payload)
    assert "duplicate_display_order" in issue_codes(copied_valid_set)


def test_duplicate_trait_display_order_is_reported(
    copied_valid_set: Path, load_json, save_json
) -> None:
    path = copied_valid_set / "data/traits.json"
    payload = load_json(path)
    payload[1]["display_order"] = payload[0]["display_order"]
    save_json(path, payload)
    assert "duplicate_display_order" in issue_codes(copied_valid_set)


def test_unexpected_runtime_file_is_reported(copied_valid_set: Path) -> None:
    (copied_valid_set / "stale.txt").write_text("stale", encoding="ascii")
    assert "unexpected_file" in issue_codes(copied_valid_set)


def test_unexpected_nested_runtime_file_is_reported(copied_valid_set: Path) -> None:
    path = copied_valid_set / "assets" / "unused" / "stale.bin"
    path.parent.mkdir(parents=True)
    path.write_bytes(b"stale")
    assert "unexpected_file" in issue_codes(copied_valid_set)


def test_runtime_inventory_rejects_internal_link_like_entry(
    copied_valid_set: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = copied_valid_set / "assets/champions/sample_mage.png"
    original = set_loader.is_link_like
    monkeypatch.setattr(
        set_loader,
        "is_link_like",
        lambda path: path == target or original(path),
    )

    assert "unexpected_symlink" in issue_codes(copied_valid_set)


def test_runtime_set_root_link_like_path_is_rejected(
    tmp_path: Path, valid_set_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    copied = tmp_path / "set"
    shutil.copytree(valid_set_dir, copied)
    original = set_loader.is_link_like
    monkeypatch.setattr(
        set_loader,
        "is_link_like",
        lambda path: path == copied or original(path),
    )

    report = validate_set_directory(copied)
    assert not report.is_valid
    assert [issue.code for issue in report.issues] == ["unexpected_symlink"]
    assert report.loaded_set is None


def test_set_discovery_ignores_link_like_set_directories(
    tmp_path: Path, valid_set_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parent = tmp_path / "sets"
    parent.mkdir()
    linked_set = parent / "linked-set"
    shutil.copytree(valid_set_dir, linked_set)
    original = set_loader.is_link_like
    monkeypatch.setattr(
        set_loader,
        "is_link_like",
        lambda path: path == linked_set or original(path),
    )

    assert discover_set_directories(parent) == ()


def test_unreadable_manifest_is_reported(
    copied_valid_set: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = copied_valid_set / "manifest.json"
    original_read_text = Path.read_text

    def controlled_read_text(self: Path, *args, **kwargs):
        if self == manifest:
            raise OSError("simulated manifest read failure")
        return original_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", controlled_read_text)
    report = validate_set_directory(copied_valid_set)
    assert not report.is_valid
    assert [issue.code for issue in report.issues] == ["unreadable_file"]
    assert "simulated manifest read failure" in report.formatted_issues()


def test_runtime_path_resolution_failure_is_reported(
    copied_valid_set: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = copied_valid_set / "data/champions.json"
    original_resolve = Path.resolve

    def controlled_resolve(self: Path, *args, **kwargs):
        if self == target:
            raise RuntimeError("simulated path resolution failure")
        return original_resolve(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", controlled_resolve)
    report = validate_set_directory(copied_valid_set)
    assert not report.is_valid
    assert "unreadable_path" in {issue.code for issue in report.issues}
    assert "simulated path resolution failure" in report.formatted_issues()


def test_runtime_metadata_path_escape_is_reported(
    copied_valid_set: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = copied_valid_set / "data/champions.json"
    outside = tmp_path / "outside.json"
    original_resolve = Path.resolve

    def controlled_resolve(self: Path, *args, **kwargs):
        if self == target:
            return outside
        return original_resolve(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", controlled_resolve)
    report = validate_set_directory(copied_valid_set)
    assert not report.is_valid
    assert "path_escape" in {issue.code for issue in report.issues}


def test_runtime_inventory_link_like_entry_is_reported(
    copied_valid_set: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_scan = set_loader.scan_regular_files
    linked = copied_valid_set / "unexpected-link"

    def controlled_scan(path: Path):
        files, links = original_scan(path)
        if path == copied_valid_set:
            return files, (*links, linked)
        return files, links

    monkeypatch.setattr(set_loader, "scan_regular_files", controlled_scan)
    report = validate_set_directory(copied_valid_set)
    assert not report.is_valid
    assert "unexpected_symlink" in {issue.code for issue in report.issues}
    assert "unexpected-link" in report.formatted_issues()


def test_unreadable_champion_asset_is_reported(
    copied_valid_set: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = copied_valid_set / "assets/champions/sample_guardian.png"
    original_open = Path.open

    def controlled_open(self: Path, *args, **kwargs):
        if self == target and args and args[0] == "rb":
            raise OSError("simulated asset read failure")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", controlled_open)
    report = validate_set_directory(copied_valid_set)
    codes = {issue.code for issue in report.issues}
    assert "unreadable_asset" in codes
    assert "simulated asset read failure" in report.formatted_issues()


def test_generated_file_hash_read_failure_is_reported(
    copied_valid_set: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import tft_builder.set_loader as module

    target = copied_valid_set / "data/champions.json"
    original_sha256_file = module.sha256_file

    def controlled_sha256_file(path: Path) -> str:
        if path == target:
            raise OSError("simulated hash read failure")
        return original_sha256_file(path)

    monkeypatch.setattr(module, "sha256_file", controlled_sha256_file)
    report = validate_set_directory(copied_valid_set)
    assert "unreadable_file" in {issue.code for issue in report.issues}
    assert "simulated hash read failure" in report.formatted_issues()


def test_runtime_inventory_scan_failure_is_reported(
    copied_valid_set: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_scan = set_loader.scan_regular_files

    def controlled_scan(path: Path):
        if path == copied_valid_set:
            raise OSError("simulated inventory scan failure")
        return original_scan(path)

    monkeypatch.setattr(set_loader, "scan_regular_files", controlled_scan)
    report = validate_set_directory(copied_valid_set)
    assert "unreadable_set" in {issue.code for issue in report.issues}
    assert "simulated inventory scan failure" in report.formatted_issues()


def test_runtime_set_root_resolution_failure_is_reported(
    copied_valid_set: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original_resolve = Path.resolve

    def controlled_resolve(self: Path, *args, **kwargs):
        if self == copied_valid_set:
            raise RuntimeError("simulated Set root resolution failure")
        return original_resolve(self, *args, **kwargs)

    monkeypatch.setattr(Path, "resolve", controlled_resolve)
    report = validate_set_directory(copied_valid_set)
    assert not report.is_valid
    assert [issue.code for issue in report.issues] == ["unreadable_set"]
    assert "simulated Set root resolution failure" in report.formatted_issues()


def test_set_discovery_returns_empty_when_directory_listing_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    parent = tmp_path / "sets"
    parent.mkdir()
    original_iterdir = Path.iterdir

    def controlled_iterdir(self: Path):
        if self == parent:
            raise OSError("simulated directory listing failure")
        return original_iterdir(self)

    monkeypatch.setattr(Path, "iterdir", controlled_iterdir)
    assert discover_set_directories(parent) == ()
