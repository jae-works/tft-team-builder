"""Standard-library helpers for deterministic SHA-256 integrity checks."""

from __future__ import annotations

import hashlib
from pathlib import Path

from .filesystem import is_link_like, scan_regular_files

_READ_CHUNK_SIZE = 1024 * 1024


def sha256_bytes(data: bytes) -> str:
    """Return a lowercase SHA-256 digest for an in-memory byte string."""

    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    """Return a lowercase SHA-256 digest without loading the whole file into memory."""

    with Path(path).open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def directory_content_hash(root: Path) -> str:
    """Hash relative file names and contents in deterministic path order.

    Symbolic links and Windows junctions are rejected deliberately. Following either form
    would make the result depend on filesystem state outside the directory being hashed.
    """

    supplied_root = Path(root)
    if is_link_like(supplied_root):
        raise ValueError("directory hash does not allow a link-like root")
    resolved_root = supplied_root.resolve(strict=True)
    files, links = scan_regular_files(resolved_root)
    if links:
        raise ValueError(f"directory hash does not allow link-like entries: {links[0]}")

    ordered_files = sorted(
        files,
        key=lambda candidate: candidate.relative_to(resolved_root).as_posix(),
    )

    digest = hashlib.sha256()
    for path in ordered_files:
        relative = path.relative_to(resolved_root).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)

        size = path.stat().st_size
        digest.update(size.to_bytes(8, "big"))
        with path.open("rb") as handle:
            while chunk := handle.read(_READ_CHUNK_SIZE):
                digest.update(chunk)

    return digest.hexdigest()
