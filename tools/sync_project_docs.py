"""Synchronize release-facing project documentation into ``project_docs``."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path


def _load_mirrored_documents(project_root: Path) -> tuple[str, ...]:
    manifest_path = project_root / "PROJECT_MANIFEST.json"
    payload = json.loads(manifest_path.read_text(encoding="ascii"))
    values = payload.get("mirrored_project_documents")
    if (
        not isinstance(values, list)
        or not values
        or not all(isinstance(item, str) for item in values)
    ):
        raise ValueError("PROJECT_MANIFEST.json must define mirrored_project_documents")
    if len(values) != len(set(values)):
        raise ValueError("mirrored_project_documents must not contain duplicates")
    return tuple(values)


def synchronize_project_docs(project_root: Path, *, check_only: bool = False) -> list[str]:
    """Synchronize configured documents or return mismatches in check-only mode."""

    project_root = project_root.resolve()
    mirror_root = project_root / "project_docs"
    documents = _load_mirrored_documents(project_root)
    mismatches: list[str] = []

    if not check_only:
        mirror_root.mkdir(parents=True, exist_ok=True)

    for relative in documents:
        source = project_root / relative
        mirror = mirror_root / relative
        if not source.is_file():
            raise FileNotFoundError(f"required project document does not exist: {relative}")

        if check_only:
            if not mirror.is_file() or mirror.read_bytes() != source.read_bytes():
                mismatches.append(relative)
            continue

        mirror.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, mirror)

    return mismatches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    mismatches = synchronize_project_docs(args.root, check_only=args.check)
    if mismatches:
        for relative in mismatches:
            print(f"project_docs mismatch: {relative}")
        return 1

    message = (
        "Project document mirror check passed." if args.check else "Project documents synchronized."
    )
    print(message)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
