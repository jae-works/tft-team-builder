from __future__ import annotations

import json
from pathlib import Path


def test_project_manifest_is_valid_json(project_root: Path) -> None:
    payload = json.loads((project_root / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    assert payload["project"] == "TFT Team Builder"
    assert payload["version"] == "0.2.0"
    assert payload["current_state"] == "block_2_implemented_pending_windows_verification"
    assert payload["current_block"] == 2
    assert payload["next_block"] == 3


def test_every_manifest_required_document_exists(project_root: Path) -> None:
    payload = json.loads((project_root / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    required = payload["required_project_documents"]
    assert required
    missing = [relative for relative in required if not (project_root / relative).is_file()]
    assert missing == []


def test_project_docs_contains_exact_mirrors_of_core_documents(project_root: Path) -> None:
    payload = json.loads((project_root / "PROJECT_MANIFEST.json").read_text(encoding="ascii"))
    mirror_root = project_root / "project_docs"
    for filename in payload["mirrored_project_documents"]:
        source = project_root / filename
        mirror = mirror_root / filename
        assert source.is_file(), filename
        assert mirror.is_file(), filename
        assert mirror.read_bytes() == source.read_bytes(), filename


def test_manifest_records_required_engineering_language_policy(project_root: Path) -> None:
    payload = json.loads((project_root / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    engineering = payload["engineering_rules"]
    assert engineering["code_language"] == "English"
    assert engineering["documentation_language"] == "English"
    assert engineering["project_authored_technical_text_ascii_safe"] is True
    assert engineering["project_owned_paths_ascii_only"] is True


def test_manifest_records_current_verification(project_root: Path) -> None:
    payload = json.loads((project_root / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    verification = payload["verification"]
    assert verification["pytest_passed"] >= 400
    assert verification["compileall_passed"] is True
    assert verification["ascii_policy_passed"] is True
    assert verification["sample_set_regenerated"] is True
    assert verification["sample_set_validated"] is True
    assert verification["block_2_persistence_roundtrip_verified"] is True
    assert verification["block_2_migration_verified"] is True
    assert verification["block_2_backup_restore_verified"] is True


def test_manifest_records_deferred_cross_platform_direction(project_root: Path) -> None:
    payload = json.loads((project_root / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    platform = payload["platform_strategy"]
    assert platform["required_first_target"] == "Windows desktop"
    assert platform["browser"] == "deferred possible target"
    assert platform["mobile_tablet"] == "deferred possible target"
    assert platform["core_must_remain_ui_independent"] is True


def test_license_review_is_required_before_public_release(project_root: Path) -> None:
    payload = json.loads((project_root / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    assert payload["engineering_rules"]["public_release_license_audit_required"] is True
    license_review = (project_root / "LICENSE_REVIEW.md").read_text(encoding="ascii")
    assert "Public binary release gate" in license_review
    assert "Riot/TFT data and assets" in license_review
