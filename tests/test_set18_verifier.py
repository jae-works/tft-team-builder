from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from tft_builder.set_loader import load_set_directory


def load_verifier():
    path = Path(__file__).resolve().parents[1] / "tools/set_import/verify_enchanted_wilds.py"
    spec = importlib.util.spec_from_file_location("set18_verifier", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def verifier():
    return load_verifier()


def test_set18_verifier_rejects_the_small_development_sample(verifier, valid_set_dir) -> None:
    issues = verifier.verify_loaded_set(load_set_directory(valid_set_dir))

    assert "unexpected Set ID" in issues
    assert "expected 65 logical Champions" in issues
    assert "expected 136 reviewed Items" in issues
    assert "Elder Dragon is missing" in issues
    assert "Lux dynamic rule is missing" in issues
    assert "expected 246 runtime PNG assets" in issues


def test_source_lock_verifier_accepts_matching_metadata_and_reports_drift(
    verifier, valid_set_dir, tmp_path
) -> None:
    loaded = load_set_directory(valid_set_dir)
    lock = tmp_path / "source_lock.json"
    payload = {
        "set_id": loaded.manifest.set_id,
        "revision": loaded.manifest.revision,
        "sources": [],
    }
    lock.write_text(json.dumps(payload), encoding="utf-8")
    assert verifier.verify_source_lock(loaded, lock) == []

    payload["revision"] = "different"
    lock.write_text(json.dumps(payload), encoding="utf-8")
    assert verifier.verify_source_lock(loaded, lock) == ["source lock revision differs"]
