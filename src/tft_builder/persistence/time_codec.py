"""Stable UTC timestamp encoding for SQLite TEXT columns."""

from __future__ import annotations

from datetime import UTC, datetime


def encode_timestamp(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.utcoffset() is None:
        raise ValueError("timestamp must be timezone-aware")
    return value.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def decode_timestamp(value: str | None) -> datetime | None:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.utcoffset() is None:
        raise ValueError("stored timestamp must be timezone-aware")
    return parsed.astimezone(UTC)
