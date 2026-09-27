from __future__ import annotations

import ast
from pathlib import Path


def imported_top_level_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".", 1)[0])
    return modules


def test_flet_dependency_is_confined_to_ui_boundary(project_root: Path) -> None:
    package_root = project_root / "src" / "tft_builder"
    offenders = []
    for path in sorted(package_root.rglob("*.py")):
        if path.name == "app.py":
            continue
        if "flet" in imported_top_level_modules(path):
            offenders.append(path.relative_to(project_root))
    assert offenders == []


def test_filesystem_code_does_not_use_legacy_os_path_api(project_root: Path) -> None:
    offenders = []
    for path in sorted((project_root / "src" / "tft_builder").rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if "os.path" in text:
            offenders.append(path.relative_to(project_root))
    assert offenders == []


def test_only_path_module_reads_process_environment(project_root: Path) -> None:
    package_root = project_root / "src" / "tft_builder"
    offenders = []
    for path in sorted(package_root.rglob("*.py")):
        if path.name == "paths.py":
            continue
        text = path.read_text(encoding="utf-8")
        if "os.environ" in text or "os.getenv" in text:
            offenders.append(path.relative_to(project_root))
    assert offenders == []


def test_application_source_does_not_depend_on_assert_statements(project_root: Path) -> None:
    offenders: list[tuple[Path, int]] = []
    for path in sorted((project_root / "src" / "tft_builder").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        offenders.extend(
            (path.relative_to(project_root), node.lineno)
            for node in ast.walk(tree)
            if isinstance(node, ast.Assert)
        )
    assert offenders == []


def test_block_3_core_stays_independent_from_persistence(project_root: Path) -> None:
    package_root = project_root / "src" / "tft_builder"
    offenders = []
    for filename in ("builder.py", "trait_engine.py"):
        path = package_root / filename
        if "persistence" in imported_top_level_modules(path):
            offenders.append(path.relative_to(project_root))
    assert offenders == []
