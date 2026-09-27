from __future__ import annotations

import json
import tomllib
from pathlib import Path


def test_project_manifest_is_valid_json(project_root: Path) -> None:
    payload = json.loads((project_root / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    assert payload["project"] == "TFT Team Builder"
    with (project_root / "pyproject.toml").open("rb") as handle:
        project_version = tomllib.load(handle)["project"]["version"]
    assert payload["version"] == project_version
    assert payload["current_state"] == "block_3_implemented_pending_windows_recheck"
    assert payload["current_block"] == 3
    assert payload["next_block"] == 4


def test_release_documents_match_package_version(project_root: Path) -> None:
    with (project_root / "pyproject.toml").open("rb") as handle:
        version = tomllib.load(handle)["project"]["version"]

    expected_fragments = {
        "README.md": f"Current version: {version}",
        "PROGRESS.md": f"Current version: {version}",
        "PROJECT_CONTEXT.md": f"Current version: {version}",
        "LICENSE_REVIEW.md": f"Project version: {version}",
        "BLOCK_03_REPORT.md": f"Version: {version}",
    }
    for relative, expected in expected_fragments.items():
        text = (project_root / relative).read_text(encoding="ascii")
        assert expected in text, relative


def test_manifest_includes_block_3_plan_and_report(project_root: Path) -> None:
    payload = json.loads((project_root / "PROJECT_MANIFEST.json").read_text(encoding="ascii"))
    for filename in ("BLOCK_03_PLAN.md", "BLOCK_03_REPORT.md"):
        assert filename in payload["required_project_documents"]
        assert filename in payload["mirrored_project_documents"]


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
    assert verification["pytest_passed"] == 529
    assert verification["compileall_passed"] is True
    assert verification["ascii_policy_passed"] is True
    assert verification["sample_set_regenerated"] is True
    assert verification["sample_set_validated"] is True
    assert verification["block_2_persistence_roundtrip_verified"] is True
    assert verification["block_2_migration_verified"] is True
    assert verification["block_2_backup_restore_verified"] is True
    assert verification["block_3_editor_verified"] is True
    assert verification["block_3_trait_engine_verified"] is True
    assert verification["block_3_undo_redo_verified"] is True
    assert verification["block_3_builder_smoke_passed"] is True
    assert verification["windows_0_2_2_ruff_sim300_errors"] == 1


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
