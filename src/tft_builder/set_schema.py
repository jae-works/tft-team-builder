"""Strict schemas for external and generated TFT Set package data."""

from __future__ import annotations

import re
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .constants import (
    SET_SCHEMA_VERSION,
    SOURCE_MANIFEST_SCHEMA_VERSION,
    SOURCE_SPEC_SCHEMA_VERSION,
)

ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$"
LOCALE_PATTERN = r"^[a-z]{2}(?:_[A-Z]{2})?$"
VERSION_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$"
_PORTABLE_PATH_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}

Identifier = Annotated[str, Field(min_length=1, pattern=ID_PATTERN)]
LocaleCode = Annotated[str, Field(min_length=2, pattern=LOCALE_PATTERN)]
NonEmptyText = Annotated[str, Field(min_length=1)]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


def validate_relative_path(value: str) -> str:
    """Require portable canonical POSIX-style paths inside a Set package.

    Runtime Set packages are generated once and consumed on multiple operating systems, so
    metadata paths intentionally use a smaller portable filename alphabet than arbitrary host
    filesystem paths. This avoids path traversal, platform separators, Windows reserved names
    and filenames that work on one development machine but cannot be created on Windows.
    """

    if not value or "\\" in value:
        raise ValueError("path must be a non-empty POSIX-style relative path")

    raw_parts = value.split("/")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in raw_parts):
        raise ValueError("path must stay inside the Set package and use canonical components")
    for part in raw_parts:
        if _PORTABLE_PATH_COMPONENT.fullmatch(part) is None:
            raise ValueError("path components must use portable ASCII filename characters")
        stem = part.split(".", 1)[0].upper()
        if stem in _WINDOWS_RESERVED_NAMES:
            raise ValueError("path must not use a Windows reserved filename")

    return value


def _paths_overlap(first: str, second: str) -> bool:
    first_path = PurePosixPath(first)
    second_path = PurePosixPath(second)
    return (
        first_path == second_path
        or first_path in second_path.parents
        or second_path in first_path.parents
    )


class StrictModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        str_strip_whitespace=True,
        validate_default=True,
    )


class TraitCountingMode(StrEnum):
    UNIQUE_CHAMPION = "UNIQUE_CHAMPION"
    UNIQUE_INSTANCE = "UNIQUE_INSTANCE"
    CUSTOM_SET_RULE = "CUSTOM_SET_RULE"


class DynamicSelectionRule(StrEnum):
    NONE = "NONE"
    EXACTLY_ONE = "EXACTLY_ONE"
    ZERO_OR_ONE = "ZERO_OR_ONE"
    ANY_NUMBER = "ANY_NUMBER"
    EXACTLY_N = "EXACTLY_N"


class DynamicSelectionScope(StrEnum):
    PER_CHAMPION = "PER_CHAMPION"
    PER_INSTANCE = "PER_INSTANCE"


class SetManifest(StrictModel):
    schema_version: Literal[SET_SCHEMA_VERSION]
    set_id: Identifier
    display_name_key: Identifier
    revision: Annotated[str, Field(min_length=1, pattern=VERSION_PATTERN)]
    default_locale: LocaleCode
    supported_locales: Annotated[list[LocaleCode], Field(min_length=1)]
    champions_file: str = "data/champions.json"
    traits_file: str = "data/traits.json"
    dynamic_traits_file: str = "data/dynamic_traits.json"
    team_planner_file: str = "data/team_planner.json"
    source_manifest_file: str = "source_manifest.json"
    locales_dir: str = "locales"
    assets_dir: str = "assets"
    team_planner_supported: Annotated[bool, Field(strict=True)] = False

    _validate_champions_file = field_validator("champions_file")(validate_relative_path)
    _validate_traits_file = field_validator("traits_file")(validate_relative_path)
    _validate_dynamic_traits_file = field_validator("dynamic_traits_file")(validate_relative_path)
    _validate_team_planner_file = field_validator("team_planner_file")(validate_relative_path)
    _validate_source_manifest_file = field_validator("source_manifest_file")(validate_relative_path)
    _validate_locales_dir = field_validator("locales_dir")(validate_relative_path)
    _validate_assets_dir = field_validator("assets_dir")(validate_relative_path)

    @model_validator(mode="after")
    def validate_layout(self) -> SetManifest:
        if len(self.supported_locales) != len(set(self.supported_locales)):
            raise ValueError("supported_locales must not contain duplicates")
        if self.default_locale not in self.supported_locales:
            raise ValueError("default_locale must be present in supported_locales")

        metadata_files = (
            "manifest.json",
            self.champions_file,
            self.traits_file,
            self.dynamic_traits_file,
            self.team_planner_file,
            self.source_manifest_file,
        )
        for index, first in enumerate(metadata_files):
            for second in metadata_files[index + 1 :]:
                if _paths_overlap(first, second):
                    raise ValueError("Set metadata file paths must not overlap")

        if _paths_overlap(self.assets_dir, self.locales_dir):
            raise ValueError("assets_dir and locales_dir must not overlap")
        for metadata_file in metadata_files:
            if _paths_overlap(metadata_file, self.assets_dir):
                raise ValueError("Set metadata files must not overlap assets_dir")
            if _paths_overlap(metadata_file, self.locales_dir):
                raise ValueError("Set metadata files must not overlap locales_dir")
        return self


class TraitBreakpoint(StrictModel):
    count: Annotated[int, Field(ge=1, strict=True)]
    style: Identifier


class TraitDefinition(StrictModel):
    id: Identifier
    name_key: Identifier
    icon: str
    display_order: Annotated[int, Field(ge=0, strict=True)]
    breakpoints: Annotated[list[TraitBreakpoint], Field(min_length=1)]
    counting_mode: TraitCountingMode = TraitCountingMode.UNIQUE_CHAMPION

    _validate_icon = field_validator("icon")(validate_relative_path)

    @model_validator(mode="after")
    def validate_breakpoints(self) -> TraitDefinition:
        counts = [breakpoint.count for breakpoint in self.breakpoints]
        if counts != sorted(counts) or len(counts) != len(set(counts)):
            raise ValueError("Trait breakpoints must have strictly increasing counts")
        return self


class ChampionDefinition(StrictModel):
    id: Identifier
    name_key: Identifier
    cost: Annotated[int, Field(ge=0, strict=True)]
    traits: list[Identifier]
    image: str
    display_order: Annotated[int, Field(ge=0, strict=True)]
    search_aliases: list[str] = Field(default_factory=list)

    _validate_image = field_validator("image")(validate_relative_path)

    @model_validator(mode="after")
    def validate_unique_values(self) -> ChampionDefinition:
        if len(self.traits) != len(set(self.traits)):
            raise ValueError("Champion traits must not contain duplicates")
        if any(not alias.strip() for alias in self.search_aliases):
            raise ValueError("search_aliases must not contain empty values")
        if len(self.search_aliases) != len(set(self.search_aliases)):
            raise ValueError("search_aliases must not contain duplicates")
        return self


class DynamicTraitDefinition(StrictModel):
    champion_id: Identifier
    selection_rule: DynamicSelectionRule
    choices: list[Identifier] = Field(default_factory=list)
    selection_scope: DynamicSelectionScope = DynamicSelectionScope.PER_INSTANCE
    exact_count: Annotated[int, Field(strict=True)] | None = None

    @model_validator(mode="after")
    def validate_rule(self) -> DynamicTraitDefinition:
        if len(self.choices) != len(set(self.choices)):
            raise ValueError("dynamic Trait choices must not contain duplicates")

        if self.selection_rule is DynamicSelectionRule.NONE:
            if self.choices or self.exact_count is not None:
                raise ValueError("NONE selection must not define choices or exact_count")
            return self

        if not self.choices:
            raise ValueError("dynamic Trait selection requires at least one choice")

        if self.selection_rule is DynamicSelectionRule.EXACTLY_N:
            if self.exact_count is None:
                raise ValueError("EXACTLY_N requires exact_count")
            if self.exact_count < 1 or self.exact_count > len(self.choices):
                raise ValueError("exact_count must be between 1 and the number of choices")
        elif self.exact_count is not None:
            raise ValueError("exact_count is only valid with EXACTLY_N")

        return self


class TeamPlannerData(StrictModel):
    codec: Identifier | None = None
    champion_ids: dict[Identifier, NonEmptyText] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_mapping(self) -> TeamPlannerData:
        if self.codec is None and self.champion_ids:
            raise ValueError("champion_ids require a Team Planner codec")
        values = list(self.champion_ids.values())
        if len(values) != len(set(values)):
            raise ValueError("Team Planner IDs must be unique")
        return self


class SourceManifest(StrictModel):
    schema_version: Literal[SOURCE_MANIFEST_SCHEMA_VERSION]
    source_type: Identifier
    source_sha256: Sha256
    generated_file_sha256: dict[str, Sha256]
    asset_sha256: dict[str, Sha256]

    @field_validator("generated_file_sha256", "asset_sha256")
    @classmethod
    def validate_hashed_paths(cls, value: dict[str, str]) -> dict[str, str]:
        for path in value:
            validate_relative_path(path)
        return value


class LocalSetSpec(StrictModel):
    """Offline source specification used by the deterministic Set builder."""

    schema_version: Literal[SOURCE_SPEC_SCHEMA_VERSION]
    manifest: SetManifest
    champions: list[ChampionDefinition]
    traits: list[TraitDefinition]
    dynamic_traits: list[DynamicTraitDefinition] = Field(default_factory=list)
    team_planner: TeamPlannerData = Field(default_factory=TeamPlannerData)
    locales: dict[LocaleCode, dict[Identifier, NonEmptyText]]
    assets: dict[str, str]

    @field_validator("assets")
    @classmethod
    def validate_assets(cls, value: dict[str, str]) -> dict[str, str]:
        for target, source in value.items():
            validate_relative_path(target)
            validate_relative_path(source)
        return value

    @model_validator(mode="after")
    def validate_package_inventory(self) -> LocalSetSpec:
        expected_locales = set(self.manifest.supported_locales)
        actual_locales = set(self.locales)
        if actual_locales != expected_locales:
            missing = sorted(expected_locales - actual_locales)
            unexpected = sorted(actual_locales - expected_locales)
            raise ValueError(
                "locale inventory must match supported_locales; "
                f"missing={missing}, unexpected={unexpected}"
            )

        required_name_keys = {self.manifest.display_name_key}
        required_name_keys.update(champion.name_key for champion in self.champions)
        required_name_keys.update(trait.name_key for trait in self.traits)
        for locale, catalog in self.locales.items():
            missing_keys = sorted(required_name_keys - catalog.keys())
            if missing_keys:
                raise ValueError(
                    f"locale '{locale}' is missing required translation keys: {missing_keys}"
                )

        assets_root = PurePosixPath(self.manifest.assets_dir)
        asset_targets = tuple(PurePosixPath(target) for target in self.assets)
        for target in asset_targets:
            if assets_root not in target.parents:
                raise ValueError("all generated asset targets must be stored under assets_dir")

        for index, first in enumerate(asset_targets):
            for second in asset_targets[index + 1 :]:
                if first in second.parents or second in first.parents:
                    raise ValueError("generated asset file paths must not overlap")

        referenced_assets = {champion.image for champion in self.champions}
        referenced_assets.update(trait.icon for trait in self.traits)
        mapped_assets = set(self.assets)
        missing_assets = sorted(referenced_assets - mapped_assets)
        unexpected_assets = sorted(mapped_assets - referenced_assets)
        if missing_assets:
            raise ValueError(f"source spec has no asset mapping for: {missing_assets}")
        if unexpected_assets:
            raise ValueError(f"source spec maps unreferenced runtime assets: {unexpected_assets}")

        return self
