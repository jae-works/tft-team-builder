from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from tft_builder.builder import TeamEditor
from tft_builder.models import ChampionInstance, Slot, Team, TeamList, TraitSelection

BASE = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def make_team(*lists: TeamList, primary_index: int = 0) -> Team:
    chosen = list(lists) or [TeamList.empty("Main")]
    return Team(
        set_id="sample_set",
        name="Team",
        lists=chosen,
        primary_list_id=chosen[primary_index].list_id,
        created_at=BASE,
        updated_at=BASE,
    )


def make_list(name: str, *champion_ids: str | None) -> TeamList:
    return TeamList(
        name=name,
        slots=[
            Slot(index, None if champion_id is None else ChampionInstance(champion_id))
            for index, champion_id in enumerate(champion_ids)
        ],
    )


def ids(team_list: TeamList) -> list[str | None]:
    return [slot.champion.champion_id if slot.champion else None for slot in team_list.slots]


def instance_ids(team_list: TeamList) -> list[UUID | None]:
    return [slot.champion.instance_id if slot.champion else None for slot in team_list.slots]


def test_editor_requires_team() -> None:
    with pytest.raises(TypeError, match="Team"):
        TeamEditor(object())  # type: ignore[arg-type]


def test_editor_starts_with_empty_history() -> None:
    editor = TeamEditor(make_team())
    assert editor.can_undo is False
    assert editor.can_redo is False
    assert editor.undo_depth == 0
    assert editor.redo_depth == 0
    assert editor.undo() is False
    assert editor.redo() is False


def test_clear_history_drops_both_stacks_without_changing_team() -> None:
    editor = TeamEditor(make_team())
    editor.rename_team("Renamed", when=BASE + timedelta(seconds=1))
    editor.undo()
    before = deepcopy(editor.team)
    editor.clear_history()
    assert editor.team == before
    assert editor.can_undo is False
    assert editor.can_redo is False


def test_successful_edit_updates_timestamp_in_utc_and_preserves_team_object() -> None:
    team = make_team()
    editor = TeamEditor(team)
    supplied = datetime(2026, 1, 1, 14, 0, tzinfo=timezone(timedelta(hours=2)))
    assert editor.rename_team("Renamed", when=supplied) is True
    assert editor.team is team
    assert team.name == "Renamed"
    assert team.updated_at == datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    assert editor.undo_depth == 1


def test_generated_edit_timestamp_is_timezone_aware_utc() -> None:
    team = make_team()
    editor = TeamEditor(team)
    editor.rename_team("Renamed")
    assert team.updated_at.tzinfo is UTC
    assert team.updated_at >= BASE


def test_edit_timestamp_validation_rejects_non_datetime_naive_and_older_values() -> None:
    editor = TeamEditor(make_team())
    with pytest.raises(TypeError, match="datetime"):
        editor.rename_team("A", when="later")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timezone-aware"):
        editor.rename_team("A", when=datetime(2026, 1, 2))
    with pytest.raises(ValueError, match="earlier"):
        editor.rename_team("A", when=BASE - timedelta(seconds=1))
    assert editor.undo_depth == 0


def test_rename_team_and_list_are_undoable_and_noops_are_not_recorded() -> None:
    team_list = make_list("Main")
    editor = TeamEditor(make_team(team_list))
    assert editor.rename_team("Team", when=BASE) is False
    assert editor.rename_list(team_list.list_id, "Main", when=BASE) is False
    assert editor.rename_team("New Team", when=BASE + timedelta(seconds=1)) is True
    assert (
        editor.rename_list(team_list.list_id, "New List", when=BASE + timedelta(seconds=2)) is True
    )
    assert editor.undo_depth == 2
    assert editor.undo() is True
    assert editor.team.lists[0].name == "Main"
    assert editor.undo() is True
    assert editor.team.name == "Team"


def test_invalid_rename_is_atomic_and_does_not_create_history() -> None:
    editor = TeamEditor(make_team())
    before = deepcopy(editor.team)
    with pytest.raises(ValueError, match="team name"):
        editor.rename_team("  ", when=BASE + timedelta(seconds=1))
    assert editor.team == before
    assert editor.undo_depth == 0


def test_unknown_or_invalid_list_id_is_rejected_without_history() -> None:
    editor = TeamEditor(make_team())
    with pytest.raises(TypeError, match="UUID"):
        editor.rename_list(  # type: ignore[arg-type]
            "bad", "Name", when=BASE + timedelta(seconds=1)
        )
    with pytest.raises(ValueError, match="unknown List ID"):
        editor.rename_list(uuid4(), "Name", when=BASE + timedelta(seconds=1))
    assert editor.undo_depth == 0


def test_set_primary_list_changes_identity_and_same_primary_is_noop() -> None:
    first = make_list("First")
    second = make_list("Second")
    editor = TeamEditor(make_team(first, second))
    assert editor.set_primary_list(first.list_id, when=BASE) is False
    assert editor.set_primary_list(second.list_id, when=BASE + timedelta(seconds=1)) is True
    assert editor.team.primary_list_id == second.list_id


def test_create_list_appends_or_inserts_and_returns_stable_id() -> None:
    first = make_list("First")
    editor = TeamEditor(make_team(first))
    appended = editor.create_list("Third", when=BASE + timedelta(seconds=1))
    inserted = editor.create_list("Second", index=1, when=BASE + timedelta(seconds=2))
    assert [item.name for item in editor.team.lists] == ["First", "Second", "Third"]
    assert editor.team.lists[1].list_id == inserted
    assert editor.team.lists[2].list_id == appended
    assert len({item.list_id for item in editor.team.lists}) == 3


@pytest.mark.parametrize("index", [-1, 2])
def test_create_list_rejects_out_of_range_index(index: int) -> None:
    editor = TeamEditor(make_team())
    with pytest.raises(IndexError, match="insertion range"):
        editor.create_list("New", index=index, when=BASE + timedelta(seconds=1))
    assert editor.undo_depth == 0


def test_create_list_rejects_boolean_index() -> None:
    editor = TeamEditor(make_team())
    with pytest.raises(TypeError, match="integer"):
        editor.create_list("New", index=True, when=BASE + timedelta(seconds=1))


def test_duplicate_list_preserves_layout_values_but_replaces_all_instance_ids() -> None:
    selection = TraitSelection(("trait_a",))
    source = TeamList(
        name="Source",
        slots=[
            Slot(0, ChampionInstance("a", trait_selection=selection)),
            Slot(1),
            Slot(2, ChampionInstance("a", trait_selection=selection)),
        ],
    )
    editor = TeamEditor(make_team(source))
    source_ids = {item for item in instance_ids(source) if item is not None}
    duplicate_id = editor.duplicate_list(source.list_id, when=BASE + timedelta(seconds=1))
    duplicate = editor.team.lists[1]
    duplicate_ids = {item for item in instance_ids(duplicate) if item is not None}
    assert duplicate.list_id == duplicate_id
    assert duplicate.list_id != source.list_id
    assert duplicate.name == "Source"
    assert ids(duplicate) == ["a", None, "a"]
    assert source_ids.isdisjoint(duplicate_ids)
    assert [
        slot.champion.trait_selection if slot.champion else None for slot in duplicate.slots
    ] == [
        selection,
        None,
        selection,
    ]


def test_duplicate_list_can_use_new_name_and_is_inserted_after_source() -> None:
    first = make_list("First")
    second = make_list("Second")
    editor = TeamEditor(make_team(first, second))
    editor.duplicate_list(first.list_id, name="Copy", when=BASE + timedelta(seconds=1))
    assert [item.name for item in editor.team.lists] == ["First", "Copy", "Second"]


def test_duplicate_list_rejects_invalid_custom_name_atomically() -> None:
    source = make_list("Source", "a")
    editor = TeamEditor(make_team(source))
    before = deepcopy(editor.team)
    with pytest.raises(ValueError, match="list name"):
        editor.duplicate_list(source.list_id, name=" ", when=BASE + timedelta(seconds=1))
    assert editor.team == before


def test_delete_non_primary_list_preserves_primary() -> None:
    first = make_list("First")
    second = make_list("Second")
    editor = TeamEditor(make_team(first, second))
    assert editor.delete_list(second.list_id, when=BASE + timedelta(seconds=1)) is True
    assert [item.list_id for item in editor.team.lists] == [first.list_id]
    assert editor.team.primary_list_id == first.list_id


def test_delete_primary_middle_uses_list_at_resulting_position() -> None:
    first = make_list("First")
    middle = make_list("Middle")
    last = make_list("Last")
    editor = TeamEditor(make_team(first, middle, last, primary_index=1))
    editor.delete_list(middle.list_id, when=BASE + timedelta(seconds=1))
    assert editor.team.primary_list_id == last.list_id


def test_delete_primary_last_uses_previous_final_list() -> None:
    first = make_list("First")
    last = make_list("Last")
    editor = TeamEditor(make_team(first, last, primary_index=1))
    editor.delete_list(last.list_id, when=BASE + timedelta(seconds=1))
    assert editor.team.primary_list_id == first.list_id


def test_delete_final_list_is_rejected_atomically() -> None:
    editor = TeamEditor(make_team())
    before = deepcopy(editor.team)
    with pytest.raises(ValueError, match="final remaining"):
        editor.delete_list(editor.team.lists[0].list_id, when=BASE + timedelta(seconds=1))
    assert editor.team == before
    assert editor.undo_depth == 0


def test_reorder_list_moves_without_changing_ids_or_primary_identity() -> None:
    first = make_list("First")
    second = make_list("Second")
    third = make_list("Third")
    editor = TeamEditor(make_team(first, second, third, primary_index=1))
    assert editor.reorder_list(first.list_id, 2, when=BASE + timedelta(seconds=1)) is True
    assert [item.list_id for item in editor.team.lists] == [
        second.list_id,
        third.list_id,
        first.list_id,
    ]
    assert editor.team.primary_list_id == second.list_id
    assert editor.reorder_list(first.list_id, 2, when=BASE + timedelta(seconds=2)) is False


def test_reorder_list_rejects_invalid_existing_index() -> None:
    editor = TeamEditor(make_team())
    with pytest.raises(IndexError, match="existing range"):
        editor.reorder_list(editor.team.lists[0].list_id, 1, when=BASE + timedelta(seconds=1))


def test_clear_list_preserves_slot_count_and_gaps_and_noops_when_already_clear() -> None:
    team_list = make_list("Main", "a", None, "b")
    editor = TeamEditor(make_team(team_list))
    assert editor.clear_list(team_list.list_id, when=BASE + timedelta(seconds=1)) is True
    assert ids(editor.team.lists[0]) == [None, None, None]
    assert editor.clear_list(team_list.list_id, when=BASE + timedelta(seconds=2)) is False


def test_compact_list_removes_gaps_preserving_order_and_ids() -> None:
    team_list = make_list("Main", None, "a", None, "b", None)
    original = [item for item in instance_ids(team_list) if item is not None]
    editor = TeamEditor(make_team(team_list))
    assert editor.compact_list(team_list.list_id, when=BASE + timedelta(seconds=1)) is True
    compacted = editor.team.lists[0]
    assert ids(compacted) == ["a", "b"]
    assert instance_ids(compacted) == original
    assert [slot.index for slot in compacted.slots] == [0, 1]
    assert editor.compact_list(team_list.list_id, when=BASE + timedelta(seconds=2)) is False


def test_compact_empty_cleared_list_reduces_to_zero_slots() -> None:
    team_list = make_list("Main", None, None)
    editor = TeamEditor(make_team(team_list))
    editor.compact_list(team_list.list_id, when=BASE + timedelta(seconds=1))
    assert editor.team.lists[0].slots == []


def test_insert_slot_shifts_later_slots_without_changing_instance_ids() -> None:
    team_list = make_list("Main", "a", "b")
    before_ids = instance_ids(team_list)
    editor = TeamEditor(make_team(team_list))
    editor.insert_slot(team_list.list_id, 1, when=BASE + timedelta(seconds=1))
    assert ids(editor.team.lists[0]) == ["a", None, "b"]
    assert instance_ids(editor.team.lists[0]) == [before_ids[0], None, before_ids[1]]
    assert [slot.index for slot in editor.team.lists[0].slots] == [0, 1, 2]


def test_insert_slot_allows_append() -> None:
    team_list = make_list("Main", "a")
    editor = TeamEditor(make_team(team_list))
    editor.insert_slot(team_list.list_id, 1, when=BASE + timedelta(seconds=1))
    assert ids(editor.team.lists[0]) == ["a", None]


def test_remove_slot_removes_position_and_reindexes_survivors() -> None:
    team_list = make_list("Main", "a", "b", "c")
    survivor_ids = [instance_ids(team_list)[0], instance_ids(team_list)[2]]
    editor = TeamEditor(make_team(team_list))
    editor.remove_slot(team_list.list_id, 1, when=BASE + timedelta(seconds=1))
    assert ids(editor.team.lists[0]) == ["a", "c"]
    assert instance_ids(editor.team.lists[0]) == survivor_ids
    assert [slot.index for slot in editor.team.lists[0].slots] == [0, 1]


@pytest.mark.parametrize(
    "method,index",
    [("insert_slot", -1), ("insert_slot", 2), ("remove_slot", -1), ("remove_slot", 1)],
)
def test_slot_structure_operations_reject_invalid_indexes(method: str, index: int) -> None:
    team_list = make_list("Main", "a")
    editor = TeamEditor(make_team(team_list))
    with pytest.raises(IndexError):
        getattr(editor, method)(team_list.list_id, index, when=BASE + timedelta(seconds=1))
    assert editor.undo_depth == 0


def test_clear_slot_preserves_gap_and_is_noop_for_empty_slot() -> None:
    team_list = make_list("Main", "a", None)
    editor = TeamEditor(make_team(team_list))
    assert editor.clear_slot(team_list.list_id, 0, when=BASE + timedelta(seconds=1)) is True
    assert ids(editor.team.lists[0]) == [None, None]
    assert editor.clear_slot(team_list.list_id, 1, when=BASE + timedelta(seconds=2)) is False


def test_add_champion_appends_to_empty_list() -> None:
    team_list = make_list("Main")
    editor = TeamEditor(make_team(team_list))
    instance_id = editor.add_champion(team_list.list_id, 0, "a", when=BASE + timedelta(seconds=1))
    assert ids(editor.team.lists[0]) == ["a"]
    assert instance_ids(editor.team.lists[0]) == [instance_id]


def test_add_champion_fills_empty_existing_slot() -> None:
    team_list = make_list("Main", None, "b")
    second_id = instance_ids(team_list)[1]
    editor = TeamEditor(make_team(team_list))
    added = editor.add_champion(
        team_list.list_id,
        0,
        "a",
        trait_selection=TraitSelection(("trait_a",)),
        when=BASE + timedelta(seconds=1),
    )
    assert ids(editor.team.lists[0]) == ["a", "b"]
    assert instance_ids(editor.team.lists[0]) == [added, second_id]
    assert editor.team.lists[0].slots[0].champion.trait_selection == TraitSelection(("trait_a",))


def test_add_champion_to_occupied_slot_inserts_without_overwriting() -> None:
    team_list = make_list("Main", "a", "b")
    old_ids = instance_ids(team_list)
    editor = TeamEditor(make_team(team_list))
    added = editor.add_champion(team_list.list_id, 1, "x", when=BASE + timedelta(seconds=1))
    assert ids(editor.team.lists[0]) == ["a", "x", "b"]
    assert instance_ids(editor.team.lists[0]) == [old_ids[0], added, old_ids[1]]


def test_add_champion_rejects_invalid_trait_selection_type_atomically() -> None:
    team_list = make_list("Main")
    editor = TeamEditor(make_team(team_list))
    with pytest.raises(TypeError, match="TraitSelection"):
        editor.add_champion(
            team_list.list_id,
            0,
            "a",
            trait_selection=("trait",),  # type: ignore[arg-type]
            when=BASE + timedelta(seconds=1),
        )
    assert editor.team.lists[0].slots == []


def test_move_same_list_to_empty_slot_preserves_identity_and_source_gap() -> None:
    team_list = make_list("Main", "a", None, "b")
    source_id = instance_ids(team_list)[0]
    editor = TeamEditor(make_team(team_list))
    editor.move_champion(
        team_list.list_id, 0, team_list.list_id, 1, when=BASE + timedelta(seconds=1)
    )
    assert ids(editor.team.lists[0]) == [None, "a", "b"]
    assert instance_ids(editor.team.lists[0])[1] == source_id


def test_move_same_list_to_occupied_slot_swaps_instances() -> None:
    team_list = make_list("Main", "a", "b")
    before = instance_ids(team_list)
    editor = TeamEditor(make_team(team_list))
    editor.move_champion(
        team_list.list_id, 0, team_list.list_id, 1, when=BASE + timedelta(seconds=1)
    )
    assert ids(editor.team.lists[0]) == ["b", "a"]
    assert instance_ids(editor.team.lists[0]) == [before[1], before[0]]


def test_move_same_slot_is_noop() -> None:
    team_list = make_list("Main", "a")
    editor = TeamEditor(make_team(team_list))
    assert editor.move_champion(team_list.list_id, 0, team_list.list_id, 0, when=BASE) is False
    assert editor.undo_depth == 0


def test_move_same_list_to_append_adds_target_slot_and_leaves_source_gap() -> None:
    team_list = make_list("Main", "a", "b")
    moved_id = instance_ids(team_list)[0]
    editor = TeamEditor(make_team(team_list))
    editor.move_champion(
        team_list.list_id, 0, team_list.list_id, 2, when=BASE + timedelta(seconds=1)
    )
    assert ids(editor.team.lists[0]) == [None, "b", "a"]
    assert instance_ids(editor.team.lists[0])[2] == moved_id


def test_cross_list_move_to_empty_slot_preserves_instance_identity() -> None:
    source = make_list("Source", "a")
    target = make_list("Target", None)
    moved_id = instance_ids(source)[0]
    editor = TeamEditor(make_team(source, target))
    editor.move_champion(source.list_id, 0, target.list_id, 0, when=BASE + timedelta(seconds=1))
    assert ids(editor.team.lists[0]) == [None]
    assert ids(editor.team.lists[1]) == ["a"]
    assert instance_ids(editor.team.lists[1]) == [moved_id]


def test_cross_list_move_to_occupied_slot_swaps_both_instances() -> None:
    source = make_list("Source", "a")
    target = make_list("Target", "b")
    source_id = instance_ids(source)[0]
    target_id = instance_ids(target)[0]
    editor = TeamEditor(make_team(source, target))
    editor.move_champion(source.list_id, 0, target.list_id, 0, when=BASE + timedelta(seconds=1))
    assert ids(editor.team.lists[0]) == ["b"]
    assert ids(editor.team.lists[1]) == ["a"]
    assert instance_ids(editor.team.lists[0]) == [target_id]
    assert instance_ids(editor.team.lists[1]) == [source_id]


def test_cross_list_move_to_append_preserves_source_gap() -> None:
    source = make_list("Source", "a")
    target = make_list("Target", "b")
    moved_id = instance_ids(source)[0]
    editor = TeamEditor(make_team(source, target))
    editor.move_champion(source.list_id, 0, target.list_id, 1, when=BASE + timedelta(seconds=1))
    assert ids(editor.team.lists[0]) == [None]
    assert ids(editor.team.lists[1]) == ["b", "a"]
    assert instance_ids(editor.team.lists[1])[1] == moved_id


def test_move_rejects_empty_source_and_invalid_target_without_partial_changes() -> None:
    source = make_list("Source", None)
    target = make_list("Target")
    editor = TeamEditor(make_team(source, target))
    before = deepcopy(editor.team)
    with pytest.raises(ValueError, match="does not contain"):
        editor.move_champion(source.list_id, 0, target.list_id, 0, when=BASE + timedelta(seconds=1))
    assert editor.team == before
    source.slots[0].champion = ChampionInstance("a")
    editor = TeamEditor(make_team(source, target))
    with pytest.raises(IndexError, match="insertion range"):
        editor.move_champion(source.list_id, 0, target.list_id, 1, when=BASE + timedelta(seconds=1))


def test_copy_to_empty_slot_preserves_definition_selection_but_uses_new_id() -> None:
    selection = TraitSelection(("trait_a",))
    source = TeamList(
        name="Source", slots=[Slot(0, ChampionInstance("a", trait_selection=selection))]
    )
    target = make_list("Target", None)
    source_id = instance_ids(source)[0]
    editor = TeamEditor(make_team(source, target))
    copied_id = editor.copy_champion(
        source.list_id, 0, target.list_id, 0, when=BASE + timedelta(seconds=1)
    )
    copied = editor.team.lists[1].slots[0].champion
    assert copied is not None
    assert copied.champion_id == "a"
    assert copied.instance_id == copied_id
    assert copied.instance_id != source_id
    assert copied.trait_selection == selection


def test_copy_to_occupied_slot_inserts_and_shifts_target() -> None:
    source = make_list("Source", "a")
    target = make_list("Target", "b", "c")
    old_target_ids = instance_ids(target)
    editor = TeamEditor(make_team(source, target))
    copied_id = editor.copy_champion(
        source.list_id, 0, target.list_id, 0, when=BASE + timedelta(seconds=1)
    )
    assert ids(editor.team.lists[1]) == ["a", "b", "c"]
    assert instance_ids(editor.team.lists[1]) == [copied_id, *old_target_ids]


def test_copy_to_append_adds_new_slot() -> None:
    source = make_list("Source", "a")
    target = make_list("Target", "b")
    editor = TeamEditor(make_team(source, target))
    copied_id = editor.copy_champion(
        source.list_id, 0, target.list_id, 1, when=BASE + timedelta(seconds=1)
    )
    assert ids(editor.team.lists[1]) == ["b", "a"]
    assert instance_ids(editor.team.lists[1])[1] == copied_id


def test_copy_inside_same_list_at_source_inserts_before_original() -> None:
    team_list = make_list("Main", "a", "b")
    original_id = instance_ids(team_list)[0]
    editor = TeamEditor(make_team(team_list))
    copied_id = editor.copy_champion(
        team_list.list_id, 0, team_list.list_id, 0, when=BASE + timedelta(seconds=1)
    )
    assert ids(editor.team.lists[0]) == ["a", "a", "b"]
    assert instance_ids(editor.team.lists[0])[:2] == [copied_id, original_id]


def test_copy_rejects_empty_source_atomically() -> None:
    team_list = make_list("Main", None)
    editor = TeamEditor(make_team(team_list))
    with pytest.raises(ValueError, match="does not contain"):
        editor.copy_champion(
            team_list.list_id, 0, team_list.list_id, 0, when=BASE + timedelta(seconds=1)
        )
    assert editor.undo_depth == 0


def test_set_trait_selection_changes_existing_champion_and_is_undoable() -> None:
    team_list = make_list("Main", "a")
    editor = TeamEditor(make_team(team_list))
    selection = TraitSelection(("trait_a", "trait_b"))
    assert editor.set_trait_selection(
        team_list.list_id, 0, selection, when=BASE + timedelta(seconds=1)
    )
    assert editor.team.lists[0].slots[0].champion.trait_selection == selection
    assert editor.undo() is True
    assert editor.team.lists[0].slots[0].champion.trait_selection == TraitSelection()


def test_set_trait_selection_noop_and_validation() -> None:
    team_list = make_list("Main", "a", None)
    editor = TeamEditor(make_team(team_list))
    assert editor.set_trait_selection(team_list.list_id, 0, TraitSelection(), when=BASE) is False
    with pytest.raises(TypeError, match="TraitSelection"):
        editor.set_trait_selection(
            team_list.list_id,
            0,
            object(),  # type: ignore[arg-type]
            when=BASE + timedelta(seconds=1),
        )
    with pytest.raises(ValueError, match="does not contain"):
        editor.set_trait_selection(
            team_list.list_id, 1, TraitSelection(("a",)), when=BASE + timedelta(seconds=1)
        )


def test_multi_step_undo_redo_restores_exact_full_team_state_and_timestamps() -> None:
    team_list = make_list("Main", "a", None)
    team = make_team(team_list)
    original = deepcopy(team)
    editor = TeamEditor(team)
    editor.rename_team("Renamed", when=BASE + timedelta(seconds=1))
    after_rename = deepcopy(team)
    editor.move_champion(
        team_list.list_id, 0, team_list.list_id, 1, when=BASE + timedelta(seconds=2)
    )
    after_move = deepcopy(team)
    editor.create_list("Second", when=BASE + timedelta(seconds=3))
    final = deepcopy(team)

    assert editor.undo_depth == 3
    assert editor.undo() is True
    assert team == after_move
    assert editor.undo() is True
    assert team == after_rename
    assert editor.undo() is True
    assert team == original
    assert editor.can_undo is False
    assert editor.redo_depth == 3
    assert editor.redo() is True
    assert team == after_rename
    assert editor.redo() is True
    assert team == after_move
    assert editor.redo() is True
    assert team == final
    assert editor.can_redo is False


def test_new_edit_after_undo_clears_redo_branch() -> None:
    editor = TeamEditor(make_team())
    editor.rename_team("One", when=BASE + timedelta(seconds=1))
    editor.rename_team("Two", when=BASE + timedelta(seconds=2))
    editor.undo()
    assert editor.can_redo is True
    editor.rename_team("Branch", when=BASE + timedelta(seconds=3))
    assert editor.can_redo is False
    assert editor.redo() is False
    assert editor.team.name == "Branch"


def test_failed_edit_after_undo_does_not_clear_redo_branch() -> None:
    editor = TeamEditor(make_team())
    editor.rename_team("One", when=BASE + timedelta(seconds=1))
    editor.undo()
    with pytest.raises(ValueError, match="team name"):
        editor.rename_team(" ", when=BASE + timedelta(seconds=2))
    assert editor.can_redo is True


def test_noop_after_undo_does_not_clear_redo_branch() -> None:
    editor = TeamEditor(make_team())
    editor.rename_team("One", when=BASE + timedelta(seconds=1))
    editor.undo()
    assert editor.rename_team("Team", when=BASE + timedelta(seconds=2)) is False
    assert editor.can_redo is True


def test_history_snapshots_are_isolated_from_current_state() -> None:
    team_list = make_list("Main", "a")
    editor = TeamEditor(make_team(team_list))
    editor.rename_team("Changed", when=BASE + timedelta(seconds=1))
    editor.team.lists[0].name = "Manual mutation"
    assert editor.undo() is True
    assert editor.team.name == "Team"
    assert editor.team.lists[0].name == "Main"


def test_large_realistic_list_compaction_is_correct() -> None:
    slots = [
        Slot(index, None if index % 3 == 0 else ChampionInstance(f"champion_{index % 20}"))
        for index in range(300)
    ]
    team_list = TeamList(name="Large", slots=slots)
    expected_ids = [slot.champion.instance_id for slot in slots if slot.champion is not None]
    editor = TeamEditor(make_team(team_list))
    editor.compact_list(team_list.list_id, when=BASE + timedelta(seconds=1))
    compacted = editor.team.lists[0]
    assert len(compacted.slots) == 200
    assert [slot.champion.instance_id for slot in compacted.slots] == expected_ids
    assert [slot.index for slot in compacted.slots] == list(range(200))


def test_returned_ids_remain_stable_across_undo_redo() -> None:
    source = make_list("Source", "a")
    editor = TeamEditor(make_team(source))

    created_list_id = editor.create_list("Second", when=BASE + timedelta(seconds=1))
    copied_id = editor.copy_champion(
        source.list_id,
        0,
        created_list_id,
        0,
        when=BASE + timedelta(seconds=2),
    )
    expected = deepcopy(editor.team)

    assert editor.undo() is True
    assert editor.undo() is True
    assert [item.list_id for item in editor.team.lists] == [source.list_id]

    assert editor.redo() is True
    assert editor.redo() is True
    assert editor.team == expected
    assert editor.team.lists[1].list_id == created_list_id
    assert editor.team.lists[1].slots[0].champion.instance_id == copied_id


def test_remove_occupied_slot_discards_champion_and_undo_restores_exact_instance() -> None:
    team_list = make_list("Main", "a", "b")
    removed_id = instance_ids(team_list)[0]
    editor = TeamEditor(make_team(team_list))

    assert editor.remove_slot(team_list.list_id, 0, when=BASE + timedelta(seconds=1)) is True
    assert ids(editor.team.lists[0]) == ["b"]
    assert removed_id not in instance_ids(editor.team.lists[0])

    assert editor.undo() is True
    assert ids(editor.team.lists[0]) == ["a", "b"]
    assert instance_ids(editor.team.lists[0])[0] == removed_id


def test_copy_inside_same_list_after_source_uses_original_source_before_insertion() -> None:
    team_list = make_list("Main", "a", "b", "c")
    source_id = instance_ids(team_list)[0]
    editor = TeamEditor(make_team(team_list))

    copied_id = editor.copy_champion(
        team_list.list_id,
        0,
        team_list.list_id,
        2,
        when=BASE + timedelta(seconds=1),
    )

    assert ids(editor.team.lists[0]) == ["a", "b", "a", "c"]
    assert instance_ids(editor.team.lists[0])[0] == source_id
    assert instance_ids(editor.team.lists[0])[2] == copied_id
    assert copied_id != source_id


def test_complete_builder_workflow_round_trips_every_snapshot() -> None:
    main = make_list("Main", "a", None, "b")
    editor = TeamEditor(make_team(main))
    original = deepcopy(editor.team)
    snapshots: list[Team] = []

    second_id = editor.create_list("Second", when=BASE + timedelta(seconds=1))
    snapshots.append(deepcopy(editor.team))
    editor.add_champion(second_id, 0, "c", when=BASE + timedelta(seconds=2))
    snapshots.append(deepcopy(editor.team))
    editor.copy_champion(main.list_id, 0, second_id, 0, when=BASE + timedelta(seconds=3))
    snapshots.append(deepcopy(editor.team))
    editor.set_trait_selection(
        second_id,
        0,
        TraitSelection(("trait_a",)),
        when=BASE + timedelta(seconds=4),
    )
    snapshots.append(deepcopy(editor.team))
    duplicate_id = editor.duplicate_list(
        second_id, name="Second copy", when=BASE + timedelta(seconds=5)
    )
    snapshots.append(deepcopy(editor.team))
    editor.reorder_list(duplicate_id, 0, when=BASE + timedelta(seconds=6))
    snapshots.append(deepcopy(editor.team))
    editor.set_primary_list(duplicate_id, when=BASE + timedelta(seconds=7))
    snapshots.append(deepcopy(editor.team))
    editor.clear_list(second_id, when=BASE + timedelta(seconds=8))
    snapshots.append(deepcopy(editor.team))
    editor.compact_list(second_id, when=BASE + timedelta(seconds=9))
    snapshots.append(deepcopy(editor.team))

    for expected in reversed([original, *snapshots[:-1]]):
        assert editor.undo() is True
        assert editor.team == expected
    assert editor.can_undo is False

    for expected in snapshots:
        assert editor.redo() is True
        assert editor.team == expected
    assert editor.can_redo is False
