"""Search text normalization shared by future search features."""

from __future__ import annotations

import unicodedata


def normalize_search_text(value: str) -> str:
    """Return a compact comparison key for user-facing search text.

    The product requirements intentionally make champion and Trait searches forgiving.
    We case-fold first, use Unicode compatibility decomposition, remove combining marks,
    and finally keep only ASCII letters and digits. The result makes values such as
    ``Kha'Zix``, ``KHA ZIX`` and ``kha-zix`` compare as the same search key.

    This is deliberately not a general transliteration system. Stable IDs remain separate
    from localized display names, and future locale-specific indexing can add aliases when
    a language needs richer transliteration than the standard library can provide.
    """

    folded = unicodedata.normalize("NFKD", value.casefold())
    characters: list[str] = []
    for character in folded:
        if unicodedata.combining(character):
            continue
        if character.isascii() and character.isalnum():
            characters.append(character)
    return "".join(characters)
