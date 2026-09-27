"""JSON helpers shared by Set building and validation.

The standard JSON decoder silently keeps the last value when an object contains duplicate
keys. Set metadata is configuration, so duplicate keys are rejected instead of being accepted
with surprising last-value-wins behavior.
"""

from __future__ import annotations

import json
from typing import Any


class DuplicateJsonKeyError(ValueError):
    """Raised when a JSON object repeats the same key."""


def _unique_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKeyError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def loads_json(text: str) -> Any:
    """Decode JSON while rejecting duplicate object keys at every nesting level."""

    return json.loads(text, object_pairs_hook=_unique_object_pairs)


def canonical_json_bytes(value: object) -> bytes:
    """Encode deterministic human-readable JSON used by generated Set packages."""

    text = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    return text.encode("utf-8")
