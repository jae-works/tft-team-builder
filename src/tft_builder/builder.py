"""UI-independent Team editing operations with exact in-memory undo/redo history."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from datetime import UTC, datetime
from uuid import UUID, uuid4

from .models import ChampionInstance, Slot, Team, TeamList, TraitSelection


class TeamEditor:
    """Apply concrete Team edits while recording exact reversible snapshots.

    The editor intentionally owns no persistence or Flet behavior. Each successful edit is
    committed atomically from a working copy, updates ``Team.updated_at`` once, and records one
    pre-edit snapshot. Failed and no-op edits leave both Team state and history untouched.
    """

    def __init__(self, team: Team) -> None:
        if not isinstance(team, Team):
            raise TypeError("team must be a Team")
        team.validate_invariants()
        self.team = team
        self._undo: list[Team] = []
        self._redo: list[Team] = []

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)

    @property
    def undo_depth(self) -> int:
        return len(self._undo)

    @property
    def redo_depth(self) -> int:
        return len(self._redo)

    def clear_history(self) -> None:
        """Discard transient edit history without changing the Team."""

        self._undo.clear()
        self._redo.clear()

    def undo(self) -> bool:
        """Restore the exact Team snapshot before the most recent successful edit."""

        if not self._undo:
            return False
        self._redo.append(deepcopy(self.team))
        previous = self._undo.pop()
        self._restore(previous)
        return True

    def redo(self) -> bool:
        """Restore the exact Team snapshot after the most recently undone edit."""

        if not self._redo:
            return False
        self._undo.append(deepcopy(self.team))
        following = self._redo.pop()
        self._restore(following)
        return True

    def rename_team(self, name: str, *, when: datetime | None = None) -> bool:
        return self._edit(lambda team: setattr(team, "name", name), when=when)

    def rename_list(self, list_id: UUID, name: str, *, when: datetime | None = None) -> bool:
        def mutate(team: Team) -> None:
            self._get_list(team, list_id).name = name

        return self._edit(mutate, when=when)

    def set_primary_list(self, list_id: UUID, *, when: datetime | None = None) -> bool:
        def mutate(team: Team) -> None:
            self._get_list(team, list_id)
            team.primary_list_id = list_id

        return self._edit(mutate, when=when)

    def create_list(
        self,
        name: str,
        *,
        index: int | None = None,
        when: datetime | None = None,
    ) -> UUID:
        list_id = uuid4()

        def mutate(team: Team) -> None:
            target = (
                len(team.lists) if index is None else self._insert_index(index, len(team.lists))
            )
            team.lists.insert(target, TeamList(name=name, list_id=list_id))

        self._edit(mutate, when=when)
        return list_id

    def duplicate_list(
        self,
        list_id: UUID,
        *,
        name: str | None = None,
        when: datetime | None = None,
    ) -> UUID:
        duplicate_id = uuid4()

        def mutate(team: Team) -> None:
            source_index = self._get_list_index(team, list_id)
            source = team.lists[source_index]
            slots = [
                Slot(
                    index=slot.index,
                    champion=(
                        None
                        if slot.champion is None
                        else ChampionInstance(
                            champion_id=slot.champion.champion_id,
                            trait_selection=slot.champion.trait_selection,
                        )
                    ),
                )
                for slot in source.slots
            ]
            team.lists.insert(
                source_index + 1,
                TeamList(
                    name=source.name if name is None else name,
                    list_id=duplicate_id,
                    slots=slots,
                ),
            )

        self._edit(mutate, when=when)
        return duplicate_id

    def delete_list(self, list_id: UUID, *, when: datetime | None = None) -> bool:
        def mutate(team: Team) -> None:
            if len(team.lists) == 1:
                raise ValueError("the final remaining List cannot be deleted")
            index = self._get_list_index(team, list_id)
            was_primary = team.primary_list_id == list_id
            team.lists.pop(index)
            if was_primary:
                replacement_index = min(index, len(team.lists) - 1)
                team.primary_list_id = team.lists[replacement_index].list_id

        return self._edit(mutate, when=when)

    def reorder_list(self, list_id: UUID, new_index: int, *, when: datetime | None = None) -> bool:
        def mutate(team: Team) -> None:
            source_index = self._get_list_index(team, list_id)
            target_index = self._existing_index(new_index, len(team.lists))
            if source_index == target_index:
                return
            team.lists.insert(target_index, team.lists.pop(source_index))

        return self._edit(mutate, when=when)

    def clear_list(self, list_id: UUID, *, when: datetime | None = None) -> bool:
        def mutate(team: Team) -> None:
            for slot in self._get_list(team, list_id).slots:
                slot.champion = None

        return self._edit(mutate, when=when)

    def compact_list(self, list_id: UUID, *, when: datetime | None = None) -> bool:
        def mutate(team: Team) -> None:
            team_list = self._get_list(team, list_id)
            champions = [slot.champion for slot in team_list.slots if slot.champion is not None]
            team_list.slots = [
                Slot(index=index, champion=champion) for index, champion in enumerate(champions)
            ]

        return self._edit(mutate, when=when)

    def insert_slot(self, list_id: UUID, index: int, *, when: datetime | None = None) -> bool:
        def mutate(team: Team) -> None:
            team_list = self._get_list(team, list_id)
            target = self._insert_index(index, len(team_list.slots))
            team_list.slots.insert(target, Slot(index=target))
            self._reindex(team_list)

        return self._edit(mutate, when=when)

    def remove_slot(self, list_id: UUID, index: int, *, when: datetime | None = None) -> bool:
        def mutate(team: Team) -> None:
            team_list = self._get_list(team, list_id)
            target = self._existing_index(index, len(team_list.slots))
            team_list.slots.pop(target)
            self._reindex(team_list)

        return self._edit(mutate, when=when)

    def clear_slot(self, list_id: UUID, index: int, *, when: datetime | None = None) -> bool:
        def mutate(team: Team) -> None:
            team_list = self._get_list(team, list_id)
            team_list.slots[self._existing_index(index, len(team_list.slots))].champion = None

        return self._edit(mutate, when=when)

    def add_champion(
        self,
        list_id: UUID,
        index: int,
        champion_id: str,
        *,
        trait_selection: TraitSelection | None = None,
        when: datetime | None = None,
    ) -> UUID:
        champion = ChampionInstance(
            champion_id=champion_id,
            trait_selection=TraitSelection() if trait_selection is None else trait_selection,
        )

        def mutate(team: Team) -> None:
            team_list = self._get_list(team, list_id)
            self._place_new_champion(team_list, index, champion)

        self._edit(mutate, when=when)
        return champion.instance_id

    def move_champion(
        self,
        source_list_id: UUID,
        source_index: int,
        target_list_id: UUID,
        target_index: int,
        *,
        when: datetime | None = None,
    ) -> bool:
        def mutate(team: Team) -> None:
            source_list = self._get_list(team, source_list_id)
            source_slot = source_list.slots[
                self._existing_index(source_index, len(source_list.slots))
            ]
            if source_slot.champion is None:
                raise ValueError("source slot does not contain a Champion")

            target_list = self._get_list(team, target_list_id)
            target = self._insert_index(target_index, len(target_list.slots))
            if source_list_id == target_list_id and source_index == target:
                return

            if target == len(target_list.slots):
                target_list.slots.append(Slot(index=target, champion=source_slot.champion))
                source_slot.champion = None
                return

            target_slot = target_list.slots[target]
            source_slot.champion, target_slot.champion = target_slot.champion, source_slot.champion

        return self._edit(mutate, when=when)

    def copy_champion(
        self,
        source_list_id: UUID,
        source_index: int,
        target_list_id: UUID,
        target_index: int,
        *,
        when: datetime | None = None,
    ) -> UUID:
        copied_id = uuid4()

        def mutate(team: Team) -> None:
            source_list = self._get_list(team, source_list_id)
            source_slot = source_list.slots[
                self._existing_index(source_index, len(source_list.slots))
            ]
            if source_slot.champion is None:
                raise ValueError("source slot does not contain a Champion")
            copied = ChampionInstance(
                champion_id=source_slot.champion.champion_id,
                instance_id=copied_id,
                trait_selection=source_slot.champion.trait_selection,
            )
            target_list = self._get_list(team, target_list_id)
            self._place_new_champion(target_list, target_index, copied)

        self._edit(mutate, when=when)
        return copied_id

    def set_trait_selection(
        self,
        list_id: UUID,
        index: int,
        selection: TraitSelection,
        *,
        when: datetime | None = None,
    ) -> bool:
        if not isinstance(selection, TraitSelection):
            raise TypeError("selection must be a TraitSelection")

        def mutate(team: Team) -> None:
            team_list = self._get_list(team, list_id)
            slot = team_list.slots[self._existing_index(index, len(team_list.slots))]
            if slot.champion is None:
                raise ValueError("slot does not contain a Champion")
            slot.champion.trait_selection = selection

        return self._edit(mutate, when=when)

    def _edit(self, mutate: Callable[[Team], None], *, when: datetime | None) -> bool:
        timestamp = self._edit_timestamp(when)
        working = deepcopy(self.team)
        mutate(working)
        if working == self.team:
            return False

        working.updated_at = timestamp
        working.validate_invariants()
        self._undo.append(deepcopy(self.team))
        self._redo.clear()
        self._restore(working)
        return True

    def _edit_timestamp(self, when: datetime | None) -> datetime:
        timestamp = datetime.now(UTC) if when is None else when
        if not isinstance(timestamp, datetime):
            raise TypeError("when must be a datetime or None")
        if timestamp.utcoffset() is None:
            raise ValueError("when must be timezone-aware")
        timestamp = timestamp.astimezone(UTC)
        if timestamp < self.team.updated_at:
            raise ValueError("when must not be earlier than the current Team updated_at")
        return timestamp

    def _restore(self, source: Team) -> None:
        """Replace Team fields while preserving the top-level Team object identity."""

        # Restore only snapshots owned by this editor; callers never receive these objects.
        self.team.set_id = source.set_id
        self.team.name = source.name
        self.team.lists = source.lists
        self.team.primary_list_id = source.primary_list_id
        self.team.team_id = source.team_id
        self.team.created_at = source.created_at
        self.team.updated_at = source.updated_at
        self.team.last_opened_at = source.last_opened_at
        self.team.deleted_at = source.deleted_at
        self.team.validate_invariants()

    @staticmethod
    def _get_list_index(team: Team, list_id: UUID) -> int:
        if not isinstance(list_id, UUID):
            raise TypeError("list_id must be a UUID")
        for index, team_list in enumerate(team.lists):
            if team_list.list_id == list_id:
                return index
        raise ValueError(f"unknown List ID: {list_id}")

    @classmethod
    def _get_list(cls, team: Team, list_id: UUID) -> TeamList:
        return team.lists[cls._get_list_index(team, list_id)]

    @staticmethod
    def _existing_index(index: int, length: int) -> int:
        TeamEditor._require_integer_index(index)
        if index < 0 or index >= length:
            raise IndexError(f"index {index} is outside the existing range 0..{length - 1}")
        return index

    @staticmethod
    def _insert_index(index: int, length: int) -> int:
        TeamEditor._require_integer_index(index)
        if index < 0 or index > length:
            raise IndexError(f"index {index} is outside the insertion range 0..{length}")
        return index

    @staticmethod
    def _require_integer_index(index: int) -> None:
        if isinstance(index, bool) or not isinstance(index, int):
            raise TypeError("index must be an integer")

    @staticmethod
    def _reindex(team_list: TeamList) -> None:
        for index, slot in enumerate(team_list.slots):
            slot.index = index

    @staticmethod
    def _place_new_champion(team_list: TeamList, index: int, champion: ChampionInstance) -> None:
        target = TeamEditor._insert_index(index, len(team_list.slots))
        if target == len(team_list.slots):
            team_list.slots.append(Slot(index=target, champion=champion))
            return
        if team_list.slots[target].champion is None:
            team_list.slots[target].champion = champion
            return
        team_list.slots.insert(target, Slot(index=target, champion=champion))
        TeamEditor._reindex(team_list)
