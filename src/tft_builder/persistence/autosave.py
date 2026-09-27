"""Deterministic autosave primitives without UI timers or background threads."""

from __future__ import annotations

from copy import deepcopy
from uuid import UUID

from ..models import Team
from .team_repository import TeamRepository


class AutosaveService:
    """Save structural changes immediately and queue debounced text snapshots for later flush."""

    def __init__(self, repository: TeamRepository):
        self.repository = repository
        self._pending: dict[UUID, Team] = {}

    @property
    def pending_count(self) -> int:
        return len(self._pending)

    def save_now(self, team: Team) -> None:
        self.repository.save(team)
        self._pending.pop(team.team_id, None)

    def queue(self, team: Team) -> None:
        team.validate_invariants()
        self._pending[team.team_id] = deepcopy(team)

    def flush(self, team_id: UUID | None = None) -> int:
        ids = (team_id,) if team_id is not None else tuple(self._pending)
        saved = 0
        for pending_id in ids:
            team = self._pending.get(pending_id)
            if team is None:
                continue
            self.repository.save(team)
            self._pending.pop(pending_id, None)
            saved += 1
        return saved

    def discard(self, team_id: UUID) -> bool:
        return self._pending.pop(team_id, None) is not None
