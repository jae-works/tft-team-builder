from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from tft_builder.models import Team
from tft_builder.persistence import AutosaveService, Database, TeamRepository


def make_autosave(tmp_path: Path) -> tuple[AutosaveService, TeamRepository]:
    database = Database(tmp_path / "builder.db")
    database.initialize()
    repository = TeamRepository(database)
    return AutosaveService(repository), repository


def test_save_now_persists_immediately(tmp_path: Path) -> None:
    autosave, repository = make_autosave(tmp_path)
    team = Team.create(set_id="set", name="Immediate")
    autosave.save_now(team)
    assert repository.load(team.team_id) == team
    assert autosave.pending_count == 0


def test_queue_does_not_write_until_flush(tmp_path: Path) -> None:
    autosave, repository = make_autosave(tmp_path)
    team = Team.create(set_id="set", name="Queued")
    autosave.queue(team)
    assert autosave.pending_count == 1
    assert repository.list_ids() == ()
    assert autosave.flush() == 1
    assert repository.load(team.team_id) == team


def test_queue_snapshots_mutable_team_state(tmp_path: Path) -> None:
    autosave, repository = make_autosave(tmp_path)
    team = Team.create(set_id="set", name="Snapshot")
    autosave.queue(team)
    team.name = "Changed later"
    autosave.flush()
    assert repository.load(team.team_id).name == "Snapshot"


def test_queue_replaces_older_snapshot_for_same_team(tmp_path: Path) -> None:
    autosave, repository = make_autosave(tmp_path)
    team = Team.create(set_id="set", name="First")
    autosave.queue(team)
    team.name = "Second"
    autosave.queue(team)
    assert autosave.pending_count == 1
    autosave.flush()
    assert repository.load(team.team_id).name == "Second"


def test_flush_specific_team_leaves_other_team_pending(tmp_path: Path) -> None:
    autosave, repository = make_autosave(tmp_path)
    first = Team.create(set_id="set", name="First")
    second = Team.create(set_id="set", name="Second")
    autosave.queue(first)
    autosave.queue(second)
    assert autosave.flush(first.team_id) == 1
    assert autosave.pending_count == 1
    assert repository.load(first.team_id) == first
    assert repository.list_ids() == (first.team_id,)


def test_flush_unknown_team_id_is_noop(tmp_path: Path) -> None:
    autosave, _ = make_autosave(tmp_path)
    assert autosave.flush(uuid4()) == 0


def test_discard_removes_pending_snapshot(tmp_path: Path) -> None:
    autosave, _ = make_autosave(tmp_path)
    team = Team.create(set_id="set", name="Discard")
    autosave.queue(team)
    assert autosave.discard(team.team_id)
    assert not autosave.discard(team.team_id)
    assert autosave.pending_count == 0


def test_save_now_clears_queued_snapshot(tmp_path: Path) -> None:
    autosave, repository = make_autosave(tmp_path)
    team = Team.create(set_id="set", name="Queued")
    autosave.queue(team)
    team.name = "Immediate"
    autosave.save_now(team)
    assert autosave.pending_count == 0
    assert repository.load(team.team_id).name == "Immediate"


def test_editor_changes_round_trip_through_immediate_autosave(tmp_path: Path) -> None:
    from datetime import timedelta

    from tft_builder.builder import TeamEditor

    autosave, repository = make_autosave(tmp_path)
    team = Team.create(set_id="set", name="Builder")
    editor = TeamEditor(team)
    changed_at = team.updated_at + timedelta(seconds=1)

    list_id = team.primary_list_id
    editor.add_champion(list_id, 0, "champion", when=changed_at)
    autosave.save_now(team)
    assert repository.load(team.team_id) == team

    assert editor.undo() is True
    autosave.save_now(team)
    assert repository.load(team.team_id) == team
    assert repository.load(team.team_id).primary_list.slots == []
