"""Verify one reviewed Set package from its Set-owned policy and refresh its review report."""

from __future__ import annotations

import argparse
from pathlib import Path

from tft_builder.set_loader import load_set_directory
from tft_builder.set_review import verify_review_policy, write_set_review_report
from tft_builder.source_verification import verify_source_lock_file


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("set_dir", type=Path)
    parser.add_argument("--source-lock", type=Path)
    args = parser.parse_args()

    loaded = load_set_directory(args.set_dir)
    # Always refresh the derived inspection document, including on review-policy drift.
    report_path = write_set_review_report(loaded)
    issues = verify_review_policy(loaded)
    if args.source_lock is not None:
        issues.extend(verify_source_lock_file(loaded, args.source_lock))

    if issues:
        print(f"INVALID reviewed Set package: {loaded.manifest.set_id}")
        for issue in issues:
            print(f"- {issue}")
        print(f"Review report: {report_path}")
        return 1

    print(f"VALID reviewed Set package: {loaded.manifest.set_id}")
    print(
        f"Champions: {len(loaded.champions)} | Traits: {len(loaded.traits)} | "
        f"Items: {len(loaded.items)} | PNGs: {loaded.review.png_count if loaded.review else 0} | "
        f"Sources: {len(loaded.source_manifest.sources)}"
    )
    print(f"Review report: {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
