"""Minimal Block 1 application shell and startup integration.

The complete Builder UI starts in Block 4. Block 1 wires the non-visual startup path so
runtime directories, logging, and bundled Set validation are exercised together without
putting those responsibilities inside Flet controls.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .logging_config import configure_logging
from .paths import ApplicationPaths, build_application_paths
from .persistence import Database
from .set_loader import validate_all_sets

if TYPE_CHECKING:
    import flet as ft


@dataclass(frozen=True, slots=True)
class StartupState:
    paths: ApplicationPaths
    log_path: Path
    set_summary: tuple[str, ...]
    database_schema_version: int


def startup_set_summary(sets_dir: Path) -> tuple[str, ...]:
    reports = validate_all_sets(sets_dir)
    if not reports:
        return ("No bundled Sets found.",)

    lines: list[str] = []
    for report in reports:
        if report.is_valid and report.loaded_set is not None:
            loaded = report.loaded_set
            lines.append(
                f"{loaded.manifest.set_id}: valid - "
                f"{len(loaded.champions)} champions, {len(loaded.traits)} traits"
            )
        else:
            lines.append(f"{report.root.name}: invalid - {len(report.issues)} issue(s)")
    return tuple(lines)


def initialize_application(
    *,
    project_root: Path | None = None,
    data_dir_override: Path | None = None,
    assets_dir_override: Path | None = None,
) -> StartupState:
    """Initialize non-visual runtime services and return their resolved state."""

    paths = build_application_paths(
        project_root=project_root,
        data_dir_override=data_dir_override,
        assets_dir_override=assets_dir_override,
    )
    paths.ensure_runtime_directories()
    log_path = configure_logging(paths.user_log_dir)
    database_schema_version = Database(
        paths.database_path, backups_dir=paths.backups_dir
    ).initialize()
    set_summary = startup_set_summary(paths.bundled_sets_dir)

    logger = logging.getLogger("tft_builder.app")
    logger.info("Application startup initialized")
    logger.info("Bundled Set directory: %s", paths.bundled_sets_dir)
    for line in set_summary:
        logger.info("Set status: %s", line)

    return StartupState(
        paths=paths,
        log_path=log_path,
        set_summary=set_summary,
        database_schema_version=database_schema_version,
    )


def main(page: ft.Page) -> None:
    """Render the small Block 1 smoke-test shell."""

    import flet as ft

    state = initialize_application()
    page.title = "TFT Team Builder"
    page.add(
        ft.SafeArea(
            content=ft.Column(
                controls=[
                    ft.Text("TFT Team Builder", size=28, weight=ft.FontWeight.BOLD),
                    ft.Text("Block 2 persistence foundation is active."),
                    ft.Text(f"Database schema: {state.database_schema_version}"),
                    ft.Text("Bundled Set validation:"),
                    *[ft.Text(line) for line in state.set_summary],
                ]
            )
        )
    )
