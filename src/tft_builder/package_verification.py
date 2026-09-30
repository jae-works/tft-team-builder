"""Small checks for platform package layouts that unit tests cannot execute directly."""

from __future__ import annotations

from pathlib import Path


def _package_marker_issues(site_packages: Path) -> list[str]:
    """Return missing-package issues shared by staging and final bundle checks."""

    issues: list[str] = []
    if not (site_packages / "pydantic" / "__init__.py").is_file():
        issues.append("pydantic package is missing from site-packages")
    if not (site_packages / "pydantic_core" / "__init__.py").is_file():
        issues.append("pydantic_core package is missing from site-packages")
    return issues


def windows_staging_issues(site_packages_dir: Path) -> tuple[str, ...]:
    """Return issues for Serious Python's pre-Flutter Windows dependency staging area."""

    site_packages = site_packages_dir.resolve()
    if not site_packages.is_dir():
        return (f"site-packages directory does not exist: {site_packages}",)

    # Flet/Serious Python may consume or clean pure-Python package files after creating
    # the temporary packaged app, so post-run __init__.py markers are not a reliable
    # staging contract. The native wheel extension is the startup-critical artifact.
    core_dir = site_packages / "pydantic_core"
    native_core = tuple(core_dir.glob("_pydantic_core*.pyd")) if core_dir.is_dir() else ()
    if len(native_core) != 1:
        return (
            f"expected exactly one staged pydantic_core/_pydantic_core*.pyd; found {len(native_core)}",
        )

    return ()


def windows_bundle_issues(bundle_dir: Path) -> tuple[str, ...]:
    """Return actionable issues for a final Serious Python Windows bundle directory."""

    root = bundle_dir.resolve()
    if not root.is_dir():
        return (f"bundle directory does not exist: {root}",)

    site_packages = root / "site-packages"
    issues = _package_marker_issues(site_packages)
    dlls = root / "DLLs"

    # Serious Python documents Windows extension modules as relocated into DLLs.
    native_core = tuple(dlls.glob("_pydantic_core*.pyd")) if dlls.is_dir() else ()
    if len(native_core) != 1:
        issues.append(f"expected exactly one _pydantic_core*.pyd in DLLs; found {len(native_core)}")

    return tuple(issues)
