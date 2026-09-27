# Dependency and Release License Review

Review date: 2026-09-27
Project version: 0.2.2

This document is an engineering release checklist, not legal advice. License obligations must be reviewed again against the exact dependency lockfile and final packaged artifact before public distribution.

## Project license status

- The project itself does not yet declare a public source-code license.
- Private development can continue without selecting one.
- Before a public source release, choose an explicit project license or an explicit proprietary/all-rights-reserved distribution model.
- Do not copy a third-party license onto this repository as if it were the license of this project.

## Direct runtime dependencies

Current reviewed direct runtime dependencies:

- Flet 1.0.1: Apache-2.0.
- Pydantic 2.13.5: MIT.
- platformdirs 4.11.15: MIT.

These licenses are permissive and do not currently block the planned Windows desktop distribution model.

## Development and build tooling

Current reviewed development/build tools include:

- Hatchling 1.32.4: MIT.
- pytest 9.1.1: MIT.
- Ruff 0.16.9: MIT.
- uv: MIT OR Apache-2.0. uv is a development tool and is not intended to be bundled as an application runtime dependency. The project requires uv 0.12.18 or newer within the 0.12 line because that release contains a Windows wheel-install path-traversal security fix; CI uses 0.12.19.

The Flet CLI/Desktop/test packages are part of the default development toolchain. Flet Web is isolated in a deferred optional dependency group. Any of these packages that are bundled or used for a release target must be included in that target-specific license audit.

## Why Flet remains acceptable

Flet was re-evaluated in Block 1 because future browser/mobile support remains desirable.

Reasons to retain it:
- Windows desktop is supported now.
- Flet has official web, Android, and iOS build paths.
- The Flet project uses a permissive Apache-2.0 license.
- It avoids committing the project to Qt LGPL/commercial-license handling solely for a desktop-first UI.
- It gives more future platform options than a desktop-only toolkit while still allowing the core to remain independent from Flet.

Known risk:
- Flet 1.0 is a recent major API line. The project therefore pins the exact Flet version and keeps Flet imports at the UI boundary.

## Public binary release gate

Before any public executable/package is distributed:

- generate or inspect the final `uv.lock` dependency graph;
- inventory all packages actually bundled into the final artifact, including transitive Flet/Flutter/runtime components;
- record required copyright/license notices;
- ship required third-party notices with the release where applicable;
- re-check the license terms of every bundled dependency at the exact shipped version;
- re-check Riot/TFT asset and third-party-product policy separately;
- confirm that the selected project license/distribution model is compatible with all bundled dependencies;
- set final product/company/organization/bundle metadata from an actual independent project identity instead of placeholders or Flet defaults;
- do not assume that reviewing only direct Python dependencies is sufficient.

## Riot/TFT data and assets

Riot/TFT data and assets are not covered by the open-source software licenses listed above. Their permitted use is governed separately by Riot policies and asset rules.

Before public release:
- re-check the current Riot policy;
- confirm which Riot assets/data are shipped;
- confirm the required Riot legal notice and product registration status;
- audit any CommunityDragon-derived shipped material separately from development-only metadata use.

## Future platform note

Browser and mobile builds can bundle a different dependency/runtime set than the Windows desktop build. Each target therefore requires its own final artifact license inventory before public distribution.

Block 2 selected the Python 3.13 standard-library `sqlite3` module and added no ORM dependency. This keeps the current Windows runtime dependency graph smaller. A future browser/mobile target must still re-evaluate persistence compatibility for that target instead of assuming the desktop SQLite design transfers unchanged.


## Block 2 dependency impact

Block 2 adds no third-party runtime dependency. Persistence uses Python's standard-library `sqlite3` module and SQLite supplied with the approved CPython runtime. No ORM or migration framework was added.
