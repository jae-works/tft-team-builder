"""Straightforward persistence for complete Team aggregates."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from datetime import UTC, datetime
from uuid import UUID

from ..models import ChampionInstance, Slot, Team, TeamList, TraitSelection
from .database import Database
from .time_codec import decode_timestamp, encode_timestamp


class TeamNotFoundError(LookupError):
    """Raised when a requested Team does not exist in the selected visibility scope."""


class TeamRepository:
    def __init__(self, database: Database):
        self.database = database

    def save(self, team: Team) -> None:
        """Persist one complete Team in a single transaction."""

        team.validate_invariants()
        list_rows: list[tuple[str, str, str, int]] = []
        slot_rows: list[tuple[str, int]] = []
        champion_rows: list[tuple[str, str, int, str]] = []
        trait_rows: list[tuple[str, int, str]] = []

        for order_index, team_list in enumerate(team.lists):
            list_id = str(team_list.list_id)
            list_rows.append((list_id, str(team.team_id), team_list.name, order_index))
            for slot in team_list.slots:
                slot_rows.append((list_id, slot.index))
                champion = slot.champion
                if champion is None:
                    continue
                instance_id = str(champion.instance_id)
                champion_rows.append((instance_id, list_id, slot.index, champion.champion_id))
                trait_rows.extend(
                    (instance_id, index, trait_id)
                    for index, trait_id in enumerate(champion.trait_selection.trait_ids)
                )

        with self.database.transaction() as connection:
            connection.execute(
                """
                INSERT INTO teams(
                    team_id, set_id, name, primary_list_id, created_at, updated_at,
                    last_opened_at, deleted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(team_id) DO UPDATE SET
                    set_id = excluded.set_id,
                    name = excluded.name,
                    primary_list_id = excluded.primary_list_id,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at,
                    last_opened_at = excluded.last_opened_at,
                    deleted_at = excluded.deleted_at
                """,
                (
                    str(team.team_id),
                    team.set_id,
                    team.name,
                    str(team.primary_list_id),
                    encode_timestamp(team.created_at),
                    encode_timestamp(team.updated_at),
                    encode_timestamp(team.last_opened_at),
                    encode_timestamp(team.deleted_at),
                ),
            )
            connection.execute("DELETE FROM team_lists WHERE team_id = ?", (str(team.team_id),))
            connection.executemany(
                "INSERT INTO team_lists(list_id, team_id, name, order_index) VALUES (?, ?, ?, ?)",
                list_rows,
            )
            connection.executemany(
                "INSERT INTO slots(list_id, slot_index) VALUES (?, ?)",
                slot_rows,
            )
            connection.executemany(
                """
                INSERT INTO champion_instances(instance_id, list_id, slot_index, champion_id)
                VALUES (?, ?, ?, ?)
                """,
                champion_rows,
            )
            connection.executemany(
                """
                INSERT INTO trait_selections(instance_id, selection_index, trait_id)
                VALUES (?, ?, ?)
                """,
                trait_rows,
            )

    def load(self, team_id: UUID, *, include_deleted: bool = False) -> Team:
        """Load one complete Team aggregate with a bounded four-query read."""

        team_id_text = str(team_id)
        with self.database.connection() as connection:
            query = "SELECT * FROM teams WHERE team_id = ?"
            parameters: tuple[object, ...] = (team_id_text,)
            if not include_deleted:
                query += " AND deleted_at IS NULL"
            team_row = connection.execute(query, parameters).fetchone()
            if team_row is None:
                raise TeamNotFoundError(team_id_text)

            list_rows = connection.execute(
                "SELECT * FROM team_lists WHERE team_id = ? ORDER BY order_index",
                (team_id_text,),
            ).fetchall()
            slot_rows = connection.execute(
                """
                SELECT l.list_id, s.slot_index, c.instance_id, c.champion_id
                FROM team_lists AS l
                JOIN slots AS s ON s.list_id = l.list_id
                LEFT JOIN champion_instances AS c
                  ON c.list_id = s.list_id AND c.slot_index = s.slot_index
                WHERE l.team_id = ?
                ORDER BY l.order_index, s.slot_index
                """,
                (team_id_text,),
            ).fetchall()
            trait_rows = connection.execute(
                """
                SELECT c.instance_id, t.trait_id
                FROM team_lists AS l
                JOIN champion_instances AS c ON c.list_id = l.list_id
                JOIN trait_selections AS t ON t.instance_id = c.instance_id
                WHERE l.team_id = ?
                ORDER BY c.instance_id, t.selection_index
                """,
                (team_id_text,),
            ).fetchall()

        return _assemble_teams((team_row,), list_rows, slot_rows, trait_rows)[0]

    def load_all(self, *, include_deleted: bool = False) -> tuple[Team, ...]:
        """Load every visible Team aggregate in four SELECTs regardless of Team count."""

        team_filter = "" if include_deleted else "WHERE t.deleted_at IS NULL"
        trait_team_filter = "" if include_deleted else "WHERE team.deleted_at IS NULL"
        with self.database.connection() as connection:
            team_rows = connection.execute(
                f"""
                SELECT t.*
                FROM teams AS t
                {team_filter}
                ORDER BY t.updated_at DESC, t.team_id
                """
            ).fetchall()
            if not team_rows:
                return ()

            list_rows = connection.execute(
                f"""
                SELECT l.*
                FROM team_lists AS l
                JOIN teams AS t ON t.team_id = l.team_id
                {team_filter}
                ORDER BY t.updated_at DESC, t.team_id, l.order_index
                """
            ).fetchall()
            slot_rows = connection.execute(
                f"""
                SELECT l.list_id, s.slot_index, c.instance_id, c.champion_id
                FROM team_lists AS l
                JOIN teams AS t ON t.team_id = l.team_id
                JOIN slots AS s ON s.list_id = l.list_id
                LEFT JOIN champion_instances AS c
                  ON c.list_id = s.list_id AND c.slot_index = s.slot_index
                {team_filter}
                ORDER BY t.updated_at DESC, t.team_id, l.order_index, s.slot_index
                """
            ).fetchall()
            trait_rows = connection.execute(
                f"""
                SELECT c.instance_id, t.trait_id
                FROM team_lists AS l
                JOIN teams AS team ON team.team_id = l.team_id
                JOIN champion_instances AS c ON c.list_id = l.list_id
                JOIN trait_selections AS t ON t.instance_id = c.instance_id
                {trait_team_filter}
                ORDER BY team.updated_at DESC, team.team_id, l.order_index,
                         c.instance_id, t.selection_index
                """
            ).fetchall()

        return _assemble_teams(team_rows, list_rows, slot_rows, trait_rows)

    def list_ids(self, *, include_deleted: bool = False) -> tuple[UUID, ...]:
        query = "SELECT team_id FROM teams"
        if not include_deleted:
            query += " WHERE deleted_at IS NULL"
        query += " ORDER BY updated_at DESC, team_id"
        with self.database.connection() as connection:
            return tuple(UUID(row[0]) for row in connection.execute(query))

    def mark_opened(self, team_id: UUID, *, when: datetime | None = None) -> bool:
        timestamp = when or datetime.now(UTC)
        with self.database.transaction() as connection:
            cursor = connection.execute(
                "UPDATE teams SET last_opened_at = ? WHERE team_id = ?",
                (encode_timestamp(timestamp), str(team_id)),
            )
            return cursor.rowcount == 1

    def soft_delete(self, team_id: UUID, *, when: datetime | None = None) -> bool:
        timestamp = when or datetime.now(UTC)
        encoded = encode_timestamp(timestamp)
        with self.database.transaction() as connection:
            cursor = connection.execute(
                """
                UPDATE teams SET deleted_at = ?, updated_at = ?
                WHERE team_id = ? AND deleted_at IS NULL
                """,
                (encoded, encoded, str(team_id)),
            )
            return cursor.rowcount == 1

    def restore(self, team_id: UUID, *, when: datetime | None = None) -> bool:
        timestamp = when or datetime.now(UTC)
        with self.database.transaction() as connection:
            cursor = connection.execute(
                """
                UPDATE teams SET deleted_at = NULL, updated_at = ?
                WHERE team_id = ? AND deleted_at IS NOT NULL
                """,
                (encode_timestamp(timestamp), str(team_id)),
            )
            return cursor.rowcount == 1

    def delete_permanently(self, team_id: UUID) -> bool:
        with self.database.transaction() as connection:
            cursor = connection.execute("DELETE FROM teams WHERE team_id = ?", (str(team_id),))
            return cursor.rowcount == 1


def _assemble_teams(
    team_rows: Sequence[sqlite3.Row],
    list_rows: Sequence[sqlite3.Row],
    slot_rows: Sequence[sqlite3.Row],
    trait_rows: Sequence[sqlite3.Row],
) -> tuple[Team, ...]:
    """Rebuild Team aggregates from already ordered relational rows."""

    traits_by_instance: dict[str, list[str]] = {}
    for row in trait_rows:
        traits_by_instance.setdefault(row["instance_id"], []).append(row["trait_id"])

    slots_by_list: dict[str, list[Slot]] = {row["list_id"]: [] for row in list_rows}
    for row in slot_rows:
        champion = None
        instance_id = row["instance_id"]
        if instance_id is not None:
            champion = ChampionInstance(
                champion_id=row["champion_id"],
                instance_id=UUID(instance_id),
                trait_selection=TraitSelection(tuple(traits_by_instance.get(instance_id, ()))),
            )
        slots_by_list[row["list_id"]].append(Slot(index=row["slot_index"], champion=champion))

    lists_by_team: dict[str, list[TeamList]] = {row["team_id"]: [] for row in team_rows}
    for row in list_rows:
        lists_by_team[row["team_id"]].append(
            TeamList(
                name=row["name"],
                list_id=UUID(row["list_id"]),
                slots=slots_by_list[row["list_id"]],
            )
        )

    return tuple(
        Team(
            set_id=row["set_id"],
            name=row["name"],
            lists=lists_by_team[row["team_id"]],
            primary_list_id=UUID(row["primary_list_id"]),
            team_id=UUID(row["team_id"]),
            created_at=decode_timestamp(row["created_at"]),
            updated_at=decode_timestamp(row["updated_at"]),
            last_opened_at=decode_timestamp(row["last_opened_at"]),
            deleted_at=decode_timestamp(row["deleted_at"]),
        )
        for row in team_rows
    )
