"""Mutable domain models for user-created Teams and Lists.

External Set package data is validated by Pydantic models in ``set_schema.py``. User build
state is intentionally represented by standard-library dataclasses because it is mutable,
small, and does not benefit from a second validation framework layer at this stage.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


def _require_non_empty(value: str, field_name: str) -> None:
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


@dataclass(frozen=True, slots=True)
class TraitSelection:
    """Dynamic Trait choices made for one Champion instance."""

    trait_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if len(self.trait_ids) != len(set(self.trait_ids)):
            raise ValueError("trait_ids must not contain duplicates")
        if any(not trait_id.strip() for trait_id in self.trait_ids):
            raise ValueError("trait_ids must not contain empty values")


@dataclass(slots=True)
class ChampionInstance:
    """One concrete Champion placed on a List."""

    champion_id: str
    instance_id: UUID = field(default_factory=uuid4)
    trait_selection: TraitSelection = field(default_factory=TraitSelection)

    def __post_init__(self) -> None:
        _require_non_empty(self.champion_id, "champion_id")


@dataclass(slots=True)
class Slot:
    """One ordered position in a List. Empty slots are represented by ``champion=None``."""

    index: int
    champion: ChampionInstance | None = None

    def __post_init__(self) -> None:
        if self.index < 0:
            raise ValueError("slot index must be zero or greater")


@dataclass(slots=True)
class TeamList:
    """One stage or variant inside a Team."""

    name: str
    list_id: UUID = field(default_factory=uuid4)
    slots: list[Slot] = field(default_factory=list)

    def __post_init__(self) -> None:
        _require_non_empty(self.name, "list name")
        self.validate_slots()

    def validate_slots(self) -> None:
        """Require a dense ordered slot index range while still allowing empty slots."""

        indexes = [slot.index for slot in self.slots]
        if indexes != list(range(len(self.slots))):
            raise ValueError("slots must be ordered and indexed contiguously from zero")

    @classmethod
    def empty(cls, name: str) -> TeamList:
        return cls(name=name)


@dataclass(slots=True)
class Team:
    """Top-level user build containing one or more Lists and one primary List."""

    set_id: str
    name: str
    lists: list[TeamList]
    primary_list_id: UUID
    team_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        _require_non_empty(self.set_id, "set_id")
        _require_non_empty(self.name, "team name")
        if not self.lists:
            raise ValueError("a Team must contain at least one List")

        list_ids = [team_list.list_id for team_list in self.lists]
        if len(list_ids) != len(set(list_ids)):
            raise ValueError("List IDs must be unique inside a Team")
        if self.primary_list_id not in set(list_ids):
            raise ValueError("primary_list_id must reference a List in the Team")

        instance_ids = [
            slot.champion.instance_id
            for team_list in self.lists
            for slot in team_list.slots
            if slot.champion is not None
        ]
        if len(instance_ids) != len(set(instance_ids)):
            raise ValueError("Champion instance IDs must be unique inside a Team")

        if self.created_at.utcoffset() is None or self.updated_at.utcoffset() is None:
            raise ValueError("Team timestamps must be timezone-aware")

    @classmethod
    def create(cls, *, set_id: str, name: str, first_list_name: str = "Main") -> Team:
        """Create the only valid initial Team shape: one primary List."""

        first_list = TeamList.empty(first_list_name)
        return cls(
            set_id=set_id,
            name=name,
            lists=[first_list],
            primary_list_id=first_list.list_id,
        )

    @property
    def primary_list(self) -> TeamList:
        for team_list in self.lists:
            if team_list.list_id == self.primary_list_id:
                return team_list
        raise RuntimeError("Team invariant broken: primary List is missing")
