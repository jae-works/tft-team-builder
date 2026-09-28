"""Application startup, Builder bootstrap and Flet composition boundary."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .builder import TeamEditor
from .constants import APP_NAME
from .logging_config import configure_logging
from .models import Team
from .paths import ApplicationPaths, build_application_paths
from .persistence import AutosaveService, Database, TeamRepository
from .set_loader import LoadedSet, validate_all_sets

if TYPE_CHECKING:
    import flet as ft


@dataclass(frozen=True, slots=True)
class StartupState:
    paths: ApplicationPaths
    log_path: Path
    set_summary: tuple[str, ...]
    database_schema_version: int


@dataclass(frozen=True, slots=True)
class BuilderRuntime:
    loaded_set: LoadedSet
    editor: TeamEditor
    autosave: AutosaveService


class BuilderStartupError(RuntimeError):
    """Raised when the current pre-library Builder bootstrap cannot continue safely."""


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


def initialize_builder_runtime(state: StartupState) -> BuilderRuntime:
    """Open or create the current Builder Team and resolve its exact validated Set."""

    reports = validate_all_sets(state.paths.bundled_sets_dir)
    loaded_sets = [
        report.loaded_set for report in reports if report.is_valid and report.loaded_set is not None
    ]
    if not loaded_sets:
        raise BuilderStartupError("No valid bundled Set is available for the Builder")

    sets_by_id: dict[str, LoadedSet] = {}
    for loaded_set in loaded_sets:
        set_id = loaded_set.manifest.set_id
        if set_id in sets_by_id:
            raise BuilderStartupError(f"Duplicate bundled Set ID: {set_id}")
        sets_by_id[set_id] = loaded_set

    repository = TeamRepository(
        Database(state.paths.database_path, backups_dir=state.paths.backups_dir)
    )
    team_ids = repository.list_ids()
    if team_ids:
        team = repository.load(team_ids[0])
    else:
        first_set = min(loaded_sets, key=lambda item: item.manifest.set_id)
        team = Team.create(set_id=first_set.manifest.set_id, name="Untitled Team")
        repository.save(team)

    loaded_set = sets_by_id.get(team.set_id)
    if loaded_set is None:
        raise BuilderStartupError(
            f"Team requires Set '{team.set_id}', but that Set is not available and valid"
        )
    return BuilderRuntime(
        loaded_set=loaded_set,
        editor=TeamEditor(team),
        autosave=AutosaveService(repository),
    )


def main(page: ft.Page) -> None:
    """Initialize the application and render the first complete functional Builder screen."""

    import flet as ft

    from .builder_view import BuilderView

    state = initialize_application()
    page.title = APP_NAME
    try:
        runtime = initialize_builder_runtime(state)
    except BuilderStartupError as error:
        logging.getLogger("tft_builder.app").error("Builder startup blocked: %s", error)
        page.add(
            ft.SafeArea(
                expand=True,
                content=ft.Column(
                    controls=[
                        ft.Text(APP_NAME, size=28, weight=ft.FontWeight.BOLD),
                        ft.Text("Builder startup failed", weight=ft.FontWeight.BOLD),
                        ft.Text(str(error), key="builder-startup-error"),
                    ]
                ),
            )
        )
        return

    BuilderView(
        page,
        runtime.loaded_set,
        runtime.editor,
        runtime.autosave,
        assets_dir=state.paths.bundled_assets_dir,
    ).mount()
