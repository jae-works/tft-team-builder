from __future__ import annotations

from pathlib import Path

from tft_builder.devtools import main


def test_validate_set_command_returns_zero_for_valid_set(valid_set_dir: Path, capsys) -> None:
    result = main(["validate-set", str(valid_set_dir)])
    captured = capsys.readouterr()
    assert result == 0
    assert "VALID: sample_set" in captured.out


def test_validate_set_command_returns_one_for_invalid_set(fixture_sets_dir: Path, capsys) -> None:
    result = main(["validate-set", str(fixture_sets_dir / "invalid_missing_asset")])
    captured = capsys.readouterr()
    assert result == 1
    assert "INVALID" in captured.out
    assert "missing_asset" in captured.out


def test_inspect_set_command_prints_counts(valid_set_dir: Path, capsys) -> None:
    result = main(["inspect-set", str(valid_set_dir)])
    captured = capsys.readouterr()
    assert result == 0
    assert "Set ID: sample_set" in captured.out
    assert "Champions: 3" in captured.out
    assert "Traits: 3" in captured.out
    assert "Dynamic rules: 1" in captured.out


def test_build_set_command_builds_valid_output(project_root: Path, tmp_path: Path, capsys) -> None:
    output = tmp_path / "output"
    result = main(
        [
            "build-set",
            str(project_root / "set_sources/specs/sample_set"),
            str(output),
        ]
    )
    captured = capsys.readouterr()
    assert result == 0
    assert output.is_dir()
    assert "Built:" in captured.out


def test_build_set_command_overwrite_flag_is_forwarded(project_root: Path, tmp_path: Path) -> None:
    output = tmp_path / "output"
    output.mkdir()
    (output / "junk.txt").write_text("junk", encoding="utf-8")
    result = main(
        [
            "build-set",
            str(project_root / "set_sources/specs/sample_set"),
            str(output),
            "--overwrite",
        ]
    )
    assert result == 0
    assert not (output / "junk.txt").exists()
