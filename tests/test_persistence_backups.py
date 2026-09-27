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
            if statement == "PRAGMA integrity_check":
                return FakeCursor()
            assert statement == "PRAGMA foreign_key_check"

            class EmptyCursor:
                def fetchone(self):
                    return None

            return EmptyCursor()

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


def test_backup_prefix_rejects_path_characters(tmp_path: Path) -> None:
    _, _, manager = setup_store(tmp_path)
    with pytest.raises(ValueError, match="backup prefix"):
        manager.create_backup(prefix="../escape")
    assert not (tmp_path / "escape").exists()


def test_prune_ignores_unmanaged_database_files(tmp_path: Path) -> None:
    _, _, manager = setup_store(tmp_path)
    unmanaged = manager.backup_dir / "personal.db"
    manager.backup_dir.mkdir(parents=True, exist_ok=True)
    unmanaged.write_bytes(b"do not delete")
    manager.create_backup(now=datetime(2026, 9, 27, tzinfo=UTC))
    removed = manager.prune(keep=0)
    assert len(removed) == 1
    assert unmanaged.read_bytes() == b"do not delete"


def test_create_backup_rejects_uninitialized_database(tmp_path: Path) -> None:
    database = Database(tmp_path / "builder.db")
    manager = BackupManager(database, tmp_path / "backups")
    with pytest.raises(BackupError, match="unsupported backup schema version 0"):
        manager.create_backup()
    assert not manager.backup_dir.exists()


def test_create_backup_removes_partial_file_when_verification_fails(
    tmp_path: Path, monkeypatch
) -> None:
    _, _, manager = setup_store(tmp_path)

    def reject(_path: Path) -> None:
        raise BackupError("verification failed")

    monkeypatch.setattr(manager, "_verify", reject)
    with pytest.raises(BackupError, match="verification failed"):
        manager.create_backup(now=datetime(2026, 9, 27, tzinfo=UTC))
    assert manager.list_backups() == ()


def test_verify_rejects_foreign_key_damage(tmp_path: Path) -> None:
    import sqlite3
    from contextlib import closing

    path = tmp_path / "broken.db"
    with closing(sqlite3.connect(path, autocommit=True)) as connection:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("CREATE TABLE parent(id INTEGER PRIMARY KEY)")
        connection.execute(
            "CREATE TABLE child(parent_id INTEGER REFERENCES parent(id))"
        )
        connection.execute("INSERT INTO child(parent_id) VALUES (99)")
    with pytest.raises(BackupError, match="foreign key check"):
        BackupManager._verify(path)


def test_create_backup_rejects_application_integrity_damage(tmp_path: Path) -> None:
    database, _, manager = setup_store(tmp_path)
    with database.connection() as connection:
        connection.execute(
            "INSERT INTO teams(team_id,set_id,name,primary_list_id,created_at,updated_at) "
            "VALUES('team','set','name','missing',"
            "'2026-01-01T00:00:00.000000Z','2026-01-01T00:00:00.000000Z')"
        )
    with pytest.raises(BackupError, match="database failed integrity check"):
        manager.create_backup()


def test_restore_rejects_application_integrity_damage(tmp_path: Path) -> None:
    import sqlite3
    from contextlib import closing

    _, _, manager = setup_store(tmp_path)
    damaged = tmp_path / "damaged.db"
    source = Database(damaged)
    source.initialize()
    with closing(sqlite3.connect(damaged, autocommit=True)) as connection:
        connection.execute(
            "INSERT INTO teams(team_id,set_id,name,primary_list_id,created_at,updated_at) "
            "VALUES('team','set','name','missing',"
            "'2026-01-01T00:00:00.000000Z','2026-01-01T00:00:00.000000Z')"
        )
    with pytest.raises(BackupError, match="application integrity check"):
        manager.restore(damaged)


def test_create_backup_wraps_corrupt_source_database_error(tmp_path: Path) -> None:
    path = tmp_path / "builder.db"
    path.write_text("not sqlite", encoding="ascii")
    manager = BackupManager(Database(path), tmp_path / "backups")
    with pytest.raises(BackupError, match="database is not a valid SQLite database"):
        manager.create_backup()
