from __future__ import annotations

from dataclasses import fields
from pathlib import Path

from tft_builder.paths import (
    ASSETS_DIR_ENV,
    DATA_DIR_ENV,
    FLET_ASSETS_DIR_ENV,
    FLET_CACHE_DIR_ENV,
    FLET_DATA_DIR_ENV,
    build_application_paths,
    default_project_root,
    default_source_assets_dir,
)


def clear_path_environment(monkeypatch) -> None:
    for name in (
        ASSETS_DIR_ENV,
        DATA_DIR_ENV,
        FLET_ASSETS_DIR_ENV,
        FLET_DATA_DIR_ENV,
        FLET_CACHE_DIR_ENV,
    ):
        monkeypatch.delenv(name, raising=False)


def test_default_project_root_contains_pyproject() -> None:
    root = default_project_root()
    assert (root / "pyproject.toml").is_file()


def test_default_source_assets_live_under_src_assets(project_root: Path) -> None:
    assert default_source_assets_dir(project_root) == project_root.resolve() / "src" / "assets"


def test_paths_use_explicit_project_root_and_local_assets(tmp_path: Path, monkeypatch) -> None:
    clear_path_environment(monkeypatch)
    root = tmp_path / "project"
    root.mkdir()
    paths = build_application_paths(project_root=root, data_dir_override=tmp_path / "data")
    assert paths.project_root == root.resolve()
    assert paths.bundled_assets_dir == root.resolve() / "src" / "assets"
    assert paths.bundled_sets_dir == root.resolve() / "src" / "assets" / "sets"


def test_explicit_assets_dir_has_highest_priority(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(ASSETS_DIR_ENV, str(tmp_path / "project-assets"))
    monkeypatch.setenv(FLET_ASSETS_DIR_ENV, str(tmp_path / "flet-assets"))
    explicit = tmp_path / "explicit-assets"
    paths = build_application_paths(
        project_root=tmp_path,
        data_dir_override=tmp_path / "data",
        assets_dir_override=explicit,
    )
    assert paths.bundled_assets_dir == explicit.resolve()


def test_project_assets_environment_wins_over_flet_assets(tmp_path: Path, monkeypatch) -> None:
    project_assets = tmp_path / "project-assets"
    monkeypatch.setenv(ASSETS_DIR_ENV, str(project_assets))
    monkeypatch.setenv(FLET_ASSETS_DIR_ENV, str(tmp_path / "flet-assets"))
    paths = build_application_paths(project_root=tmp_path, data_dir_override=tmp_path / "data")
    assert paths.bundled_assets_dir == project_assets.resolve()


def test_flet_assets_environment_is_used_when_no_project_override(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv(ASSETS_DIR_ENV, raising=False)
    flet_assets = tmp_path / "flet-assets"
    monkeypatch.setenv(FLET_ASSETS_DIR_ENV, str(flet_assets))
    paths = build_application_paths(project_root=tmp_path, data_dir_override=tmp_path / "data")
    assert paths.bundled_assets_dir == flet_assets.resolve()
    assert paths.bundled_sets_dir == flet_assets.resolve() / "sets"


def test_explicit_data_dir_controls_writable_children(tmp_path: Path, monkeypatch) -> None:
    clear_path_environment(monkeypatch)
    data = tmp_path / "custom-data"
    paths = build_application_paths(project_root=tmp_path, data_dir_override=data)
    assert paths.user_data_dir == data.resolve()
    assert paths.database_path == data.resolve() / "builder.db"
    assert paths.user_config_dir == data.resolve() / "config"
    assert paths.user_cache_dir == data.resolve() / "cache"
    assert paths.user_log_dir == data.resolve() / "logs"
    assert paths.user_sets_dir == data.resolve() / "sets"
    assert paths.backups_dir == data.resolve() / "backups"
    assert paths.exports_dir == data.resolve() / "exports"


def test_environment_data_dir_is_honored(tmp_path: Path, monkeypatch) -> None:
    data = tmp_path / "environment-data"
    monkeypatch.setenv(DATA_DIR_ENV, str(data))
    monkeypatch.setenv(FLET_DATA_DIR_ENV, str(tmp_path / "flet-data"))
    paths = build_application_paths(project_root=tmp_path)
    assert paths.user_data_dir == data.resolve()


def test_explicit_data_dir_wins_over_all_environment_values(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(DATA_DIR_ENV, str(tmp_path / "environment-data"))
    monkeypatch.setenv(FLET_DATA_DIR_ENV, str(tmp_path / "flet-data"))
    explicit = tmp_path / "explicit-data"
    paths = build_application_paths(project_root=tmp_path, data_dir_override=explicit)
    assert paths.user_data_dir == explicit.resolve()


def test_flet_storage_is_used_when_project_data_override_is_absent(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv(DATA_DIR_ENV, raising=False)
    data = tmp_path / "flet-data"
    cache = tmp_path / "flet-cache"
    monkeypatch.setenv(FLET_DATA_DIR_ENV, str(data))
    monkeypatch.setenv(FLET_CACHE_DIR_ENV, str(cache))
    paths = build_application_paths(project_root=tmp_path)
    assert paths.user_data_dir == data.resolve()
    assert paths.database_path == data.resolve() / "builder.db"
    assert paths.user_config_dir == data.resolve() / "config"
    assert paths.user_cache_dir == cache.resolve()
    assert paths.user_log_dir == data.resolve() / "logs"


def test_flet_data_falls_back_to_data_subdir_cache_when_cache_env_missing(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.delenv(DATA_DIR_ENV, raising=False)
    monkeypatch.delenv(FLET_CACHE_DIR_ENV, raising=False)
    data = tmp_path / "flet-data"
    monkeypatch.setenv(FLET_DATA_DIR_ENV, str(data))
    paths = build_application_paths(project_root=tmp_path)
    assert paths.user_cache_dir == data.resolve() / "cache"


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
    assert not paths.database_path.exists()


def test_ensure_runtime_directories_is_idempotent(tmp_path: Path) -> None:
    paths = build_application_paths(project_root=tmp_path, data_dir_override=tmp_path / "data")
    paths.ensure_runtime_directories()
    paths.ensure_runtime_directories()
    assert paths.user_data_dir.is_dir()


def test_path_resolution_does_not_depend_on_current_working_directory(
    tmp_path: Path, monkeypatch
) -> None:
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


def test_environment_variable_names_are_ascii_and_stable() -> None:
    assert DATA_DIR_ENV == "TFT_BUILDER_DATA_DIR"
    assert ASSETS_DIR_ENV == "TFT_BUILDER_ASSETS_DIR"
    assert FLET_ASSETS_DIR_ENV == "FLET_ASSETS_DIR"
    assert FLET_DATA_DIR_ENV == "FLET_APP_STORAGE_DATA"
    assert FLET_CACHE_DIR_ENV == "FLET_APP_STORAGE_CACHE"
    assert all(
        value.isascii()
        for value in (
            DATA_DIR_ENV,
            ASSETS_DIR_ENV,
            FLET_ASSETS_DIR_ENV,
            FLET_DATA_DIR_ENV,
            FLET_CACHE_DIR_ENV,
        )
    )


def test_environment_override_uses_platform_tilde_expansion(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv(DATA_DIR_ENV, "~/builder-data")
    paths = build_application_paths(project_root=tmp_path)
    assert paths.user_data_dir == Path("~/builder-data").expanduser().resolve()


def test_platformdirs_fallback_is_used_outside_flet(tmp_path: Path, monkeypatch) -> None:
    import tft_builder.paths as paths_module

    clear_path_environment(monkeypatch)

    class FakePlatformDirs:
        def __init__(self, appname: str, appauthor: bool, roaming: bool) -> None:
            assert appname == "TFT Team Builder"
            assert appauthor is False
            assert roaming is True
            self.user_data_path = tmp_path / "platform-data"
            self.user_cache_path = tmp_path / "platform-cache"

    monkeypatch.setattr(paths_module, "PlatformDirs", FakePlatformDirs)
    paths = build_application_paths(project_root=tmp_path)

    assert paths.user_data_dir == (tmp_path / "platform-data").resolve()
    assert paths.database_path == (tmp_path / "platform-data/builder.db").resolve()
    assert paths.user_config_dir == (tmp_path / "platform-data/config").resolve()
    assert paths.user_cache_dir == (tmp_path / "platform-cache").resolve()
    assert paths.user_log_dir == (tmp_path / "platform-data/logs").resolve()
