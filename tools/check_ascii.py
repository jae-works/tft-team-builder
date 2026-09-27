"""Reject unintended non-ASCII characters in project-authored technical text files."""

from __future__ import annotations

import argparse
from pathlib import Path

TEXT_SUFFIXES = {".json", ".md", ".py", ".toml", ".txt", ".yaml", ".yml"}
SKIP_DIRECTORY_NAMES = {
    ".cache",
    ".flet",
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "build",
    "dist",
    "htmlcov",
}


def is_allowed_unicode_path(relative: Path) -> bool:
    """Allow localized catalogs to contain the characters required by their language."""

    parts = relative.parts
    return "locales" in parts


def _is_link_like(path: Path) -> bool:
    return path.is_symlink() or path.is_junction()


def _iter_technical_text_files(root: Path):
    for directory, directory_names, file_names in root.walk(
        top_down=True,
        follow_symlinks=False,
    ):
        directory_names[:] = [
            name
            for name in directory_names
            if name not in SKIP_DIRECTORY_NAMES and not _is_link_like(directory / name)
        ]
        for name in file_names:
            path = directory / name
            if _is_link_like(path) or path.suffix.casefold() not in TEXT_SUFFIXES:
                continue
            yield path


def find_non_ascii_files(root: Path) -> list[tuple[Path, int, str]]:
    root = root.resolve()
    failures: list[tuple[Path, int, str]] = []
    for path in sorted(_iter_technical_text_files(root)):
        relative = path.relative_to(root)
        if is_allowed_unicode_path(relative):
            continue

        text = path.read_text(encoding="utf-8")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if not line.isascii():
                offending = "".join(
                    sorted({character for character in line if not character.isascii()})
                )
                failures.append((relative, line_number, offending))
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)

    failures = find_non_ascii_files(args.root)
    if not failures:
        print("ASCII policy check passed.")
        return 0

    for path, line_number, offending in failures:
        codepoints = ", ".join(f"U+{ord(character):04X}" for character in offending)
        print(f"{path}:{line_number}: non-ASCII characters: {codepoints}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
