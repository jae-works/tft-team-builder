from __future__ import annotations

from pathlib import Path

import pytest

import tft_builder.filesystem as filesystem
from tft_builder.filesystem import is_link_like, scan_regular_files


def test_is_link_like_returns_false_for_regular_file(tmp_path: Path) -> None:
    path = tmp_path / "file.txt"
    path.write_text("payload", encoding="ascii")
    assert not is_link_like(path)


def test_is_link_like_detects_symbolic_link_semantics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "candidate"
    original = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda self: self == path or original(self))
    assert is_link_like(path)


def test_is_link_like_detects_windows_junction_semantics(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "candidate"
    original = Path.is_junction
    monkeypatch.setattr(Path, "is_junction", lambda self: self == path or original(self))
    assert is_link_like(path)


def test_scan_regular_files_returns_nested_files_in_filesystem_order_independent_shape(
    tmp_path: Path,
) -> None:
    root = tmp_path / "tree"
    (root / "nested").mkdir(parents=True)
    first = root / "first.txt"
    second = root / "nested" / "second.txt"
    first.write_text("first", encoding="ascii")
    second.write_text("second", encoding="ascii")

    files, links = scan_regular_files(root)
    assert set(files) == {first, second}
    assert links == ()


def test_scan_regular_files_prunes_link_like_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "tree"
    linked_directory = root / "linked"
    linked_directory.mkdir(parents=True)
    hidden_file = linked_directory / "hidden.txt"
    hidden_file.write_text("hidden", encoding="ascii")
    visible_file = root / "visible.txt"
    visible_file.write_text("visible", encoding="ascii")

    original = filesystem.is_link_like
    monkeypatch.setattr(
        filesystem,
        "is_link_like",
        lambda path: path == linked_directory or original(path),
    )

    files, links = scan_regular_files(root)
    assert files == (visible_file,)
    assert links == (linked_directory,)


def test_scan_regular_files_reports_link_like_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    linked_file = root / "linked.txt"
    linked_file.write_text("payload", encoding="ascii")
    original = filesystem.is_link_like
    monkeypatch.setattr(
        filesystem,
        "is_link_like",
        lambda path: path == linked_file or original(path),
    )

    files, links = scan_regular_files(root)
    assert files == ()
    assert links == (linked_file,)


def test_scan_regular_files_propagates_walk_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "tree"
    root.mkdir()

    def controlled_walk(self: Path, *, top_down: bool, on_error, follow_symlinks: bool):
        assert self == root
        assert top_down is True
        assert follow_symlinks is False
        on_error(OSError("simulated walk failure"))
        yield from ()

    monkeypatch.setattr(Path, "walk", controlled_walk)
    with pytest.raises(OSError, match="simulated walk failure"):
        scan_regular_files(root)


def test_scan_regular_files_ignores_non_regular_non_link_entries(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "tree"
    root.mkdir()
    ghost = root / "ghost"

    def controlled_walk(self: Path, *, top_down: bool, on_error, follow_symlinks: bool):
        assert self == root
        assert top_down is True
        assert on_error is not None
        assert follow_symlinks is False
        yield root, [], ["ghost"]

    original_is_file = Path.is_file
    monkeypatch.setattr(Path, "walk", controlled_walk)
    monkeypatch.setattr(
        Path,
        "is_file",
        lambda self, *, follow_symlinks=True: (
            False if self == ghost else original_is_file(self, follow_symlinks=follow_symlinks)
        ),
    )

    files, links = scan_regular_files(root)
    assert files == ()
    assert links == ()
