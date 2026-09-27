from __future__ import annotations

import importlib.util
from pathlib import Path


def load_ascii_tool(project_root: Path):
    path = project_root / "tools/check_ascii.py"
    spec = importlib.util.spec_from_file_location("check_ascii", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_repository_passes_ascii_policy(project_root: Path) -> None:
    module = load_ascii_tool(project_root)
    assert module.find_non_ascii_files(project_root) == []


def test_ascii_policy_detects_non_ascii_in_python_file(project_root: Path, tmp_path: Path) -> None:
    module = load_ascii_tool(project_root)
    (tmp_path / "bad.py").write_text("message = 'bad \u2192 arrow'\n", encoding="utf-8")
    failures = module.find_non_ascii_files(tmp_path)
    assert len(failures) == 1
    assert failures[0][0] == Path("bad.py")
    assert failures[0][1] == 1


def test_ascii_policy_allows_unicode_in_locales_directory(project_root: Path, tmp_path: Path) -> None:
    module = load_ascii_tool(project_root)
    locale = tmp_path / "sets/example/locales/de.json"
    locale.parent.mkdir(parents=True)
    locale.write_text('{"name": "K\u00e4mpfer"}\n', encoding="utf-8")
    assert module.find_non_ascii_files(tmp_path) == []


def test_ascii_policy_ignores_binary_assets(project_root: Path, tmp_path: Path) -> None:
    module = load_ascii_tool(project_root)
    binary = tmp_path / "image.png"
    binary.write_bytes(bytes(range(256)))
    assert module.find_non_ascii_files(tmp_path) == []


def test_project_owned_path_names_are_ascii(project_root: Path) -> None:
    bad_paths = []
    for path in project_root.rglob("*"):
        relative = path.relative_to(project_root)
        if any(part in {".git", ".cache", ".venv", ".pytest_cache", ".ruff_cache"} for part in relative.parts):
            continue
        if not relative.as_posix().isascii():
            bad_paths.append(relative)
    assert bad_paths == []
