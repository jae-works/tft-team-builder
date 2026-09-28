"""Loading and semantic validation for local TFT Set packages."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any

from pydantic import BaseModel, ValidationError

from .file_integrity import sha256_file
from .filesystem import is_link_like, scan_regular_files
from .json_utils import DuplicateJsonKeyError, loads_json
from .set_schema import (
    ChampionDefinition,
    DynamicTraitDefinition,
    SetManifest,
    SourceManifest,
    TeamPlannerData,
    TraitDefinition,
)

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


@dataclass(frozen=True, slots=True, order=True)
class ValidationIssue:
    """One stable, human-readable Set validation problem."""

    code: str
    message: str
    location: str = ""

    def format(self) -> str:
        if self.location:
            return f"[{self.code}] {self.location}: {self.message}"
        return f"[{self.code}] {self.message}"


@dataclass(frozen=True, slots=True)
class LoadedSet:
    """A fully validated runtime Set package."""

    root: Path
    manifest: SetManifest
    champions: tuple[ChampionDefinition, ...]
    traits: tuple[TraitDefinition, ...]
    dynamic_traits: tuple[DynamicTraitDefinition, ...]
    team_planner: TeamPlannerData
    locales: dict[str, dict[str, str]]
    source_manifest: SourceManifest
    _champions_by_id: Mapping[str, ChampionDefinition] = field(
        init=False, repr=False, compare=False
    )
    _traits_by_id: Mapping[str, TraitDefinition] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Cache immutable ID lookups once for GUI and engine hot paths."""

        object.__setattr__(
            self,
            "_champions_by_id",
            MappingProxyType({champion.id: champion for champion in self.champions}),
        )
        object.__setattr__(
            self,
            "_traits_by_id",
            MappingProxyType({trait.id: trait for trait in self.traits}),
        )

    @property
    def champions_by_id(self) -> Mapping[str, ChampionDefinition]:
        return self._champions_by_id

    @property
    def traits_by_id(self) -> Mapping[str, TraitDefinition]:
        return self._traits_by_id


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """Validation result that can report several independent Set problems at once."""

    root: Path
    issues: tuple[ValidationIssue, ...]
    loaded_set: LoadedSet | None = None

    @property
    def is_valid(self) -> bool:
        return not self.issues and self.loaded_set is not None

    def formatted_issues(self) -> str:
        return "\n".join(issue.format() for issue in self.issues)


class SetValidationError(ValueError):
    """Raised when code explicitly requests a valid Set package."""

    def __init__(self, report: ValidationReport) -> None:
        self.report = report
        super().__init__(report.formatted_issues() or "Set validation failed")


def _json_load(path: Path, issues: list[ValidationIssue], location: str) -> Any | None:
    if not path.is_file():
        issues.append(ValidationIssue("missing_file", "required file does not exist", location))
        return None

    try:
        return loads_json(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as error:
        issues.append(ValidationIssue("invalid_utf8", str(error), location))
    except DuplicateJsonKeyError as error:
        issues.append(ValidationIssue("duplicate_json_key", str(error), location))
    except json.JSONDecodeError as error:
        issues.append(
            ValidationIssue(
                "invalid_json",
                f"line {error.lineno}, column {error.colno}: {error.msg}",
                location,
            )
        )
    except OSError as error:
        issues.append(ValidationIssue("unreadable_file", str(error), location))
    return None


def _model_error_issues(error: ValidationError, prefix: str) -> list[ValidationIssue]:
    converted: list[ValidationIssue] = []
    for item in error.errors(include_url=False):
        location_parts = [str(part) for part in item["loc"]]
        location = ".".join([prefix, *location_parts]) if location_parts else prefix
        converted.append(ValidationIssue("schema_error", item["msg"], location))
    return converted


def _parse_model[ModelT: BaseModel](
    model_type: type[ModelT],
    payload: Any,
    issues: list[ValidationIssue],
    prefix: str,
) -> ModelT | None:
    try:
        return model_type.model_validate(payload)
    except ValidationError as error:
        issues.extend(_model_error_issues(error, prefix))
        return None


def _parse_model_list[ModelT: BaseModel](
    model_type: type[ModelT],
    payload: Any,
    issues: list[ValidationIssue],
    prefix: str,
) -> list[ModelT] | None:
    if not isinstance(payload, list):
        issues.append(ValidationIssue("schema_error", "expected a JSON array", prefix))
        return None

    values: list[ModelT] = []
    for index, item in enumerate(payload):
        value = _parse_model(model_type, item, issues, f"{prefix}[{index}]")
        if value is not None:
            values.append(value)
    return values


def _safe_package_path(
    resolved_root: Path,
    relative: str,
    issues: list[ValidationIssue],
    location: str,
) -> Path | None:
    """Resolve a schema-validated relative path and reject symlink/path escapes."""

    candidate = resolved_root.joinpath(*relative.split("/"))
    current = resolved_root
    try:
        for component in relative.split("/"):
            current = current / component
            if is_link_like(current):
                issues.append(
                    ValidationIssue(
                        "unexpected_symlink",
                        "runtime Set paths must not contain symbolic links or junctions",
                        location,
                    )
                )
                return None

        resolved_candidate = candidate.resolve(strict=False)
        resolved_candidate.relative_to(resolved_root)
    except ValueError:
        issues.append(
            ValidationIssue("path_escape", "path resolves outside the Set directory", location)
        )
        return None
    except (OSError, RuntimeError) as error:
        issues.append(ValidationIssue("unreadable_path", str(error), location))
        return None
    return candidate


def _check_unique_ids(
    values: list[ChampionDefinition] | list[TraitDefinition],
    kind: str,
    issues: list[ValidationIssue],
) -> None:
    seen: set[str] = set()
    for value in values:
        if value.id in seen:
            issues.append(
                ValidationIssue(
                    "duplicate_id",
                    f"duplicate {kind} ID '{value.id}'",
                    f"data.{kind}s",
                )
            )
        seen.add(value.id)


def _check_unique_display_orders(
    values: list[ChampionDefinition] | list[TraitDefinition],
    kind: str,
    issues: list[ValidationIssue],
) -> None:
    seen: dict[int, str] = {}
    for value in values:
        previous_id = seen.get(value.display_order)
        if previous_id is not None:
            issues.append(
                ValidationIssue(
                    "duplicate_display_order",
                    f"{kind} '{value.id}' shares display_order {value.display_order} "
                    f"with '{previous_id}'",
                    f"data.{kind}s",
                )
            )
        else:
            seen[value.display_order] = value.id


def _validate_asset(
    root: Path,
    relative: str,
    issues: list[ValidationIssue],
    location: str,
) -> None:
    path = _safe_package_path(root, relative, issues, location)
    if path is None:
        return
    if not path.is_file():
        issues.append(ValidationIssue("missing_asset", "asset file does not exist", location))
        return

    try:
        if path.stat().st_size == 0:
            issues.append(ValidationIssue("empty_asset", "asset file is empty", location))
            return
        if path.suffix.casefold() == ".png":
            with path.open("rb") as handle:
                if handle.read(len(PNG_SIGNATURE)) != PNG_SIGNATURE:
                    issues.append(
                        ValidationIssue("invalid_png", "PNG signature is invalid", location)
                    )
    except OSError as error:
        issues.append(ValidationIssue("unreadable_asset", str(error), location))


def _validate_hash_inventory(
    *,
    root: Path,
    required_paths: set[str],
    declared_hashes: dict[str, str],
    issues: list[ValidationIssue],
    location: str,
    missing_code: str,
    unexpected_code: str,
    mismatch_code: str,
    unreadable_code: str,
    item_label: str,
) -> None:
    """Compare one required file inventory with its declared SHA-256 mapping."""

    declared_paths = set(declared_hashes)
    for relative in sorted(required_paths - declared_paths):
        issues.append(
            ValidationIssue(
                missing_code,
                f"required {item_label} '{relative}' has no source-manifest hash",
                location,
            )
        )

    for relative in sorted(declared_paths - required_paths):
        issues.append(
            ValidationIssue(
                unexpected_code,
                f"source manifest hashes unexpected {item_label} '{relative}'",
                location,
            )
        )

    for relative in sorted(required_paths & declared_paths):
        path = _safe_package_path(root, relative, issues, f"{location}.{relative}")
        if path is None or not path.is_file():
            continue
        try:
            actual = sha256_file(path)
        except OSError as error:
            issues.append(ValidationIssue(unreadable_code, str(error), f"{location}.{relative}"))
            continue
        if actual != declared_hashes[relative]:
            issues.append(
                ValidationIssue(
                    mismatch_code,
                    f"{item_label} hash does not match source manifest for '{relative}'",
                    location,
                )
            )


def _validate_package_inventory(
    root: Path,
    expected_files: set[str],
    issues: list[ValidationIssue],
) -> None:
    """Reject symlinks and stale/untracked files in a schema-v1 runtime Set package."""

    try:
        files, links = scan_regular_files(root)
    except OSError as error:
        issues.append(ValidationIssue("unreadable_set", str(error), str(root)))
        return

    for candidate in links:
        issues.append(
            ValidationIssue(
                "unexpected_symlink",
                "runtime Set packages must not contain symbolic links or junctions",
                candidate.relative_to(root).as_posix(),
            )
        )

    actual_files = {candidate.relative_to(root).as_posix() for candidate in files}

    for relative in sorted(actual_files - expected_files):
        issues.append(
            ValidationIssue(
                "unexpected_file",
                "file is not part of the declared Set package inventory",
                relative,
            )
        )


def validate_set_directory(root: Path) -> ValidationReport:
    """Validate one Set directory and collect all practical errors in one pass."""

    supplied_root = Path(root)
    if is_link_like(supplied_root):
        return ValidationReport(
            root=supplied_root,
            issues=(
                ValidationIssue(
                    "unexpected_symlink",
                    "runtime Set directory must not be a symbolic link or junction",
                    str(supplied_root),
                ),
            ),
        )
    if not supplied_root.is_dir():
        return ValidationReport(
            root=supplied_root,
            issues=(
                ValidationIssue(
                    "missing_set",
                    "Set directory does not exist",
                    str(supplied_root),
                ),
            ),
        )

    try:
        root = supplied_root.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        return ValidationReport(
            root=supplied_root,
            issues=(ValidationIssue("unreadable_set", str(error), str(supplied_root)),),
        )

    issues: list[ValidationIssue] = []
    manifest_payload = _json_load(root / "manifest.json", issues, "manifest.json")
    manifest = (
        _parse_model(SetManifest, manifest_payload, issues, "manifest")
        if manifest_payload is not None
        else None
    )
    if manifest is None:
        return ValidationReport(root=root, issues=tuple(sorted(issues)))

    paths: dict[str, Path | None] = {
        "champions": _safe_package_path(
            root, manifest.champions_file, issues, "manifest.champions_file"
        ),
        "traits": _safe_package_path(root, manifest.traits_file, issues, "manifest.traits_file"),
        "dynamic_traits": _safe_package_path(
            root,
            manifest.dynamic_traits_file,
            issues,
            "manifest.dynamic_traits_file",
        ),
        "team_planner": _safe_package_path(
            root,
            manifest.team_planner_file,
            issues,
            "manifest.team_planner_file",
        ),
        "source_manifest": _safe_package_path(
            root,
            manifest.source_manifest_file,
            issues,
            "manifest.source_manifest_file",
        ),
    }

    champion_payload = (
        _json_load(paths["champions"], issues, manifest.champions_file)
        if paths["champions"] is not None
        else None
    )
    trait_payload = (
        _json_load(paths["traits"], issues, manifest.traits_file)
        if paths["traits"] is not None
        else None
    )
    dynamic_payload = (
        _json_load(paths["dynamic_traits"], issues, manifest.dynamic_traits_file)
        if paths["dynamic_traits"] is not None
        else None
    )
    team_planner_payload = (
        _json_load(paths["team_planner"], issues, manifest.team_planner_file)
        if paths["team_planner"] is not None
        else None
    )
    source_manifest_payload = (
        _json_load(paths["source_manifest"], issues, manifest.source_manifest_file)
        if paths["source_manifest"] is not None
        else None
    )

    champions = (
        _parse_model_list(ChampionDefinition, champion_payload, issues, "champions")
        if champion_payload is not None
        else None
    )
    traits = (
        _parse_model_list(TraitDefinition, trait_payload, issues, "traits")
        if trait_payload is not None
        else None
    )
    dynamic_traits = (
        _parse_model_list(DynamicTraitDefinition, dynamic_payload, issues, "dynamic_traits")
        if dynamic_payload is not None
        else None
    )
    team_planner = (
        _parse_model(TeamPlannerData, team_planner_payload, issues, "team_planner")
        if team_planner_payload is not None
        else None
    )
    source_manifest = (
        _parse_model(SourceManifest, source_manifest_payload, issues, "source_manifest")
        if source_manifest_payload is not None
        else None
    )

    if champions is not None:
        if not champions:
            issues.append(
                ValidationIssue(
                    "empty_champions",
                    "Set must define at least one Champion",
                    "champions",
                )
            )
        _check_unique_ids(champions, "champion", issues)
        _check_unique_display_orders(champions, "champion", issues)

    if traits is not None:
        if not traits:
            issues.append(
                ValidationIssue("empty_traits", "Set must define at least one Trait", "traits")
            )
        _check_unique_ids(traits, "trait", issues)
        _check_unique_display_orders(traits, "trait", issues)

    if dynamic_traits is not None:
        dynamic_ids = [item.champion_id for item in dynamic_traits]
        if len(dynamic_ids) != len(set(dynamic_ids)):
            issues.append(
                ValidationIssue(
                    "duplicate_dynamic_rule",
                    "a Champion may have at most one dynamic Trait rule",
                    "dynamic_traits",
                )
            )

    champion_ids = {champion.id for champion in champions or []}
    trait_ids = {trait.id for trait in traits or []}
    required_assets: set[str] = set()

    for champion in champions or []:
        for trait_id in champion.traits:
            if trait_id not in trait_ids:
                issues.append(
                    ValidationIssue(
                        "unknown_trait",
                        f"Champion '{champion.id}' references unknown Trait '{trait_id}'",
                        f"champions.{champion.id}.traits",
                    )
                )
        if not champion.image.startswith(f"{manifest.assets_dir}/"):
            issues.append(
                ValidationIssue(
                    "asset_outside_assets_dir",
                    "Champion image must be stored under manifest.assets_dir",
                    f"champions.{champion.id}.image",
                )
            )
        required_assets.add(champion.image)
        _validate_asset(root, champion.image, issues, f"champions.{champion.id}.image")

    for trait in traits or []:
        if not trait.icon.startswith(f"{manifest.assets_dir}/"):
            issues.append(
                ValidationIssue(
                    "asset_outside_assets_dir",
                    "Trait icon must be stored under manifest.assets_dir",
                    f"traits.{trait.id}.icon",
                )
            )
        required_assets.add(trait.icon)
        _validate_asset(root, trait.icon, issues, f"traits.{trait.id}.icon")

    for dynamic_trait in dynamic_traits or []:
        if dynamic_trait.champion_id not in champion_ids:
            issues.append(
                ValidationIssue(
                    "unknown_champion",
                    f"dynamic Trait rule references unknown Champion '{dynamic_trait.champion_id}'",
                    f"dynamic_traits.{dynamic_trait.champion_id}",
                )
            )
        for trait_id in dynamic_trait.choices:
            if trait_id not in trait_ids:
                issues.append(
                    ValidationIssue(
                        "unknown_trait",
                        f"dynamic Trait rule references unknown Trait '{trait_id}'",
                        f"dynamic_traits.{dynamic_trait.champion_id}.choices",
                    )
                )

    locales: dict[str, dict[str, str]] = {}
    required_name_keys = {manifest.display_name_key}
    required_name_keys.update(champion.name_key for champion in champions or [])
    required_name_keys.update(trait.name_key for trait in traits or [])

    locales_dir = _safe_package_path(root, manifest.locales_dir, issues, "manifest.locales_dir")
    if locales_dir is not None:
        for locale in manifest.supported_locales:
            relative_locale = f"{manifest.locales_dir}/{locale}.json"
            payload = _json_load(locales_dir / f"{locale}.json", issues, relative_locale)
            if payload is None:
                continue
            if not isinstance(payload, dict) or not all(
                isinstance(key, str) and key.strip() and isinstance(value, str) and value.strip()
                for key, value in payload.items()
            ):
                issues.append(
                    ValidationIssue(
                        "invalid_locale",
                        "locale file must be an object of non-empty string keys and values",
                        f"locales.{locale}",
                    )
                )
                continue
            locales[locale] = payload
            for key in sorted(required_name_keys - payload.keys()):
                issues.append(
                    ValidationIssue(
                        "missing_translation",
                        f"missing required translation key '{key}'",
                        f"locales.{locale}",
                    )
                )

    if team_planner is not None:
        mapped_ids = set(team_planner.champion_ids)
        for champion_id in sorted(mapped_ids - champion_ids):
            issues.append(
                ValidationIssue(
                    "unknown_champion",
                    f"Team Planner mapping references unknown Champion '{champion_id}'",
                    "team_planner.champion_ids",
                )
            )
        if manifest.team_planner_supported:
            if team_planner.codec is None:
                issues.append(
                    ValidationIssue(
                        "missing_team_planner_codec",
                        "Team Planner support requires a codec",
                        "team_planner.codec",
                    )
                )
            for champion_id in sorted(champion_ids - mapped_ids):
                issues.append(
                    ValidationIssue(
                        "missing_team_planner_mapping",
                        f"Champion '{champion_id}' has no Team Planner mapping",
                        "team_planner.champion_ids",
                    )
                )

    required_generated_files = {
        "manifest.json",
        manifest.champions_file,
        manifest.traits_file,
        manifest.dynamic_traits_file,
        manifest.team_planner_file,
        *(f"{manifest.locales_dir}/{locale}.json" for locale in manifest.supported_locales),
    }

    if source_manifest is not None:
        _validate_hash_inventory(
            root=root,
            required_paths=required_generated_files,
            declared_hashes=source_manifest.generated_file_sha256,
            issues=issues,
            location="source_manifest.generated_file_sha256",
            missing_code="missing_generated_file_hash",
            unexpected_code="unexpected_generated_file_hash",
            mismatch_code="generated_file_hash_mismatch",
            unreadable_code="unreadable_file",
            item_label="generated file",
        )
        _validate_hash_inventory(
            root=root,
            required_paths=required_assets,
            declared_hashes=source_manifest.asset_sha256,
            issues=issues,
            location="source_manifest.asset_sha256",
            missing_code="missing_asset_hash",
            unexpected_code="unexpected_asset_hash",
            mismatch_code="asset_hash_mismatch",
            unreadable_code="unreadable_asset",
            item_label="asset",
        )

    expected_files = required_generated_files | required_assets | {manifest.source_manifest_file}
    _validate_package_inventory(root, expected_files, issues)

    sorted_issues = tuple(sorted(issues))
    if sorted_issues:
        return ValidationReport(root=root, issues=sorted_issues)

    if (
        champions is None
        or traits is None
        or dynamic_traits is None
        or team_planner is None
        or source_manifest is None
    ):
        return ValidationReport(
            root=root,
            issues=(
                ValidationIssue(
                    "internal_validation_error",
                    "validation completed without required parsed data",
                    str(root),
                ),
            ),
        )

    loaded_set = LoadedSet(
        root=root,
        manifest=manifest,
        champions=tuple(sorted(champions, key=lambda item: (item.display_order, item.id))),
        traits=tuple(sorted(traits, key=lambda item: (item.display_order, item.id))),
        dynamic_traits=tuple(sorted(dynamic_traits, key=lambda item: item.champion_id)),
        team_planner=team_planner,
        locales=locales,
        source_manifest=source_manifest,
    )
    return ValidationReport(root=root, issues=(), loaded_set=loaded_set)


def load_set_directory(root: Path) -> LoadedSet:
    """Return a fully validated Set or raise ``SetValidationError``."""

    report = validate_set_directory(root)
    if not report.is_valid or report.loaded_set is None:
        raise SetValidationError(report)
    return report.loaded_set


def discover_set_directories(parent: Path) -> tuple[Path, ...]:
    """Discover direct child directories that look like Set packages."""

    parent = Path(parent)
    if not parent.is_dir():
        return ()
    try:
        children = tuple(parent.iterdir())
    except OSError:
        return ()
    return tuple(
        sorted(
            (
                child
                for child in children
                if not is_link_like(child)
                and child.is_dir()
                and (child / "manifest.json").is_file()
            ),
            key=lambda path: path.name.casefold(),
        )
    )


def validate_all_sets(parent: Path) -> tuple[ValidationReport, ...]:
    """Validate every discoverable Set package below one parent directory."""

    return tuple(validate_set_directory(path) for path in discover_set_directories(parent))
