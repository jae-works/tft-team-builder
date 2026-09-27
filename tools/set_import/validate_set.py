"""Repository-local wrapper for strict Set validation."""

from __future__ import annotations

import argparse
from pathlib import Path

from tft_builder.set_loader import validate_set_directory


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("set_dir", type=Path)
    args = parser.parse_args()
    report = validate_set_directory(args.set_dir)
    if report.is_valid:
        print("VALID")
        return 0
    print(report.formatted_issues())
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
