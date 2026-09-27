from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest

from tft_builder.persistence.time_codec import decode_timestamp, encode_timestamp


def test_none_round_trips() -> None:
    assert encode_timestamp(None) is None
    assert decode_timestamp(None) is None


def test_utc_timestamp_has_stable_z_format() -> None:
    value = datetime(2026, 9, 27, 12, 34, 56, 123456, tzinfo=UTC)
    assert encode_timestamp(value) == "2026-09-27T12:34:56.123456Z"


def test_non_utc_timestamp_is_normalized_to_utc() -> None:
    value = datetime(2026, 9, 27, 14, 34, 56, tzinfo=timezone(timedelta(hours=2)))
    assert encode_timestamp(value) == "2026-09-27T12:34:56.000000Z"


def test_decode_returns_utc_datetime() -> None:
    assert decode_timestamp("2026-09-27T12:34:56.000000Z") == datetime(
        2026, 9, 27, 12, 34, 56, tzinfo=UTC
    )


def test_encode_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        encode_timestamp(datetime(2026, 1, 1))


def test_decode_rejects_naive_stored_timestamp() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        decode_timestamp("2026-01-01T00:00:00")
