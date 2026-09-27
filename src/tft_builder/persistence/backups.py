"""SQLite online backups, validation, retention and restore."""

from __future__ import annotations

import re
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

from .database import Database
from .migrations import CURRENT_SCHEMA_VERSION

_MANAGED_FILE_PREFIX = "tft-builder-"
_SAFE_PREFIX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class BackupError(RuntimeError):
    pass


class BackupManager:
    def __init__(self, database: Database, backup_dir: Path):
        self.database = database
        self.backup_dir = Path(backup_dir).expanduser().resolve()

    def create_backup(self, *, prefix: str = "backup", now: datetime | None = None) -> Path:
        self._validate_prefix(prefix)
        try:
            version = self.database.schema_version()
        except sqlite3.DatabaseError as error:
            raise BackupError(
                f"database is not a valid SQLite database: {self.database.path}"
            ) from error
        self._ensure_supported_version(version, self.database.path)
        if not self.database.integrity_check():
            raise BackupError(f"database failed integrity check: {self.database.path}")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        moment = (now or datetime.now(UTC)).astimezone(UTC)
        stamp = moment.strftime("%Y%m%dT%H%M%S%fZ")
        destination = self._unique_path(prefix, stamp)
        try:
            with (
                self.database.connection() as source,
                closing(sqlite3.connect(destination, autocommit=True)) as target,
            ):
                source.backup(target)
            self._verify(destination)
            self._verify_supported_schema(destination)
        except BaseException:
            destination.unlink(missing_ok=True)
            raise
        return destination

    def list_backups(self) -> tuple[Path, ...]:
        if not self.backup_dir.exists():
            return ()
        return tuple(
            sorted(
                self.backup_dir.glob(f"{_MANAGED_FILE_PREFIX}*.db"),
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
            with (
                closing(sqlite3.connect(backup, autocommit=True)) as source,
                closing(sqlite3.connect(temporary, autocommit=True)) as target,
            ):
                source.backup(target)
            self._verify(temporary)
            self._verify_supported_schema(temporary)
            if not Database(temporary).integrity_check():
                raise BackupError(f"backup failed application integrity check: {backup}")
            for suffix in ("-wal", "-shm"):
                Path(f"{self.database.path}{suffix}").unlink(missing_ok=True)
            temporary.replace(self.database.path)
        finally:
            temporary.unlink(missing_ok=True)
        self.database.initialize()

    def _unique_path(self, prefix: str, stamp: str) -> Path:
        candidate = self.backup_dir / f"{_MANAGED_FILE_PREFIX}{prefix}-{stamp}.db"
        counter = 1
        while candidate.exists():
            candidate = self.backup_dir / f"{_MANAGED_FILE_PREFIX}{prefix}-{stamp}-{counter}.db"
            counter += 1
        return candidate

    @staticmethod
    def _validate_prefix(prefix: str) -> None:
        if not _SAFE_PREFIX.fullmatch(prefix):
            raise ValueError(
                "backup prefix must contain only ASCII letters, digits, dot, dash or underscore"
            )

    @staticmethod
    def _ensure_supported_version(version: int, path: Path) -> None:
        if not 1 <= version <= CURRENT_SCHEMA_VERSION:
            raise BackupError(f"unsupported backup schema version {version}: {path}")

    @classmethod
    def _verify_supported_schema(cls, path: Path) -> None:
        uri = f"{path.as_uri()}?mode=ro"
        with closing(sqlite3.connect(uri, uri=True, autocommit=True)) as connection:
            version = int(connection.execute("PRAGMA user_version").fetchone()[0])
        cls._ensure_supported_version(version, path)

    @staticmethod
    def _verify(path: Path) -> None:
        if not path.is_file():
            raise BackupError(f"backup does not exist: {path}")
        try:
            uri = f"{path.as_uri()}?mode=ro"
            with closing(sqlite3.connect(uri, uri=True, autocommit=True)) as connection:
                row = connection.execute("PRAGMA integrity_check").fetchone()
                foreign_key_issue = connection.execute("PRAGMA foreign_key_check").fetchone()
        except sqlite3.DatabaseError as error:
            raise BackupError(f"backup is not a valid SQLite database: {path}") from error
        if row is None or row[0] != "ok":
            raise BackupError(f"backup failed integrity check: {path}")
        if foreign_key_issue is not None:
            raise BackupError(f"backup failed foreign key check: {path}")
