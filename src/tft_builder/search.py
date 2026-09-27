"""Search text normalization shared by future search features."""

from __future__ import annotations

import unicodedata


def normalize_search_text(value: str) -> str:
    """Return a compact comparison key for localized user-facing search text.

    Search should ignore case, whitespace, punctuation and common accent differences without
    destroying letters from future non-Latin locales. Unicode case folding and compatibility
    decomposition normalize values such as ``Kha'Zix``, ``KHA ZIX`` and ``kha-zix`` to the
    same key while still preserving meaningful Greek, Cyrillic, CJK or other alphanumeric
    characters. Locale-specific aliases can later add transliterations where desired.
    """

    folded = unicodedata.normalize("NFKD", value.casefold())
    return "".join(
        character
        for character in folded
        if not unicodedata.combining(character) and character.isalnum()
    )
