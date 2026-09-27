from __future__ import annotations

import tomllib
from pathlib import Path


def load_pyproject(project_root: Path) -> dict:
    with (project_root / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def test_pyproject_declares_expected_project_identity(project_root: Path) -> None:
    config = load_pyproject(project_root)
    project = config["project"]
    assert project["name"] == "tft-team-builder"
    assert project["version"] == "0.1.0"
    assert project["requires-python"] == ">=3.13,<3.14"


def test_runtime_dependencies_are_pinned_directly(project_root: Path) -> None:
    config = load_pyproject(project_root)
    dependencies = set(config["project"]["dependencies"])
    assert dependencies == {
        "flet==1.0.1",
        "platformdirs==4.11.14",
        "pydantic==2.13.5",
    }


def test_development_tools_use_standard_dependency_group(project_root: Path) -> None:
    config = load_pyproject(project_root)
    assert "optional-dependencies" not in config["project"]
    dev = set(config["dependency-groups"]["dev"])
    assert dev == {
        "flet-cli==1.0.1",
        "flet-desktop==1.0.1",
        "pytest==9.1.1",
        "ruff==0.16.9",
    }


def test_hatchling_build_backend_is_pinned(project_root: Path) -> None:
    config = load_pyproject(project_root)
    build = config["build-system"]
    assert build["build-backend"] == "hatchling.build"
    assert build["requires"] == ["hatchling==1.32.4"]


def test_flet_uses_src_app_path_and_current_entry_module(project_root: Path) -> None:
    config = load_pyproject(project_root)
    flet = config["tool"]["flet"]
    assert flet["desktop_flavor"] == "full"
    assert flet["app"]["path"] == "src"
    assert flet["app"]["module"] == "main.py"


def test_pytest_is_configured_for_src_layout(project_root: Path) -> None:
    config = load_pyproject(project_root)
    pytest_config = config["tool"]["pytest"]["ini_options"]
    assert pytest_config["testpaths"] == ["tests"]
    assert pytest_config["pythonpath"] == ["src"]
    assert "--strict-config" in pytest_config["addopts"]
    assert "--strict-markers" in pytest_config["addopts"]


def test_ruff_targets_python_313_and_all_project_code(project_root: Path) -> None:
    config = load_pyproject(project_root)
    ruff = config["tool"]["ruff"]
    assert ruff["target-version"] == "py313"
    assert ruff["src"] == ["src", "tests", "tools"]
    assert ruff["format"]["line-ending"] == "lf"
    assert "E" in ruff["lint"]["select"]
    assert "F" in ruff["lint"]["select"]
    assert "I" in ruff["lint"]["select"]
