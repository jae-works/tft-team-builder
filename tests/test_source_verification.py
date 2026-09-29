from __future__ import annotations

import json
from pathlib import Path

from tft_builder.set_loader import load_set_directory
from tft_builder.source_verification import verify_source_lock_file, verify_source_lock_payload


def real_set18(project_root: Path):
    return load_set_directory(project_root / "src/assets/sets/enchanted_wilds")


def matching_lock_payload(loaded) -> dict:
    return {
        "set_id": loaded.manifest.set_id,
        "revision": loaded.manifest.revision,
        "sources": [record.model_dump(mode="json") for record in loaded.source_manifest.sources],
    }


def test_generic_source_lock_accepts_complete_real_set18_provenance(project_root: Path) -> None:
    loaded = real_set18(project_root)
    payload = matching_lock_payload(loaded)

    assert verify_source_lock_payload(loaded, payload) == []


def test_generic_source_lock_reports_top_level_and_inventory_drift(project_root: Path) -> None:
    loaded = real_set18(project_root)
    payload = matching_lock_payload(loaded)
    first = dict(payload["sources"][0])

    payload["set_id"] = "other_set"
    payload["revision"] = "other_revision"
    payload["sources"] = payload["sources"][1:]
    payload["sources"].append(
        {
            **first,
            "id": "unexpected_source",
        }
    )

    issues = verify_source_lock_payload(loaded, payload)
    assert "source lock Set ID differs" in issues
    assert "source lock revision differs" in issues
    assert any(issue.startswith("source lock is missing provenance IDs:") for issue in issues)
    assert "source lock has unexpected provenance IDs: unexpected_source" in issues


def test_generic_source_lock_reports_duplicate_invalid_and_nonlist_sources(
    project_root: Path,
) -> None:
    loaded = real_set18(project_root)
    payload = matching_lock_payload(loaded)
    first = payload["sources"][0]

    duplicate = {**payload, "sources": [*payload["sources"], dict(first)]}
    assert f"source lock has duplicate source ID: {first['id']}" in verify_source_lock_payload(
        loaded, duplicate
    )

    invalid = {**payload, "sources": [{"id": "broken"}, *payload["sources"][1:]]}
    invalid_issues = verify_source_lock_payload(loaded, invalid)
    assert "source lock record 0 is invalid" in invalid_issues
    assert any(
        issue.startswith("source lock is missing provenance IDs:") for issue in invalid_issues
    )

    assert verify_source_lock_payload(loaded, []) == ["source lock root must be an object"]
    nonlist = {
        "set_id": loaded.manifest.set_id,
        "revision": loaded.manifest.revision,
        "sources": {},
    }
    assert verify_source_lock_payload(loaded, nonlist) == ["source lock sources must be a list"]


def test_generic_source_lock_compares_every_provenance_field(project_root: Path) -> None:
    loaded = real_set18(project_root)
    payload = matching_lock_payload(loaded)
    first = payload["sources"][0]

    replacements = {
        "url": "https://example.invalid/changed",
        "revision": "changed",
        "locale": "fr_FR" if first["locale"] != "fr_FR" else "de_DE",
        "sha256": "f" * 64 if first["sha256"] != "f" * 64 else "e" * 64,
        "byte_length": first["byte_length"] + 1,
    }
    for field, value in replacements.items():
        changed = matching_lock_payload(loaded)
        changed["sources"][0] = {**changed["sources"][0], field: value}
        assert verify_source_lock_payload(loaded, changed) == [
            f"source lock {field} differs for {first['id']}"
        ]


def test_generic_source_lock_file_rejects_invalid_json_and_accepts_real_lock(
    project_root: Path, tmp_path: Path
) -> None:
    loaded = real_set18(project_root)
    real_lock = project_root / "set_sources/sets/enchanted_wilds/source_lock.json"
    assert verify_source_lock_file(loaded, real_lock) == []

    broken = tmp_path / "source_lock.json"
    broken.write_text("{not-json", encoding="utf-8")
    assert verify_source_lock_file(loaded, broken) == [
        "source lock could not be read as valid JSON"
    ]

    missing = tmp_path / "missing.json"
    assert verify_source_lock_file(loaded, missing) == [
        "source lock could not be read as valid JSON"
    ]

    duplicate_key = tmp_path / "duplicate.json"
    duplicate_key.write_text(
        json.dumps({"set_id": loaded.manifest.set_id})[:-1]
        + ', "set_id": "duplicate", "revision": "x", "sources": []}',
        encoding="utf-8",
    )
    assert verify_source_lock_file(loaded, duplicate_key) == [
        "source lock could not be read as valid JSON"
    ]
