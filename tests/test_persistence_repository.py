from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from tft_builder.models import ChampionInstance, Slot, Team, TeamList, TraitSelection
from tft_builder.persistence import Database, TeamRepository
from tft_builder.persistence.team_repository import TeamNotFoundError


def make_repository(tmp_path: Path) -> TeamRepository:
    database = Database(tmp_path / "builder.db")
    database.initialize()
    return TeamRepository(database)


def make_complex_team() -> Team:
    created = datetime(2026, 9, 27, 10, 0, tzinfo=UTC)
    first = TeamList(
        name="Level 8",
        slots=[
            Slot(0, ChampionInstance("lux", trait_selection=TraitSelection(("arcane",)))),
            Slot(1),
            Slot(2, ChampionInstance("lux")),
        ],
    )
    second = TeamList(
        name="Level 9",
        slots=[Slot(0, ChampionInstance("garen")), Slot(1, ChampionInstance("ahri"))],
    )
    return Team(
        set_id="set_test",
        name="Fast 9",
        lists=[first, second],
        primary_list_id=second.list_id,
        created_at=created,
        updated_at=created + timedelta(minutes=2),
        last_opened_at=created + timedelta(minutes=1),
    )


def test_complex_team_round_trip_is_exact(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    team = make_complex_team()
    repository.save(team)
    assert repository.load(team.team_id) == team


def test_round_trip_survives_new_database_and_repository_instance(tmp_path: Path) -> None:
    path = tmp_path / "builder.db"
    first_database = Database(path)
    first_database.initialize()
    team = make_complex_team()
    TeamRepository(first_database).save(team)
    second_database = Database(path)
    second_database.initialize()
    assert TeamRepository(second_database).load(team.team_id) == team


def test_save_replaces_existing_child_graph_without_orphans(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    team = make_complex_team()
    removed_instance = team.lists[0].slots[0].champion.instance_id
    repository.save(team)
    team.lists = [TeamList(name="Replacement", slots=[Slot(0)])]
    team.primary_list_id = team.lists[0].list_id
    repository.save(team)
    loaded = repository.load(team.team_id)
    assert loaded == team
    with repository.database.connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) FROM champion_instances WHERE instance_id = ?",
            (str(removed_instance),),
        ).fetchone()[0]
        assert count == 0


def test_save_is_atomic_when_invariant_fails(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    team = make_complex_team()
    repository.save(team)
    team.lists[0].slots[0].index = 9
    with pytest.raises(ValueError, match="contiguously"):
        repository.save(team)
    persisted = repository.load(team.team_id)
    assert persisted.lists[0].slots[0].index == 0


def test_missing_team_raises(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    with pytest.raises(TeamNotFoundError):
        repository.load(uuid4())


def test_deleted_team_is_hidden_by_default(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    team = make_complex_team()
    repository.save(team)
    assert repository.soft_delete(team.team_id)
    with pytest.raises(TeamNotFoundError):
        repository.load(team.team_id)
    deleted = repository.load(team.team_id, include_deleted=True)
    assert deleted.deleted_at is not None


def test_soft_delete_is_idempotent_by_return_value(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    team = make_complex_team()
    repository.save(team)
    when = datetime(2026, 9, 28, tzinfo=UTC)
    assert repository.soft_delete(team.team_id, when=when)
    assert not repository.soft_delete(team.team_id, when=when)


def test_restore_makes_team_visible_again(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    team = make_complex_team()
    repository.save(team)
    repository.soft_delete(team.team_id, when=datetime(2026, 9, 28, tzinfo=UTC))
    assert repository.restore(team.team_id, when=datetime(2026, 9, 29, tzinfo=UTC))
    restored = repository.load(team.team_id)
    assert restored.deleted_at is None
    assert restored.updated_at == datetime(2026, 9, 29, tzinfo=UTC)
    assert not repository.restore(team.team_id)


def test_mark_opened_updates_only_last_opened_timestamp(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    team = make_complex_team()
    repository.save(team)
    updated_before = team.updated_at
    opened = datetime(2026, 9, 30, tzinfo=UTC)
    assert repository.mark_opened(team.team_id, when=opened)
    loaded = repository.load(team.team_id)
    assert loaded.last_opened_at == opened
    assert loaded.updated_at == updated_before


def test_mark_opened_returns_false_for_unknown_team(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    assert not repository.mark_opened(uuid4())


def test_list_ids_excludes_deleted_and_orders_by_updated_at(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    older = make_complex_team()
    older.updated_at = datetime(2026, 9, 27, 11, tzinfo=UTC)
    newer = make_complex_team()
    newer.updated_at = datetime(2026, 9, 27, 12, tzinfo=UTC)
    deleted = make_complex_team()
    deleted.updated_at = datetime(2026, 9, 27, 13, tzinfo=UTC)
    for team in (older, newer, deleted):
        repository.save(team)
    repository.soft_delete(deleted.team_id, when=datetime(2026, 9, 28, tzinfo=UTC))
    assert repository.list_ids() == (newer.team_id, older.team_id)
    assert set(repository.list_ids(include_deleted=True)) == {
        older.team_id,
        newer.team_id,
        deleted.team_id,
    }


def test_permanent_delete_cascades_every_child_row(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    team = make_complex_team()
    repository.save(team)
    assert repository.delete_permanently(team.team_id)
    assert not repository.delete_permanently(team.team_id)
    with repository.database.connection() as connection:
        for table in ("teams", "team_lists", "slots", "champion_instances", "trait_selections"):
            assert connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def test_empty_trait_selection_and_empty_slots_round_trip(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    team = Team.create(set_id="set", name="Empty details")
    team.primary_list.slots.extend([Slot(0), Slot(1, ChampionInstance("unit")), Slot(2)])
    repository.save(team)
    assert repository.load(team.team_id) == team


def test_duplicate_champion_definitions_round_trip_as_distinct_instances(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    team = Team.create(set_id="set", name="Duplicates")
    first = ChampionInstance("lux")
    second = ChampionInstance("lux")
    team.primary_list.slots.extend([Slot(0, first), Slot(1, second)])
    repository.save(team)
    loaded = repository.load(team.team_id)
    assert loaded.primary_list.slots[0].champion.champion_id == "lux"
    assert loaded.primary_list.slots[1].champion.champion_id == "lux"
    first_id = loaded.primary_list.slots[0].champion.instance_id
    second_id = loaded.primary_list.slots[1].champion.instance_id
    assert first_id != second_id


def test_large_team_round_trip_preserves_all_slots_and_traits(tmp_path: Path) -> None:
    repository = make_repository(tmp_path)
    team = Team.create(set_id="set", name="Large")
    team.primary_list.slots = [
        Slot(
            index,
            ChampionInstance(
                f"unit-{index % 7}",
                trait_selection=TraitSelection((f"trait-{index % 3}", f"extra-{index}")),
            ),
        )
        for index in range(200)
    ]
    repository.save(team)
    assert repository.load(team.team_id) == team
