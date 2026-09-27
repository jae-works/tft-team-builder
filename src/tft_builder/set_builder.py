"""Deterministic offline Set package builder used by Block 1 fixtures and sample data.

Block 7 will add upstream Riot/CommunityDragon acquisition. This module already defines the
stable normalization boundary: source adapters produce a local spec, and this builder emits
the runtime package consumed by the application.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

from pydantic import ValidationError

from .constants import SOURCE_MANIFEST_SCHEMA_VERSION
from .set_loader import load_set_directory
from .set_schema import LocalSetSpec


def _read_bytes(path: Path) -> bytes:
    with path.open("rb") as handle:
        return handle.read()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json_bytes(value: object) -> bytes:
    text = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    return text.encode("utf-8")


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_json_bytes(value))


def _load_source_spec(spec_dir: Path) -> tuple[LocalSetSpec, bytes]:
    spec_path = spec_dir / "set_spec.json"
    raw = _read_bytes(spec_path)
    payload = json.loads(raw.decode("utf-8"))
    try:
        return LocalSetSpec.model_validate(payload), raw
    except ValidationError as error:
        raise ValueError(f"invalid source spec: {error}") from error


def _resolve_source_asset(spec_dir: Path, relative: str) -> Path:
    """Resolve one project-owned source asset without allowing symlink escapes."""

    candidate = spec_dir.joinpath(*relative.split("/"))
    if not candidate.exists():
        raise FileNotFoundError(f"source asset does not exist: {candidate}")

    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(spec_dir)
    except ValueError as error:
        raise ValueError(f"source asset resolves outside source spec directory: {relative}") from error

    if not resolved.is_file():
        raise FileNotFoundError(f"source asset is not a file: {resolved}")
    return resolved


def _populate_staging_directory(spec_dir: Path, staging_dir: Path) -> None:
    """Write a complete candidate package into an isolated staging directory."""

    spec, raw_spec = _load_source_spec(spec_dir)

    _write_json(staging_dir / "manifest.json", spec.manifest.model_dump(mode="json"))
    _write_json(
        staging_dir / spec.manifest.champions_file,
        [value.model_dump(mode="json") for value in spec.champions],
    )
    _write_json(
        staging_dir / spec.manifest.traits_file,
        [value.model_dump(mode="json") for value in spec.traits],
    )
    _write_json(
        staging_dir / spec.manifest.dynamic_traits_file,
        [value.model_dump(mode="json") for value in spec.dynamic_traits],
    )
    _write_json(
        staging_dir / spec.manifest.team_planner_file,
        spec.team_planner.model_dump(mode="json"),
    )

    for locale, catalog in sorted(spec.locales.items()):
        _write_json(staging_dir / spec.manifest.locales_dir / f"{locale}.json", catalog)

    asset_hashes: dict[str, str] = {}
    for target, source in sorted(spec.assets.items()):
        source_path = _resolve_source_asset(spec_dir, source)
        target_path = staging_dir.joinpath(*target.split("/"))
        target_path.parent.mkdir(parents=True, exist_ok=True)
        data = _read_bytes(source_path)
        target_path.write_bytes(data)
        asset_hashes[target] = _sha256_bytes(data)

    generated_paths = {
        "manifest.json",
        spec.manifest.champions_file,
        spec.manifest.traits_file,
        spec.manifest.dynamic_traits_file,
        spec.manifest.team_planner_file,
        *(f"{spec.manifest.locales_dir}/{locale}.json" for locale in spec.manifest.supported_locales),
    }
    generated_file_hashes = {
        relative: _sha256_bytes(_read_bytes(staging_dir.joinpath(*relative.split("/"))))
        for relative in sorted(generated_paths)
    }

    source_manifest = {
        "schema_version": SOURCE_MANIFEST_SCHEMA_VERSION,
        "source_type": "local_spec",
        "source_sha256": _sha256_bytes(raw_spec),
        "generated_file_sha256": generated_file_hashes,
        "asset_sha256": asset_hashes,
    }
    _write_json(staging_dir / spec.manifest.source_manifest_file, source_manifest)

    # The exact runtime loader validates the staging directory before it can replace an
    # existing output. Build-time and runtime validity therefore cannot silently diverge.
    load_set_directory(staging_dir)


def _promote_staging_directory(staging_dir: Path, output_dir: Path) -> None:
    """Replace output with a validated staging directory while preserving rollback safety."""

    backup_dir: Path | None = None
    if output_dir.exists():
        backup_dir = output_dir.with_name(f".{output_dir.name}.previous-{uuid4().hex}")
        output_dir.rename(backup_dir)

    try:
        staging_dir.rename(output_dir)
    except Exception:
        # If promotion fails after the previous output was moved aside, restore it before
        # propagating the original error. This keeps overwrite failures non-destructive.
        if backup_dir is not None and backup_dir.exists() and not output_dir.exists():
            backup_dir.rename(output_dir)
        raise
    else:
        if backup_dir is not None:
            shutil.rmtree(backup_dir, ignore_errors=True)


def build_set_from_local_spec(
    spec_dir: Path,
    output_dir: Path,
    *,
    overwrite: bool = False,
) -> Path:
    """Build and validate a runtime Set package from an offline local source spec.

    Generation is transactional at directory level: all files are written and validated in a
    sibling staging directory. Only a fully valid package is promoted to the requested output.
    Existing output is left untouched if generation fails before promotion.
    """

    spec_dir = Path(spec_dir).resolve()
    output_dir = Path(output_dir).resolve()
    if not spec_dir.is_dir():
        raise FileNotFoundError(f"source spec directory does not exist: {spec_dir}")

    # Overlapping input/output trees are dangerous with overwrite=True because removing or
    # replacing output could also destroy all or part of the source specification.
    if output_dir == spec_dir or output_dir.is_relative_to(spec_dir) or spec_dir.is_relative_to(output_dir):
        raise ValueError("source spec and output directories must not overlap")

    if output_dir.exists():
        if not output_dir.is_dir():
            raise FileExistsError(f"output path exists and is not a directory: {output_dir}")
        if not overwrite:
            raise FileExistsError(f"output directory already exists: {output_dir}")

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}.build-", dir=output_dir.parent)
    )
    try:
        _populate_staging_directory(spec_dir, staging_dir)
        _promote_staging_directory(staging_dir, output_dir)
    except Exception:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise

    return output_dir


def directory_content_hash(root: Path) -> str:
    """Hash relative file names and contents for deterministic-generation tests."""

    root = Path(root).resolve()
    digest = hashlib.sha256()
    for path in sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda item: item.as_posix(),
    ):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        data = _read_bytes(path)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()
