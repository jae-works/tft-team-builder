from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import tft_builder.set_builder as set_builder
from tft_builder.file_integrity import directory_content_hash
from tft_builder.set_builder import build_set_from_local_spec
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
    assert directory_content_hash(output) == directory_content_hash(
        project_root / "src/assets/sets/sample_set"
    )


def test_builder_is_deterministic_across_two_output_directories(
    project_root: Path, tmp_path: Path
) -> None:
    spec = project_root / "set_sources/specs/sample_set"
    first = tmp_path / "first"
    second = tmp_path / "second"
    build_set_from_local_spec(spec, first)
    build_set_from_local_spec(spec, second)
    assert directory_content_hash(first) == directory_content_hash(second)


def test_builder_rejects_missing_spec_directory(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="source spec directory"):
        build_set_from_local_spec(tmp_path / "missing", tmp_path / "output")


def test_builder_rejects_existing_output_without_overwrite(
    project_root: Path, tmp_path: Path
) -> None:
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


def test_builder_fails_when_referenced_source_asset_is_missing(
    project_root: Path, tmp_path: Path
) -> None:
    source = project_root / "set_sources/specs/sample_set"
    spec = tmp_path / "spec"
    shutil.copytree(source, spec)
    (spec / "assets/champions/sample_guardian.png").unlink()
    with pytest.raises(FileNotFoundError, match="source asset"):
        build_set_from_local_spec(spec, tmp_path / "output")


def test_builder_rejects_invalid_source_spec_json(project_root: Path, tmp_path: Path) -> None:
    source = project_root / "set_sources/specs/sample_set"
    spec = tmp_path / "spec"
    shutil.copytree(source, spec)
    (spec / "set_spec.json").write_text("{broken", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        build_set_from_local_spec(spec, tmp_path / "output")


def test_builder_rejects_schema_invalid_source_spec(project_root: Path, tmp_path: Path) -> None:
    source = project_root / "set_sources/specs/sample_set"
    spec = tmp_path / "spec"
    shutil.copytree(source, spec)
    path = spec / "set_spec.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["manifest"]["schema_version"] = 999
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid source spec"):
        build_set_from_local_spec(spec, tmp_path / "output")


def test_source_manifest_contains_spec_hash_and_all_asset_hashes(
    project_root: Path, tmp_path: Path
) -> None:
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
    property_lines = [
        line.strip().split(":", 1)[0] for line in first_lines if line.startswith('  "')
    ]
    assert property_lines == sorted(property_lines)


def test_builder_rejects_output_equal_to_source_spec(project_root: Path) -> None:
    spec = project_root / "set_sources/specs/sample_set"
    with pytest.raises(ValueError, match="must not overlap"):
        build_set_from_local_spec(spec, spec, overwrite=True)


def test_builder_rejects_output_inside_source_spec(project_root: Path) -> None:
    spec = project_root / "set_sources/specs/sample_set"
    with pytest.raises(ValueError, match="must not overlap"):
        build_set_from_local_spec(spec, spec / "generated")


def test_builder_rejects_output_ancestor_of_source_spec(project_root: Path, tmp_path: Path) -> None:
    parent = tmp_path / "parent"
    spec = parent / "spec"
    shutil.copytree(project_root / "set_sources/specs/sample_set", spec)
    with pytest.raises(ValueError, match="must not overlap"):
        build_set_from_local_spec(spec, parent, overwrite=True)
    assert (spec / "set_spec.json").is_file()


def test_builder_rejects_source_asset_link_like_path(
    project_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = project_root / "set_sources/specs/sample_set"
    spec = tmp_path / "spec"
    shutil.copytree(source, spec)
    target = spec / "assets/champions/sample_guardian.png"
    original = set_builder.is_link_like
    monkeypatch.setattr(
        set_builder,
        "is_link_like",
        lambda path: path == target or original(path),
    )

    with pytest.raises(ValueError, match="symbolic links or junctions"):
        build_set_from_local_spec(spec, tmp_path / "output")


def test_failed_new_build_does_not_leave_partial_output(project_root: Path, tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(project_root / "set_sources/specs/sample_set", spec)
    (spec / "assets/champions/sample_guardian.png").unlink()
    output = tmp_path / "output"

    with pytest.raises(FileNotFoundError, match="source asset"):
        build_set_from_local_spec(spec, output)

    assert not output.exists()
    assert list(tmp_path.glob(".output.build-*")) == []


def test_failed_overwrite_preserves_previous_valid_output(
    project_root: Path, tmp_path: Path
) -> None:
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


def test_builder_rejects_duplicate_json_key_in_source_spec(
    project_root: Path, tmp_path: Path
) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(project_root / "set_sources/specs/sample_set", spec)
    path = spec / "set_spec.json"
    original = path.read_text(encoding="utf-8").rstrip()
    assert original.endswith("}")
    broken = original[:-1] + ', "schema_version": 1}\n'
    path.write_text(broken, encoding="utf-8")

    with pytest.raises(ValueError, match="duplicate JSON object key"):
        build_set_from_local_spec(spec, tmp_path / "output")


def test_builder_rejects_source_asset_that_is_directory(project_root: Path, tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(project_root / "set_sources/specs/sample_set", spec)
    source_path = spec / "assets/champions/sample_guardian.png"
    source_path.unlink()
    source_path.mkdir()

    with pytest.raises(FileNotFoundError, match="source asset is not a file"):
        build_set_from_local_spec(spec, tmp_path / "output")


@pytest.mark.parametrize(
    "has_previous_output", [True, False], ids=["restore", "no-previous-output"]
)
def test_promotion_failure_preserves_recoverable_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, has_previous_output: bool
) -> None:
    from tft_builder.set_builder import _promote_staging_directory

    staging = tmp_path / ".output.build-test"
    output = tmp_path / "output"
    staging.mkdir()
    (staging / "new.txt").write_text("new", encoding="ascii")
    if has_previous_output:
        output.mkdir()
        (output / "old.txt").write_text("old", encoding="ascii")

    original_rename = Path.rename

    def controlled_rename(self: Path, target: Path):
        if self == staging and Path(target) == output:
            raise OSError("simulated promotion failure")
        return original_rename(self, target)

    monkeypatch.setattr(Path, "rename", controlled_rename)

    with pytest.raises(OSError, match="simulated promotion failure"):
        _promote_staging_directory(staging, output)

    if has_previous_output:
        assert output.is_dir()
        assert (output / "old.txt").read_text(encoding="ascii") == "old"
    else:
        assert not output.exists()
    assert staging.is_dir()


def test_builder_rejects_source_asset_link_even_when_target_stays_inside_spec(
    project_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = project_root / "set_sources/specs/sample_set"
    spec = tmp_path / "spec"
    shutil.copytree(source, spec)
    linked = spec / "assets/champions/internal_link.png"
    linked.write_bytes((spec / "assets/champions/sample_guardian.png").read_bytes())

    spec_path = spec / "set_spec.json"
    payload = json.loads(spec_path.read_text(encoding="utf-8"))
    payload["assets"]["assets/champions/sample_guardian.png"] = "assets/champions/internal_link.png"
    spec_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    original = set_builder.is_link_like
    monkeypatch.setattr(
        set_builder,
        "is_link_like",
        lambda path: path == linked or original(path),
    )

    with pytest.raises(ValueError, match="symbolic links or junctions"):
        build_set_from_local_spec(spec, tmp_path / "output")


def test_builder_rejects_source_spec_file_link_like_path(
    project_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(project_root / "set_sources/specs/sample_set", spec)
    spec_file = spec / "set_spec.json"
    original = set_builder.is_link_like
    monkeypatch.setattr(
        set_builder,
        "is_link_like",
        lambda path: path == spec_file or original(path),
    )

    with pytest.raises(ValueError, match="source spec file must not be"):
        build_set_from_local_spec(spec, tmp_path / "output")


def test_builder_rejects_source_spec_directory_link_like_path(
    project_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(project_root / "set_sources/specs/sample_set", spec)
    original = set_builder.is_link_like
    monkeypatch.setattr(
        set_builder,
        "is_link_like",
        lambda path: path == spec or original(path),
    )

    with pytest.raises(ValueError, match="source spec directory must not be"):
        build_set_from_local_spec(spec, tmp_path / "output")


def test_builder_rejects_existing_output_directory_link_like_path(
    project_root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "output"
    output.mkdir()
    original = set_builder.is_link_like
    monkeypatch.setattr(
        set_builder,
        "is_link_like",
        lambda path: path == output or original(path),
    )

    with pytest.raises(ValueError, match="output directory must not be"):
        build_set_from_local_spec(
            project_root / "set_sources/specs/sample_set", output, overwrite=True
        )


def test_builder_rejects_missing_source_spec_file(project_root: Path, tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(project_root / "set_sources/specs/sample_set", spec)
    (spec / "set_spec.json").unlink()

    with pytest.raises(FileNotFoundError):
        build_set_from_local_spec(spec, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_builder_rejects_non_utf8_source_spec(project_root: Path, tmp_path: Path) -> None:
    spec = tmp_path / "spec"
    shutil.copytree(project_root / "set_sources/specs/sample_set", spec)
    (spec / "set_spec.json").write_bytes(b"\xff\xfe\x00")

    with pytest.raises(UnicodeDecodeError):
        build_set_from_local_spec(spec, tmp_path / "output")
    assert not (tmp_path / "output").exists()


def test_builder_cleans_staging_directory_after_keyboard_interrupt(
    project_root: Path, tmp_path: Path, monkeypatch
) -> None:
    import tft_builder.set_builder as module

    def interrupted(*_args, **_kwargs) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(module, "_populate_staging_directory", interrupted)
    output = tmp_path / "output"

    with pytest.raises(KeyboardInterrupt):
        build_set_from_local_spec(project_root / "set_sources/specs/sample_set", output)

    assert not output.exists()
    assert list(tmp_path.glob(".output.build-*")) == []


def test_promotion_keyboard_interrupt_restores_previous_output(tmp_path: Path, monkeypatch) -> None:
    from tft_builder.set_builder import _promote_staging_directory

    staging = tmp_path / ".output.build-test"
    output = tmp_path / "output"
    staging.mkdir()
    output.mkdir()
    (staging / "new.txt").write_text("new", encoding="ascii")
    (output / "old.txt").write_text("old", encoding="ascii")

    original_rename = Path.rename

    def controlled_rename(self: Path, target: Path):
        if self == staging and Path(target) == output:
            raise KeyboardInterrupt
        return original_rename(self, target)

    monkeypatch.setattr(Path, "rename", controlled_rename)

    with pytest.raises(KeyboardInterrupt):
        _promote_staging_directory(staging, output)

    assert output.is_dir()
    assert (output / "old.txt").read_text(encoding="ascii") == "old"
    assert staging.is_dir()


def test_source_asset_resolver_rejects_defensive_parent_escape(tmp_path: Path) -> None:
    from tft_builder.set_builder import _resolve_source_asset

    spec = tmp_path / "spec"
    spec.mkdir()
    outside = tmp_path / "outside.png"
    outside.write_bytes(b"outside")

    with pytest.raises(ValueError, match="resolves outside source spec directory"):
        _resolve_source_asset(spec.resolve(), "../outside.png")
