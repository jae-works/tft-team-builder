"""Centralized project and runtime path handling.

No application code should depend on the process current working directory. The helper
functions in this module are intentionally small so path behavior stays obvious and easy
to test.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from platformdirs import PlatformDirs

from .constants import APP_AUTHOR, APP_NAME

DATA_DIR_ENV = "TFT_BUILDER_DATA_DIR"


@dataclass(frozen=True, slots=True)
class ApplicationPaths:
    """Resolved read-only and writable locations used by the application."""

    project_root: Path
    bundled_sets_dir: Path
    user_data_dir: Path
    user_config_dir: Path
    user_cache_dir: Path
    user_log_dir: Path
    user_sets_dir: Path
    backups_dir: Path
    exports_dir: Path

    def ensure_runtime_directories(self) -> None:
        """Create writable runtime directories that the application owns."""

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
    """Return the source or packaged application root without using the CWD."""

    return Path(__file__).resolve().parents[2]


def build_application_paths(
    *,
    project_root: Path | None = None,
    data_dir_override: Path | None = None,
) -> ApplicationPaths:
    """Resolve all application paths in one place.

    ``data_dir_override`` is primarily useful for tests and portable/development workflows.
    The environment variable exists as a user-visible escape hatch and is also convenient
    for automated testing. When neither is provided, platformdirs selects the normal
    per-user data/config/cache/log locations for the operating system.
    """

    root = (project_root or default_project_root()).resolve()
    explicit_data_dir = data_dir_override
    if explicit_data_dir is None:
        environment_value = os.environ.get(DATA_DIR_ENV)
        if environment_value:
            explicit_data_dir = Path(environment_value)

    platform = PlatformDirs(APP_NAME, APP_AUTHOR, roaming=False)
    if explicit_data_dir is not None:
        user_data_dir = explicit_data_dir.expanduser().resolve()
        user_config_dir = user_data_dir / "config"
        user_cache_dir = user_data_dir / "cache"
        user_log_dir = user_data_dir / "logs"
    else:
        user_data_dir = Path(platform.user_data_path)
        user_config_dir = Path(platform.user_config_path)
        user_cache_dir = Path(platform.user_cache_path)
        user_log_dir = Path(platform.user_log_path)

    return ApplicationPaths(
        project_root=root,
        bundled_sets_dir=root / "sets",
        user_data_dir=user_data_dir,
        user_config_dir=user_config_dir,
        user_cache_dir=user_cache_dir,
        user_log_dir=user_log_dir,
        user_sets_dir=user_data_dir / "sets",
        backups_dir=user_data_dir / "backups",
        exports_dir=user_data_dir / "exports",
    )
