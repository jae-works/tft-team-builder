"""SQLite connection, transaction and schema-migration management."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

from .migrations import CURRENT_SCHEMA_VERSION, MIGRATIONS
from .time_codec import encode_timestamp


class DatabaseVersionError(RuntimeError):
    """Raised when a database was created by a newer unsupported schema."""


class Database:
    """Own database configuration and explicit transactions.

    Connections use SQLite autocommit mode and application-controlled ``BEGIN IMMEDIATE``
    transactions. This avoids the legacy sqlite3 transaction mode while making write
    boundaries explicit and deterministic.
    """

    def __init__(self, path: Path, *, backups_dir: Path | None = None, timeout: float = 5.0):
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
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA trusted_schema = OFF")
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = FULL")
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

        current = self.schema_version()
        if current > CURRENT_SCHEMA_VERSION:
            raise DatabaseVersionError(
                f"database schema {current} is newer than supported schema "
                f"{CURRENT_SCHEMA_VERSION}"
            )
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
        return CURRENT_SCHEMA_VERSION

    def integrity_check(self) -> bool:
        with self.connection() as connection:
            row = connection.execute("PRAGMA integrity_check").fetchone()
            foreign_key_issue = connection.execute("PRAGMA foreign_key_check").fetchone()
            return row is not None and row[0] == "ok" and foreign_key_issue is None
