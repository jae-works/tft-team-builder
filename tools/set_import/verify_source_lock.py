"""Verify a generic Set acquisition source lock against packaged provenance."""

from __future__ import annotations

import argparse
from pathlib import Path

from tft_builder.set_loader import load_set_directory
from tft_builder.source_verification import verify_source_lock_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("set_dir", type=Path)
    parser.add_argument("source_lock", type=Path)
    args = parser.parse_args()

    loaded = load_set_directory(args.set_dir)
    issues = verify_source_lock_file(loaded, args.source_lock)
    if issues:
        print("INVALID source provenance")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("VALID source provenance")
    print(f"Sources: {len(loaded.source_manifest.sources)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
