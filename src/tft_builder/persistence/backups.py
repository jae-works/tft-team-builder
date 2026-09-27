"""SQLite online backups, validation, retention and restore."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from .database import Database
from .migrations import CURRENT_SCHEMA_VERSION


class BackupError(RuntimeError):
    pass


class BackupManager:
    def __init__(self, database: Database, backup_dir: Path):
        self.database = database
        self.backup_dir = Path(backup_dir).expanduser().resolve()

    def create_backup(self, *, prefix: str = "backup", now: datetime | None = None) -> Path:
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        moment = (now or datetime.now(UTC)).astimezone(UTC)
        stamp = moment.strftime("%Y%m%dT%H%M%S%fZ")
        destination = self._unique_path(prefix, stamp)
        with self.database.connection() as source:
            with closing(sqlite3.connect(destination, autocommit=True)) as target:
                source.backup(target)
        self._verify(destination)
        return destination

    def list_backups(self) -> tuple[Path, ...]:
        if not self.backup_dir.exists():
            return ()
        return tuple(
            sorted(
                self.backup_dir.glob("*.db"),
                key=lambda path: (path.stat().st_mtime_ns, path.name),
                reverse=True,
            )
        )

    def prune(self, *, keep: int = 10) -> tuple[Path, ...]:
        if keep < 0:
            raise ValueError("keep must be zero or greater")
        backups = self.list_backups()
        removed = backups[keep:]
        for path in removed:
            path.unlink()
        return removed

    def restore(self, backup_path: Path) -> None:
        backup = Path(backup_path).expanduser().resolve()
        self._verify(backup)
        self._verify_supported_schema(backup)
        self.database.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.database.path.with_suffix(self.database.path.suffix + ".restore.tmp")
        temporary.unlink(missing_ok=True)
        try:
            with closing(sqlite3.connect(backup, autocommit=True)) as source:
                with closing(sqlite3.connect(temporary, autocommit=True)) as target:
                    source.backup(target)
            self._verify(temporary)
            for suffix in ("-wal", "-shm"):
                Path(f"{self.database.path}{suffix}").unlink(missing_ok=True)
            temporary.replace(self.database.path)
        finally:
            temporary.unlink(missing_ok=True)
        self.database.initialize()

    def _unique_path(self, prefix: str, stamp: str) -> Path:
        candidate = self.backup_dir / f"{prefix}-{stamp}.db"
        counter = 1
        while candidate.exists():
            candidate = self.backup_dir / f"{prefix}-{stamp}-{counter}.db"
            counter += 1
        return candidate

    @staticmethod
    def _verify_supported_schema(path: Path) -> None:
        uri = f"{path.as_uri()}?mode=ro"
        with closing(sqlite3.connect(uri, uri=True, autocommit=True)) as connection:
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        if not 1 <= version <= CURRENT_SCHEMA_VERSION:
            raise BackupError(f"unsupported backup schema version {version}: {path}")

    @staticmethod
    def _verify(path: Path) -> None:
        if not path.is_file():
            raise BackupError(f"backup does not exist: {path}")
        try:
            uri = f"{path.as_uri()}?mode=ro"
            with closing(sqlite3.connect(uri, uri=True, autocommit=True)) as connection:
                row = connection.execute("PRAGMA integrity_check").fetchone()
        except sqlite3.DatabaseError as error:
            raise BackupError(f"backup is not a valid SQLite database: {path}") from error
        if row is None or row[0] != "ok":
            raise BackupError(f"backup failed integrity check: {path}")
