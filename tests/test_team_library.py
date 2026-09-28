from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tft_builder.models import ChampionInstance, Slot, Team, TeamList
from tft_builder.team_library import (
    filter_teams_by_name,
    list_champion_counts,
    rank_teams_by_champions,
)

BASE = datetime(2026, 9, 28, 10, 0, tzinfo=UTC)


def make_team(name: str, *lists: tuple[str, ...], updated_offset: int = 0) -> Team:
    built = [
        TeamList(
            name=f"L{index + 1}",
            slots=[
                Slot(slot, ChampionInstance(champion_id)) for slot, champion_id in enumerate(ids)
            ],
        )
        for index, ids in enumerate(lists or ((),))
    ]
    return Team(
        set_id="sample_set",
        name=name,
        lists=built,
        primary_list_id=built[0].list_id,
        created_at=BASE,
        updated_at=BASE + timedelta(minutes=updated_offset),
    )


def test_name_filter_is_normalized_and_preserves_input_order() -> None:
    teams = (make_team("Fast Nine"), make_team("Guardian Tempo"), make_team("Other"))
    assert filter_teams_by_name(teams, "  FAST   nine ") == (teams[0],)
    assert filter_teams_by_name(teams, "") == teams
    assert filter_teams_by_name(teams, "zzz") == ()


def test_list_champion_counts_ignores_empty_slots_and_preserves_duplicates() -> None:
    team_list = TeamList(
        name="Main",
        slots=[
            Slot(0, ChampionInstance("a")),
            Slot(1),
            Slot(2, ChampionInstance("a")),
            Slot(3, ChampionInstance("b")),
        ],
    )
    assert list_champion_counts(team_list) == {"a": 2, "b": 1}


def test_empty_similarity_uses_normal_updated_order_then_name() -> None:
    older = make_team("Zed", ("a",), updated_offset=1)
    newer_b = make_team("Beta", ("b",), updated_offset=2)
    newer_a = make_team("Alpha", ("c",), updated_offset=2)
    ranked = rank_teams_by_champions((older, newer_b, newer_a), ())
    assert [item.team.name for item in ranked] == ["Alpha", "Beta", "Zed"]
    assert all(item.matches == 0 for item in ranked)


def test_similarity_prefers_more_matches_then_fewer_extras() -> None:
    exact = make_team("Exact", ("a", "b"))
    extra = make_team("Extra", ("a", "b", "c"))
    partial = make_team("Partial", ("a",))
    ranked = rank_teams_by_champions((partial, extra, exact), ("a", "b"))
    assert [item.team.name for item in ranked] == ["Exact", "Extra", "Partial"]
    assert [(item.matches, item.extras) for item in ranked] == [(2, 0), (2, 1), (1, 0)]


def test_duplicate_desired_champions_are_counted_as_multiset() -> None:
    one = make_team("One", ("a",))
    two = make_team("Two", ("a", "a"))
    ranked = rank_teams_by_champions((one, two), ("a", "a"))
    assert [item.team.name for item in ranked] == ["Two", "One"]
    assert [item.matches for item in ranked] == [2, 1]


def test_best_list_is_selected_without_flattening_team() -> None:
    team = make_team("Stages", ("a", "x", "x"), ("a", "b"))
    result = rank_teams_by_champions((team,), ("a", "b"))[0]
    assert result.best_list_id == team.lists[1].list_id
    assert (result.matches, result.extras) == (2, 0)


def test_equal_best_list_score_keeps_earlier_list_order() -> None:
    team = make_team("Tie", ("a",), ("a",))
    result = rank_teams_by_champions((team,), ("a",))[0]
    assert result.best_list_id == team.lists[0].list_id


def test_similarity_tie_uses_newer_team_then_name_deterministically() -> None:
    old = make_team("Old", ("a",), updated_offset=1)
    zed = make_team("Zed", ("a",), updated_offset=2)
    alpha = make_team("Alpha", ("a",), updated_offset=2)
    ranked = rank_teams_by_champions((old, zed, alpha), ("a",))
    assert [item.team.name for item in ranked] == ["Alpha", "Zed", "Old"]


def test_similarity_handles_no_matches_without_negative_extras() -> None:
    team = make_team("Nope", ())
    result = rank_teams_by_champions((team,), ("missing",))[0]
    assert result.matches == 0
    assert result.extras == 0
