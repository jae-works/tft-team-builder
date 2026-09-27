from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from tft_builder.models import ChampionInstance, Slot, Team, TeamList, TraitSelection


def test_trait_selection_defaults_to_empty_tuple() -> None:
    assert TraitSelection().trait_ids == ()


def test_trait_selection_accepts_multiple_unique_traits() -> None:
    selection = TraitSelection(("trait_a", "trait_b"))
    assert selection.trait_ids == ("trait_a", "trait_b")


def test_trait_selection_rejects_duplicate_traits() -> None:
    with pytest.raises(ValueError, match="duplicates"):
        TraitSelection(("trait_a", "trait_a"))


@pytest.mark.parametrize("invalid", ["", " ", "   "])
def test_trait_selection_rejects_empty_or_blank_trait_id(invalid: str) -> None:
    with pytest.raises(ValueError, match="empty"):
        TraitSelection(("trait_a", invalid))


def test_champion_instance_generates_unique_ids() -> None:
    first = ChampionInstance("champion_a")
    second = ChampionInstance("champion_a")
    assert first.instance_id != second.instance_id
    assert first.champion_id == second.champion_id


def test_champion_instance_accepts_duplicate_champion_identity_as_separate_instances() -> None:
    first = ChampionInstance("champion_a")
    second = ChampionInstance("champion_a")
    assert first.champion_id == second.champion_id
    assert first.instance_id != second.instance_id


def test_champion_instance_rejects_empty_champion_id() -> None:
    with pytest.raises(ValueError, match="champion_id"):
        ChampionInstance("  ")


def test_champion_instance_preserves_trait_selection() -> None:
    selection = TraitSelection(("trait_a",))
    champion = ChampionInstance("champion_a", trait_selection=selection)
    assert champion.trait_selection is selection


@pytest.mark.parametrize("index", [0, 1, 1000])
def test_slot_accepts_non_negative_indexes(index: int) -> None:
    slot = Slot(index=index)
    assert slot.index == index
    assert slot.champion is None


def test_slot_rejects_negative_index() -> None:
    with pytest.raises(ValueError, match="zero or greater"):
        Slot(index=-1)


def test_slot_can_hold_champion_instance() -> None:
    champion = ChampionInstance("champion_a")
    slot = Slot(index=0, champion=champion)
    assert slot.champion is champion


def test_team_list_empty_factory_creates_no_slots() -> None:
    team_list = TeamList.empty("Main")
    assert team_list.name == "Main"
    assert team_list.slots == []


def test_team_list_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="list name"):
        TeamList.empty("   ")


def test_team_list_accepts_contiguous_slots_with_gaps_in_champion_content() -> None:
    team_list = TeamList(
        name="Main",
        slots=[
            Slot(0, ChampionInstance("champion_a")),
            Slot(1, None),
            Slot(2, ChampionInstance("champion_b")),
        ],
    )
    assert [slot.champion is None for slot in team_list.slots] == [False, True, False]


@pytest.mark.parametrize(
    "slots",
    [
        [Slot(1)],
        [Slot(0), Slot(2)],
        [Slot(0), Slot(0)],
        [Slot(2), Slot(1), Slot(0)],
    ],
)
def test_team_list_rejects_non_contiguous_or_unsorted_slot_indexes(slots: list[Slot]) -> None:
    with pytest.raises(ValueError, match="contiguously"):
        TeamList(name="Main", slots=slots)


def test_team_create_makes_one_primary_list() -> None:
    team = Team.create(set_id="sample_set", name="My Team")
    assert len(team.lists) == 1
    assert team.primary_list_id == team.lists[0].list_id
    assert team.primary_list.name == "Main"


def test_team_create_supports_custom_first_list_name() -> None:
    team = Team.create(set_id="sample_set", name="My Team", first_list_name="Level 8")
    assert team.primary_list.name == "Level 8"


def test_team_create_rejects_empty_set_id() -> None:
    with pytest.raises(ValueError, match="set_id"):
        Team.create(set_id=" ", name="My Team")


def test_team_create_rejects_empty_team_name() -> None:
    with pytest.raises(ValueError, match="team name"):
        Team.create(set_id="sample_set", name=" ")


def test_team_rejects_zero_lists() -> None:
    with pytest.raises(ValueError, match="at least one"):
        Team(set_id="sample_set", name="Team", lists=[], primary_list_id=uuid4())


def test_team_rejects_primary_list_not_in_team() -> None:
    team_list = TeamList.empty("Main")
    with pytest.raises(ValueError, match="primary_list_id"):
        Team(
            set_id="sample_set",
            name="Team",
            lists=[team_list],
            primary_list_id=uuid4(),
        )


def test_team_rejects_duplicate_list_ids() -> None:
    first = TeamList.empty("First")
    second = TeamList(name="Second", list_id=first.list_id)
    with pytest.raises(ValueError, match="unique"):
        Team(
            set_id="sample_set",
            name="Team",
            lists=[first, second],
            primary_list_id=first.list_id,
        )


def test_team_rejects_naive_created_timestamp() -> None:
    team_list = TeamList.empty("Main")
    with pytest.raises(ValueError, match="timezone-aware"):
        Team(
            set_id="sample_set",
            name="Team",
            lists=[team_list],
            primary_list_id=team_list.list_id,
            created_at=datetime.now(),
            updated_at=datetime.now(UTC),
        )


def test_team_rejects_naive_updated_timestamp() -> None:
    team_list = TeamList.empty("Main")
    with pytest.raises(ValueError, match="timezone-aware"):
        Team(
            set_id="sample_set",
            name="Team",
            lists=[team_list],
            primary_list_id=team_list.list_id,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(),
        )


def test_team_allows_duplicate_list_names_because_ids_define_identity() -> None:
    first = TeamList.empty("Variant")
    second = TeamList.empty("Variant")
    team = Team(
        set_id="sample_set",
        name="Team",
        lists=[first, second],
        primary_list_id=first.list_id,
    )
    assert [item.name for item in team.lists] == ["Variant", "Variant"]
    assert first.list_id != second.list_id


def test_user_visible_team_names_preserve_arbitrary_user_text() -> None:
    name = f"Cafe{chr(0xE9)} strategy"
    team = Team.create(set_id="sample_set", name=name)
    assert team.name == name


def test_team_name_has_no_artificial_length_limit() -> None:
    long_name = "A" * 10_000
    team = Team.create(set_id="sample_set", name=long_name)
    assert team.name == long_name


def test_team_rejects_duplicate_champion_instance_ids_across_lists() -> None:
    shared_id = uuid4()
    first = TeamList(
        name="First",
        slots=[Slot(0, ChampionInstance("champion_a", instance_id=shared_id))],
    )
    second = TeamList(
        name="Second",
        slots=[Slot(0, ChampionInstance("champion_b", instance_id=shared_id))],
    )
    with pytest.raises(ValueError, match="Champion instance IDs must be unique"):
        Team(
            set_id="sample_set",
            name="Team",
            lists=[first, second],
            primary_list_id=first.list_id,
        )


def test_team_accepts_duplicate_champion_definitions_with_unique_instance_ids() -> None:
    team_list = TeamList(
        name="Main",
        slots=[
            Slot(0, ChampionInstance("champion_a")),
            Slot(1, ChampionInstance("champion_a")),
        ],
    )
    team = Team(
        set_id="sample_set",
        name="Team",
        lists=[team_list],
        primary_list_id=team_list.list_id,
    )
    assert team.lists[0].slots[0].champion is not None
    assert team.lists[0].slots[1].champion is not None
    assert team.lists[0].slots[0].champion.instance_id != team.lists[0].slots[1].champion.instance_id
