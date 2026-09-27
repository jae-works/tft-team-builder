from __future__ import annotations

import pytest

from tft_builder.json_utils import DuplicateJsonKeyError, canonical_json_bytes, loads_json


def test_loads_json_accepts_normal_nested_objects() -> None:
    assert loads_json('{"a": {"b": 1}, "c": [1, 2]}') == {"a": {"b": 1}, "c": [1, 2]}


def test_loads_json_rejects_duplicate_top_level_key() -> None:
    with pytest.raises(DuplicateJsonKeyError, match="duplicate JSON object key"):
        loads_json('{"a": 1, "a": 2}')


def test_loads_json_rejects_duplicate_nested_key() -> None:
    with pytest.raises(DuplicateJsonKeyError, match="duplicate JSON object key"):
        loads_json('{"outer": {"a": 1, "a": 2}}')


def test_canonical_json_bytes_is_sorted_indented_and_newline_terminated() -> None:
    assert canonical_json_bytes({"b": 2, "a": 1}) == b'{\n  "a": 1,\n  "b": 2\n}\n'


def test_canonical_json_bytes_preserves_legitimate_unicode_data() -> None:
    encoded = canonical_json_bytes({"name": "Cafe\u0301"})
    assert "Cafe\u0301" in encoded.decode("utf-8")
