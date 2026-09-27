from __future__ import annotations

import logging
import shutil
from pathlib import Path

from tft_builder.app import initialize_application, startup_set_summary


def test_startup_summary_reports_no_sets_for_empty_directory(tmp_path: Path) -> None:
    empty = tmp_path / "sets"
    empty.mkdir()
    assert startup_set_summary(empty) == ("No bundled Sets found.",)


def test_startup_summary_reports_valid_sample(project_root: Path) -> None:
    summary = startup_set_summary(project_root / "src" / "assets" / "sets")
    assert len(summary) == 1
    assert summary[0] == "sample_set: valid - 3 champions, 3 traits"


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
    finally:
        close_application_logging()


def test_main_renders_smoke_shell_without_real_flet_runtime(monkeypatch) -> None:
    import sys
    from types import SimpleNamespace

    import tft_builder.app as app_module

    class FakeText:
        def __init__(self, value: str, **kwargs) -> None:
            self.value = value
            self.kwargs = kwargs

    class FakeColumn:
        def __init__(self, *, controls) -> None:
            self.controls = controls

    class FakeSafeArea:
        def __init__(self, *, content) -> None:
            self.content = content

    class FakePage:
        def __init__(self) -> None:
            self.title = ""
            self.controls = []

        def add(self, control) -> None:
            self.controls.append(control)

    fake_flet = SimpleNamespace(
        Text=FakeText,
        Column=FakeColumn,
        SafeArea=FakeSafeArea,
        FontWeight=SimpleNamespace(BOLD="bold"),
    )
    monkeypatch.setitem(sys.modules, "flet", fake_flet)
    monkeypatch.setattr(
        app_module,
        "initialize_application",
        lambda: SimpleNamespace(set_summary=("sample_set: valid - 3 champions, 3 traits",)),
    )

    page = FakePage()
    app_module.main(page)

    assert page.title == "TFT Team Builder"
    assert len(page.controls) == 1
    texts = [control.value for control in page.controls[0].content.controls]
    assert texts == [
        "TFT Team Builder",
        "Block 1 foundation is active.",
        "Bundled Set validation:",
        "sample_set: valid - 3 champions, 3 traits",
    ]
