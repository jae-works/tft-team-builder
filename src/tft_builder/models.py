"""Mutable domain models for user-created Teams and Lists.

External Set package data is validated by Pydantic models in ``set_schema.py``. User build
state is represented by standard-library dataclasses because it is mutable, small, and does
not benefit from adding a second validation framework to normal in-memory operations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


def _require_non_empty(value: str, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")


def _require_uuid(value: UUID, field_name: str) -> None:
    if not isinstance(value, UUID):
        raise TypeError(f"{field_name} must be a UUID")


def _require_aware_timestamp(value: datetime, field_name: str) -> None:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


@dataclass(frozen=True, slots=True)
class TraitSelection:
    """Dynamic Trait choices made for one Champion instance."""

    trait_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.trait_ids, tuple):
            raise TypeError("trait_ids must be a tuple")
        if any(not isinstance(trait_id, str) for trait_id in self.trait_ids):
            raise TypeError("trait_ids must contain only strings")
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
        _require_uuid(self.instance_id, "instance_id")
        if not isinstance(self.trait_selection, TraitSelection):
            raise TypeError("trait_selection must be a TraitSelection")


@dataclass(slots=True)
class Slot:
    """One ordered List position. Empty slots use ``champion=None``."""

    index: int
    champion: ChampionInstance | None = None

    def __post_init__(self) -> None:
        if isinstance(self.index, bool) or not isinstance(self.index, int):
            raise TypeError("slot index must be an integer")
        if self.index < 0:
            raise ValueError("slot index must be zero or greater")
        if self.champion is not None and not isinstance(self.champion, ChampionInstance):
            raise TypeError("slot champion must be a ChampionInstance or None")


@dataclass(slots=True)
class TeamList:
    """One stage or variant inside a Team."""

    name: str
    list_id: UUID = field(default_factory=uuid4)
    slots: list[Slot] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.validate_invariants()

    def validate_invariants(self) -> None:
        """Validate constraints that must remain true after future mutable operations."""

        _require_non_empty(self.name, "list name")
        _require_uuid(self.list_id, "list_id")
        if not isinstance(self.slots, list):
            raise TypeError("slots must be a list")
        if any(not isinstance(slot, Slot) for slot in self.slots):
            raise TypeError("slots must contain only Slot values")

        indexes = [slot.index for slot in self.slots]
        if indexes != list(range(len(self.slots))):
            raise ValueError("slots must be ordered and indexed contiguously from zero")

        instance_ids = [
            slot.champion.instance_id for slot in self.slots if slot.champion is not None
        ]
        if len(instance_ids) != len(set(instance_ids)):
            raise ValueError("Champion instance IDs must be unique inside a List")

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
        self.validate_invariants()

    def validate_invariants(self) -> None:
        """Validate all Team-wide invariants after construction or mutation."""

        _require_non_empty(self.set_id, "set_id")
        _require_non_empty(self.name, "team name")
        _require_uuid(self.primary_list_id, "primary_list_id")
        _require_uuid(self.team_id, "team_id")
        if not isinstance(self.lists, list):
            raise TypeError("lists must be a list")
        if any(not isinstance(team_list, TeamList) for team_list in self.lists):
            raise TypeError("lists must contain only TeamList values")
        if not self.lists:
            raise ValueError("a Team must contain at least one List")

        for team_list in self.lists:
            team_list.validate_invariants()

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

        _require_aware_timestamp(self.created_at, "created_at")
        _require_aware_timestamp(self.updated_at, "updated_at")
        if self.updated_at < self.created_at:
            raise ValueError("updated_at must not be earlier than created_at")

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
