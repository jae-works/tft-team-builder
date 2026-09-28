"""Pure Team-library filtering and Champion-similarity ranking."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from .models import Team, TeamList
from .search import normalize_search_text


@dataclass(frozen=True, slots=True)
class TeamSimilarity:
    """Best matching List information for one Team."""

    team: Team
    best_list_id: UUID
    matches: int
    extras: int


def filter_teams_by_name(teams: tuple[Team, ...], query: str) -> tuple[Team, ...]:
    """Filter Teams by normalized name while preserving input order."""

    needle = normalize_search_text(query)
    if not needle:
        return teams
    return tuple(team for team in teams if needle in normalize_search_text(team.name))


def list_champion_counts(team_list: TeamList) -> Counter[str]:
    """Return Champion-definition multiplicities for one List."""

    return Counter(
        slot.champion.champion_id for slot in team_list.slots if slot.champion is not None
    )


def _score_list(team_list: TeamList, desired: Counter[str]) -> tuple[int, int]:
    counts = list_champion_counts(team_list)
    matches = sum(min(counts[champion_id], amount) for champion_id, amount in desired.items())
    extras = max(0, sum(counts.values()) - matches)
    return matches, extras


def rank_teams_by_champions(
    teams: tuple[Team, ...], desired_champion_ids: tuple[str, ...]
) -> tuple[TeamSimilarity, ...]:
    """Rank Teams by their best List using deterministic multiset similarity."""

    desired = Counter(desired_champion_ids)
    results: list[TeamSimilarity] = []
    for team in teams:
        best_list = team.lists[0]
        best_matches, best_extras = _score_list(best_list, desired)
        for team_list in team.lists[1:]:
            matches, extras = _score_list(team_list, desired)
            if (matches, -extras) > (best_matches, -best_extras):
                best_list = team_list
                best_matches = matches
                best_extras = extras
        results.append(
            TeamSimilarity(
                team=team,
                best_list_id=best_list.list_id,
                matches=best_matches,
                extras=best_extras,
            )
        )

    if not desired:
        return tuple(
            sorted(
                results,
                key=lambda result: (
                    _descending_datetime_key(result.team.updated_at),
                    result.team.name.casefold(),
                    str(result.team.team_id),
                ),
            )
        )

    return tuple(
        sorted(
            results,
            key=lambda result: (
                -result.matches,
                result.extras,
                _descending_datetime_key(result.team.updated_at),
                result.team.name.casefold(),
                str(result.team.team_id),
            ),
        )
    )


def _descending_datetime_key(value: datetime) -> float:
    """Return a numeric key that sorts newer aware timestamps first."""

    return -value.timestamp()
