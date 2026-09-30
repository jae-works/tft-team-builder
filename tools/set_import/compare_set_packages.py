"""Compare two validated Set packages for deterministic byte-for-byte content."""

from __future__ import annotations

import argparse
from pathlib import Path

from tft_builder.file_integrity import directory_content_hash
from tft_builder.set_loader import SetValidationError, load_set_directory


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("first", type=Path)
    parser.add_argument("second", type=Path)
    args = parser.parse_args()

    # Validate both packages before comparing their complete directory contents. A matching
    # hash is useful only when each side is independently a valid runtime Set package.
    try:
        load_set_directory(args.first)
        load_set_directory(args.second)
    except SetValidationError as error:
        print("INVALID reproducibility comparison")
        print(error)
        return 1

    first_hash = directory_content_hash(args.first)
    second_hash = directory_content_hash(args.second)

    if first_hash != second_hash:
        print("INVALID reproducibility comparison")
        print(f"First:  {first_hash}")
        print(f"Second: {second_hash}")
        return 1

    print("VALID reproducible Set package")
    print(f"SHA-256: {first_hash}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
