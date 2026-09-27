from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


def load_sync_tool(project_root: Path):
    path = project_root / "tools" / "sync_project_docs.py"
    spec = importlib.util.spec_from_file_location("sync_project_docs_tool", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_small_project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    root.mkdir()
    (root / "A.md").write_text("A\n", encoding="ascii")
    (root / "B.md").write_text("B\n", encoding="ascii")
    (root / "PROJECT_MANIFEST.json").write_text(
        json.dumps({"mirrored_project_documents": ["A.md", "B.md"]}) + "\n",
        encoding="ascii",
    )
    return root


def test_sync_tool_copies_all_manifest_documents(project_root: Path, tmp_path: Path) -> None:
    module = load_sync_tool(project_root)
    root = make_small_project(tmp_path)

    assert module.synchronize_project_docs(root) == []
    assert (root / "project_docs/A.md").read_text(encoding="ascii") == "A\n"
    assert (root / "project_docs/B.md").read_text(encoding="ascii") == "B\n"
    assert module.synchronize_project_docs(root, check_only=True) == []


def test_check_only_reports_missing_and_stale_mirrors(project_root: Path, tmp_path: Path) -> None:
    module = load_sync_tool(project_root)
    root = make_small_project(tmp_path)
    mirror = root / "project_docs"
    mirror.mkdir()
    (mirror / "A.md").write_text("stale\n", encoding="ascii")

    assert module.synchronize_project_docs(root, check_only=True) == ["A.md", "B.md"]


def test_sync_repairs_existing_stale_mirror(project_root: Path, tmp_path: Path) -> None:
    module = load_sync_tool(project_root)
    root = make_small_project(tmp_path)
    mirror = root / "project_docs"
    mirror.mkdir()
    (mirror / "A.md").write_text("stale\n", encoding="ascii")

    module.synchronize_project_docs(root)
    assert (mirror / "A.md").read_text(encoding="ascii") == "A\n"


def test_sync_rejects_missing_source_document(project_root: Path, tmp_path: Path) -> None:
    module = load_sync_tool(project_root)
    root = make_small_project(tmp_path)
    (root / "B.md").unlink()

    with pytest.raises(FileNotFoundError, match=r"B\.md"):
        module.synchronize_project_docs(root)


@pytest.mark.parametrize(
    "value",
    [None, [], "A.md", ["A.md", 1], ["A.md", "A.md"]],
)
def test_manifest_mirror_list_validation(project_root: Path, tmp_path: Path, value) -> None:
    module = load_sync_tool(project_root)
    root = make_small_project(tmp_path)
    (root / "PROJECT_MANIFEST.json").write_text(
        json.dumps({"mirrored_project_documents": value}) + "\n",
        encoding="ascii",
    )

    with pytest.raises(ValueError):
        module.synchronize_project_docs(root)


def test_cli_check_returns_nonzero_for_mismatch(project_root: Path, tmp_path: Path, capsys) -> None:
    module = load_sync_tool(project_root)
    root = make_small_project(tmp_path)

    assert module.main([str(root), "--check"]) == 1
    assert "project_docs mismatch: A.md" in capsys.readouterr().out


def test_cli_sync_then_check_succeeds(project_root: Path, tmp_path: Path, capsys) -> None:
    module = load_sync_tool(project_root)
    root = make_small_project(tmp_path)

    assert module.main([str(root)]) == 0
    assert "Project documents synchronized." in capsys.readouterr().out
    assert module.main([str(root), "--check"]) == 0
    assert "Project document mirror check passed." in capsys.readouterr().out
