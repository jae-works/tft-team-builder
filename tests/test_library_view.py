from __future__ import annotations

import sys
from dataclasses import replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from tft_builder.flet_helpers import event_handler, text_value_handler
from tft_builder.library_view import LibrarySessionState, LibraryView, _format_updated
from tft_builder.models import ChampionInstance, Slot, Team, TeamList
from tft_builder.persistence import Database, TeamRepository
from tft_builder.set_loader import load_set_directory


class DynamicValues:
    def __getattr__(self, name: str) -> str:
        return name.lower()


class FakeBorder:
    @staticmethod
    def all(width, color):
        return (width, color)


class FakeControl:
    def __init__(self, *args, **kwargs) -> None:
        self.args = args
        self.value = args[0] if args else kwargs.pop("value", None)
        for name, value in kwargs.items():
            setattr(self, name, value)
        if not hasattr(self, "controls"):
            self.controls = []
        if not hasattr(self, "items"):
            self.items = []
        if not hasattr(self, "actions"):
            self.actions = []


class FakePage:
    def __init__(self) -> None:
        self.title = ""
        self.controls = []
        self.updated = 0
        self.dialogs = []

    def add(self, control) -> None:
        self.controls.append(control)

    def update(self) -> None:
        self.updated += 1

    def show_dialog(self, dialog) -> None:
        self.dialogs.append(dialog)

    def pop_dialog(self) -> None:
        if self.dialogs:
            self.dialogs.pop()


@pytest.fixture
def fake_flet(monkeypatch):
    namespace = SimpleNamespace(
        SafeArea=FakeControl,
        Column=FakeControl,
        Row=FakeControl,
        Container=FakeControl,
        Divider=FakeControl,
        VerticalDivider=FakeControl,
        Text=FakeControl,
        TextField=FakeControl,
        Button=FakeControl,
        TextButton=FakeControl,
        IconButton=FakeControl,
        Icon=FakeControl,
        PopupMenuButton=FakeControl,
        PopupMenuItem=FakeControl,
        AlertDialog=FakeControl,
        ListView=FakeControl,
        Border=FakeBorder,
        Icons=DynamicValues(),
        Colors=DynamicValues(),
        FontWeight=SimpleNamespace(BOLD="bold"),
        CrossAxisAlignment=SimpleNamespace(STRETCH="stretch", CENTER="center"),
        Alignment=SimpleNamespace(CENTER="center"),
    )
    monkeypatch.setitem(sys.modules, "flet", namespace)
    return namespace


@pytest.fixture
def loaded_set(valid_set_dir: Path):
    return load_set_directory(valid_set_dir)


def make_repository(tmp_path: Path) -> TeamRepository:
    database = Database(tmp_path / "library.db")
    database.initialize()
    return TeamRepository(database)


def walk(control):
    yield control
    content = getattr(control, "content", None)
    if content is not None and not isinstance(content, str):
        yield from walk(content)
    for name in ("controls", "items", "actions"):
        for child in getattr(control, name, []):
            yield from walk(child)


def by_key(root, key: str):
    return next(item for item in walk(root) if getattr(item, "key", None) == key)


def make_view(loaded_set, tmp_path: Path, *, session=None):
    page = FakePage()
    repository = make_repository(tmp_path)
    opened = []
    view = LibraryView(
        page,
        (loaded_set,),
        repository,
        on_open=opened.append,
        assets_dir=loaded_set.root.parents[1],
        session=session,
    )
    return view, page, repository, opened


def make_team(set_id: str, name: str, champions: tuple[str, ...] = ()) -> Team:
    team = Team.create(set_id=set_id, name=name)
    team.primary_list.slots = [
        Slot(index, ChampionInstance(champion_id)) for index, champion_id in enumerate(champions)
    ]
    return team


def test_constructor_validates_sets_and_repository(loaded_set, tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    with pytest.raises(ValueError, match="loaded_sets"):
        LibraryView(FakePage(), (), repository, on_open=lambda _id: None, assets_dir=tmp_path)
    with pytest.raises(TypeError, match="repository"):
        LibraryView(
            FakePage(),
            (loaded_set,),
            object(),
            on_open=lambda _id: None,
            assets_dir=tmp_path,
        )


def test_mount_empty_library_has_clear_primary_action(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, _, _ = make_view(loaded_set, tmp_path)
    view.mount()
    assert page.title == "TFT Team Builder"
    root = page.controls[0]
    assert by_key(root, "library-team-search")
    assert by_key(root, "library-create-team")
    assert by_key(root, "library-empty-state")
    assert by_key(root, "library-create-empty")


def test_create_persists_before_opening(fake_flet, loaded_set, tmp_path: Path) -> None:
    view, _, repository, opened = make_view(loaded_set, tmp_path)
    view.create_team()
    assert len(opened) == 1
    team = repository.load(opened[0])
    assert team.name == "Untitled Team"
    assert team.set_id == loaded_set.manifest.set_id
    assert len(team.lists) == 1


def test_search_similarity_duplicates_and_clear_preserve_session(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    session = LibrarySessionState()
    view, _, repository, _ = make_view(loaded_set, tmp_path, session=session)
    exact = make_team("sample_set", "Exact", ("sample_guardian", "sample_guardian"))
    partial = make_team("sample_set", "Partial", ("sample_guardian", "sample_mage"))
    repository.save(partial)
    repository.save(exact)

    view.set_team_search("exact")
    assert [item.team.name for item in view._visible_ranked_teams()] == ["Exact"]
    view.set_team_search("")
    view.add_similarity_champion("sample_guardian")
    view.add_similarity_champion("sample_guardian")
    assert session.desired_champion_ids == ["sample_guardian", "sample_guardian"]
    assert [item.team.name for item in view._visible_ranked_teams()] == ["Exact", "Partial"]
    view.remove_similarity_champion("sample_guardian")
    assert session.desired_champion_ids == ["sample_guardian"]
    view.remove_similarity_champion("missing")
    assert session.desired_champion_ids == ["sample_guardian"]
    view.clear_filters()
    assert session.team_search_query == ""
    assert session.champion_search_query == ""
    assert session.desired_champion_ids == []


def test_selected_set_validation_and_session_fallback(loaded_set, tmp_path: Path) -> None:
    session = LibrarySessionState(selected_set_id="missing")
    view, _, _, _ = make_view(loaded_set, tmp_path, session=session)
    assert session.selected_set_id == "sample_set"
    with pytest.raises(ValueError, match="unknown Set ID"):
        view.set_selected_set("missing")
    view.add_similarity_champion("sample_guardian")
    with pytest.raises(ValueError, match="unknown Champion ID"):
        view.add_similarity_champion("missing")


def test_soft_delete_restore_trash_and_permanent_delete(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, repository, _ = make_view(loaded_set, tmp_path)
    team = make_team("sample_set", "Delete me")
    repository.save(team)
    view.mount()
    view.soft_delete(team.team_id)
    assert repository.list_ids() == ()
    assert view.recently_deleted_team_id == team.team_id
    view.toggle_deleted()
    assert view.session.show_deleted is True
    assert [item.team.team_id for item in view._visible_ranked_teams()] == [team.team_id]
    view.restore(team.team_id)
    assert repository.list_ids() == (team.team_id,)

    repository.soft_delete(team.team_id)
    view.confirm_permanent_delete(team.team_id)
    dialog = page.dialogs[-1]
    assert dialog.title.value == "Permanently delete Team?"
    assert dialog.actions[-1].content == "Delete permanently"
    dialog.actions[-1].on_click(None)
    assert repository.list_ids(include_deleted=True) == ()
    assert page.dialogs == []


def test_recent_restore_and_idempotent_delete_paths(fake_flet, loaded_set, tmp_path: Path) -> None:
    view, _, repository, _ = make_view(loaded_set, tmp_path)
    team = make_team("sample_set", "Recent")
    repository.save(team)
    view.soft_delete(team.team_id)
    view.restore_recent()
    assert repository.load(team.team_id).deleted_at is None
    assert view.recently_deleted_team_id is None
    view.restore_recent()
    view.soft_delete(team.team_id)
    view.soft_delete(team.team_id)


def test_missing_set_disables_open_and_zero_results_show_reset(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, repository, _ = make_view(loaded_set, tmp_path)
    team = make_team("missing_set", "Unavailable", ("x",))
    repository.save(team)
    view.mount()
    root = page.controls[0]
    card = by_key(root, f"library-team-{team.team_id}")
    assert any(
        getattr(item, "disabled", False)
        for item in walk(card)
        if getattr(item, "content", None) == "Open"
    )

    view.set_team_search("no such team")
    assert by_key(page.controls[0], "library-empty-state")
    assert by_key(page.controls[0], "library-clear-filters-empty")


def test_empty_trash_state_and_clear_disabled_state(fake_flet, loaded_set, tmp_path: Path) -> None:
    view, page, _, _ = make_view(loaded_set, tmp_path)
    view.toggle_deleted()
    view.mount()
    assert any(getattr(item, "value", None) == "Trash is empty" for item in walk(page.controls[0]))
    clear = by_key(page.controls[0], "library-clear-filters")
    assert clear.disabled is True


def test_similarity_panel_filters_by_trait_text_and_caps_results(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, _, _ = make_view(loaded_set, tmp_path)
    view.session.champion_search_query = "arcane"
    view.mount()
    keys = {getattr(item, "key", None) for item in walk(page.controls[0])}
    assert "library-similarity-add-sample_mage" in keys
    assert "library-similarity-add-sample_flex" in keys
    assert "library-similarity-add-sample_guardian" not in keys


def test_event_and_text_handlers_forward_values() -> None:
    calls = []
    event_handler(lambda a: calls.append(a), 4)(None)
    event = SimpleNamespace(control=SimpleNamespace(value=None))
    text_value_handler(calls.append)(event)
    assert calls == [4, ""]


def test_format_updated_is_compact_and_timezone_safe() -> None:
    text = _format_updated(datetime(2026, 9, 28, 12, 30, tzinfo=UTC))
    assert text.startswith("Updated 2026-09-28")


def test_unmounted_refresh_and_noop_filter_paths(fake_flet, loaded_set, tmp_path: Path) -> None:
    view, page, _, _ = make_view(loaded_set, tmp_path)
    view.refresh()
    assert page.updated == 0
    view.clear_filters()
    assert page.updated == 0
    view.remove_similarity_champion("missing")
    assert page.updated == 0


def test_open_and_selected_set_change_paths(fake_flet, loaded_set, tmp_path: Path) -> None:
    other_manifest = loaded_set.manifest.model_copy(update={"set_id": "other_set"})
    other_set = replace(loaded_set, manifest=other_manifest)
    page = FakePage()
    repository = make_repository(tmp_path)
    opened = []
    session = LibrarySessionState(selected_set_id="sample_set", champion_search_query="guard")
    session.desired_champion_ids.append("sample_guardian")
    view = LibraryView(
        page,
        (loaded_set, other_set),
        repository,
        on_open=opened.append,
        assets_dir=tmp_path,
        session=session,
    )
    team = make_team("sample_set", "Open me")
    repository.save(team)
    view.open_team(team.team_id)
    assert opened == [team.team_id]
    view.set_selected_set("other_set")
    assert session.selected_set_id == "other_set"
    assert session.champion_search_query == ""
    assert session.desired_champion_ids == []
    updated = page.updated
    view.set_selected_set("other_set")
    assert page.updated == updated


def test_delete_last_team_keeps_visible_restore_action(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, repository, _ = make_view(loaded_set, tmp_path)
    team = make_team("sample_set", "Only Team")
    repository.save(team)
    view.mount()
    view.soft_delete(team.team_id)
    assert by_key(page.controls[0], "library-delete-undo")
    assert by_key(page.controls[0], "library-empty-state")


def test_failed_restore_and_delete_do_not_refresh(fake_flet, loaded_set, tmp_path: Path) -> None:
    view, page, repository, _ = make_view(loaded_set, tmp_path)
    team = make_team("sample_set", "Active")
    repository.save(team)
    view.mount()
    before = page.updated
    view.restore(team.team_id)
    view.soft_delete(uuid4())
    assert page.updated == before


def test_similarity_rendering_duplicate_chip_and_score(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, repository, _ = make_view(loaded_set, tmp_path)
    team = make_team("sample_set", "Double", ("sample_guardian", "sample_guardian"))
    repository.save(team)
    view.session.desired_champion_ids[:] = ["sample_guardian", "sample_guardian"]
    view.mount()
    chip = by_key(page.controls[0], "library-selected-sample_guardian")
    assert chip.content.endswith("x2")
    assert any(
        "Best List: 2/2 matches" in str(getattr(item, "value", ""))
        for item in walk(page.controls[0])
    )


def test_permanent_delete_clears_recent_marker(fake_flet, loaded_set, tmp_path: Path) -> None:
    view, page, repository, _ = make_view(loaded_set, tmp_path)
    team = make_team("sample_set", "Gone")
    repository.save(team)
    view.mount()
    view.soft_delete(team.team_id)
    view.toggle_deleted()
    view.confirm_permanent_delete(team.team_id)
    page.dialogs[-1].actions[-1].on_click(None)
    assert view.recently_deleted_team_id is None


def test_champion_search_updates_session_and_refreshes(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, _, _ = make_view(loaded_set, tmp_path)
    view.mount()
    before = page.updated
    view.set_champion_search("arcane")
    assert view.session.champion_search_query == "arcane"
    assert page.updated == before + 1


def test_restore_refreshes_when_recent_marker_points_elsewhere(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, repository, _ = make_view(loaded_set, tmp_path)
    team = make_team("sample_set", "Deleted")
    repository.save(team)
    repository.soft_delete(team.team_id)
    view.recently_deleted_team_id = uuid4()
    view.mount()
    before = page.updated
    view.restore(team.team_id)
    assert repository.load(team.team_id).deleted_at is None
    assert view.recently_deleted_team_id != team.team_id
    assert page.updated == before + 1


def test_library_search_and_filter_refreshes_reuse_cached_aggregate_snapshot(
    fake_flet, loaded_set, tmp_path: Path, monkeypatch
) -> None:
    view, page, repository, _ = make_view(loaded_set, tmp_path)
    repository.save(make_team("sample_set", "Alpha", ("sample_guardian",)))
    calls = 0
    original_load_all = repository.load_all

    def tracked_load_all(*, include_deleted: bool = False):
        nonlocal calls
        calls += 1
        return original_load_all(include_deleted=include_deleted)

    monkeypatch.setattr(repository, "load_all", tracked_load_all)
    view.mount()
    assert calls == 1

    view.set_team_search("a")
    view.set_team_search("al")
    view.set_champion_search("guard")
    view.add_similarity_champion("sample_guardian")
    view.toggle_deleted()
    view.toggle_deleted()

    assert page.updated == 6
    assert calls == 1


def test_repository_mutations_reload_library_snapshot(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, _, repository, _ = make_view(loaded_set, tmp_path)
    team = make_team("sample_set", "Mutable")
    repository.save(team)
    view.mount()
    assert [item.team.name for item in view._visible_ranked_teams()] == ["Mutable"]

    view.soft_delete(team.team_id)
    assert view._visible_ranked_teams() == ()
    view.toggle_deleted()
    assert [item.team.name for item in view._visible_ranked_teams()] == ["Mutable"]
    view.restore(team.team_id)
    assert view._visible_ranked_teams() == ()
    view.toggle_deleted()
    assert [item.team.name for item in view._visible_ranked_teams()] == ["Mutable"]


def test_similarity_card_previews_best_matching_list_instead_of_primary(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, repository, _ = make_view(loaded_set, tmp_path)
    team = Team.create(set_id="sample_set", name="Stages")
    team.primary_list.slots = [Slot(0, ChampionInstance("sample_mage"))]
    matching = TeamList(
        name="Guardian Stage",
        slots=[Slot(0, ChampionInstance("sample_guardian"))],
    )
    team.lists.append(matching)
    repository.save(team)
    view.session.desired_champion_ids.append("sample_guardian")

    view.mount()
    card = by_key(page.controls[0], f"library-team-{team.team_id}")
    texts = {str(getattr(item, "value", "")) for item in walk(card)}

    assert any(text.startswith("Best match: Guardian Stage") for text in texts)
    assert not any(text.startswith("Primary:") for text in texts)
