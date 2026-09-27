# Block 2 Report - Persistence, migrations, autosave primitives and backups

Version: 0.2.0
Status: implemented and verified in the implementation environment; final Windows verification required before Block 3.

## Scope delivered

- Standard-library SQLite persistence using Python 3.13 `sqlite3`.
- Explicit modern transaction handling with `autocommit=True` plus application-controlled `BEGIN IMMEDIATE`, `COMMIT`, and `ROLLBACK` boundaries.
- SQLite configured with foreign keys, WAL journal mode, `synchronous=FULL`, a 5-second busy timeout, and `trusted_schema=OFF`.
- Schema versioning through `PRAGMA user_version` plus a migration history table.
- Two explicit migrations, including a tested v1-to-v2 upgrade path.
- Automatic pre-migration backup for existing databases.
- Complete Team aggregate persistence for Teams, Lists, ordered Slots, ChampionInstances, and ordered TraitSelections.
- Exact persistence of empty slots, duplicate Champion definitions with distinct instance IDs, primary List identity, timestamps, and List ordering.
- `last_opened_at` and recoverable `deleted_at` Team metadata.
- Team soft delete, restore, permanent delete, last-opened update, and visible/deleted listing semantics.
- SQLite online backups, integrity validation, retention pruning, and atomic restore through a temporary database.
- Autosave primitives with immediate structural saves and queued immutable snapshots for future GUI debounce integration.
- Application startup now initializes/migrates `builder.db` in the central writable data path.
- Developer `database-smoke` command for round-trip persistence and backup verification.

## Persistence design decision

Direct `sqlite3` was selected instead of SQLAlchemy for Block 2. The application has one local embedded database, a small explicit schema, and aggregate-oriented writes. Direct SQLite currently produces less code, fewer runtime dependencies, easier auditability, and a smaller future packaging surface. The persistence package is isolated so this choice can still be revisited if later requirements justify an ORM.

## Database schema

Current schema version: 2.

Tables:
- `schema_migrations`
- `teams`
- `team_lists`
- `slots`
- `champion_instances`
- `trait_selections`

The child graph uses foreign keys and cascading deletes. `primary_list_id` remains an application-validated Team invariant instead of creating a circular database foreign-key dependency.

## Transaction and durability policy

Every complete Team save is one write transaction. Child rows are replaced only inside that transaction, so a failed write does not leave a partially saved Team.

SQLite runs in WAL mode with `synchronous=FULL`. This favors durability over maximum write throughput, which is appropriate for small local user-authored build data.

Backups use SQLite's online backup API. Restore first validates the source, restores into a temporary SQLite database, validates that temporary database, then atomically replaces the active database file.

## Autosave boundary

Block 2 deliberately does not start background threads or UI timers. `AutosaveService` provides:
- immediate `save_now()` for structural edits,
- snapshot-based `queue()` for future debounced text edits,
- deterministic `flush()` and `discard()` operations.

The actual GUI debounce timer belongs to the later UI block. This keeps persistence deterministic and fully testable now.

## Verification

Implementation-environment result:
- 407 pytest tests passed.
- 0 skipped tests.
- 100.00 percent statement coverage.
- 100.00 percent branch coverage.
- All persistence modules reached 100 percent coverage.
- Existing Block 1 production modules also reached 100 percent coverage in this run.
- ASCII policy passed.
- Python compileall passed.
- Project document mirroring passed after synchronization.
- Bundled sample Set validation remained green.
- Database migration, rollback, integrity, backup, restore, soft-delete, and restart round-trip behavior are covered by tests.

Exact Ruff 0.16.9 and Flet desktop runtime checks still require the user's Windows environment before Block 3 begins.
