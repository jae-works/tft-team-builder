from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from tft_builder.persistence.database import Database, DatabaseVersionError
from tft_builder.persistence.migrations import CURRENT_SCHEMA_VERSION, MIGRATIONS


def test_initialize_creates_database_and_current_schema(tmp_path: Path) -> None:
    database = Database(tmp_path / "nested" / "builder.db")
    assert database.initialize() == CURRENT_SCHEMA_VERSION
    assert database.path.is_file()
    assert database.schema_version() == CURRENT_SCHEMA_VERSION
    assert database.integrity_check()


def test_initialize_is_idempotent(tmp_path: Path) -> None:
    database = Database(tmp_path / "builder.db")
    first = database.initialize()
    second = database.initialize()
    assert first == second == CURRENT_SCHEMA_VERSION


def test_connection_configures_required_pragmas(tmp_path: Path) -> None:
    database = Database(tmp_path / "builder.db")
    database.initialize()
    with database.connection() as connection:
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 5000
        assert connection.execute("PRAGMA trusted_schema").fetchone()[0] == 0
        assert connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert connection.execute("PRAGMA synchronous").fetchone()[0] == 2


def test_connection_uses_row_objects(tmp_path: Path) -> None:
    database = Database(tmp_path / "builder.db")
    database.initialize()
    with database.connection() as connection:
        row = connection.execute("SELECT 7 AS value").fetchone()
        assert row["value"] == 7


def test_successful_transaction_commits(tmp_path: Path) -> None:
    database = Database(tmp_path / "builder.db")
    database.initialize()
    with database.transaction() as connection:
        connection.execute(
            "INSERT INTO teams(team_id,set_id,name,primary_list_id,created_at,updated_at) "
            "VALUES('t','s','n','l','2026-01-01T00:00:00.000000Z','2026-01-01T00:00:00.000000Z')"
        )
    with database.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM teams").fetchone()[0] == 1


def test_failed_transaction_rolls_back(tmp_path: Path) -> None:
    database = Database(tmp_path / "builder.db")
    database.initialize()
    with pytest.raises(RuntimeError, match="stop"):
        with database.transaction() as connection:
            connection.execute(
                "INSERT INTO teams(team_id,set_id,name,primary_list_id,created_at,updated_at) "
                "VALUES('t','s','n','l',"
                "'2026-01-01T00:00:00.000000Z','2026-01-01T00:00:00.000000Z')"
            )
            raise RuntimeError("stop")
    with database.connection() as connection:
        assert connection.execute("SELECT COUNT(*) FROM teams").fetchone()[0] == 0


def test_schema_version_is_zero_before_database_exists(tmp_path: Path) -> None:
    database = Database(tmp_path / "builder.db")
    assert database.schema_version() == 0
    assert not database.path.exists()


def test_newer_schema_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "builder.db"
    with closing(sqlite3.connect(path, autocommit=True)) as connection:
        connection.execute(f"PRAGMA user_version = {CURRENT_SCHEMA_VERSION + 1}")
    database = Database(path)
    with pytest.raises(DatabaseVersionError, match="newer than supported"):
        database.initialize()


def test_migration_history_contains_every_version(tmp_path: Path) -> None:
    database = Database(tmp_path / "builder.db")
    database.initialize()
    with database.connection() as connection:
        versions = tuple(
            row[0]
            for row in connection.execute(
                "SELECT version FROM schema_migrations ORDER BY version"
            )
        )
    assert versions == tuple(migration.version for migration in MIGRATIONS)


def _create_v1_database(path: Path) -> None:
    with closing(sqlite3.connect(path, autocommit=True)) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("BEGIN IMMEDIATE")
        for statement in MIGRATIONS[0].statements:
            connection.execute(statement)
        connection.execute(
            "INSERT INTO schema_migrations(version, applied_at) "
            "VALUES (1, '2026-01-01T00:00:00.000000Z')"
        )
        connection.execute("PRAGMA user_version = 1")
        connection.execute("COMMIT")


def test_existing_v1_database_migrates_and_creates_pre_migration_backup(tmp_path: Path) -> None:
    path = tmp_path / "builder.db"
    backup_dir = tmp_path / "backups"
    _create_v1_database(path)
    database = Database(path, backups_dir=backup_dir)
    assert database.initialize() == CURRENT_SCHEMA_VERSION
    backups = tuple(backup_dir.glob("pre-migration-*.db"))
    assert len(backups) == 1
    with closing(sqlite3.connect(backups[0], autocommit=True)) as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 1
    with database.connection() as connection:
        columns = {row[1] for row in connection.execute("PRAGMA table_info(teams)")}
    assert {"last_opened_at", "deleted_at"} <= columns


def test_integrity_check_includes_foreign_keys(tmp_path: Path) -> None:
    database = Database(tmp_path / "builder.db")
    database.initialize()
    with database.connection() as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            "INSERT INTO team_lists(list_id, team_id, name, order_index) "
            "VALUES('orphan','missing','Orphan',0)"
        )
        connection.execute("PRAGMA foreign_keys = ON")
    assert not database.integrity_check()
