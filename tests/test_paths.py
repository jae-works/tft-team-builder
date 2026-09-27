from __future__ import annotations

import os
from dataclasses import fields
from pathlib import Path

from tft_builder.paths import DATA_DIR_ENV, build_application_paths, default_project_root


def test_default_project_root_contains_pyproject() -> None:
    root = default_project_root()
    assert (root / "pyproject.toml").is_file()


def test_paths_use_explicit_project_root(tmp_path: Path) -> None:
    root = tmp_path / "project"
    root.mkdir()
    paths = build_application_paths(project_root=root, data_dir_override=tmp_path / "data")
    assert paths.project_root == root.resolve()
    assert paths.bundled_sets_dir == root.resolve() / "sets"


def test_explicit_data_dir_controls_all_writable_children(tmp_path: Path) -> None:
    data = tmp_path / "custom-data"
    paths = build_application_paths(project_root=tmp_path, data_dir_override=data)
    assert paths.user_data_dir == data.resolve()
    assert paths.user_config_dir == data.resolve() / "config"
    assert paths.user_cache_dir == data.resolve() / "cache"
    assert paths.user_log_dir == data.resolve() / "logs"
    assert paths.user_sets_dir == data.resolve() / "sets"
    assert paths.backups_dir == data.resolve() / "backups"
    assert paths.exports_dir == data.resolve() / "exports"


def test_environment_data_dir_is_honored(monkeypatch, tmp_path: Path) -> None:
    data = tmp_path / "environment-data"
    monkeypatch.setenv(DATA_DIR_ENV, str(data))
    paths = build_application_paths(project_root=tmp_path)
    assert paths.user_data_dir == data.resolve()


def test_explicit_data_dir_wins_over_environment(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path / "environment-data"))
    explicit = tmp_path / "explicit-data"
    paths = build_application_paths(project_root=tmp_path, data_dir_override=explicit)
    assert paths.user_data_dir == explicit.resolve()


def test_runtime_directories_are_created_only_when_requested(tmp_path: Path) -> None:
    data = tmp_path / "data"
    paths = build_application_paths(project_root=tmp_path, data_dir_override=data)
    assert not data.exists()
    paths.ensure_runtime_directories()
    expected = {
        paths.user_data_dir,
        paths.user_config_dir,
        paths.user_cache_dir,
        paths.user_log_dir,
        paths.user_sets_dir,
        paths.backups_dir,
        paths.exports_dir,
    }
    assert all(path.is_dir() for path in expected)


def test_path_resolution_does_not_depend_on_current_working_directory(tmp_path: Path, monkeypatch) -> None:
    original = default_project_root()
    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    monkeypatch.chdir(unrelated)
    assert default_project_root() == original


def test_every_application_path_field_is_a_path(tmp_path: Path) -> None:
    paths = build_application_paths(project_root=tmp_path, data_dir_override=tmp_path / "data")
    values = [getattr(paths, field.name) for field in fields(paths)]
    assert values
    assert all(isinstance(value, Path) for value in values)


def test_environment_variable_name_is_ascii_and_stable() -> None:
    assert DATA_DIR_ENV == "TFT_BUILDER_DATA_DIR"
    assert DATA_DIR_ENV.isascii()


def test_environment_override_expands_user_home(monkeypatch, tmp_path: Path) -> None:
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.setenv(DATA_DIR_ENV, "~/builder-data")
    paths = build_application_paths(project_root=tmp_path)
    assert paths.user_data_dir == (fake_home / "builder-data").resolve()
