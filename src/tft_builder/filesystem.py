"""Cross-platform filesystem safety helpers."""

from __future__ import annotations

from pathlib import Path
from typing import NoReturn


def is_link_like(path: Path) -> bool:
    """Return whether ``path`` can redirect traversal outside its apparent tree.

    On Windows, directory junctions are reparse points but are not symbolic links.
    Treat both forms alike anywhere reproducibility or containment matters.
    """

    candidate = Path(path)
    return candidate.is_symlink() or candidate.is_junction()


def _raise_walk_error(error: OSError) -> NoReturn:
    raise error


def scan_regular_files(root: Path) -> tuple[tuple[Path, ...], tuple[Path, ...]]:
    """Return regular files and link-like entries without traversing link-like directories.

    ``Path.walk()`` is used instead of recursive globbing so directory names can be pruned
    before descent. This is important on Windows because junctions are not symbolic links.
    """

    root = Path(root)
    files: list[Path] = []
    links: list[Path] = []

    for directory, directory_names, file_names in root.walk(
        top_down=True,
        on_error=_raise_walk_error,
        follow_symlinks=False,
    ):
        safe_directory_names: list[str] = []
        for name in directory_names:
            candidate = directory / name
            if is_link_like(candidate):
                links.append(candidate)
            else:
                safe_directory_names.append(name)
        directory_names[:] = safe_directory_names

        for name in file_names:
            candidate = directory / name
            if is_link_like(candidate):
                links.append(candidate)
            elif candidate.is_file(follow_symlinks=False):
                files.append(candidate)

    return tuple(files), tuple(links)
