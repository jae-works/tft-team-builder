from __future__ import annotations

from datetime import UTC, datetime, timedelta
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
    assert (
        team.lists[0].slots[0].champion.instance_id != team.lists[0].slots[1].champion.instance_id
    )


def test_team_list_rejects_duplicate_instance_ids_inside_same_list() -> None:
    shared_id = uuid4()
    with pytest.raises(ValueError, match="Champion instance IDs must be unique"):
        TeamList(
            name="Main",
            slots=[
                Slot(0, ChampionInstance("champion_a", instance_id=shared_id)),
                Slot(1, ChampionInstance("champion_b", instance_id=shared_id)),
            ],
        )


def test_team_list_validate_invariants_detects_invalid_mutation() -> None:
    team_list = TeamList(name="Main", slots=[Slot(0)])
    team_list.slots.append(Slot(3))
    with pytest.raises(ValueError, match="contiguously"):
        team_list.validate_invariants()


def test_team_validate_invariants_detects_primary_list_removed_after_mutation() -> None:
    team = Team.create(set_id="sample_set", name="Team")
    team.lists.clear()
    with pytest.raises(ValueError, match="at least one"):
        team.validate_invariants()


def test_team_rejects_updated_timestamp_earlier_than_created_timestamp() -> None:
    team_list = TeamList.empty("Main")
    created = datetime(2026, 1, 2, tzinfo=UTC)
    updated = datetime(2026, 1, 1, tzinfo=UTC)
    with pytest.raises(ValueError, match="earlier"):
        Team(
            set_id="sample_set",
            name="Team",
            lists=[team_list],
            primary_list_id=team_list.list_id,
            created_at=created,
            updated_at=updated,
        )


def test_trait_selection_requires_tuple_storage() -> None:
    with pytest.raises(TypeError, match="tuple"):
        TraitSelection(["trait_a"])  # type: ignore[arg-type]


def test_trait_selection_requires_string_values() -> None:
    with pytest.raises(TypeError, match="strings"):
        TraitSelection(("trait_a", 42))  # type: ignore[arg-type]


def test_champion_instance_rejects_non_string_champion_id() -> None:
    with pytest.raises(TypeError, match="champion_id"):
        ChampionInstance(42)  # type: ignore[arg-type]


def test_champion_instance_requires_uuid_instance_id() -> None:
    with pytest.raises(TypeError, match="instance_id"):
        ChampionInstance("champion_a", instance_id="not-a-uuid")  # type: ignore[arg-type]


def test_champion_instance_requires_trait_selection_model() -> None:
    with pytest.raises(TypeError, match="TraitSelection"):
        ChampionInstance("champion_a", trait_selection=("trait_a",))  # type: ignore[arg-type]


@pytest.mark.parametrize("index", [True, 1.5, "1"])
def test_slot_rejects_non_integer_index(index: object) -> None:
    with pytest.raises(TypeError, match="integer"):
        Slot(index=index)  # type: ignore[arg-type]


def test_slot_rejects_non_champion_payload() -> None:
    with pytest.raises(TypeError, match="ChampionInstance"):
        Slot(index=0, champion="champion_a")  # type: ignore[arg-type]


def test_team_list_requires_uuid_list_id() -> None:
    with pytest.raises(TypeError, match="list_id"):
        TeamList(name="Main", list_id="not-a-uuid")  # type: ignore[arg-type]


def test_team_list_requires_mutable_slot_list() -> None:
    with pytest.raises(TypeError, match="slots must be a list"):
        TeamList(name="Main", slots=())  # type: ignore[arg-type]


def test_team_list_requires_slot_values() -> None:
    with pytest.raises(TypeError, match="only Slot"):
        TeamList(name="Main", slots=["not-a-slot"])  # type: ignore[list-item]


def test_team_requires_uuid_primary_list_id() -> None:
    team_list = TeamList.empty("Main")
    with pytest.raises(TypeError, match="primary_list_id"):
        Team(
            set_id="sample_set",
            name="Team",
            lists=[team_list],
            primary_list_id="not-a-uuid",  # type: ignore[arg-type]
        )


def test_team_requires_uuid_team_id() -> None:
    team_list = TeamList.empty("Main")
    with pytest.raises(TypeError, match="team_id"):
        Team(
            set_id="sample_set",
            name="Team",
            lists=[team_list],
            primary_list_id=team_list.list_id,
            team_id="not-a-uuid",  # type: ignore[arg-type]
        )


def test_team_requires_mutable_list_collection() -> None:
    team_list = TeamList.empty("Main")
    with pytest.raises(TypeError, match="lists must be a list"):
        Team(
            set_id="sample_set",
            name="Team",
            lists=(team_list,),  # type: ignore[arg-type]
            primary_list_id=team_list.list_id,
        )


def test_team_requires_team_list_values() -> None:
    with pytest.raises(TypeError, match="only TeamList"):
        Team(
            set_id="sample_set",
            name="Team",
            lists=["not-a-list"],  # type: ignore[list-item]
            primary_list_id=uuid4(),
        )


def test_team_rejects_non_datetime_created_timestamp() -> None:
    team_list = TeamList.empty("Main")
    with pytest.raises(TypeError, match="created_at"):
        Team(
            set_id="sample_set",
            name="Team",
            lists=[team_list],
            primary_list_id=team_list.list_id,
            created_at="2026-01-01",  # type: ignore[arg-type]
        )


def test_team_rejects_non_datetime_updated_timestamp() -> None:
    team_list = TeamList.empty("Main")
    with pytest.raises(TypeError, match="updated_at"):
        Team(
            set_id="sample_set",
            name="Team",
            lists=[team_list],
            primary_list_id=team_list.list_id,
            updated_at="2026-01-01",  # type: ignore[arg-type]
        )


def test_primary_list_property_detects_invariant_break_after_external_mutation() -> None:
    from uuid import uuid4

    team = Team.create(set_id="sample_set", name="Example")
    team.primary_list_id = uuid4()

    with pytest.raises(RuntimeError, match="primary List is missing"):
        _ = team.primary_list


def test_team_optional_timestamps_must_be_timezone_aware() -> None:
    team = Team.create(set_id="set", name="Time")
    team.last_opened_at = datetime(2026, 9, 27)
    with pytest.raises(ValueError, match="last_opened_at must be timezone-aware"):
        team.validate_invariants()


def test_team_optional_timestamps_cannot_precede_creation() -> None:
    created = datetime(2026, 9, 27, tzinfo=UTC)
    team = Team.create(set_id="set", name="Time")
    team.created_at = created
    team.updated_at = created
    team.deleted_at = created - timedelta(seconds=1)
    with pytest.raises(ValueError, match="deleted_at must not be earlier"):
        team.validate_invariants()
