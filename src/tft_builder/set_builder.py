"""Deterministic offline Set package builder used by Block 1 fixtures and sample data.

Block 7 will add upstream Riot/CommunityDragon acquisition. This module already defines the
stable normalization boundary: source adapters produce a local spec, and this builder emits
the runtime package consumed by the application.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

from pydantic import ValidationError

from .constants import SOURCE_MANIFEST_SCHEMA_VERSION
from .file_integrity import sha256_bytes, sha256_file
from .filesystem import is_link_like
from .json_utils import canonical_json_bytes, loads_json
from .set_loader import load_set_directory
from .set_schema import LocalSetSpec


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def _load_source_spec(spec_dir: Path) -> tuple[LocalSetSpec, bytes]:
    spec_path = spec_dir / "set_spec.json"
    if is_link_like(spec_path):
        raise ValueError("source spec file must not be a symbolic link or junction")
    raw = spec_path.read_bytes()
    payload = loads_json(raw.decode("utf-8"))
    try:
        return LocalSetSpec.model_validate(payload), raw
    except ValidationError as error:
        raise ValueError(f"invalid source spec: {error}") from error


def _resolve_source_asset(spec_dir: Path, relative: str) -> Path:
    """Resolve one project-owned source asset without allowing symlink escapes."""

    candidate = spec_dir.joinpath(*relative.split("/"))
    if not candidate.exists():
        raise FileNotFoundError(f"source asset does not exist: {candidate}")

    current = spec_dir
    for component in relative.split("/"):
        current = current / component
        if is_link_like(current):
            raise ValueError(
                f"source asset path must not contain symbolic links or junctions: {relative}"
            )

    resolved = candidate.resolve(strict=True)
    try:
        resolved.relative_to(spec_dir)
    except ValueError as error:
        raise ValueError(
            f"source asset resolves outside source spec directory: {relative}"
        ) from error

    if not resolved.is_file():
        raise FileNotFoundError(f"source asset is not a file: {resolved}")
    return resolved


def _markdown_cell(value: str) -> str:
    """Keep generated overview tables readable without embedding arbitrary Markdown."""

    return value.replace("|", "\\|").replace("\n", " ").strip()


def _render_set_overview(spec: LocalSetSpec) -> str:
    """Render a deterministic human-reviewable inventory beside the runtime data."""

    catalog = spec.locales[spec.manifest.default_locale]
    lines = [
        f"# {catalog[spec.manifest.display_name_key]} - Set package overview",
        "",
        "Generated from the validated Set source specification. Images use local package paths.",
        "",
        f"- Champions: {len(spec.champions)}",
        f"- Traits: {len(spec.traits)}",
        f"- Items: {len(spec.items)}",
        "",
        "## Champions",
        "",
        "| Image | Champion | Cost | Traits | Trait points | Slots |",
        "| --- | --- | ---: | --- | --- | ---: |",
    ]
    trait_names = {trait.id: catalog[trait.name_key] for trait in spec.traits}
    for champion in sorted(spec.champions, key=lambda item: (item.display_order, item.id)):
        traits = ", ".join(trait_names[trait_id] for trait_id in champion.traits)
        points = ", ".join(
            f"{trait_id}={champion.trait_points.get(trait_id, 1)}" for trait_id in champion.traits
        )
        lines.append(
            "| "
            f"![{_markdown_cell(catalog[champion.name_key])}]({champion.image}) | "
            f"{_markdown_cell(catalog[champion.name_key])} | {champion.cost} | "
            f"{_markdown_cell(traits)} | {_markdown_cell(points)} | {champion.board_slots} |"
        )

    lines.extend(
        [
            "",
            "## Dynamic Trait choices",
            "",
            "| Champion | Rule | Scope | Choice | Points | Choice image |",
            "| --- | --- | --- | --- | ---: | --- |",
        ]
    )
    champions_by_id = {champion.id: champion for champion in spec.champions}
    for rule in sorted(spec.dynamic_traits, key=lambda item: item.champion_id):
        champion_name = catalog[champions_by_id[rule.champion_id].name_key]
        for trait_id in rule.choices:
            image = rule.choice_images.get(trait_id, "-")
            image_cell = f"![{_markdown_cell(trait_names[trait_id])}]({image})" if image != "-" else "-"
            lines.append(
                f"| {_markdown_cell(champion_name)} | {rule.selection_rule.value} | "
                f"{rule.selection_scope.value} | {_markdown_cell(trait_names[trait_id])} | "
                f"{rule.choice_points.get(trait_id, 1)} | {image_cell} |"
            )

    lines.extend(
        [
            "",
            "## Traits",
            "",
            "| Icon | Trait | Breakpoints | Activation | Derived from | Description |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for trait in sorted(spec.traits, key=lambda item: (item.display_order, item.id)):
        breakpoint_parts = []
        for breakpoint in trait.breakpoints:
            text = f"{breakpoint.count} ({breakpoint.style})"
            if breakpoint.description_key:
                text += f": {catalog[breakpoint.description_key]}"
            breakpoint_parts.append(text)
        breakpoints = " / ".join(breakpoint_parts)
        description = catalog.get(trait.description_key, "-") if trait.description_key else "-"
        derived = ", ".join(
            f"{trait_id}>={count}"
            for trait_id, count in sorted(trait.derived_requirements.items())
        ) or "-"
        lines.append(
            f"| ![{_markdown_cell(catalog[trait.name_key])}]({trait.icon}) | "
            f"{_markdown_cell(catalog[trait.name_key])} | {_markdown_cell(breakpoints)} | "
            f"{trait.activation_mode.value} | {_markdown_cell(derived)} | "
            f"{_markdown_cell(description)} |"
        )

    lines.extend(
        [
            "",
            "## Items",
            "",
            "| Icon | Item | Category | Components | Associated Traits | Description |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
    )
    for item in sorted(spec.items, key=lambda value: (value.display_order, value.id)):
        description = catalog.get(item.description_key, "-") if item.description_key else "-"
        lines.append(
            f"| ![{_markdown_cell(catalog[item.name_key])}]({item.icon}) | "
            f"{_markdown_cell(catalog[item.name_key])} | {item.category.value} | "
            f"{_markdown_cell(', '.join(item.composition) or '-')} | "
            f"{_markdown_cell(', '.join(item.associated_traits) or '-')} | "
            f"{_markdown_cell(description)} |"
        )

    lines.extend(
        [
            "",
            "## Source candidate accounting",
            "",
            f"Included/excluded source candidates: {len(spec.source_inventory)}",
        ]
    )
    return "\n".join(lines) + "\n"


def _populate_staging_directory(spec_dir: Path, staging_dir: Path) -> None:
    """Write a complete candidate package into an isolated staging directory."""

    spec, raw_spec = _load_source_spec(spec_dir)

    _write_json(staging_dir / "manifest.json", spec.manifest.model_dump(mode="json"))
    _write_json(
        staging_dir / spec.manifest.champions_file,
        [value.model_dump(mode="json") for value in spec.champions],
    )
    _write_json(
        staging_dir / spec.manifest.items_file,
        [value.model_dump(mode="json") for value in spec.items],
    )
    _write_json(
        staging_dir / spec.manifest.traits_file,
        [value.model_dump(mode="json") for value in spec.traits],
    )
    _write_json(
        staging_dir / spec.manifest.dynamic_traits_file,
        [value.model_dump(mode="json") for value in spec.dynamic_traits],
    )
    _write_json(
        staging_dir / spec.manifest.team_planner_file,
        spec.team_planner.model_dump(mode="json"),
    )
    _write_json(
        staging_dir / spec.manifest.source_inventory_file,
        [value.model_dump(mode="json") for value in spec.source_inventory],
    )
    overview_path = staging_dir / spec.manifest.overview_file
    overview_path.parent.mkdir(parents=True, exist_ok=True)
    overview_path.write_text(_render_set_overview(spec), encoding="utf-8", newline="\n")

    for locale, catalog in sorted(spec.locales.items()):
        _write_json(staging_dir / spec.manifest.locales_dir / f"{locale}.json", catalog)

    asset_hashes: dict[str, str] = {}
    for target, source in sorted(spec.assets.items()):
        source_path = _resolve_source_asset(spec_dir, source)
        target_path = staging_dir.joinpath(*target.split("/"))
        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source_path, target_path)
        asset_hashes[target] = sha256_file(target_path)

    generated_paths = {
        "manifest.json",
        spec.manifest.champions_file,
        spec.manifest.items_file,
        spec.manifest.traits_file,
        spec.manifest.dynamic_traits_file,
        spec.manifest.team_planner_file,
        spec.manifest.source_inventory_file,
        spec.manifest.overview_file,
        *(
            f"{spec.manifest.locales_dir}/{locale}.json"
            for locale in spec.manifest.supported_locales
        ),
    }
    generated_file_hashes = {
        relative: sha256_file(staging_dir.joinpath(*relative.split("/")))
        for relative in sorted(generated_paths)
    }

    source_manifest = {
        "schema_version": SOURCE_MANIFEST_SCHEMA_VERSION,
        "source_type": "local_spec",
        "source_sha256": sha256_bytes(raw_spec),
        "generated_file_sha256": generated_file_hashes,
        "asset_sha256": asset_hashes,
        "sources": [value.model_dump(mode="json") for value in spec.sources],
    }
    _write_json(staging_dir / spec.manifest.source_manifest_file, source_manifest)

    # The exact runtime loader validates the staging directory before it can replace an
    # existing output. Build-time and runtime validity therefore cannot silently diverge.
    load_set_directory(staging_dir)


def _promote_staging_directory(staging_dir: Path, output_dir: Path) -> None:
    """Replace output with a validated staging directory while preserving rollback safety."""

    backup_dir: Path | None = None
    if output_dir.exists():
        backup_dir = output_dir.with_name(f".{output_dir.name}.previous-{uuid4().hex}")
        output_dir.rename(backup_dir)

    try:
        staging_dir.rename(output_dir)
    except BaseException:
        # If promotion fails after the previous output was moved aside, restore it before
        # propagating the original error. This keeps overwrite failures non-destructive.
        if backup_dir is not None and backup_dir.exists() and not output_dir.exists():
            backup_dir.rename(output_dir)
        raise
    else:
        if backup_dir is not None:
            shutil.rmtree(backup_dir, ignore_errors=True)


def build_set_from_local_spec(
    spec_dir: Path,
    output_dir: Path,
    *,
    overwrite: bool = False,
) -> Path:
    """Build and validate a runtime Set package from an offline local source spec.

    Generation is transactional at directory level: all files are written and validated in a
    sibling staging directory. Only a fully valid package is promoted to the requested output.
    Existing output is left untouched if generation fails before promotion.
    """

    raw_spec_dir = Path(spec_dir).expanduser()
    raw_output_dir = Path(output_dir).expanduser()
    if is_link_like(raw_spec_dir):
        raise ValueError("source spec directory must not be a symbolic link or junction")
    if is_link_like(raw_output_dir):
        raise ValueError("output directory must not be a symbolic link or junction")

    spec_dir = raw_spec_dir.resolve()
    output_dir = raw_output_dir.resolve()
    if not spec_dir.is_dir():
        raise FileNotFoundError(f"source spec directory does not exist: {spec_dir}")

    # Overlapping input/output trees are dangerous with overwrite=True because removing or
    # replacing output could also destroy all or part of the source specification.
    if (
        output_dir == spec_dir
        or output_dir.is_relative_to(spec_dir)
        or spec_dir.is_relative_to(output_dir)
    ):
        raise ValueError("source spec and output directories must not overlap")

    if output_dir.exists():
        if not output_dir.is_dir():
            raise FileExistsError(f"output path exists and is not a directory: {output_dir}")
        if not overwrite:
            raise FileExistsError(f"output directory already exists: {output_dir}")

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging_dir = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}.build-", dir=output_dir.parent))
    try:
        _populate_staging_directory(spec_dir, staging_dir)
        _promote_staging_directory(staging_dir, output_dir)
    except BaseException:
        shutil.rmtree(staging_dir, ignore_errors=True)
        raise

    return output_dir
