from __future__ import annotations

import logging
from pathlib import Path

from tft_builder.app import initialize_application, startup_set_summary


def test_startup_summary_reports_no_sets_for_empty_directory(tmp_path: Path) -> None:
    empty = tmp_path / "sets"
    empty.mkdir()
    assert startup_set_summary(empty) == ("No bundled Sets found.",)


def test_startup_summary_reports_valid_sample(project_root: Path) -> None:
    summary = startup_set_summary(project_root / "sets")
    assert len(summary) == 1
    assert summary[0] == "sample_set: valid - 3 champions, 3 traits"


def test_startup_summary_reports_invalid_set_without_crashing(tmp_path: Path, valid_set_dir: Path) -> None:
    import shutil

    sets_dir = tmp_path / "sets"
    sets_dir.mkdir()
    broken = sets_dir / "broken"
    shutil.copytree(valid_set_dir, broken)
    (broken / "assets/champions/sample_guardian.png").unlink()
    summary = startup_set_summary(sets_dir)
    assert summary == ("broken: invalid - 1 issue(s)",)


def close_application_logging() -> None:
    logger = logging.getLogger("tft_builder")
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def test_initialize_application_creates_runtime_dirs_logging_and_set_summary(
    project_root: Path, tmp_path: Path
) -> None:
    data_dir = tmp_path / "runtime"
    try:
        state = initialize_application(project_root=project_root, data_dir_override=data_dir)
        assert state.paths.user_data_dir == data_dir.resolve()
        assert state.paths.user_log_dir.is_dir()
        assert state.paths.backups_dir.is_dir()
        assert state.paths.exports_dir.is_dir()
        assert state.log_path == state.paths.user_log_dir / "app.log"
        assert state.log_path.is_file()
        assert state.set_summary == ("sample_set: valid - 3 champions, 3 traits",)
    finally:
        close_application_logging()


def test_initialize_application_handles_project_with_no_bundled_sets(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "sets").mkdir(parents=True)
    try:
        state = initialize_application(
            project_root=project,
            data_dir_override=tmp_path / "runtime",
        )
        assert state.set_summary == ("No bundled Sets found.",)
    finally:
        close_application_logging()
