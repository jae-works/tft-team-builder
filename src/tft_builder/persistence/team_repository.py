"""Straightforward persistence for complete Team aggregates."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from ..models import ChampionInstance, Slot, Team, TeamList, TraitSelection
from .database import Database
from .time_codec import decode_timestamp, encode_timestamp


class TeamNotFoundError(LookupError):
    pass


class TeamRepository:
    def __init__(self, database: Database):
        self.database = database

    def save(self, team: Team) -> None:
        """Persist one complete Team in a single transaction."""

        team.validate_invariants()
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
            for order_index, team_list in enumerate(team.lists):
                connection.execute(
                    "INSERT INTO team_lists(list_id, team_id, name, order_index) "
                    "VALUES (?, ?, ?, ?)",
                    (str(team_list.list_id), str(team.team_id), team_list.name, order_index),
                )
                for slot in team_list.slots:
                    connection.execute(
                        "INSERT INTO slots(list_id, slot_index) VALUES (?, ?)",
                        (str(team_list.list_id), slot.index),
                    )
                    champion = slot.champion
                    if champion is None:
                        continue
                    connection.execute(
                        """
                        INSERT INTO champion_instances(
                            instance_id, list_id, slot_index, champion_id
                        ) VALUES (?, ?, ?, ?)
                        """,
                        (
                            str(champion.instance_id),
                            str(team_list.list_id),
                            slot.index,
                            champion.champion_id,
                        ),
                    )
                    connection.executemany(
                        """
                        INSERT INTO trait_selections(instance_id, selection_index, trait_id)
                        VALUES (?, ?, ?)
                        """,
                        [
                            (str(champion.instance_id), index, trait_id)
                            for index, trait_id in enumerate(champion.trait_selection.trait_ids)
                        ],
                    )

    def load(self, team_id: UUID, *, include_deleted: bool = False) -> Team:
        with self.database.connection() as connection:
            query = "SELECT * FROM teams WHERE team_id = ?"
            parameters: tuple[object, ...] = (str(team_id),)
            if not include_deleted:
                query += " AND deleted_at IS NULL"
            team_row = connection.execute(query, parameters).fetchone()
            if team_row is None:
                raise TeamNotFoundError(str(team_id))

            list_rows = connection.execute(
                "SELECT * FROM team_lists WHERE team_id = ? ORDER BY order_index",
                (str(team_id),),
            ).fetchall()
            lists: list[TeamList] = []
            for list_row in list_rows:
                slot_rows = connection.execute(
                    """
                    SELECT s.slot_index, c.instance_id, c.champion_id
                    FROM slots AS s
                    LEFT JOIN champion_instances AS c
                      ON c.list_id = s.list_id AND c.slot_index = s.slot_index
                    WHERE s.list_id = ?
                    ORDER BY s.slot_index
                    """,
                    (list_row["list_id"],),
                ).fetchall()
                slots: list[Slot] = []
                for slot_row in slot_rows:
                    champion = None
                    instance_id = slot_row["instance_id"]
                    if instance_id is not None:
                        trait_rows = connection.execute(
                            """
                            SELECT trait_id FROM trait_selections
                            WHERE instance_id = ? ORDER BY selection_index
                            """,
                            (instance_id,),
                        ).fetchall()
                        champion = ChampionInstance(
                            champion_id=slot_row["champion_id"],
                            instance_id=UUID(instance_id),
                            trait_selection=TraitSelection(
                                tuple(row["trait_id"] for row in trait_rows)
                            ),
                        )
                    slots.append(Slot(index=slot_row["slot_index"], champion=champion))
                lists.append(
                    TeamList(name=list_row["name"], list_id=UUID(list_row["list_id"]), slots=slots)
                )

        return Team(
            set_id=team_row["set_id"],
            name=team_row["name"],
            lists=lists,
            primary_list_id=UUID(team_row["primary_list_id"]),
            team_id=UUID(team_row["team_id"]),
            created_at=decode_timestamp(team_row["created_at"]),
            updated_at=decode_timestamp(team_row["updated_at"]),
            last_opened_at=decode_timestamp(team_row["last_opened_at"]),
            deleted_at=decode_timestamp(team_row["deleted_at"]),
        )

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
