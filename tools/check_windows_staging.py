"""Verify native dependencies in Flet/Serious Python Windows package staging."""

from __future__ import annotations

import argparse
from pathlib import Path

from tft_builder.package_verification import windows_staging_issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "site_packages_dir",
        nargs="?",
        type=Path,
        default=Path("build/site-packages"),
        help="Serious Python dependency staging directory (default: build/site-packages).",
    )
    args = parser.parse_args()

    issues = windows_staging_issues(args.site_packages_dir)
    if issues:
        print("INVALID Windows package staging")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("VALID Windows package staging")
    print("pydantic-core native extension: staged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
