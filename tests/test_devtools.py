from __future__ import annotations

import sys
from pathlib import Path

import pytest

from tft_builder.devtools import main


def test_validate_set_command_returns_zero_for_valid_set(valid_set_dir: Path, capsys) -> None:
    result = main(["validate-set", str(valid_set_dir)])
    captured = capsys.readouterr()
    assert result == 0
    assert "VALID: sample_set" in captured.out


def test_validate_set_command_returns_one_for_invalid_set(copied_valid_set: Path, capsys) -> None:
    (copied_valid_set / "assets/champions/sample_guardian.png").unlink()
    result = main(["validate-set", str(copied_valid_set)])
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


def test_importing_package_main_module_has_no_cli_side_effect() -> None:
    import importlib

    module = importlib.import_module("tft_builder.__main__")
    assert module.main is main


def test_package_module_entry_point_executes_developer_cli(
    valid_set_dir: Path, project_root: Path, monkeypatch: pytest.MonkeyPatch, capsys
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["python -m tft_builder", "validate-set", str(valid_set_dir)],
    )
    entry_path = project_root / "src" / "tft_builder" / "__main__.py"
    namespace = {
        "__name__": "__main__",
        "__package__": "tft_builder",
        "__file__": str(entry_path),
    }

    with pytest.raises(SystemExit) as exc_info:
        exec(compile(entry_path.read_bytes(), str(entry_path), "exec"), namespace)

    assert exc_info.value.code == 0
    assert "VALID: sample_set" in capsys.readouterr().out
