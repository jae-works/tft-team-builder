"""Strict schemas for external/generated TFT Set package data."""

from __future__ import annotations

from enum import StrEnum
from pathlib import PurePosixPath
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .constants import SET_SCHEMA_VERSION, SOURCE_MANIFEST_SCHEMA_VERSION, SOURCE_SPEC_SCHEMA_VERSION

ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$"
LOCALE_PATTERN = r"^[a-z]{2}(?:_[A-Z]{2})?$"
VERSION_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9_.+-]*$"

Identifier = Annotated[str, Field(min_length=1, pattern=ID_PATTERN)]
LocaleCode = Annotated[str, Field(min_length=2, pattern=LOCALE_PATTERN)]


def validate_relative_path(value: str) -> str:
    """Reject absolute paths, traversal and platform separators in package metadata."""

    if not value or "\\" in value:
        raise ValueError("path must be a non-empty POSIX-style relative path")
    raw_parts = value.split("/")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in raw_parts):
        raise ValueError("path must stay inside the Set package and use canonical components")
    if path.as_posix() != value:
        raise ValueError("path must use canonical POSIX spelling")
    return value


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, str_strip_whitespace=True)


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
    team_planner_supported: bool = False

    _validate_champions_file = field_validator("champions_file")(validate_relative_path)
    _validate_traits_file = field_validator("traits_file")(validate_relative_path)
    _validate_dynamic_traits_file = field_validator("dynamic_traits_file")(validate_relative_path)
    _validate_team_planner_file = field_validator("team_planner_file")(validate_relative_path)
    _validate_source_manifest_file = field_validator("source_manifest_file")(validate_relative_path)
    _validate_locales_dir = field_validator("locales_dir")(validate_relative_path)
    _validate_assets_dir = field_validator("assets_dir")(validate_relative_path)

    @model_validator(mode="after")
    def validate_locales(self) -> SetManifest:
        if len(self.supported_locales) != len(set(self.supported_locales)):
            raise ValueError("supported_locales must not contain duplicates")
        if self.default_locale not in self.supported_locales:
            raise ValueError("default_locale must be present in supported_locales")
        return self


class TraitBreakpoint(StrictModel):
    count: Annotated[int, Field(ge=1)]
    style: Identifier


class TraitDefinition(StrictModel):
    id: Identifier
    name_key: Identifier
    icon: str
    display_order: int
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
    cost: Annotated[int, Field(ge=0)]
    traits: list[Identifier]
    image: str
    display_order: int
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
    exact_count: int | None = None

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
    champion_ids: dict[Identifier, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_mapping(self) -> TeamPlannerData:
        if self.codec is None and self.champion_ids:
            raise ValueError("champion_ids require a Team Planner codec")
        if any(not value.strip() for value in self.champion_ids.values()):
            raise ValueError("Team Planner IDs must not be empty")
        return self


class SourceManifest(StrictModel):
    schema_version: Literal[SOURCE_MANIFEST_SCHEMA_VERSION]
    source_type: Identifier
    source_sha256: Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
    generated_file_sha256: dict[str, Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]]
    asset_sha256: dict[str, Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]]

    @field_validator("generated_file_sha256", "asset_sha256")
    @classmethod
    def validate_hashed_paths(cls, value: dict[str, str]) -> dict[str, str]:
        for path in value:
            validate_relative_path(path)
        return value


class LocalSetSpec(StrictModel):
    """Offline source specification used by the Block 1 deterministic builder."""

    schema_version: Literal[SOURCE_SPEC_SCHEMA_VERSION]
    manifest: SetManifest
    champions: list[ChampionDefinition]
    traits: list[TraitDefinition]
    dynamic_traits: list[DynamicTraitDefinition] = Field(default_factory=list)
    team_planner: TeamPlannerData = Field(default_factory=TeamPlannerData)
    locales: dict[LocaleCode, dict[str, str]]
    assets: dict[str, str]

    @field_validator("assets")
    @classmethod
    def validate_assets(cls, value: dict[str, str]) -> dict[str, str]:
        for target, source in value.items():
            validate_relative_path(target)
            validate_relative_path(source)
        return value
