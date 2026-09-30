"""Verify native dependencies in a final Flet/Serious Python Windows bundle."""

from __future__ import annotations

import argparse
from pathlib import Path

from tft_builder.package_verification import windows_bundle_issues


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "bundle_dir",
        type=Path,
        help="Final directory containing the executable, site-packages and DLLs directories.",
    )
    args = parser.parse_args()

    issues = windows_bundle_issues(args.bundle_dir)
    if issues:
        print("INVALID Windows bundle")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("VALID Windows bundle")
    print("pydantic-core native extension: present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
