"""Ordered SQLite schema migrations.

Migrations are intentionally small Python data structures rather than an ORM migration
framework. This keeps the local-only persistence layer transparent and easy to audit.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Migration:
    version: int
    statements: tuple[str, ...]


MIGRATIONS = (
    Migration(
        version=1,
        statements=(
            """
            CREATE TABLE schema_migrations (
                version INTEGER PRIMARY KEY,
                applied_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE teams (
                team_id TEXT PRIMARY KEY,
                set_id TEXT NOT NULL,
                name TEXT NOT NULL,
                primary_list_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE team_lists (
                list_id TEXT PRIMARY KEY,
                team_id TEXT NOT NULL,
                name TEXT NOT NULL,
                order_index INTEGER NOT NULL CHECK (order_index >= 0),
                UNIQUE (team_id, order_index),
                FOREIGN KEY (team_id) REFERENCES teams(team_id) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE slots (
                list_id TEXT NOT NULL,
                slot_index INTEGER NOT NULL CHECK (slot_index >= 0),
                PRIMARY KEY (list_id, slot_index),
                FOREIGN KEY (list_id) REFERENCES team_lists(list_id) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE champion_instances (
                instance_id TEXT PRIMARY KEY,
                list_id TEXT NOT NULL,
                slot_index INTEGER NOT NULL,
                champion_id TEXT NOT NULL,
                UNIQUE (list_id, slot_index),
                FOREIGN KEY (list_id, slot_index)
                    REFERENCES slots(list_id, slot_index) ON DELETE CASCADE
            )
            """,
            """
            CREATE TABLE trait_selections (
                instance_id TEXT NOT NULL,
                selection_index INTEGER NOT NULL CHECK (selection_index >= 0),
                trait_id TEXT NOT NULL,
                PRIMARY KEY (instance_id, selection_index),
                UNIQUE (instance_id, trait_id),
                FOREIGN KEY (instance_id)
                    REFERENCES champion_instances(instance_id) ON DELETE CASCADE
            )
            """,
            "CREATE INDEX team_lists_team_id_idx ON team_lists(team_id)",
            "CREATE INDEX champion_instances_list_idx ON champion_instances(list_id, slot_index)",
        ),
    ),
    Migration(
        version=2,
        statements=(
            "ALTER TABLE teams ADD COLUMN last_opened_at TEXT",
            "ALTER TABLE teams ADD COLUMN deleted_at TEXT",
            "CREATE INDEX teams_deleted_at_idx ON teams(deleted_at)",
            "CREATE INDEX teams_updated_at_idx ON teams(updated_at DESC)",
        ),
    ),
)

CURRENT_SCHEMA_VERSION = MIGRATIONS[-1].version
