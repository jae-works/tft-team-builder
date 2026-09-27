"""SQLite connection, transaction and schema-migration management."""

from __future__ import annotations

import math
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from .migrations import CURRENT_SCHEMA_VERSION, MIGRATIONS
from .time_codec import encode_timestamp


class DatabaseVersionError(RuntimeError):
    """Raised when a database was created by a newer unsupported schema."""


class DatabaseIntegrityError(RuntimeError):
    """Raised when the application database is structurally invalid or corrupt."""


_REQUIRED_SCHEMA_COLUMNS = {
    "schema_migrations": {"version", "applied_at"},
    "teams": {
        "team_id",
        "set_id",
        "name",
        "primary_list_id",
        "created_at",
        "updated_at",
    },
    "team_lists": {"list_id", "team_id", "name", "order_index"},
    "slots": {"list_id", "slot_index"},
    "champion_instances": {"instance_id", "list_id", "slot_index", "champion_id"},
    "trait_selections": {"instance_id", "selection_index", "trait_id"},
}
_V2_TEAM_COLUMNS = {"last_opened_at", "deleted_at"}


class Database:
    """Own database configuration and explicit transactions.

    Connections use SQLite autocommit mode and application-controlled ``BEGIN IMMEDIATE``
    transactions. This avoids the legacy sqlite3 transaction mode while making write
    boundaries explicit and deterministic.
    """

    def __init__(self, path: Path, *, backups_dir: Path | None = None, timeout: float = 5.0):
        if not math.isfinite(timeout) or timeout < 0:
            raise ValueError("timeout must be a finite value greater than or equal to zero")
        self.path = Path(path).expanduser().resolve()
        self.backups_dir = Path(backups_dir).expanduser().resolve() if backups_dir else None
        self.timeout = timeout

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(
            self.path,
            timeout=self.timeout,
            autocommit=True,
        )
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA foreign_keys = ON")
            connection.execute(f"PRAGMA busy_timeout = {round(self.timeout * 1000)}")
            connection.execute("PRAGMA trusted_schema = OFF")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = FULL")
        except BaseException:
            connection.close()
            raise
        return connection

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            yield connection
        finally:
            connection.close()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        with self.connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                yield connection
            except BaseException:
                connection.execute("ROLLBACK")
                raise
            else:
                connection.execute("COMMIT")

    def schema_version(self) -> int:
        if not self.path.exists():
            return 0
        with self.connection() as connection:
            return int(connection.execute("PRAGMA user_version").fetchone()[0])

    def initialize(self) -> int:
        """Create or migrate the database and return the resulting schema version."""

        try:
            current = self.schema_version()
        except sqlite3.DatabaseError as error:
            raise DatabaseIntegrityError(
                f"database is not a valid SQLite database: {self.path}"
            ) from error

        if current > CURRENT_SCHEMA_VERSION:
            raise DatabaseVersionError(
                f"database schema {current} is newer than supported schema {CURRENT_SCHEMA_VERSION}"
            )
        if current > 0 and not self.integrity_check():
            raise DatabaseIntegrityError(f"database failed integrity check: {self.path}")
        if current == CURRENT_SCHEMA_VERSION:
            return current

        if current > 0 and self.backups_dir is not None:
            from .backups import BackupManager

            BackupManager(self, self.backups_dir).create_backup(prefix="pre-migration")

        with self.transaction() as connection:
            for migration in MIGRATIONS:
                if migration.version <= current:
                    continue
                for statement in migration.statements:
                    connection.execute(statement)
                applied_at = encode_timestamp(datetime.now(UTC))
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (migration.version, applied_at),
                )
                connection.execute(f"PRAGMA user_version = {migration.version}")

        if not self.integrity_check():
            raise DatabaseIntegrityError(
                f"database failed integrity check after migration: {self.path}"
            )
        return CURRENT_SCHEMA_VERSION

    @staticmethod
    def _schema_structure_is_valid(connection: sqlite3.Connection, version: int) -> bool:
        """Check the concrete schema expected for an initialized database version."""

        if not 1 <= version <= CURRENT_SCHEMA_VERSION:
            return False

        for table, required_columns in _REQUIRED_SCHEMA_COLUMNS.items():
            columns = {
                row["name"] for row in connection.execute(f"PRAGMA table_info({table})").fetchall()
            }
            if not required_columns <= columns:
                return False

        team_columns = {
            row["name"] for row in connection.execute("PRAGMA table_info(teams)").fetchall()
        }
        if version >= 2 and not team_columns >= _V2_TEAM_COLUMNS:
            return False

        migration_versions = tuple(
            row[0]
            for row in connection.execute(
                "SELECT version FROM schema_migrations ORDER BY version"
            ).fetchall()
        )
        return migration_versions == tuple(range(1, version + 1))

    def integrity_check(self) -> bool:
        if not self.path.exists():
            return False
        try:
            with self.connection() as connection:
                row = connection.execute("PRAGMA integrity_check").fetchone()
                foreign_key_issue = connection.execute("PRAGMA foreign_key_check").fetchone()
                version = int(connection.execute("PRAGMA user_version").fetchone()[0])
                schema_structure_valid = self._schema_structure_is_valid(connection, version)
                primary_list_issue = connection.execute(
                    """
                    SELECT 1
                    FROM teams AS t
                    LEFT JOIN team_lists AS l
                      ON l.team_id = t.team_id AND l.list_id = t.primary_list_id
                    WHERE l.list_id IS NULL
                    LIMIT 1
                    """
                ).fetchone()
                list_order_issue = connection.execute(
                    """
                    SELECT 1
                    FROM (
                        SELECT team_id, COUNT(*) AS item_count,
                               MIN(order_index) AS min_index, MAX(order_index) AS max_index
                        FROM team_lists
                        GROUP BY team_id
                    )
                    WHERE min_index != 0 OR max_index != item_count - 1
                    LIMIT 1
                    """
                ).fetchone()
                slot_order_issue = connection.execute(
                    """
                    SELECT 1
                    FROM (
                        SELECT list_id, COUNT(*) AS item_count,
                               MIN(slot_index) AS min_index, MAX(slot_index) AS max_index
                        FROM slots
                        GROUP BY list_id
                    )
                    WHERE min_index != 0 OR max_index != item_count - 1
                    LIMIT 1
                    """
                ).fetchone()
        except sqlite3.DatabaseError:
            return False
        return (
            row is not None
            and row[0] == "ok"
            and foreign_key_issue is None
            and schema_structure_valid
            and primary_list_issue is None
            and list_order_issue is None
            and slot_order_issue is None
        )
