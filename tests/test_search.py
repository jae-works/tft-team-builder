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
    ],
)
def test_normalize_search_text(raw: str, expected: str) -> None:
    assert normalize_search_text(raw) == expected


def test_search_normalization_is_idempotent() -> None:
    value = "Kha'Zix - The Voidreaver"
    once = normalize_search_text(value)
    assert normalize_search_text(once) == once


def test_search_normalization_removes_combining_marks() -> None:
    value = "Cafe\u0301"
    assert normalize_search_text(value) == "cafe"


def test_search_normalization_drops_non_ascii_characters_without_transliteration() -> None:
    assert normalize_search_text("Alpha \u03b2eta") == "alphaeta"
