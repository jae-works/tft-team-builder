from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from tft_builder.models import Team
from tft_builder.persistence import BackupManager, Database, TeamRepository
from tft_builder.persistence.backups import BackupError


def setup_store(tmp_path: Path) -> tuple[Database, TeamRepository, BackupManager]:
    database = Database(tmp_path / "builder.db")
    database.initialize()
    repository = TeamRepository(database)
    manager = BackupManager(database, tmp_path / "backups")
    return database, repository, manager


def test_backup_captures_committed_database_state(tmp_path: Path) -> None:
    database, repository, manager = setup_store(tmp_path)
    team = Team.create(set_id="set", name="Before backup")
    repository.save(team)
    backup = manager.create_backup(now=datetime(2026, 9, 27, tzinfo=UTC))
    assert backup.is_file()
    backup_database = Database(backup)
    assert backup_database.schema_version() == database.schema_version()
    assert TeamRepository(backup_database).load(team.team_id) == team


def test_same_timestamp_generates_unique_backup_names(tmp_path: Path) -> None:
    _, _, manager = setup_store(tmp_path)
    now = datetime(2026, 9, 27, tzinfo=UTC)
    first = manager.create_backup(now=now)
    second = manager.create_backup(now=now)
    assert first != second
    assert first.is_file() and second.is_file()


def test_list_backups_is_empty_before_directory_exists(tmp_path: Path) -> None:
    database = Database(tmp_path / "builder.db")
    manager = BackupManager(database, tmp_path / "missing")
    assert manager.list_backups() == ()


def test_list_backups_returns_newest_name_first(tmp_path: Path) -> None:
    _, _, manager = setup_store(tmp_path)
    first = manager.create_backup(now=datetime(2026, 9, 27, tzinfo=UTC))
    second = manager.create_backup(now=datetime(2026, 9, 28, tzinfo=UTC))
    assert manager.list_backups() == (second, first)


def test_prune_keeps_requested_number(tmp_path: Path) -> None:
    _, _, manager = setup_store(tmp_path)
    base = datetime(2026, 9, 27, tzinfo=UTC)
    created = [manager.create_backup(now=base + timedelta(days=index)) for index in range(4)]
    removed = manager.prune(keep=2)
    assert len(removed) == 2
    assert len(manager.list_backups()) == 2
    assert set(removed) == set(created[:2])


def test_prune_zero_removes_every_backup(tmp_path: Path) -> None:
    _, _, manager = setup_store(tmp_path)
    manager.create_backup()
    assert len(manager.prune(keep=0)) == 1
    assert manager.list_backups() == ()


def test_prune_rejects_negative_keep(tmp_path: Path) -> None:
    _, _, manager = setup_store(tmp_path)
    with pytest.raises(ValueError, match="zero or greater"):
        manager.prune(keep=-1)


def test_restore_replaces_current_database_with_backup_state(tmp_path: Path) -> None:
    _, repository, manager = setup_store(tmp_path)
    original = Team.create(set_id="set", name="Original")
    repository.save(original)
    backup = manager.create_backup()
    replacement = Team.create(set_id="set", name="Replacement")
    repository.save(replacement)
    manager.restore(backup)
    restored_repository = TeamRepository(manager.database)
    assert restored_repository.load(original.team_id) == original
    with pytest.raises(LookupError):
        restored_repository.load(replacement.team_id)


def test_restore_rejects_missing_file(tmp_path: Path) -> None:
    _, _, manager = setup_store(tmp_path)
    with pytest.raises(BackupError, match="does not exist"):
        manager.restore(tmp_path / "missing.db")


def test_restore_rejects_non_sqlite_file(tmp_path: Path) -> None:
    _, _, manager = setup_store(tmp_path)
    bad = tmp_path / "bad.db"
    bad.write_text("not sqlite", encoding="ascii")
    with pytest.raises(BackupError, match="not a valid SQLite database"):
        manager.restore(bad)


def test_verify_rejects_failed_integrity_check(tmp_path: Path, monkeypatch) -> None:
    import tft_builder.persistence.backups as backups_module

    path = tmp_path / "fake.db"
    path.write_bytes(b"placeholder")

    class FakeCursor:
        def fetchone(self):
            return ("corrupt",)

    class FakeConnection:
        def execute(self, statement: str):
            assert statement == "PRAGMA integrity_check"
            return FakeCursor()

        def close(self) -> None:
            pass

    monkeypatch.setattr(backups_module.sqlite3, "connect", lambda *args, **kwargs: FakeConnection())
    with pytest.raises(BackupError, match="failed integrity check"):
        BackupManager._verify(path)


def test_restore_rejects_sqlite_file_with_unsupported_schema(tmp_path: Path) -> None:
    import sqlite3
    from contextlib import closing

    _, _, manager = setup_store(tmp_path)
    unsupported = tmp_path / "unsupported.db"
    with closing(sqlite3.connect(unsupported, autocommit=True)) as connection:
        connection.execute("PRAGMA user_version = 999")
    with pytest.raises(BackupError, match="unsupported backup schema version"):
        manager.restore(unsupported)
