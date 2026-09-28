from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def valid_set_dir(project_root: Path) -> Path:
    """Use the bundled sample Set as the single canonical valid integration fixture."""

    return project_root / "src" / "assets" / "sets" / "sample_set"


@pytest.fixture
def copied_valid_set(tmp_path: Path, valid_set_dir: Path) -> Path:
    destination = tmp_path / "set"
    shutil.copytree(valid_set_dir, destination)
    return destination


@pytest.fixture
def load_json():
    def _load(path: Path):
        return json.loads(path.read_text(encoding="utf-8"))

    return _load


@pytest.fixture
def save_json():
    def _save(path: Path, value: object) -> None:
        path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    return _save


@pytest.fixture
def refresh_generated_hashes(load_json, save_json):
    def _refresh(set_dir: Path) -> None:
        manifest = load_json(set_dir / "manifest.json")
        source_path = set_dir / manifest.get("source_manifest_file", "source_manifest.json")
        source = load_json(source_path)
        generated = {
            "manifest.json",
            manifest.get("champions_file", "data/champions.json"),
            manifest.get("items_file", "data/items.json"),
            manifest.get("traits_file", "data/traits.json"),
            manifest.get("dynamic_traits_file", "data/dynamic_traits.json"),
            manifest.get("team_planner_file", "data/team_planner.json"),
            manifest.get("source_inventory_file", "reports/source_inventory.json"),
            manifest.get("overview_file", "SET_OVERVIEW.md"),
        }
        locales_dir = manifest.get("locales_dir", "locales")
        generated.update(
            f"{locales_dir}/{locale}.json" for locale in manifest.get("supported_locales", [])
        )
        source["generated_file_sha256"] = {
            relative: hashlib.sha256((set_dir / relative).read_bytes()).hexdigest()
            for relative in sorted(generated)
            if (set_dir / relative).is_file()
        }
        save_json(source_path, source)

    return _refresh
