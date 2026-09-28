"""Application startup, Team-library navigation and Flet composition boundary."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import UUID

from .builder import TeamEditor
from .constants import APP_NAME
from .logging_config import configure_logging
from .paths import ApplicationPaths, build_application_paths
from .persistence import AutosaveService, Database, TeamRepository
from .set_loader import LoadedSet, ValidationReport, validate_all_sets

if TYPE_CHECKING:
    import flet as ft


@dataclass(frozen=True, slots=True)
class StartupState:
    paths: ApplicationPaths
    log_path: Path
    set_summary: tuple[str, ...]
    loaded_sets: tuple[LoadedSet, ...]
    database_schema_version: int


@dataclass(frozen=True, slots=True)
class ApplicationRuntime:
    """Validated Sets and one repository shared by Library and Builder screens."""

    loaded_sets: tuple[LoadedSet, ...]
    repository: TeamRepository


class ApplicationStartupError(RuntimeError):
    """Raised when no safe interactive application runtime can be created."""


def _summarize_set_reports(reports: tuple[ValidationReport, ...]) -> tuple[str, ...]:
    """Return startup log lines without repeating Set validation work."""

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


def startup_set_summary(sets_dir: Path) -> tuple[str, ...]:
    """Validate bundled Sets once and return human-readable startup status lines."""

    return _summarize_set_reports(validate_all_sets(sets_dir))


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
    reports = validate_all_sets(paths.bundled_sets_dir)
    set_summary = _summarize_set_reports(reports)
    loaded_sets = tuple(
        report.loaded_set
        for report in reports
        if report.is_valid and report.loaded_set is not None
    )

    logger = logging.getLogger("tft_builder.app")
    logger.info("Application startup initialized")
    logger.info("Bundled Set directory: %s", paths.bundled_sets_dir)
    for line in set_summary:
        logger.info("Set status: %s", line)

    return StartupState(
        paths=paths,
        log_path=log_path,
        set_summary=set_summary,
        loaded_sets=loaded_sets,
        database_schema_version=database_schema_version,
    )


def initialize_runtime(state: StartupState) -> ApplicationRuntime:
    """Resolve validated Sets and the shared Team repository."""

    loaded_sets = state.loaded_sets
    if not loaded_sets:
        raise ApplicationStartupError("No valid bundled Set is available")

    seen: set[str] = set()
    for loaded_set in loaded_sets:
        set_id = loaded_set.manifest.set_id
        if set_id in seen:
            raise ApplicationStartupError(f"Duplicate bundled Set ID: {set_id}")
        seen.add(set_id)

    repository = TeamRepository(
        Database(state.paths.database_path, backups_dir=state.paths.backups_dir)
    )
    return ApplicationRuntime(loaded_sets=loaded_sets, repository=repository)


def main(page: ft.Page) -> None:
    """Initialize the application and render the Team library with Builder navigation."""

    import flet as ft

    from .builder_view import BuilderView
    from .library_view import LibrarySessionState, LibraryView

    state = initialize_application()
    page.title = APP_NAME
    try:
        runtime = initialize_runtime(state)
    except ApplicationStartupError as error:
        logging.getLogger("tft_builder.app").error("Application startup blocked: %s", error)
        page.add(
            ft.SafeArea(
                expand=True,
                content=ft.Column(
                    controls=[
                        ft.Text(APP_NAME, size=28, weight=ft.FontWeight.BOLD),
                        ft.Text("Application startup failed", weight=ft.FontWeight.BOLD),
                        ft.Text(str(error), key="app-startup-error"),
                    ]
                ),
            )
        )
        return

    sets_by_id = {loaded_set.manifest.set_id: loaded_set for loaded_set in runtime.loaded_sets}
    session = LibrarySessionState()

    def show_library() -> None:
        page.on_keyboard_event = None
        page.clean()
        LibraryView(
            page,
            runtime.loaded_sets,
            runtime.repository,
            assets_dir=state.paths.bundled_assets_dir,
            on_open=show_builder,
            session=session,
        ).mount()

    def show_builder(team_id: UUID) -> None:
        if not runtime.repository.mark_opened(team_id):
            raise ApplicationStartupError(f"Unknown Team ID: {team_id}")
        team = runtime.repository.load(team_id)
        loaded_set = sets_by_id.get(team.set_id)
        if loaded_set is None:
            raise ApplicationStartupError(
                f"Team requires Set '{team.set_id}', but that Set is not available and valid"
            )
        page.clean()
        BuilderView(
            page,
            loaded_set,
            TeamEditor(team),
            AutosaveService(runtime.repository),
            assets_dir=state.paths.bundled_assets_dir,
            on_back=show_library,
        ).mount()

    show_library()
