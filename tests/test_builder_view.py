from __future__ import annotations

import asyncio
import sys
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from tft_builder.builder import TeamEditor
from tft_builder.builder_view import (
    BuilderView,
    asset_source,
    champion_details_text,
    champion_portrait_path,
    champion_trait_ids,
    dynamic_selection_text,
    dynamic_rule_summary,
    filtered_champion_groups,
    localized_text,
    parse_drag_source_key,
    reconcile_active_list,
    visible_trait_results,
)
from tft_builder.flet_helpers import event_handler, text_value_handler
from tft_builder.models import ChampionInstance, Slot, Team, TeamList, TraitSelection
from tft_builder.persistence import AutosaveService
from tft_builder.set_loader import load_set_directory
from tft_builder.set_schema import (
    DynamicSelectionRule,
    DynamicSelectionScope,
    DynamicTraitDefinition,
)
from tft_builder.trait_engine import calculate_traits


class FakeRepo:
    def __init__(self) -> None:
        self.saved: list[Team] = []
        self.error: Exception | None = None

    def save(self, team: Team) -> None:
        if self.error is not None:
            raise self.error
        self.saved.append(deepcopy(team))


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
        self.updated = 0
        self.focused = False
        for name, value in kwargs.items():
            setattr(self, name, value)
        if not hasattr(self, "controls"):
            self.controls = []

    def update(self) -> None:
        self.updated += 1

    async def focus(self) -> None:
        self.focused = True


class FakePage:
    def __init__(self) -> None:
        self.title = ""
        self.controls: list[FakeControl] = []
        self.updated = 0
        self.tasks: list[tuple] = []
        self.dialogs: list[FakeControl] = []

    def add(self, control) -> None:
        self.controls.append(control)

    def update(self) -> None:
        self.updated += 1

    def run_task(self, handler, *args) -> None:
        self.tasks.append((handler, args))

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
        VerticalDivider=FakeControl,
        Divider=FakeControl,
        TextField=FakeControl,
        Button=FakeControl,
        Text=FakeControl,
        Checkbox=FakeControl,
        ListView=FakeControl,
        Image=FakeControl,
        Icon=FakeControl,
        IconButton=FakeControl,
        Draggable=FakeControl,
        DragTarget=FakeControl,
        PopupMenuButton=FakeControl,
        PopupMenuItem=FakeControl,
        AlertDialog=FakeControl,
        TextButton=FakeControl,
        Border=FakeBorder,
        Icons=DynamicValues(),
        Colors=DynamicValues(),
        FontWeight=SimpleNamespace(BOLD="bold"),
        CrossAxisAlignment=SimpleNamespace(STRETCH="stretch", CENTER="center"),
        MainAxisAlignment=SimpleNamespace(CENTER="center"),
        ScrollMode=SimpleNamespace(AUTO="auto"),
        TextOverflow=SimpleNamespace(ELLIPSIS="ellipsis"),
        Alignment=SimpleNamespace(CENTER="center"),
    )
    monkeypatch.setitem(sys.modules, "flet", namespace)
    return namespace


@pytest.fixture
def loaded_set(valid_set_dir: Path):
    return load_set_directory(valid_set_dir)


def make_view(loaded_set, tmp_path: Path) -> tuple[BuilderView, FakePage, FakeRepo]:
    team = Team.create(set_id=loaded_set.manifest.set_id, name="Team")
    page = FakePage()
    repo = FakeRepo()
    view = BuilderView(
        page,
        loaded_set,
        TeamEditor(team),
        AutosaveService(repo),
        assets_dir=loaded_set.root.parents[1],
    )
    return view, page, repo


def walk(control):
    yield control
    content = getattr(control, "content", None)
    if content is not None and not isinstance(content, str):
        yield from walk(content)
    for child in getattr(control, "controls", []):
        yield from walk(child)
    for child in getattr(control, "actions", []):
        yield from walk(child)
    for child in getattr(control, "items", []):
        yield from walk(child)


def by_key(root, key: str):
    return next(item for item in walk(root) if getattr(item, "key", None) == key)


def test_pure_builder_helpers_cover_localization_assets_groups_and_navigation(
    loaded_set, tmp_path: Path
) -> None:
    assert localized_text(loaded_set, "champion.sample_guardian.name") == "Sample Guardian"
    assert localized_text(loaded_set, "missing.key") == "missing.key"
    source = asset_source(
        loaded_set, loaded_set.root.parents[1], "assets/champions/sample_guardian.png"
    )
    assert source == "sets/sample_set/assets/champions/sample_guardian.png"
    with pytest.raises(ValueError, match="outside"):
        asset_source(loaded_set, tmp_path, "assets/champions/sample_guardian.png")

    team = Team.create(set_id="sample_set", name="T")
    assert reconcile_active_list(team, team.primary_list_id) == team.primary_list_id
    assert reconcile_active_list(team, uuid4()) == team.primary_list_id


def test_dynamic_portrait_and_text_helpers_use_choice_data_and_safe_fallbacks(loaded_set) -> None:
    flex = loaded_set.champions_by_id["sample_flex"]
    arcane = TraitSelection(("sample_arcane",))

    assert champion_portrait_path(loaded_set, flex, TraitSelection()) == flex.image
    assert champion_portrait_path(loaded_set, flex, arcane) == (
        "assets/champions/variants/sample_flex_arcane.png"
    )
    assert dynamic_selection_text(loaded_set, flex, arcane) == "Sample Arcane"

    rule_without_portraits = loaded_set.dynamic_traits[0].model_copy(
        update={"choice_images": {}}
    )
    fallback_set = replace(loaded_set, dynamic_traits=(rule_without_portraits,))
    assert champion_portrait_path(fallback_set, flex, arcane) == flex.image
    assert dynamic_selection_text(fallback_set, flex, arcane) == "Sample Arcane"

    invalid_multi = TraitSelection(("sample_arcane", "sample_wildcard"))
    assert champion_portrait_path(loaded_set, flex, invalid_multi) == flex.image
    assert dynamic_selection_text(loaded_set, flex, invalid_multi) == (
        "Sample Arcane, Sample Wildcard"
    )


def test_slot_renders_selected_dynamic_portrait_and_text(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, _ = make_view(loaded_set, tmp_path)
    instance_id = view.editor.add_champion(
        view.team.primary_list_id,
        0,
        "sample_flex",
        trait_selection=TraitSelection(("sample_arcane",)),
    )
    view.mount()

    root = page.controls[0]
    selected = by_key(root, f"slot-dynamic-{instance_id}")
    assert selected.value == "Sample Arcane"
    slot = by_key(root, f"slot-{view.team.primary_list_id}-0")
    images = [item for item in walk(slot) if getattr(item, "src", None)]
    assert any(
        item.src.endswith("assets/champions/variants/sample_flex_arcane.png")
        for item in images
    )


def test_hci_edge_fixture_does_not_assume_short_names_or_normal_costs(loaded_set) -> None:
    flex = loaded_set.champions_by_id["sample_flex"].model_copy(
        update={
            "cost": 11,
            "board_slots": 2,
            "traits": ["sample_guard", "sample_arcane", "sample_wildcard"],
            "trait_points": {"sample_guard": 2},
        }
    )
    locales = {locale: dict(catalog) for locale, catalog in loaded_set.locales.items()}
    locales[loaded_set.manifest.default_locale][flex.name_key] = (
        "A Champion Name Designed to Wrap Across Narrow Desktop Cards"
    )
    edge_set = replace(
        loaded_set,
        champions=tuple(flex if item.id == flex.id else item for item in loaded_set.champions),
        locales=locales,
    )

    details = champion_details_text(edge_set, flex)
    assert details.startswith("A Champion Name Designed to Wrap Across Narrow Desktop Cards | Cost 11")
    assert champion_trait_ids(edge_set, flex) == (
        "sample_guard",
        "sample_arcane",
        "sample_wildcard",
    )
    assert flex.board_slots == 2
    assert flex.trait_points == {"sample_guard": 2}


def test_visible_trait_results_filters_only_below_first_breakpoint(loaded_set) -> None:
    team_list = TeamList(
        name="Main",
        slots=[Slot(0, ChampionInstance("sample_guardian"))],
    )
    calculation = calculate_traits(loaded_set, team_list)
    assert len(visible_trait_results(calculation, hide_below_first_breakpoint=False)) == 1
    assert visible_trait_results(calculation, hide_below_first_breakpoint=True) == ()


def test_constructor_validates_concrete_dependencies(loaded_set, tmp_path: Path) -> None:
    team = Team.create(set_id="sample_set", name="T")
    editor = TeamEditor(team)
    autosave = AutosaveService(FakeRepo())
    with pytest.raises(TypeError, match="loaded_set"):
        BuilderView(FakePage(), object(), editor, autosave, assets_dir=tmp_path)
    with pytest.raises(TypeError, match="editor"):
        BuilderView(FakePage(), loaded_set, object(), autosave, assets_dir=tmp_path)
    with pytest.raises(TypeError, match="autosave"):
        BuilderView(FakePage(), loaded_set, editor, object(), assets_dir=tmp_path)


def test_mount_builds_three_column_screen_and_stable_keys(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, _ = make_view(loaded_set, tmp_path)
    view.mount()
    assert page.title == "TFT Team Builder"
    assert len(page.controls) == 1
    keys = {getattr(control, "key", None) for control in walk(page.controls[0])}
    assert {
        "builder-team-name",
        "builder-new-list",
        "builder-undo",
        "builder-redo",
        "builder-save-status",
        "builder-hide-below-breakpoint",
        "builder-show-next-breakpoint",
        f"list-more-{view.active_list_id}",
        "champion-add-sample_guardian",
        "champion-add-sample_mage",
        "champion-add-sample_flex",
    } <= keys


def test_structural_actions_persist_reconcile_and_update_history(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, repo = make_view(loaded_set, tmp_path)
    view.mount()
    original = view.active_list_id
    view.create_list()
    created = view.active_list_id
    assert created != original
    assert len(repo.saved) == 1
    view.add_champion("sample_guardian")
    assert view.active_list.slots[0].champion.champion_id == "sample_guardian"
    view.duplicate_list(created)
    duplicate = view.active_list_id
    assert duplicate != created
    view.set_primary_list(duplicate)
    assert view.team.primary_list_id == duplicate
    view.reorder_list(duplicate, 0)
    view.remove_champion(duplicate, 0)
    assert view.active_list.slots == []
    view.compact_list(duplicate)
    assert view.active_list.slots == []
    view.clear_list(duplicate)
    view.delete_list(duplicate)
    assert view.active_list_id == view.team.primary_list_id
    view.undo()
    assert view.editor.can_redo
    view.redo()
    assert not view.editor.can_redo
    assert page.updated > 0


def test_noop_and_invalid_structural_actions_do_not_save(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, _, repo = make_view(loaded_set, tmp_path)
    view.mount()
    view.undo()
    assert repo.saved == []
    view.reorder_list(view.team.primary_list_id, 0)
    assert repo.saved == []
    view.delete_list(view.team.primary_list_id)
    assert "failed" in view.status_message
    assert repo.saved == []


def test_structural_persistence_failure_is_queued_and_visible(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, _, repo = make_view(loaded_set, tmp_path)
    view.mount()
    repo.error = OSError("disk full")
    view.add_champion("sample_guardian")
    assert view.autosave.pending_count == 1
    assert view.status_is_error
    assert "Save failed" in view.status_message


def test_text_edit_queue_debounce_flush_and_validation(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, repo = make_view(loaded_set, tmp_path)
    view.mount()
    assert view.rename_team("Renamed")
    assert view.autosave.pending_count == 1
    assert len(page.tasks) == 1
    list_id = view.active_list_id
    assert view.rename_list(list_id, "Stage")
    assert len(page.tasks) == 2
    assert not view.rename_list(list_id, "Stage")
    assert not view.rename_team("   ")
    assert view.status_is_error
    view.flush_text()
    assert view.autosave.pending_count == 0
    assert repo.saved[-1].name == "Renamed"
    assert view.status_message == "Saved"


def test_save_status_uses_fixed_width_icon_state(fake_flet, loaded_set, tmp_path: Path) -> None:
    view, page, _ = make_view(loaded_set, tmp_path)
    view.mount()
    indicator = by_key(page.controls[0], "builder-save-status")
    assert indicator.width == 40
    assert indicator.tooltip == "Saved"
    assert indicator.content.icon == "check_circle_outline"

    assert view.rename_team("Queued")
    assert view.status_is_pending is True
    assert indicator.tooltip == "Saving changes"
    assert indicator.content.icon == "sync"

    view._set_status("failed", error=True)
    assert view.status_is_pending is False
    assert indicator.tooltip == "failed"
    assert indicator.content.icon == "error_outline"


def test_text_flush_failure_is_visible(fake_flet, loaded_set, tmp_path: Path) -> None:
    view, _, repo = make_view(loaded_set, tmp_path)
    view.mount()
    view.rename_team("Queued")
    repo.error = OSError("readonly")
    view.flush_text()
    assert view.status_is_error
    assert "text flush" in view.status_message


@pytest.mark.asyncio
async def test_debounced_flush_ignores_stale_revision_and_saves_current(
    fake_flet, loaded_set, tmp_path: Path, monkeypatch
) -> None:
    view, page, repo = make_view(loaded_set, tmp_path)
    view.mount()
    view.rename_team("Queued")

    async def no_sleep(_delay):
        return None

    async def direct_to_thread(function, *args):
        return function(*args)

    monkeypatch.setattr(asyncio, "sleep", no_sleep)
    monkeypatch.setattr(asyncio, "to_thread", direct_to_thread)
    await view._debounced_text_flush(0)
    assert repo.saved == []
    await view._debounced_text_flush(view._text_save_revision)
    assert repo.saved[-1].name == "Queued"
    assert page.updated >= 1


@pytest.mark.asyncio
async def test_debounced_flush_failure_is_visible(
    fake_flet, loaded_set, tmp_path: Path, monkeypatch
) -> None:
    view, _, repo = make_view(loaded_set, tmp_path)
    view.mount()
    view.rename_team("Queued")
    repo.error = OSError("no write")

    async def no_sleep(_delay):
        return None

    async def direct_to_thread(function, *args):
        return function(*args)

    monkeypatch.setattr(asyncio, "sleep", no_sleep)
    monkeypatch.setattr(asyncio, "to_thread", direct_to_thread)
    await view._debounced_text_flush(view._text_save_revision)
    assert view.status_is_error
    assert "debounced text save" in view.status_message


def test_active_list_selection_and_display_toggles(fake_flet, loaded_set, tmp_path: Path) -> None:
    view, _, _ = make_view(loaded_set, tmp_path)
    view.mount()
    created = view.editor.create_list("Other")
    view.select_list(created)
    assert view.active_list_id == created
    with pytest.raises(ValueError, match="unknown List ID"):
        view.select_list(uuid4())
    view.set_hide_below_first_breakpoint(True)
    view.set_show_next_breakpoint_progress(False)
    assert view.hide_below_first_breakpoint is True
    assert view.show_next_breakpoint_progress is False


def test_rendering_slots_traits_dynamic_issue_and_confirmations(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, _ = make_view(loaded_set, tmp_path)
    list_id = view.active_list_id
    view.editor.add_champion(list_id, 0, "sample_guardian")
    view.editor.add_champion(list_id, 1, "sample_flex")
    view.mount()
    root = page.controls[0]
    assert by_key(root, f"slot-remove-{list_id}-0")
    assert by_key(root, "builder-dynamic-issues")
    assert by_key(root, "trait-sample_guard").border[0] == 1

    view._confirm_clear_list(list_id)
    assert page.dialogs[-1].title.value == "Clear List?"
    page.dialogs[-1].actions[0].on_click(None)
    assert page.dialogs == []
    view._confirm_delete_list(list_id)
    dialog = page.dialogs[-1]
    assert dialog.title.value == "Delete List?"
    dialog.actions[1].on_click(None)
    assert view.status_is_error  # final remaining List cannot be deleted


def test_list_renders_only_occupied_slots_plus_one_trailing_empty_position(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, _ = make_view(loaded_set, tmp_path)
    list_id = view.active_list_id
    view.editor.add_champion(list_id, 0, "sample_guardian")
    view.editor.insert_slot(list_id, 0)
    view.editor.add_champion(list_id, 2, "sample_mage")
    view.mount()

    root = page.controls[0]
    keys = {getattr(control, "key", None) for control in walk(root)}
    assert f"slot-{list_id}-0" not in keys
    assert f"slot-{list_id}-1" in keys
    assert f"slot-{list_id}-2" in keys
    assert f"slot-end-{list_id}" in keys
    assert sum(key == f"slot-end-{list_id}" for key in keys) == 1

    view.remove_champion(list_id, 1)
    assert [
        slot.champion.champion_id if slot.champion else None for slot in view.active_list.slots
    ] == [None, "sample_mage"]


def test_trait_progress_active_style_and_empty_trait_message(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, _ = make_view(loaded_set, tmp_path)
    view.mount()
    assert any(
        getattr(control, "value", None) == "No active Trait contributions."
        for control in walk(page.controls[0])
    )
    list_id = view.active_list_id
    view.editor.add_champion(list_id, 0, "sample_guardian")
    view.editor.add_champion(list_id, 1, "sample_flex")
    view.editor.set_trait_selection(
        list_id,
        1,
        TraitSelection(("sample_arcane",)),
    )
    view.refresh()
    trait = by_key(page.controls[0], "trait-sample_guard")
    texts = [getattr(item, "value", None) for item in walk(trait)]
    assert any(value and "Next: 4" in value for value in texts)


def test_event_name_and_bool_handler_adapters(fake_flet, loaded_set, tmp_path: Path) -> None:
    calls = []
    event = SimpleNamespace(control=SimpleNamespace(value="value"))
    event_handler(lambda a, b: calls.append((a, b)), 1, 2)(event)
    BuilderView._name_change_handler(lambda prefix, value: calls.append((prefix, value)), "p")(
        event
    )
    event.control.value = "   "
    assert BuilderView._name_change_handler(lambda value: calls.append(value))(event) is None

    view, page, _ = make_view(loaded_set, tmp_path)
    view.mount()
    event.control.value = "Finished"
    view._name_finish_handler(lambda value: calls.append(value))(event)
    event.control.value = " "
    view._name_finish_handler(lambda value: calls.append(value))(event)
    assert view.status_is_error
    assert view.status_message == "Name cannot be empty"

    event.control.value = 1
    BuilderView._bool_handler(lambda value: calls.append(value))(event)
    assert calls == [(1, 2), ("p", "value"), "Finished", True]
    assert page.updated > 0


def test_unmounted_refresh_status_history_and_missing_list_cover_safe_noops(
    loaded_set, tmp_path: Path
) -> None:
    view, page, _ = make_view(loaded_set, tmp_path)
    view.refresh()
    assert page.updated == 0
    view._set_status("pre-mount")
    view._sync_history_controls()
    assert view.status_message == "pre-mount"
    with pytest.raises(ValueError, match="unknown List ID"):
        view._list(uuid4())


def test_trait_render_covers_hidden_progress_and_invalid_positive_trait(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, _ = make_view(loaded_set, tmp_path)
    list_id = view.active_list_id
    view.editor.add_champion(list_id, 0, "sample_guardian")
    view.editor.add_champion(list_id, 1, "sample_mage")
    view.editor.add_champion(list_id, 2, "sample_flex")
    view.show_next_breakpoint_progress = False
    view.mount()
    arcane = by_key(page.controls[0], "trait-sample_arcane")
    assert arcane.border[1] == "error"
    texts = [getattr(item, "value", None) for item in walk(arcane)]
    assert any(value and "Dynamic selection invalid" in value for value in texts)
    assert not any(value and "Next:" in value for value in texts)


def test_create_and_duplicate_failures_keep_active_list(
    fake_flet, loaded_set, tmp_path: Path, monkeypatch
) -> None:
    view, _, repo = make_view(loaded_set, tmp_path)
    view.mount()
    active = view.active_list_id
    monkeypatch.setattr(
        view.editor, "create_list", lambda _name: (_ for _ in ()).throw(ValueError("no"))
    )
    view.create_list()
    assert view.active_list_id == active
    assert repo.saved == []
    view.duplicate_list(uuid4())
    assert view.active_list_id == active


def test_structural_change_detection_does_not_depend_on_timestamp(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, _, repo = make_view(loaded_set, tmp_path)
    original_timestamp = view.team.updated_at

    def mutate_without_timestamp_change() -> None:
        view.team.name = "Changed without clock movement"

    assert view._run_structural("test edit", mutate_without_timestamp_change) is True
    assert view.team.updated_at == original_timestamp
    assert repo.saved[-1].name == "Changed without clock movement"


def test_block5_catalog_helpers_cover_search_traits_drag_keys_and_rule_copy(loaded_set) -> None:
    flex = loaded_set.champions_by_id["sample_flex"]
    assert champion_details_text(loaded_set, flex) == (
        "Sample Flex | Cost 7 | Traits: Sample Guard, Sample Arcane, Sample Wildcard"
    )
    assert champion_trait_ids(loaded_set, flex) == (
        "sample_guard",
        "sample_arcane",
        "sample_wildcard",
    )

    assert [
        item.id for _, group in filtered_champion_groups(loaded_set, "guardian") for item in group
    ] == ["sample_guardian"]
    assert [
        item.id for _, group in filtered_champion_groups(loaded_set, "arcane") for item in group
    ] == ["sample_mage", "sample_flex"]
    assert [
        item.id
        for _, group in filtered_champion_groups(loaded_set, "", trait_filter_id="sample_guard")
        for item in group
    ] == ["sample_guardian", "sample_flex"]
    assert filtered_champion_groups(loaded_set, "not-present") == ()

    instance_id = uuid4()
    assert parse_drag_source_key("drag-library-sample_guardian") == (
        "library",
        "sample_guardian",
    )
    assert parse_drag_source_key(f"drag-instance-{instance_id}") == ("instance", instance_id)
    assert parse_drag_source_key("drag-instance-not-a-uuid") is None
    assert parse_drag_source_key("drag-library-") is None
    assert parse_drag_source_key("other") is None
    assert parse_drag_source_key(None) is None

    assert (
        dynamic_rule_summary(
            DynamicTraitDefinition(
                champion_id="x",
                selection_rule=DynamicSelectionRule.EXACTLY_ONE,
                choices=["a"],
            )
        )
        == "Choose exactly one Trait."
    )
    assert (
        dynamic_rule_summary(
            DynamicTraitDefinition(
                champion_id="x",
                selection_rule=DynamicSelectionRule.ZERO_OR_ONE,
                choices=["a"],
            )
        )
        == "Choose zero or one Trait."
    )
    assert (
        dynamic_rule_summary(
            DynamicTraitDefinition(
                champion_id="x",
                selection_rule=DynamicSelectionRule.ANY_NUMBER,
                choices=["a"],
            )
        )
        == "Choose any number of Traits."
    )
    assert (
        dynamic_rule_summary(
            DynamicTraitDefinition(
                champion_id="x",
                selection_rule=DynamicSelectionRule.EXACTLY_N,
                choices=["a", "b"],
                exact_count=2,
            )
        )
        == "Choose exactly 2 Traits."
    )
    assert (
        dynamic_rule_summary(
            DynamicTraitDefinition(champion_id="x", selection_rule=DynamicSelectionRule.NONE)
        )
        == "This Champion does not require a dynamic Trait choice."
    )


def test_slot_layout_keeps_remove_action_visible_for_every_champion(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, _ = make_view(loaded_set, tmp_path)
    list_id = view.active_list_id
    view.editor.add_champion(list_id, 0, "sample_guardian")
    view.editor.add_champion(list_id, 1, "sample_mage")
    view.editor.add_champion(list_id, 2, "sample_flex")
    view.mount()

    for index in range(3):
        card = by_key(page.controls[0], f"slot-{list_id}-{index}")
        remove = by_key(page.controls[0], f"slot-remove-{list_id}-{index}")
        assert card.height == 142
        assert remove.height == 30
        assert remove.width == 30
    assert by_key(page.controls[0], f"slot-traits-{list_id}-2")

    view.remove_champion(list_id, 0)
    assert [slot.champion.champion_id for slot in view.active_list.slots] == [
        "sample_mage",
        "sample_flex",
    ]
    assert by_key(page.controls[0], f"slot-remove-{list_id}-0")


def test_champion_search_and_trait_click_filter_update_only_relevant_results(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, _ = make_view(loaded_set, tmp_path)
    view.mount()
    root = page.controls[0]

    search = by_key(root, "builder-champion-search")
    search.value = "arcane"
    search.on_change(SimpleNamespace(control=search))
    result_keys = {getattr(item, "key", None) for item in walk(view._champion_results)}
    assert "champion-sample_mage" in result_keys
    assert "champion-sample_flex" in result_keys
    assert "champion-sample_guardian" not in result_keys

    search.value = "nothing"
    search.on_change(SimpleNamespace(control=search))
    assert by_key(view._champion_results, "builder-champion-empty")

    view.champion_search_query = ""
    view.toggle_trait_filter("sample_guard")
    root = page.controls[0]
    assert by_key(root, "builder-trait-filter")
    result_keys = {getattr(item, "key", None) for item in walk(view._champion_results)}
    assert {"champion-sample_guardian", "champion-sample_flex"} <= result_keys
    assert "champion-sample_mage" not in result_keys
    view.clear_trait_filter()
    assert view.trait_filter_id is None
    view.clear_trait_filter()  # safe no-op
    with pytest.raises(ValueError, match="unknown Trait ID"):
        view.toggle_trait_filter("missing")


def test_drag_drop_translates_library_swap_and_dense_cross_list_moves(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, repo = make_view(loaded_set, tmp_path)
    first = view.active_list_id
    view.editor.add_champion(first, 0, "sample_guardian")
    view.editor.add_champion(first, 1, "sample_mage")
    second = view.editor.create_list("Second")
    view.editor.clear_history()
    view.mount()

    root = page.controls[0]
    guard_id = view._list(first).slots[0].champion.instance_id
    guard_drag = by_key(root, f"drag-instance-{guard_id}")
    mage_target = by_key(root, f"drop-slot-{first}-1")
    event = SimpleNamespace(src=guard_drag, control=mage_target)
    assert mage_target.on_accept(event) is True
    assert [slot.champion.champion_id for slot in view._list(first).slots] == [
        "sample_mage",
        "sample_guardian",
    ]

    root = page.controls[0]
    guard_drag = by_key(root, f"drag-instance-{guard_id}")
    end_target = by_key(root, f"drop-end-{second}")
    assert end_target.on_accept(SimpleNamespace(src=guard_drag, control=end_target)) is True
    assert [slot.champion.champion_id for slot in view._list(first).slots] == ["sample_mage"]
    assert [slot.champion.champion_id for slot in view._list(second).slots] == ["sample_guardian"]

    root = page.controls[0]
    library_drag = by_key(root, "drag-library-sample_flex")
    end_target = by_key(root, f"drop-end-{second}")
    assert end_target.on_accept(SimpleNamespace(src=library_drag, control=end_target)) is True
    assert [slot.champion.champion_id for slot in view._list(second).slots] == [
        "sample_guardian",
        "sample_flex",
    ]
    assert len(repo.saved) == 3


def test_drag_drop_rejects_invalid_sources_and_covers_target_highlight(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, repo = make_view(loaded_set, tmp_path)
    list_id = view.active_list_id
    view.editor.add_champion(list_id, 0, "sample_guardian")
    view.editor.clear_history()
    view.mount()
    target = by_key(page.controls[0], f"drop-slot-{list_id}-0")

    library = by_key(page.controls[0], "drag-library-sample_mage")
    assert target.on_accept(SimpleNamespace(src=library, control=target)) is False
    assert repo.saved == []
    invalid = SimpleNamespace(key="invalid")
    assert view._drop_on_slot(SimpleNamespace(src=invalid, control=target), list_id, 0) is False
    end = by_key(page.controls[0], f"drop-end-{list_id}")
    assert view._drop_on_end(SimpleNamespace(src=invalid, control=end), list_id) is False

    target.on_will_accept(SimpleNamespace(accept=True, control=target))
    assert target.content.border == (2, "primary")
    target.on_will_accept(SimpleNamespace(accept=False, control=target))
    assert target.content.border == (2, "error")
    target.on_leave(SimpleNamespace(control=target))
    assert target.content.border == (1, "outline_variant")
    assert target.updated == 5


def test_dynamic_trait_dialog_validates_applies_and_is_reachable_from_warning(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, repo = make_view(loaded_set, tmp_path)
    list_id = view.active_list_id
    view.editor.add_champion(list_id, 0, "sample_flex")
    view.editor.clear_history()
    view.mount()

    fix = by_key(page.controls[0], "builder-fix-dynamic")
    fix.on_click(None)
    dialog = page.dialogs[-1]
    champion = view._list(list_id).slots[0].champion
    arcane = by_key(dialog, f"dynamic-choice-{champion.instance_id}-sample_arcane")
    wildcard = by_key(dialog, f"dynamic-choice-{champion.instance_id}-sample_wildcard")
    apply = by_key(dialog, f"dynamic-apply-{champion.instance_id}")
    assert apply.disabled is True

    # Calling a disabled handler directly still cannot commit invalid state.
    apply.on_click(None)
    assert page.dialogs[-1] is dialog
    assert repo.saved == []

    arcane.value = True
    arcane.on_change(SimpleNamespace(control=arcane))
    assert apply.disabled is False
    wildcard.value = True
    wildcard.on_change(SimpleNamespace(control=wildcard))
    assert arcane.value is False
    assert wildcard.value is True
    apply.on_click(None)
    assert page.dialogs == []
    assert view._list(list_id).slots[0].champion.trait_selection == TraitSelection(
        ("sample_wildcard",)
    )
    assert len(repo.saved) == 1


def test_dynamic_dialog_supports_multiselect_and_per_champion_scope(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    any_rule = DynamicTraitDefinition(
        champion_id="sample_flex",
        selection_rule=DynamicSelectionRule.ANY_NUMBER,
        choices=["sample_arcane", "sample_wildcard"],
        selection_scope=DynamicSelectionScope.PER_CHAMPION,
    )
    custom_set = replace(loaded_set, dynamic_traits=(any_rule,))
    view, page, repo = make_view(custom_set, tmp_path)
    list_id = view.active_list_id
    view.editor.add_champion(list_id, 0, "sample_flex")
    view.editor.add_champion(list_id, 1, "sample_flex")
    view.editor.clear_history()
    view.mount()

    view.open_dynamic_selection(list_id, 0)
    dialog = page.dialogs[-1]
    first = view._list(list_id).slots[0].champion
    arcane = by_key(dialog, f"dynamic-choice-{first.instance_id}-sample_arcane")
    wildcard = by_key(dialog, f"dynamic-choice-{first.instance_id}-sample_wildcard")
    apply = by_key(dialog, f"dynamic-apply-{first.instance_id}")
    assert apply.disabled is False
    arcane.value = True
    arcane.on_change(SimpleNamespace(control=arcane))
    wildcard.value = True
    wildcard.on_change(SimpleNamespace(control=wildcard))
    wildcard.value = False
    wildcard.on_change(SimpleNamespace(control=wildcard))
    apply.on_click(None)

    selections = [slot.champion.trait_selection for slot in view._list(list_id).slots]
    assert selections == [TraitSelection(("sample_arcane",)), TraitSelection(("sample_arcane",))]
    assert len(repo.saved) == 1


def test_dynamic_dialog_rejects_invalid_locations_and_non_dynamic_champions(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, _, _ = make_view(loaded_set, tmp_path)
    list_id = view.active_list_id
    view.editor.add_champion(list_id, 0, "sample_guardian")
    view.editor.insert_slot(list_id, 1)
    with pytest.raises(IndexError, match="outside"):
        view.open_dynamic_selection(list_id, 9)
    with pytest.raises(ValueError, match="does not contain"):
        view.open_dynamic_selection(list_id, 1)
    with pytest.raises(ValueError, match="does not have"):
        view.open_dynamic_selection(list_id, 0)
    with pytest.raises(TypeError, match="instance_id"):
        view._locate_instance("bad")
    with pytest.raises(ValueError, match="unknown Champion instance"):
        view._locate_instance(uuid4())


@pytest.mark.asyncio
async def test_keyboard_shortcuts_share_builder_actions_and_preserve_text_undo(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, _ = make_view(loaded_set, tmp_path)
    view.mount()
    assert page.on_keyboard_event == view._handle_keyboard_event

    event = SimpleNamespace(key="F", ctrl=True, meta=False, shift=False)
    await page.on_keyboard_event(event)
    assert view._champion_search_field.focused is True

    view.create_list()
    list_count = len(view.team.lists)
    view._text_input_focused = True
    await page.on_keyboard_event(SimpleNamespace(key="Z", ctrl=True, meta=False, shift=False))
    assert len(view.team.lists) == list_count

    view._text_input_focused = False
    await page.on_keyboard_event(SimpleNamespace(key="Z", ctrl=True, meta=False, shift=False))
    assert len(view.team.lists) == list_count - 1
    await page.on_keyboard_event(SimpleNamespace(key="Z", ctrl=True, meta=False, shift=True))
    assert len(view.team.lists) == list_count
    await page.on_keyboard_event(SimpleNamespace(key="Z", ctrl=True, meta=False, shift=False))
    await page.on_keyboard_event(SimpleNamespace(key="Y", ctrl=False, meta=True, shift=False))
    assert len(view.team.lists) == list_count
    await page.on_keyboard_event(SimpleNamespace(key="A", ctrl=False, meta=False, shift=False))

    view._confirm_clear_list(view.active_list_id)
    assert page.dialogs
    await page.on_keyboard_event(SimpleNamespace(key="Escape", ctrl=False, meta=False, shift=False))
    assert page.dialogs == []
    await page.on_keyboard_event(SimpleNamespace(key="Escape", ctrl=False, meta=False, shift=False))


def test_dialog_focus_and_handler_helpers_cover_safe_edges(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, _ = make_view(loaded_set, tmp_path)
    view.mount()
    view._close_dialog()
    view._confirm_clear_list(view.active_list_id)
    first = page.dialogs[-1]
    view._confirm_clear_list(view.active_list_id)
    assert page.dialogs[-1] is not first
    assert len(page.dialogs) == 1

    calls = []
    event = SimpleNamespace(control=SimpleNamespace(value="hello"))
    text_value_handler(calls.append)(event)
    event.control.value = None
    text_value_handler(calls.append)(event)
    assert calls == ["hello", ""]

    wrapped = BuilderView._drop_handler(lambda event, value: (event, value), 3)
    assert wrapped("event") == ("event", 3)
    view._focus_handler(True)(None)
    assert view._text_input_focused is True
    view._focus_handler(False)(None)
    assert view._text_input_focused is False


@pytest.mark.asyncio
async def test_pre_mount_search_refresh_and_keyboard_shortcuts_are_safe(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, _, _ = make_view(loaded_set, tmp_path)
    view.set_champion_search("guard")
    assert view.champion_search_query == "guard"
    await view._handle_keyboard_event(SimpleNamespace(key="F", ctrl=True, meta=False, shift=False))
    await view._handle_keyboard_event(SimpleNamespace(key="A", ctrl=True, meta=False, shift=False))


def test_slot_copy_uses_active_list_and_list_maintenance_actions_are_in_overflow(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, page, repo = make_view(loaded_set, tmp_path)
    source = view.active_list_id
    view.editor.add_champion(source, 0, "sample_guardian")
    target = view.editor.create_list("Target")
    view.editor.clear_history()
    view.active_list_id = target
    view.mount()

    root = page.controls[0]
    copy_button = by_key(root, f"slot-copy-{source}-0")
    copy_button.on_click(None)
    assert [slot.champion.champion_id for slot in view._list(source).slots] == ["sample_guardian"]
    assert [slot.champion.champion_id for slot in view._list(target).slots] == ["sample_guardian"]
    assert (
        view._list(source).slots[0].champion.instance_id
        != view._list(target).slots[0].champion.instance_id
    )
    assert len(repo.saved) == 1

    root = page.controls[0]
    more = by_key(root, f"list-more-{target}")
    assert len(more.items) == 4
    assert {item.key for item in more.items} == {
        f"list-duplicate-{target}",
        f"list-compact-{target}",
        f"list-clear-{target}",
        f"list-delete-{target}",
    }


def test_none_dynamic_rule_dialog_can_clear_stale_selection(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    none_rule = DynamicTraitDefinition(
        champion_id="sample_guardian",
        selection_rule=DynamicSelectionRule.NONE,
    )
    custom = replace(loaded_set, dynamic_traits=(none_rule,))
    view, page, repo = make_view(custom, tmp_path)
    list_id = view.active_list_id
    view.editor.add_champion(
        list_id,
        0,
        "sample_guardian",
        trait_selection=TraitSelection(("stale_trait",)),
    )
    view.editor.clear_history()
    view.mount()
    assert by_key(page.controls[0], "builder-fix-dynamic")

    view.open_dynamic_selection(list_id, 0)
    dialog = page.dialogs[-1]
    champion = view._list(list_id).slots[0].champion
    apply = by_key(dialog, f"dynamic-apply-{champion.instance_id}")
    assert apply.disabled is False
    apply.on_click(None)
    assert view._list(list_id).slots[0].champion.trait_selection == TraitSelection()
    assert len(repo.saved) == 1


@pytest.mark.asyncio
async def test_open_dialog_suppresses_global_history_and_search_shortcuts(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    view, _, _ = make_view(loaded_set, tmp_path)
    view.mount()
    view.create_list()
    depth = view.editor.undo_depth
    view._confirm_clear_list(view.active_list_id)
    await view._handle_keyboard_event(SimpleNamespace(key="Z", ctrl=True, meta=False, shift=False))
    await view._handle_keyboard_event(SimpleNamespace(key="F", ctrl=True, meta=False, shift=False))
    assert view.editor.undo_depth == depth


def test_back_to_library_flushes_pending_text_before_navigation(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    team = Team.create(set_id=loaded_set.manifest.set_id, name="Team")
    page = FakePage()
    repo = FakeRepo()
    calls = []
    view = BuilderView(
        page,
        loaded_set,
        TeamEditor(team),
        AutosaveService(repo),
        assets_dir=loaded_set.root.parents[1],
        on_back=lambda: calls.append("back"),
    )
    view.mount()
    assert by_key(page.controls[0], "builder-back")
    view.rename_team("Queued before back")
    view.back_to_library()
    assert calls == ["back"]
    assert repo.saved[-1].name == "Queued before back"


def test_back_to_library_stays_in_builder_when_flush_fails(
    fake_flet, loaded_set, tmp_path: Path
) -> None:
    team = Team.create(set_id=loaded_set.manifest.set_id, name="Team")
    repo = FakeRepo()
    calls = []
    view = BuilderView(
        FakePage(),
        loaded_set,
        TeamEditor(team),
        AutosaveService(repo),
        assets_dir=loaded_set.root.parents[1],
        on_back=lambda: calls.append("back"),
    )
    view.rename_team("Queued")
    repo.error = OSError("readonly")
    view.back_to_library()
    assert calls == []
    assert view.status_is_error
