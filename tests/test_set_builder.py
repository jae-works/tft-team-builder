from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from tft_builder.set_builder import build_set_from_local_spec, directory_content_hash
from tft_builder.set_loader import load_set_directory


def test_builder_creates_valid_set_from_committed_spec(project_root: Path, tmp_path: Path) -> None:
    spec = project_root / "set_sources/specs/sample_set"
    output = tmp_path / "built"
    build_set_from_local_spec(spec, output)
    loaded = load_set_directory(output)
    assert loaded.manifest.set_id == "sample_set"
    assert len(loaded.champions) == 3
    assert len(loaded.traits) == 3


def test_builder_output_matches_bundled_sample_set(project_root: Path, tmp_path: Path) -> None:
    spec = project_root / "set_sources/specs/sample_set"
    output = tmp_path / "built"
    build_set_from_local_spec(spec, output)
    assert directory_content_hash(output) == directory_content_hash(project_root / "sets/sample_set")


def test_builder_is_deterministic_across_two_output_directories(project_root: Path, tmp_path: Path) -> None:
    spec = project_root / "set_sources/specs/sample_set"
    first = tmp_path / "first"
    second = tmp_path / "second"
    build_set_from_local_spec(spec, first)
    build_set_from_local_spec(spec, second)
    assert directory_content_hash(first) == directory_content_hash(second)


def test_builder_rejects_missing_spec_directory(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="source spec directory"):
        build_set_from_local_spec(tmp_path / "missing", tmp_path / "output")


def test_builder_rejects_existing_output_without_overwrite(project_root: Path, tmp_path: Path) -> None:
    spec = project_root / "set_sources/specs/sample_set"
    output = tmp_path / "output"
    output.mkdir()
    with pytest.raises(FileExistsError, match="already exists"):
        build_set_from_local_spec(spec, output)


def test_builder_overwrite_replaces_existing_output(project_root: Path, tmp_path: Path) -> None:
    spec = project_root / "set_sources/specs/sample_set"
    output = tmp_path / "output"
    output.mkdir()
    (output / "old.txt").write_text("old", encoding="utf-8")
    build_set_from_local_spec(spec, output, overwrite=True)
    assert not (output / "old.txt").exists()
    assert (output / "manifest.json").is_file()


def test_builder_fails_when_referenced_source_asset_is_missing(project_root: Path, tmp_path: Path) -> None:
    import shutil

    source = project_root / "set_sources/specs/sample_set"
    spec = tmp_path / "spec"
    shutil.copytree(source, spec)
    (spec / "assets/champions/sample_guardian.png").unlink()
    with pytest.raises(FileNotFoundError, match="source asset"):
        build_set_from_local_spec(spec, tmp_path / "output")


def test_builder_rejects_invalid_source_spec_json(project_root: Path, tmp_path: Path) -> None:
    import shutil

    source = project_root / "set_sources/specs/sample_set"
    spec = tmp_path / "spec"
    shutil.copytree(source, spec)
    (spec / "set_spec.json").write_text("{broken", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        build_set_from_local_spec(spec, tmp_path / "output")


def test_builder_rejects_schema_invalid_source_spec(project_root: Path, tmp_path: Path) -> None:
    import shutil

    source = project_root / "set_sources/specs/sample_set"
    spec = tmp_path / "spec"
    shutil.copytree(source, spec)
    path = spec / "set_spec.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["manifest"]["schema_version"] = 999
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid source spec"):
        build_set_from_local_spec(spec, tmp_path / "output")


def test_source_manifest_contains_spec_hash_and_all_asset_hashes(project_root: Path, tmp_path: Path) -> None:
    spec = project_root / "set_sources/specs/sample_set"
    output = tmp_path / "built"
    build_set_from_local_spec(spec, output)
    payload = json.loads((output / "source_manifest.json").read_text(encoding="utf-8"))
    assert payload["schema_version"] == 1
    assert payload["source_type"] == "local_spec"
    assert len(payload["source_sha256"]) == 64
    assert set(payload["generated_file_sha256"]) == {
        "manifest.json",
        "data/champions.json",
        "data/traits.json",
        "data/dynamic_traits.json",
        "data/team_planner.json",
        "locales/en.json",
    }
    assert all(len(value) == 64 for value in payload["generated_file_sha256"].values())
    assert set(payload["asset_sha256"]) == {
        "assets/champions/sample_flex.png",
        "assets/champions/sample_guardian.png",
        "assets/champions/sample_mage.png",
        "assets/traits/sample_arcane.png",
        "assets/traits/sample_guard.png",
        "assets/traits/sample_wildcard.png",
    }
    assert all(len(value) == 64 for value in payload["asset_sha256"].values())


def test_generated_json_files_end_with_newline(project_root: Path, tmp_path: Path) -> None:
    output = tmp_path / "built"
    build_set_from_local_spec(project_root / "set_sources/specs/sample_set", output)
    for path in output.rglob("*.json"):
        assert path.read_bytes().endswith(b"\n"), path


def test_generated_json_uses_deterministic_sorted_keys(project_root: Path, tmp_path: Path) -> None:
    output = tmp_path / "built"
    build_set_from_local_spec(project_root / "set_sources/specs/sample_set", output)
    first_lines = (output / "manifest.json").read_text(encoding="utf-8").splitlines()
    property_lines = [line.strip().split(":", 1)[0] for line in first_lines if line.startswith("  \"")]
    assert property_lines == sorted(property_lines)


def test_directory_content_hash_changes_when_file_content_changes(project_root: Path, tmp_path: Path) -> None:
    import shutil

    source = project_root / "sets/sample_set"
    copied = tmp_path / "copied"
    shutil.copytree(source, copied)
    before = directory_content_hash(copied)
    path = copied / "locales/en.json"
    path.write_text(path.read_text(encoding="utf-8") + " ", encoding="utf-8")
    assert directory_content_hash(copied) != before


def test_directory_content_hash_changes_when_file_name_changes(project_root: Path, tmp_path: Path) -> None:
    import shutil

    source = project_root / "sets/sample_set"
    copied = tmp_path / "copied"
    shutil.copytree(source, copied)
    before = directory_content_hash(copied)
    path = copied / "locales/en.json"
    path.rename(copied / "locales/en-renamed.json")
    assert directory_content_hash(copied) != before


def test_builder_rejects_output_equal_to_source_spec(project_root: Path) -> None:
    spec = project_root / "set_sources/specs/sample_set"
    with pytest.raises(ValueError, match="must not overlap"):
        build_set_from_local_spec(spec, spec, overwrite=True)


def test_builder_rejects_output_inside_source_spec(project_root: Path) -> None:
    spec = project_root / "set_sources/specs/sample_set"
    with pytest.raises(ValueError, match="must not overlap"):
        build_set_from_local_spec(spec, spec / "generated")


def test_builder_rejects_output_ancestor_of_source_spec(project_root: Path, tmp_path: Path) -> None:
    import shutil

    parent = tmp_path / "parent"
    spec = parent / "spec"
    shutil.copytree(project_root / "set_sources/specs/sample_set", spec)
    with pytest.raises(ValueError, match="must not overlap"):
        build_set_from_local_spec(spec, parent, overwrite=True)
    assert (spec / "set_spec.json").is_file()


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks not supported")
def test_builder_rejects_source_asset_symlink_escape(project_root: Path, tmp_path: Path) -> None:
    import shutil

    spec = tmp_path / "spec"
    shutil.copytree(project_root / "set_sources/specs/sample_set", spec)
    outside = tmp_path / "outside.png"
    outside.write_bytes((spec / "assets/champions/sample_guardian.png").read_bytes())
    target = spec / "assets/champions/sample_guardian.png"
    target.unlink()
    try:
        target.symlink_to(outside)
    except OSError:
        pytest.skip("environment does not permit symlink creation")

    with pytest.raises(ValueError, match="resolves outside"):
        build_set_from_local_spec(spec, tmp_path / "output")


def test_failed_new_build_does_not_leave_partial_output(project_root: Path, tmp_path: Path) -> None:
    import shutil

    spec = tmp_path / "spec"
    shutil.copytree(project_root / "set_sources/specs/sample_set", spec)
    (spec / "assets/champions/sample_guardian.png").unlink()
    output = tmp_path / "output"

    with pytest.raises(FileNotFoundError, match="source asset"):
        build_set_from_local_spec(spec, output)

    assert not output.exists()
    assert list(tmp_path.glob(".output.build-*")) == []


def test_failed_overwrite_preserves_previous_valid_output(project_root: Path, tmp_path: Path) -> None:
    import shutil

    source_spec = project_root / "set_sources/specs/sample_set"
    output = tmp_path / "output"
    build_set_from_local_spec(source_spec, output)
    before = directory_content_hash(output)

    broken_spec = tmp_path / "broken-spec"
    shutil.copytree(source_spec, broken_spec)
    (broken_spec / "assets/champions/sample_guardian.png").unlink()

    with pytest.raises(FileNotFoundError, match="source asset"):
        build_set_from_local_spec(broken_spec, output, overwrite=True)

    assert output.is_dir()
    assert directory_content_hash(output) == before
    assert list(tmp_path.glob(".output.build-*")) == []
    assert list(tmp_path.glob(".output.previous-*")) == []


def test_builder_rejects_existing_non_directory_output(project_root: Path, tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.write_text("not a directory", encoding="utf-8")
    with pytest.raises(FileExistsError, match="not a directory"):
        build_set_from_local_spec(
            project_root / "set_sources/specs/sample_set",
            output,
            overwrite=True,
        )
