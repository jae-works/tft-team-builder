from __future__ import annotations

import pytest

from tft_builder.search import normalize_search_text


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Kha'Zix", "khazix"),
        ("KHA ZIX", "khazix"),
        ("kha-zix", "khazix"),
        ("kha.zix", "khazix"),
        ("  Kha   Zix  ", "khazix"),
        ("Kai'Sa", "kaisa"),
        ("Cho'Gath", "chogath"),
        ("A-B_C.D", "abcd"),
        ("123 45", "12345"),
        ("", ""),
        ("---", ""),
        ("Cafe", "cafe"),
        ("CAF\u00c9", "cafe"),
        ("Stra\u00dfe", "strasse"),
        ("Alpha \u03b2eta", "alpha\u03b2eta"),
        ("\u6771\u4eac 2026", "\u6771\u4eac2026"),
    ],
)
def test_normalize_search_text(raw: str, expected: str) -> None:
    assert normalize_search_text(raw) == expected


def test_search_normalization_is_idempotent() -> None:
    value = "Kha'Zix - The Voidreaver"
    once = normalize_search_text(value)
    assert normalize_search_text(once) == once


def test_search_normalization_removes_combining_marks() -> None:
    assert normalize_search_text("Cafe\u0301") == "cafe"


def test_search_normalization_preserves_non_latin_alphanumeric_characters() -> None:
    assert normalize_search_text("\u0391\u03b8\u03ae\u03bd\u03b1!") == (
        "\u03b1\u03b8\u03b7\u03bd\u03b1"
    )
