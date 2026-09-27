from __future__ import annotations

import re
import tomllib
from pathlib import Path

from tft_builder.paths import build_application_paths


def load_pyproject(project_root: Path) -> dict:
    with (project_root / "pyproject.toml").open("rb") as handle:
        return tomllib.load(handle)


def test_pyproject_declares_expected_project_identity(project_root: Path) -> None:
    project = load_pyproject(project_root)["project"]
    assert project["name"] == "tft-team-builder"
    assert re.fullmatch(r"\d+\.\d+\.\d+", project["version"])
    assert project["requires-python"] == ">=3.13,<3.14"


def test_python_version_file_matches_supported_runtime(project_root: Path) -> None:
    assert (project_root / ".python-version").read_text(encoding="ascii") == "3.13\n"


def test_runtime_constants_do_not_duplicate_release_version(project_root: Path) -> None:
    constants = (project_root / "src" / "tft_builder" / "constants.py").read_text(encoding="ascii")
    assert not re.search(r"^APP_VERSION\s*=", constants, flags=re.MULTILINE)


def test_runtime_dependencies_are_minimal_and_pinned(project_root: Path) -> None:
    dependencies = set(load_pyproject(project_root)["project"]["dependencies"])
    assert dependencies == {
        "flet==1.0.1",
        "platformdirs==4.11.15",
        "pydantic==2.13.5",
    }
    assert not any("desktop" in dependency or "web" in dependency for dependency in dependencies)


def test_uv_version_floor_includes_windows_security_fix(project_root: Path) -> None:
    uv_config = load_pyproject(project_root)["tool"]["uv"]
    assert uv_config["required-version"] == ">=0.12.18,<0.13"


def test_development_tools_use_standard_dependency_group(project_root: Path) -> None:
    config = load_pyproject(project_root)
    assert "optional-dependencies" not in config["project"]
    assert set(config["dependency-groups"]["dev"]) == {
        "flet-cli==1.0.1",
        "flet-desktop==1.0.1",
        "flet[test]==1.0.1",
        "pytest==9.1.1",
        "pytest-cov==7.1.0",
        "ruff==0.16.9",
    }
    assert config["dependency-groups"]["web"] == ["flet-web==1.0.1"]


def test_hatchling_build_backend_is_pinned(project_root: Path) -> None:
    build = load_pyproject(project_root)["build-system"]
    assert build["build-backend"] == "hatchling.build"
    assert build["requires"] == ["hatchling==1.32.4"]


def test_flet_uses_src_app_path_and_current_entry_module(project_root: Path) -> None:
    flet = load_pyproject(project_root)["tool"]["flet"]
    assert "desktop_flavor" not in flet
    assert flet["app"]["path"] == "src"
    assert flet["app"]["module"] == "main.py"
    assert "company" not in flet
    assert "org" not in flet
    assert "bundle_id" not in flet
    bundled_sets = project_root / "src" / "assets" / "sets"
    assert (bundled_sets / "sample_set").is_dir()

    # The clean project layout has one authoritative bundled Set root. Keeping this explicit
    # avoids accidentally reintroducing the obsolete repository-level Set directory.
    paths = build_application_paths(project_root=project_root)
    assert paths.bundled_sets_dir == bundled_sets.resolve()
    assert not (project_root / "sets").exists()


def test_pytest_is_configured_for_src_layout_and_coverage(project_root: Path) -> None:
    config = load_pyproject(project_root)
    pytest_config = config["tool"]["pytest"]["ini_options"]
    assert pytest_config["testpaths"] == ["tests"]
    assert pytest_config["asyncio_mode"] == "auto"
    assert "pythonpath" not in pytest_config
    assert "--import-mode=importlib" in pytest_config["addopts"]
    assert "--strict-config" in pytest_config["addopts"]
    assert "--strict-markers" in pytest_config["addopts"]
    assert "--cov=tft_builder" in pytest_config["addopts"]
    assert "--cov-branch" in pytest_config["addopts"]
    assert "--cov-fail-under=100" in pytest_config["addopts"]
    assert pytest_config["filterwarnings"] == ["error::ResourceWarning"]
    assert config["tool"]["coverage"]["report"]["fail_under"] == 100


def test_ruff_targets_python_313_and_all_project_code(project_root: Path) -> None:
    ruff = load_pyproject(project_root)["tool"]["ruff"]
    assert ruff["target-version"] == "py313"
    assert ruff["src"] == ["src", "tests", "tools"]
    assert ruff["format"]["line-ending"] == "lf"
    assert {"E", "F", "I", "UP", "B", "RUF", "PTH"} <= set(ruff["lint"]["select"])


def test_uv_lock_project_version_matches_pyproject(project_root: Path) -> None:
    config = load_pyproject(project_root)
    with (project_root / "uv.lock").open("rb") as handle:
        lock = tomllib.load(handle)
    project_package = next(
        package for package in lock["package"] if package["name"] == config["project"]["name"]
    )
    assert project_package["version"] == config["project"]["version"]


def test_uv_lock_is_not_ignored(project_root: Path) -> None:
    gitignore = (project_root / ".gitignore").read_text(encoding="ascii")
    assert "uv.lock" not in gitignore


def test_quality_workflow_runs_on_windows_and_linux_with_python_313(project_root: Path) -> None:
    workflow = (project_root / ".github" / "workflows" / "quality.yml").read_text(encoding="ascii")
    assert "windows-latest" in workflow
    assert "ubuntu-latest" in workflow
    assert 'python-version: "3.13"' in workflow
    assert 'version: "0.12.19"' in workflow
    assert "setup-uv@c18668ad3cf93ea998bef934396af7bb5c839dc7 # v10.2.0" in workflow
    assert "3.14" not in workflow
    assert "uv lock --check" in workflow
    assert "uv sync --frozen" in workflow
    assert "uv run python -m compileall -q src tests tools" in workflow
    assert "uv run pytest" in workflow
    assert "uv run ruff check ." in workflow
    assert "uv run ruff format --check ." in workflow
    assert "tools/check_ascii.py" in workflow
    assert "tools/sync_project_docs.py --check" in workflow
    assert "uv run tft-builder-dev validate-set src/assets/sets/sample_set" in workflow
    assert "uv run tft-builder-dev database-smoke .runtime-smoke" in workflow
    assert "uv run tft-builder-dev builder-smoke src/assets/sets/sample_set" in workflow
    assert "uv run flet --version" in workflow


def test_gitattributes_normalizes_project_text_to_lf(project_root: Path) -> None:
    attributes = (project_root / ".gitattributes").read_text(encoding="ascii")
    assert "* text=auto eol=lf" in attributes
