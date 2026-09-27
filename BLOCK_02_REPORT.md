# Block 2 Report - Persistence, migrations, autosave primitives and backups

Version: 0.2.2
Status: implemented and hardened; version 0.2.2 is the final correction candidate pending one clean Windows recheck before Block 3.

## Scope delivered

- Standard-library SQLite persistence using Python 3.13 `sqlite3`.
- Explicit modern transaction handling with `autocommit=True` plus application-controlled `BEGIN IMMEDIATE`, `COMMIT`, and `ROLLBACK` boundaries.
- SQLite configured with foreign keys, WAL journal mode, `synchronous=FULL`, a configurable busy timeout, and `trusted_schema=OFF`.
- Schema versioning through `PRAGMA user_version` plus a migration history table.
- Two explicit migrations, including a tested v1-to-v2 upgrade path.
- Automatic pre-migration backup for existing databases.
- Complete Team aggregate persistence for Teams, Lists, ordered Slots, ChampionInstances, and ordered TraitSelections.
- Exact persistence of empty slots, duplicate Champion definitions with distinct instance IDs, primary List identity, timestamps, and List ordering.
- `last_opened_at` and recoverable `deleted_at` Team metadata.
- Team soft delete, restore, permanent delete, last-opened update, and visible/deleted listing semantics.
- SQLite online backups, integrity validation, application-structure validation, namespaced retention pruning, and atomic restore through a temporary database.
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
- 438 pytest tests passed in the version 0.2.2 implementation audit.
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

## v0.2.1 hardening after Windows verification

The user's v0.2.0 Windows run confirmed 407 tests at 100 percent coverage, Set validation, database smoke, and Flet startup. It also found five Ruff lint findings and two formatter drift files. v0.2.1 fixes those reported style issues and additionally hardens persistence behavior:

- Backup filenames are namespaced with `tft-builder-`; retention ignores unrelated `.db` files.
- Backup prefixes are validated as one ASCII-safe filename token.
- Backup creation rejects uninitialized or application-corrupt source databases.
- Restore validates SQLite integrity, foreign keys, supported schema version, and Team/List/slot structural integrity before replacing the active database.
- SQLite busy timeout now follows the configured `Database.timeout` value.
- Database integrity checks detect invalid primary List references and non-contiguous List/slot order.
- Team save batches child-row writes and Team load uses a bounded number of aggregate queries instead of per-Champion Trait queries.
- A 200-slot Team round-trip is included in the test suite.
- The enforced statement and branch coverage gate is now 100 percent.


## v0.2.2 final correction pass

The user's Windows v0.2.1 run verified 425 tests at 100 percent coverage, Ruff lint, ASCII policy, documentation mirrors, compileall, Set validation/inspection, database smoke and Flet startup. Ruff 0.16.9 reported three formatting-only files. Version 0.2.2 applies those exact formatter changes and fixes additional issues found in the complete pre-Block-3 audit:

- Removed the unused stale `APP_VERSION` constant (`0.2.0`) so source code no longer carries an independent release-version copy.
- Database integrity checks now verify the required schema tables/columns and exact migration-history sequence for schema v1/v2.
- `Database.initialize()` now rejects non-SQLite or structurally invalid existing databases instead of accepting `PRAGMA user_version` as sufficient proof of health.
- Explicit backup timestamps must be timezone-aware, avoiding host-timezone-dependent backup naming.
- Removed the unimplementable `CUSTOM_SET_RULE` Trait counting placeholder from Set schema v1. Only the concrete declarative `UNIQUE_CHAMPION` and `UNIQUE_INSTANCE` modes remain until real Set data justifies an explicit additional rule format.
- Added targeted regression tests for corrupted schema structure, incomplete migration history, v1 compatibility, post-migration validation and naive backup timestamps.
- Added `BLOCK_03_PLAN.md` so slot/copy/move/List/Trait/undo semantics are concrete before Block 3 code is written.

The implementation-environment suite now has 438 passing tests, zero skips, and 100.00 percent statement and branch coverage. The final Windows recheck remains required because this sandbox does not provide the project's required uv/Ruff/Flet toolchain versions.
