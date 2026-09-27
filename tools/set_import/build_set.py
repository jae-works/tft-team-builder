"""Repository-local wrapper around the deterministic Block 1 Set builder."""

from __future__ import annotations

import argparse
from pathlib import Path

from tft_builder.set_builder import build_set_from_local_spec


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    output = build_set_from_local_spec(args.spec_dir, args.output_dir, overwrite=args.overwrite)
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
