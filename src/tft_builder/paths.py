"""Centralized read-only asset and writable runtime path handling.

Application code must not derive important paths from the process current working directory.
Flet provides explicit environment variables for packaged assets and writable application
storage. Developer tools and non-Flet tests use platformdirs as a platform-native fallback.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from platformdirs import PlatformDirs

from .constants import APP_NAME, DATABASE_FILENAME

DATA_DIR_ENV = "TFT_BUILDER_DATA_DIR"
ASSETS_DIR_ENV = "TFT_BUILDER_ASSETS_DIR"
FLET_ASSETS_DIR_ENV = "FLET_ASSETS_DIR"
FLET_DATA_DIR_ENV = "FLET_APP_STORAGE_DATA"
FLET_CACHE_DIR_ENV = "FLET_APP_STORAGE_CACHE"


def _expanded_path(value: str | Path) -> Path:
    """Return an absolute normalized path using the platform's normal home semantics."""

    return Path(value).expanduser().resolve()


def _environment_path(name: str) -> Path | None:
    value = os.environ.get(name)
    return _expanded_path(value) if value else None


@dataclass(frozen=True, slots=True)
class ApplicationPaths:
    """Resolved read-only and writable locations used by the application."""

    project_root: Path
    bundled_assets_dir: Path
    bundled_sets_dir: Path
    user_data_dir: Path
    database_path: Path
    user_config_dir: Path
    user_cache_dir: Path
    user_log_dir: Path
    user_sets_dir: Path
    backups_dir: Path
    exports_dir: Path

    def ensure_runtime_directories(self) -> None:
        """Create writable runtime directories owned by the application."""

        for path in (
            self.user_data_dir,
            self.user_config_dir,
            self.user_cache_dir,
            self.user_log_dir,
            self.user_sets_dir,
            self.backups_dir,
            self.exports_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


def default_project_root() -> Path:
    """Return the source checkout root without consulting the current working directory."""

    return Path(__file__).resolve().parents[2]


def default_source_assets_dir(project_root: Path | None = None) -> Path:
    """Return the local-development asset directory used by the Flet app."""

    root = _expanded_path(project_root or default_project_root())
    return root / "src" / "assets"


def _resolve_assets_dir(root: Path, assets_dir_override: Path | None) -> Path:
    if assets_dir_override is not None:
        return _expanded_path(assets_dir_override)

    project_override = _environment_path(ASSETS_DIR_ENV)
    if project_override is not None:
        return project_override

    flet_assets = _environment_path(FLET_ASSETS_DIR_ENV)
    if flet_assets is not None:
        return flet_assets

    return default_source_assets_dir(root)


def _resolve_writable_roots(data_dir_override: Path | None) -> tuple[Path, Path]:
    """Resolve durable data and regenerable cache roots in documented priority order."""

    explicit_data = (
        _expanded_path(data_dir_override)
        if data_dir_override is not None
        else _environment_path(DATA_DIR_ENV)
    )
    if explicit_data is not None:
        return explicit_data, explicit_data / "cache"

    flet_data = _environment_path(FLET_DATA_DIR_ENV)
    if flet_data is not None:
        return flet_data, _environment_path(FLET_CACHE_DIR_ENV) or flet_data / "cache"

    # Flet stores durable Windows app data under the roaming application-support location.
    # roaming=True keeps the non-Flet fallback aligned with that choice as closely as
    # platformdirs permits. appauthor=False avoids an unnecessary Author/App nesting layer.
    platform = PlatformDirs(APP_NAME, appauthor=False, roaming=True)
    return _expanded_path(platform.user_data_path), _expanded_path(platform.user_cache_path)


def build_application_paths(
    *,
    project_root: Path | None = None,
    data_dir_override: Path | None = None,
    assets_dir_override: Path | None = None,
) -> ApplicationPaths:
    """Resolve all application paths in one place.

    Read-only assets use this priority: explicit argument, project override environment
    variable, Flet packaged-assets environment variable, local ``src/assets`` fallback.

    Durable data uses this priority: explicit argument, project override environment variable,
    Flet application storage, platformdirs fallback. Config, logs, user Sets, backups and
    exports are stable children of that durable root. Cache is kept separate because the OS may
    purge it and the application must be able to rebuild it.
    """

    root = _expanded_path(project_root or default_project_root())
    bundled_assets_dir = _resolve_assets_dir(root, assets_dir_override)
    user_data_dir, user_cache_dir = _resolve_writable_roots(data_dir_override)

    return ApplicationPaths(
        project_root=root,
        bundled_assets_dir=bundled_assets_dir,
        bundled_sets_dir=bundled_assets_dir / "sets",
        user_data_dir=user_data_dir,
        database_path=user_data_dir / DATABASE_FILENAME,
        user_config_dir=user_data_dir / "config",
        user_cache_dir=user_cache_dir,
        user_log_dir=user_data_dir / "logs",
        user_sets_dir=user_data_dir / "sets",
        backups_dir=user_data_dir / "backups",
        exports_dir=user_data_dir / "exports",
    )
