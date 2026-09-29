"""Generic source-lock verification for validated local Set packages."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .json_utils import loads_json
from .set_loader import LoadedSet
from .set_schema import SourceRecord

_SOURCE_FIELDS = ("url", "revision", "locale", "sha256", "byte_length")


def verify_source_lock_payload(loaded: LoadedSet, payload: object) -> list[str]:
    """Compare one decoded acquisition lock with packaged provenance metadata."""

    if not isinstance(payload, dict):
        return ["source lock root must be an object"]

    issues: list[str] = []
    if payload.get("set_id") != loaded.manifest.set_id:
        issues.append("source lock Set ID differs")
    if payload.get("revision") != loaded.manifest.revision:
        issues.append("source lock revision differs")

    raw_sources = payload.get("sources")
    if not isinstance(raw_sources, list):
        issues.append("source lock sources must be a list")
        return issues

    locked: dict[str, SourceRecord] = {}
    for index, raw_record in enumerate(raw_sources):
        try:
            record = SourceRecord.model_validate(raw_record)
        except ValidationError:
            issues.append(f"source lock record {index} is invalid")
            continue
        if record.id in locked:
            issues.append(f"source lock has duplicate source ID: {record.id}")
            continue
        locked[record.id] = record

    packaged = {record.id: record for record in loaded.source_manifest.sources}
    missing = sorted(set(packaged) - set(locked))
    extra = sorted(set(locked) - set(packaged))
    if missing:
        issues.append("source lock is missing provenance IDs: " + ", ".join(missing))
    if extra:
        issues.append("source lock has unexpected provenance IDs: " + ", ".join(extra))

    for source_id in sorted(set(locked) & set(packaged)):
        lock_record = locked[source_id]
        package_record = packaged[source_id]
        for field in _SOURCE_FIELDS:
            if getattr(lock_record, field) != getattr(package_record, field):
                issues.append(f"source lock {field} differs for {source_id}")

    return issues


def verify_source_lock_file(loaded: LoadedSet, source_lock: Path) -> list[str]:
    """Read and verify one source lock without allowing malformed JSON to escape."""

    try:
        payload: Any = loads_json(source_lock.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return ["source lock could not be read as valid JSON"]
    return verify_source_lock_payload(loaded, payload)
