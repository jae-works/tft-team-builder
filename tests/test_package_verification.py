from __future__ import annotations

from pathlib import Path

from tft_builder.package_verification import windows_bundle_issues, windows_staging_issues


def _write_package_marker(site_packages: Path, package: str) -> None:
    """Create the minimum package marker needed by the layout verifier."""

    package_dir = site_packages / package
    package_dir.mkdir(parents=True)
    (package_dir / "__init__.py").write_text("", encoding="ascii")


def test_windows_staging_verifier_accepts_native_wheel_layout(tmp_path: Path) -> None:
    site_packages = tmp_path / "site-packages"
    core_dir = site_packages / "pydantic_core"
    core_dir.mkdir(parents=True)
    (core_dir / "_pydantic_core.cp313-win_amd64.pyd").write_bytes(b"native")

    assert windows_staging_issues(site_packages) == ()


def test_windows_staging_verifier_reports_missing_or_duplicate_native_core(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    assert windows_staging_issues(missing) == (
        f"site-packages directory does not exist: {missing.resolve()}",
    )

    site_packages = tmp_path / "site-packages"
    site_packages.mkdir()
    assert windows_staging_issues(site_packages) == (
        "expected exactly one staged pydantic_core/_pydantic_core*.pyd; found 0",
    )

    core_dir = site_packages / "pydantic_core"
    core_dir.mkdir()
    (core_dir / "_pydantic_core.first.pyd").write_bytes(b"one")
    (core_dir / "_pydantic_core.second.pyd").write_bytes(b"two")
    assert windows_staging_issues(site_packages) == (
        "expected exactly one staged pydantic_core/_pydantic_core*.pyd; found 2",
    )


def test_windows_bundle_verifier_accepts_serious_python_layout(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    site_packages = bundle / "site-packages"
    _write_package_marker(site_packages, "pydantic")
    _write_package_marker(site_packages, "pydantic_core")
    (bundle / "DLLs").mkdir()
    (bundle / "DLLs" / "_pydantic_core.cp313-win_amd64.pyd").write_bytes(b"native")

    assert windows_bundle_issues(bundle) == ()


def test_windows_bundle_verifier_reports_missing_runtime_parts(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    assert windows_bundle_issues(missing) == (
        f"bundle directory does not exist: {missing.resolve()}",
    )

    bundle = tmp_path / "bundle"
    bundle.mkdir()
    assert windows_bundle_issues(bundle) == (
        "pydantic package is missing from site-packages",
        "pydantic_core package is missing from site-packages",
        "expected exactly one _pydantic_core*.pyd in DLLs; found 0",
    )


def test_windows_bundle_verifier_rejects_duplicate_native_core_files(tmp_path: Path) -> None:
    bundle = tmp_path / "bundle"
    site_packages = bundle / "site-packages"
    _write_package_marker(site_packages, "pydantic")
    _write_package_marker(site_packages, "pydantic_core")
    dlls = bundle / "DLLs"
    dlls.mkdir()
    (dlls / "_pydantic_core.first.pyd").write_bytes(b"one")
    (dlls / "_pydantic_core.second.pyd").write_bytes(b"two")

    assert windows_bundle_issues(bundle) == (
        "expected exactly one _pydantic_core*.pyd in DLLs; found 2",
    )
