from __future__ import annotations

import logging
import shutil
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from tft_builder.app import (
    ApplicationStartupError,
    initialize_application,
    initialize_runtime,
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


def test_runtime_exposes_valid_sets_and_shared_repository(
    project_root: Path, tmp_path: Path
) -> None:
    try:
        state = runtime_state(project_root, tmp_path)
        runtime = initialize_runtime(state)
        assert [item.manifest.set_id for item in runtime.loaded_sets] == ["sample_set"]
        team = Team.create(set_id="sample_set", name="Persisted")
        runtime.repository.save(team)
        assert runtime.repository.load(team.team_id) == team
    finally:
        close_application_logging()


def test_runtime_rejects_no_valid_sets(project_root: Path, tmp_path: Path) -> None:
    assets = tmp_path / "assets"
    (assets / "sets").mkdir(parents=True)
    try:
        state = initialize_application(
            project_root=project_root,
            data_dir_override=tmp_path / "runtime",
            assets_dir_override=assets,
        )
        with pytest.raises(ApplicationStartupError, match="No valid bundled Set"):
            initialize_runtime(state)
    finally:
        close_application_logging()


def test_runtime_rejects_duplicate_set_ids(project_root: Path, tmp_path: Path, monkeypatch) -> None:
    import tft_builder.app as app_module
    from tft_builder.set_loader import load_set_directory

    try:
        state = runtime_state(project_root, tmp_path)
        loaded = load_set_directory(state.paths.bundled_sets_dir / "sample_set")
        report = SimpleNamespace(is_valid=True, loaded_set=loaded)
        monkeypatch.setattr(app_module, "validate_all_sets", lambda _path: (report, report))
        with pytest.raises(ApplicationStartupError, match="Duplicate bundled Set ID"):
            initialize_runtime(state)
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
        self.on_keyboard_event = None
        self.cleaned = 0

    def add(self, control) -> None:
        self.controls.append(control)

    def clean(self) -> None:
        self.controls.clear()
        self.cleaned += 1


def test_main_mounts_library_and_open_callback_mounts_builder(monkeypatch) -> None:
    import tft_builder.app as app_module
    import tft_builder.builder_view as builder_module
    import tft_builder.library_view as library_module

    fake_flet = SimpleNamespace(
        SafeArea=FakeControl,
        Column=FakeControl,
        Text=FakeControl,
        FontWeight=SimpleNamespace(BOLD="bold"),
    )
    monkeypatch.setitem(sys.modules, "flet", fake_flet)
    paths = SimpleNamespace(bundled_assets_dir=Path("assets"))
    state = SimpleNamespace(paths=paths)
    team = Team.create(set_id="sample_set", name="Team")

    repository_events = []

    class FakeRepository:
        def mark_opened(self, team_id):
            repository_events.append(("mark", team_id))
            return team_id == team.team_id

        def load(self, team_id):
            repository_events.append(("load", team_id))
            assert team_id == team.team_id
            return team

    loaded_set = SimpleNamespace(manifest=SimpleNamespace(set_id="sample_set"))
    runtime = SimpleNamespace(loaded_sets=(loaded_set,), repository=FakeRepository())
    monkeypatch.setattr(app_module, "initialize_application", lambda: state)
    monkeypatch.setattr(app_module, "initialize_runtime", lambda _state: runtime)
    mounted = []

    class FakeLibraryView:
        def __init__(self, *args, **kwargs):
            mounted.append(("library-init", args, kwargs))
            self.on_open = kwargs["on_open"]

        def mount(self):
            mounted.append("library-mounted")

    class FakeBuilderView:
        def __init__(self, *args, **kwargs):
            mounted.append(("builder-init", args, kwargs))

        def mount(self):
            mounted.append("builder-mounted")

    monkeypatch.setattr(library_module, "LibraryView", FakeLibraryView)
    monkeypatch.setattr(builder_module, "BuilderView", FakeBuilderView)
    page = FakePage()
    app_module.main(page)
    assert mounted[-1] == "library-mounted"
    callback = next(
        item for item in mounted if isinstance(item, tuple) and item[0] == "library-init"
    )[2]["on_open"]
    callback(team.team_id)
    assert repository_events == [("mark", team.team_id), ("load", team.team_id)]
    assert mounted[-1] == "builder-mounted"
    builder_init = next(
        item for item in mounted if isinstance(item, tuple) and item[0] == "builder-init"
    )
    assert builder_init[2]["on_back"] is not None
    builder_init[2]["on_back"]()
    assert mounted[-1] == "library-mounted"


def test_main_rejects_unknown_open_and_missing_team_set(monkeypatch) -> None:
    import tft_builder.app as app_module
    import tft_builder.library_view as library_module

    fake_flet = SimpleNamespace(
        SafeArea=FakeControl,
        Column=FakeControl,
        Text=FakeControl,
        FontWeight=SimpleNamespace(BOLD="bold"),
    )
    monkeypatch.setitem(sys.modules, "flet", fake_flet)
    team = Team.create(set_id="missing", name="Broken")

    class Repo:
        def mark_opened(self, team_id):
            return team_id == team.team_id

        def load(self, _team_id):
            return team

    state = SimpleNamespace(paths=SimpleNamespace(bundled_assets_dir=Path("assets")))
    runtime = SimpleNamespace(
        loaded_sets=(SimpleNamespace(manifest=SimpleNamespace(set_id="sample_set")),),
        repository=Repo(),
    )
    monkeypatch.setattr(app_module, "initialize_application", lambda: state)
    monkeypatch.setattr(app_module, "initialize_runtime", lambda _state: runtime)
    callbacks = []

    class FakeLibraryView:
        def __init__(self, *args, **kwargs):
            callbacks.append(kwargs["on_open"])

        def mount(self):
            pass

    monkeypatch.setattr(library_module, "LibraryView", FakeLibraryView)
    page = FakePage()
    app_module.main(page)
    with pytest.raises(ApplicationStartupError, match="Unknown Team ID"):
        callbacks[-1](Team.create(set_id="x", name="X").team_id)
    with pytest.raises(ApplicationStartupError, match="missing"):
        callbacks[-1](team.team_id)


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
        "initialize_runtime",
        lambda _state: (_ for _ in ()).throw(ApplicationStartupError("broken set")),
    )
    page = FakePage()
    app_module.main(page)
    assert page.title == "TFT Team Builder"
    assert page.controls[0].content.controls[-1].value == "broken set"
    assert page.controls[0].content.controls[-1].key == "app-startup-error"
