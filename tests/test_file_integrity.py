from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import tft_builder.file_integrity as file_integrity
from tft_builder.file_integrity import directory_content_hash, sha256_bytes, sha256_file


def test_sha256_bytes_matches_hashlib_reference() -> None:
    data = b"TFT Team Builder\n"
    assert sha256_bytes(data) == hashlib.sha256(data).hexdigest()


def test_sha256_file_matches_hashlib_reference(tmp_path: Path) -> None:
    path = tmp_path / "payload.bin"
    data = (b"0123456789" * 100_000) + b"end"
    path.write_bytes(data)
    assert sha256_file(path) == hashlib.sha256(data).hexdigest()


def test_directory_content_hash_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    for root in (first, second):
        (root / "nested").mkdir(parents=True)
        (root / "b.txt").write_bytes(b"B")
        (root / "nested" / "a.txt").write_bytes(b"A")
    assert directory_content_hash(first) == directory_content_hash(second)


def test_directory_content_hash_changes_when_content_changes(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    path = root / "file.txt"
    path.write_text("one", encoding="ascii")
    first = directory_content_hash(root)
    path.write_text("two", encoding="ascii")
    assert directory_content_hash(root) != first


def test_directory_content_hash_changes_when_relative_name_changes(tmp_path: Path) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    path = root / "first.txt"
    path.write_text("same", encoding="ascii")
    first = directory_content_hash(root)
    path.rename(root / "second.txt")
    assert directory_content_hash(root) != first


def test_directory_content_hash_rejects_link_like_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    linked_file = root / "linked.txt"
    linked_file.write_text("payload", encoding="ascii")
    monkeypatch.setattr(
        file_integrity,
        "scan_regular_files",
        lambda path: ((), (linked_file,)),
    )

    with pytest.raises(ValueError, match="link-like entries"):
        directory_content_hash(root)


def test_directory_content_hash_rejects_link_like_directory_without_descending(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "tree"
    linked_directory = root / "linked-dir"
    linked_directory.mkdir(parents=True)
    (linked_directory / "payload.txt").write_text("payload", encoding="ascii")
    monkeypatch.setattr(
        file_integrity,
        "scan_regular_files",
        lambda path: ((), (linked_directory,)),
    )

    with pytest.raises(ValueError, match="link-like entries"):
        directory_content_hash(root)


def test_directory_content_hash_requires_existing_root(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        directory_content_hash(tmp_path / "missing")


def test_directory_content_hash_rejects_link_like_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    monkeypatch.setattr(file_integrity, "is_link_like", lambda path: path == root)

    with pytest.raises(ValueError, match="link-like root"):
        directory_content_hash(root)
