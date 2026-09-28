from __future__ import annotations

import logging
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tft_builder.app import (
    BuilderStartupError,
    initialize_application,
    initialize_builder_runtime,
    startup_set_summary,
)
from tft_builder.models import Team
from tft_builder.persistence import Database, TeamRepository


def test_startup_summary_reports_no_sets_for_empty_directory(tmp_path: Path) -> None:
    empty = tmp_path / "sets"
    empty.mkdir()
    assert startup_set_summary(empty) == ("No bundled Sets found.",)


def test_startup_summary_reports_valid_sample(project_root: Path) -> None:
    summary = startup_set_summary(project_root / "src" / "assets" / "sets")
    assert summary == ("sample_set: valid - 3 champions, 3 traits",)


def test_startup_summary_reports_invalid_set_without_crashing(
    tmp_path: Path, valid_set_dir: Path
) -> None:
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
        if not getattr(handler, "_tft_builder_managed_handler", False):
            continue
        logger.removeHandler(handler)
        handler.close()


def test_initialize_application_creates_runtime_dirs_logging_and_set_summary(
    project_root: Path, tmp_path: Path
) -> None:
    data_dir = tmp_path / "runtime"
    try:
        state = initialize_application(project_root=project_root, data_dir_override=data_dir)
        assert state.paths.user_data_dir == data_dir.resolve()
        assert state.paths.bundled_assets_dir == project_root / "src" / "assets"
        assert state.paths.user_log_dir.is_dir()
        assert state.paths.backups_dir.is_dir()
        assert state.paths.exports_dir.is_dir()
        assert state.log_path == state.paths.user_log_dir / "app.log"
        assert state.log_path.is_file()
        assert state.set_summary == ("sample_set: valid - 3 champions, 3 traits",)
        assert state.database_schema_version == 2
        assert state.paths.database_path.is_file()
    finally:
        close_application_logging()


def test_initialize_application_supports_explicit_packaged_assets(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    assets = tmp_path / "packaged-assets"
    (assets / "sets").mkdir(parents=True)
    try:
        state = initialize_application(
            project_root=project,
            data_dir_override=tmp_path / "runtime",
            assets_dir_override=assets,
        )
        assert state.paths.bundled_assets_dir == assets.resolve()
        assert state.set_summary == ("No bundled Sets found.",)
        assert state.database_schema_version == 2
    finally:
        close_application_logging()


def runtime_state(project_root: Path, tmp_path: Path):
    return initialize_application(
        project_root=project_root,
        data_dir_override=tmp_path / "runtime",
    )


def test_builder_runtime_creates_initial_team_and_reopens_latest(
    project_root: Path, tmp_path: Path
) -> None:
    try:
        state = runtime_state(project_root, tmp_path)
        first = initialize_builder_runtime(state)
        assert first.editor.team.name == "Untitled Team"
        assert first.editor.team.set_id == "sample_set"
        assert first.loaded_set.manifest.set_id == "sample_set"
        first.editor.rename_team("Persisted")
        first.autosave.save_now(first.editor.team)
        second = initialize_builder_runtime(state)
        assert second.editor.team.team_id == first.editor.team.team_id
        assert second.editor.team.name == "Persisted"
    finally:
        close_application_logging()


def test_builder_runtime_rejects_no_valid_sets(project_root: Path, tmp_path: Path) -> None:
    assets = tmp_path / "assets"
    (assets / "sets").mkdir(parents=True)
    try:
        state = initialize_application(
            project_root=project_root,
            data_dir_override=tmp_path / "runtime",
            assets_dir_override=assets,
        )
        with pytest.raises(BuilderStartupError, match="No valid bundled Set"):
            initialize_builder_runtime(state)
    finally:
        close_application_logging()


def test_builder_runtime_rejects_team_whose_set_is_unavailable(
    project_root: Path, tmp_path: Path
) -> None:
    try:
        state = runtime_state(project_root, tmp_path)
        repository = TeamRepository(Database(state.paths.database_path))
        repository.save(Team.create(set_id="missing_set", name="Broken"))
        with pytest.raises(BuilderStartupError, match="missing_set"):
            initialize_builder_runtime(state)
    finally:
        close_application_logging()


def test_builder_runtime_rejects_duplicate_set_ids(
    project_root: Path, tmp_path: Path, monkeypatch
) -> None:
    import tft_builder.app as app_module
    from tft_builder.set_loader import load_set_directory

    try:
        state = runtime_state(project_root, tmp_path)
        loaded = load_set_directory(state.paths.bundled_sets_dir / "sample_set")
        report = SimpleNamespace(is_valid=True, loaded_set=loaded)
        monkeypatch.setattr(app_module, "validate_all_sets", lambda _path: (report, report))
        with pytest.raises(BuilderStartupError, match="Duplicate bundled Set ID"):
            initialize_builder_runtime(state)
    finally:
        close_application_logging()


class FakeControl:
    def __init__(self, *args, **kwargs) -> None:
        self.value = args[0] if args else kwargs.pop("value", None)
        for name, value in kwargs.items():
            setattr(self, name, value)
        if not hasattr(self, "controls"):
            self.controls = []


class FakePage:
    def __init__(self) -> None:
        self.title = ""
        self.controls = []

    def add(self, control) -> None:
        self.controls.append(control)


def test_main_mounts_builder_view(monkeypatch) -> None:
    import tft_builder.app as app_module
    import tft_builder.builder_view as view_module

    fake_flet = SimpleNamespace(
        SafeArea=FakeControl,
        Column=FakeControl,
        Text=FakeControl,
        FontWeight=SimpleNamespace(BOLD="bold"),
    )
    monkeypatch.setitem(sys.modules, "flet", fake_flet)
    state = SimpleNamespace(paths=SimpleNamespace(bundled_assets_dir=Path("assets")))
    runtime = SimpleNamespace(loaded_set=object(), editor=object(), autosave=object())
    monkeypatch.setattr(app_module, "initialize_application", lambda: state)
    monkeypatch.setattr(app_module, "initialize_builder_runtime", lambda _state: runtime)
    mounted = []

    class FakeBuilderView:
        def __init__(self, *args, **kwargs) -> None:
            mounted.append((args, kwargs))

        def mount(self) -> None:
            mounted.append("mounted")

    monkeypatch.setattr(view_module, "BuilderView", FakeBuilderView)
    page = FakePage()
    app_module.main(page)
    assert page.title == "TFT Team Builder"
    assert mounted[-1] == "mounted"


def test_main_renders_blocking_startup_error(monkeypatch) -> None:
    import tft_builder.app as app_module

    fake_flet = SimpleNamespace(
        SafeArea=FakeControl,
        Column=FakeControl,
        Text=FakeControl,
        FontWeight=SimpleNamespace(BOLD="bold"),
    )
    monkeypatch.setitem(sys.modules, "flet", fake_flet)
    monkeypatch.setattr(
        app_module,
        "initialize_application",
        lambda: SimpleNamespace(paths=SimpleNamespace(bundled_assets_dir=Path("assets"))),
    )
    monkeypatch.setattr(
        app_module,
        "initialize_builder_runtime",
        lambda _state: (_ for _ in ()).throw(BuilderStartupError("broken set")),
    )
    page = FakePage()
    app_module.main(page)
    assert page.title == "TFT Team Builder"
    assert page.controls[0].content.controls[-1].value == "broken set"
    assert page.controls[0].content.controls[-1].key == "builder-startup-error"
