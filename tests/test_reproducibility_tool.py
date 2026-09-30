from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

from tft_builder.file_integrity import sha256_file


def _load_tool():
    path = Path(__file__).resolve().parents[1] / "tools/set_import/compare_set_packages.py"
    spec = importlib.util.spec_from_file_location("compare_set_packages", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_compare_set_packages_accepts_identical_valid_packages(
    valid_set_dir: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    tool = _load_tool()
    first = tmp_path / "first"
    second = tmp_path / "second"
    shutil.copytree(valid_set_dir, first)
    shutil.copytree(valid_set_dir, second)
    monkeypatch.setattr(sys, "argv", ["compare_set_packages", str(first), str(second)])

    assert tool.main() == 0
    assert "VALID reproducible Set package" in capsys.readouterr().out


def test_compare_set_packages_rejects_content_drift(
    valid_set_dir: Path, tmp_path: Path, monkeypatch, capsys
) -> None:
    tool = _load_tool()
    first = tmp_path / "first"
    second = tmp_path / "second"
    shutil.copytree(valid_set_dir, first)
    shutil.copytree(valid_set_dir, second)
    overview = second / "SET_OVERVIEW.md"
    overview.write_text(overview.read_text(encoding="utf-8") + "\nDrift.\n", encoding="utf-8")
    source_manifest_path = second / "source_manifest.json"
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    source_manifest["generated_file_sha256"]["SET_OVERVIEW.md"] = sha256_file(overview)
    source_manifest_path.write_text(
        json.dumps(source_manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(sys, "argv", ["compare_set_packages", str(first), str(second)])

    assert tool.main() == 1
    output = capsys.readouterr().out
    assert "INVALID reproducibility comparison" in output
    assert "First:" in output
    assert "Second:" in output
