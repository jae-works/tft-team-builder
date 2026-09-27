from __future__ import annotations

import json
from pathlib import Path


CORE_MIRRORED_DOCS = (
    "PROJECT_CONTEXT.md",
    "REQUIREMENTS.md",
    "PROGRESS.md",
    "IMPLEMENTATION_BLOCKS.md",
    "DEVELOPMENT_PLAN.md",
    "DECISIONS.md",
    "SET_DATA_PIPELINE.md",
    "BLOCK_01_REPORT.md",
)


def test_project_manifest_is_valid_json(project_root: Path) -> None:
    payload = json.loads((project_root / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    assert payload["project"] == "TFT Team Builder"
    assert payload["version"] == "0.1.0"
    assert payload["current_state"] == "block_1_complete"
    assert payload["current_block"] == 1
    assert payload["next_block"] == 2


def test_every_manifest_required_document_exists(project_root: Path) -> None:
    payload = json.loads((project_root / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    required = payload["required_project_documents"]
    assert required
    missing = [relative for relative in required if not (project_root / relative).is_file()]
    assert missing == []


def test_project_docs_contains_exact_mirrors_of_core_documents(project_root: Path) -> None:
    mirror_root = project_root / "project_docs"
    for filename in CORE_MIRRORED_DOCS:
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


def test_manifest_records_block_one_verification(project_root: Path) -> None:
    payload = json.loads((project_root / "PROJECT_MANIFEST.json").read_text(encoding="utf-8"))
    verification = payload["verification"]
    assert verification["pytest_passed"] >= 170
    assert verification["compileall_passed"] is True
    assert verification["ascii_policy_passed"] is True
    assert verification["sample_set_regenerated"] is True
    assert verification["sample_set_validated"] is True
