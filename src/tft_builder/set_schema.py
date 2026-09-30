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
type ScalarValue = str | int | float | bool | None


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


class TraitActivationMode(StrEnum):
    AT_LEAST = "AT_LEAST"
    EXACT = "EXACT"


class DynamicSelectionRule(StrEnum):
    NONE = "NONE"
    EXACTLY_ONE = "EXACTLY_ONE"
    ZERO_OR_ONE = "ZERO_OR_ONE"
    ANY_NUMBER = "ANY_NUMBER"
    EXACTLY_N = "EXACTLY_N"


class DynamicSelectionScope(StrEnum):
    PER_CHAMPION = "PER_CHAMPION"
    PER_INSTANCE = "PER_INSTANCE"


class ItemCategory(StrEnum):
    COMPONENT = "COMPONENT"
    CRAFTABLE = "CRAFTABLE"
    EMBLEM = "EMBLEM"
    ARTIFACT = "ARTIFACT"
    RADIANT = "RADIANT"
    SUPPORT = "SUPPORT"
    CONSUMABLE = "CONSUMABLE"
    OTHER = "OTHER"


class CandidateKind(StrEnum):
    CHAMPION = "CHAMPION"
    TRAIT = "TRAIT"
    ITEM = "ITEM"


class CandidateStatus(StrEnum):
    INCLUDED = "INCLUDED"
    EXCLUDED = "EXCLUDED"


class SetManifest(StrictModel):
    schema_version: Literal[SET_SCHEMA_VERSION]
    set_id: Identifier
    display_name_key: Identifier
    revision: Annotated[str, Field(min_length=1, pattern=VERSION_PATTERN)]
    default_locale: LocaleCode
    supported_locales: Annotated[list[LocaleCode], Field(min_length=1)]
    champions_file: str = "data/champions.json"
    items_file: str = "data/items.json"
    traits_file: str = "data/traits.json"
    dynamic_traits_file: str = "data/dynamic_traits.json"
    team_planner_file: str = "data/team_planner.json"
    source_inventory_file: str = "reports/source_inventory.json"
    overview_file: str = "SET_OVERVIEW.md"
    source_manifest_file: str = "source_manifest.json"
    review_file: str | None = None
    review_report_file: str = "SET_REVIEW.md"
    locales_dir: str = "locales"
    assets_dir: str = "assets"
    team_planner_supported: Annotated[bool, Field(strict=True)] = False

    _validate_champions_file = field_validator("champions_file")(validate_relative_path)
    _validate_items_file = field_validator("items_file")(validate_relative_path)
    _validate_traits_file = field_validator("traits_file")(validate_relative_path)
    _validate_dynamic_traits_file = field_validator("dynamic_traits_file")(validate_relative_path)
    _validate_team_planner_file = field_validator("team_planner_file")(validate_relative_path)
    _validate_source_inventory_file = field_validator("source_inventory_file")(
        validate_relative_path
    )
    _validate_overview_file = field_validator("overview_file")(validate_relative_path)
    _validate_source_manifest_file = field_validator("source_manifest_file")(validate_relative_path)
    _validate_review_file = field_validator("review_file")(
        lambda value: None if value is None else validate_relative_path(value)
    )
    _validate_review_report_file = field_validator("review_report_file")(validate_relative_path)
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
            self.items_file,
            self.traits_file,
            self.dynamic_traits_file,
            self.team_planner_file,
            self.source_inventory_file,
            self.overview_file,
            self.source_manifest_file,
            *((self.review_file,) if self.review_file is not None else ()),
            self.review_report_file,
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
    description_key: Identifier | None = None


class TraitDefinition(StrictModel):
    id: Identifier
    name_key: Identifier
    description_key: Identifier | None = None
    icon: str
    display_order: Annotated[int, Field(ge=0, strict=True)]
    breakpoints: Annotated[list[TraitBreakpoint], Field(min_length=1)]
    counting_mode: TraitCountingMode = TraitCountingMode.UNIQUE_CHAMPION
    activation_mode: TraitActivationMode = TraitActivationMode.AT_LEAST
    derived_requirements: dict[Identifier, Annotated[int, Field(ge=1, strict=True)]] = Field(
        default_factory=dict
    )

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
    trait_points: dict[Identifier, Annotated[int, Field(ge=1, strict=True)]] = Field(
        default_factory=dict
    )
    board_slots: Annotated[int, Field(ge=1, strict=True)] = 1
    image: str
    display_order: Annotated[int, Field(ge=0, strict=True)]
    search_aliases: list[str] = Field(default_factory=list)

    _validate_image = field_validator("image")(validate_relative_path)

    @model_validator(mode="after")
    def validate_unique_values(self) -> ChampionDefinition:
        if len(self.traits) != len(set(self.traits)):
            raise ValueError("Champion traits must not contain duplicates")
        if set(self.trait_points) - set(self.traits):
            raise ValueError("trait_points keys must also be present in traits")
        if any(not alias.strip() for alias in self.search_aliases):
            raise ValueError("search_aliases must not contain empty values")
        if len(self.search_aliases) != len(set(self.search_aliases)):
            raise ValueError("search_aliases must not contain duplicates")
        return self


class ItemDefinition(StrictModel):
    id: Identifier
    name_key: Identifier
    description_key: Identifier | None = None
    icon: str
    category: ItemCategory
    composition: list[Identifier] = Field(default_factory=list)
    associated_traits: list[Identifier] = Field(default_factory=list)
    display_order: Annotated[int, Field(ge=0, strict=True)]
    tags: list[Identifier] = Field(default_factory=list)

    _validate_icon = field_validator("icon")(validate_relative_path)

    @model_validator(mode="after")
    def validate_unique_values(self) -> ItemDefinition:
        # Recipes may legitimately use two copies of the same component, so composition keeps
        # multiplicity. Metadata-only collections still reject duplicates because repetition
        # carries no meaning there.
        for field_name, values in (
            ("associated_traits", self.associated_traits),
            ("tags", self.tags),
        ):
            if len(values) != len(set(values)):
                raise ValueError(f"{field_name} must not contain duplicates")
        return self


class DynamicTraitDefinition(StrictModel):
    champion_id: Identifier
    selection_rule: DynamicSelectionRule
    choices: list[Identifier] = Field(default_factory=list)
    selection_scope: DynamicSelectionScope = DynamicSelectionScope.PER_INSTANCE
    exact_count: Annotated[int, Field(strict=True)] | None = None
    choice_points: dict[Identifier, Annotated[int, Field(ge=1, strict=True)]] = Field(
        default_factory=dict
    )
    choice_images: dict[Identifier, str] = Field(default_factory=dict)

    @field_validator("choice_images")
    @classmethod
    def validate_choice_images(cls, value: dict[str, str]) -> dict[str, str]:
        # Dynamic choices may optionally select a Champion portrait. Keeping the path in Set
        # data lets Lux-like units change appearance without Champion-name branches in the UI.
        for path in value.values():
            validate_relative_path(path)
        return value

    @model_validator(mode="after")
    def validate_rule(self) -> DynamicTraitDefinition:
        if len(self.choices) != len(set(self.choices)):
            raise ValueError("dynamic Trait choices must not contain duplicates")
        if set(self.choice_points) - set(self.choices):
            raise ValueError("choice_points keys must also be present in choices")
        if set(self.choice_images) - set(self.choices):
            raise ValueError("choice_images keys must also be present in choices")

        if self.selection_rule is DynamicSelectionRule.NONE:
            if (
                self.choices
                or self.exact_count is not None
                or self.choice_points
                or self.choice_images
            ):
                raise ValueError(
                    "NONE selection must not define choices, exact_count, choice_points "
                    "or choice_images"
                )
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


class ReviewCostCount(StrictModel):
    cost: Annotated[int, Field(ge=0, strict=True)]
    count: Annotated[int, Field(ge=0, strict=True)]


class ReviewItemCategoryCount(StrictModel):
    category: ItemCategory
    count: Annotated[int, Field(ge=0, strict=True)]


class ReviewSourceCandidateCount(StrictModel):
    kind: CandidateKind
    status: CandidateStatus
    count: Annotated[int, Field(ge=0, strict=True)]


class ReviewPngDimensionCount(StrictModel):
    width: Annotated[int, Field(ge=1, strict=True)]
    height: Annotated[int, Field(ge=1, strict=True)]
    count: Annotated[int, Field(ge=0, strict=True)]


class ReviewChampionExpectation(StrictModel):
    champion_id: Identifier
    board_slots: Annotated[int, Field(ge=1, strict=True)] | None = None
    trait_points: dict[Identifier, Annotated[int, Field(ge=1, strict=True)]] = Field(
        default_factory=dict
    )


class ReviewTraitExpectation(StrictModel):
    trait_id: Identifier
    activation_mode: TraitActivationMode | None = None
    derived_requirements: dict[Identifier, Annotated[int, Field(ge=1, strict=True)]] = Field(
        default_factory=dict
    )


class ReviewDynamicTraitExpectation(StrictModel):
    champion_id: Identifier
    selection_rule: DynamicSelectionRule
    selection_scope: DynamicSelectionScope
    choices: list[Identifier]
    exact_count: Annotated[int, Field(ge=1, strict=True)] | None = None
    choice_points: dict[Identifier, Annotated[int, Field(ge=1, strict=True)]] = Field(
        default_factory=dict
    )
    choice_images: Literal["ANY", "NONE", "ALL"] = "ANY"

    @model_validator(mode="after")
    def validate_expectation(self) -> ReviewDynamicTraitExpectation:
        if len(self.choices) != len(set(self.choices)):
            raise ValueError("review dynamic choices must not contain duplicates")
        if set(self.choice_points) - set(self.choices):
            raise ValueError("review choice_points keys must also be present in choices")
        if self.selection_rule is DynamicSelectionRule.EXACTLY_N:
            if self.exact_count is None:
                raise ValueError("EXACTLY_N review expectation requires exact_count")
        elif self.exact_count is not None:
            raise ValueError("review exact_count is only valid with EXACTLY_N")
        return self


class ReviewLocaleExpectation(StrictModel):
    locale: LocaleCode
    key: Identifier
    value: NonEmptyText


class SetReviewPolicy(StrictModel):
    """Set-owned reviewed invariants used by the generic package checker."""

    expected_set_id: Identifier
    expected_revision: NonEmptyText
    champion_count: Annotated[int, Field(ge=0, strict=True)]
    trait_count: Annotated[int, Field(ge=0, strict=True)]
    item_count: Annotated[int, Field(ge=0, strict=True)]
    dynamic_trait_count: Annotated[int, Field(ge=0, strict=True)]
    champion_cost_counts: list[ReviewCostCount] = Field(default_factory=list)
    item_category_counts: list[ReviewItemCategoryCount] = Field(default_factory=list)
    champion_expectations: list[ReviewChampionExpectation] = Field(default_factory=list)
    trait_expectations: list[ReviewTraitExpectation] = Field(default_factory=list)
    dynamic_trait_expectations: list[ReviewDynamicTraitExpectation] = Field(default_factory=list)
    team_planner_codec: Identifier | None = None
    team_planner_champion_count: Annotated[int, Field(ge=0, strict=True)] | None = None
    source_candidate_counts: list[ReviewSourceCandidateCount] = Field(default_factory=list)
    png_count: Annotated[int, Field(ge=0, strict=True)]
    source_manifest_asset_count: Annotated[int, Field(ge=0, strict=True)]
    provenance_source_count: Annotated[int, Field(ge=0, strict=True)]
    png_dimensions: list[ReviewPngDimensionCount] = Field(default_factory=list)
    allowed_duplicate_asset_groups: list[list[str]] = Field(default_factory=list)
    reject_locale_markup: Annotated[bool, Field(strict=True)] = True
    locale_expectations: list[ReviewLocaleExpectation] = Field(default_factory=list)
    minimum_max_champion_traits: Annotated[int, Field(ge=0, strict=True)] = 0
    minimum_max_trait_breakpoints: Annotated[int, Field(ge=0, strict=True)] = 0

    @field_validator("allowed_duplicate_asset_groups")
    @classmethod
    def validate_duplicate_groups(cls, value: list[list[str]]) -> list[list[str]]:
        for group in value:
            if len(group) < 2 or len(group) != len(set(group)):
                raise ValueError("duplicate asset groups must contain at least two unique paths")
            for path in group:
                validate_relative_path(path)
        return value


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


class SourceRecord(StrictModel):
    id: Identifier
    url: NonEmptyText
    revision: NonEmptyText
    locale: LocaleCode | None = None
    sha256: Sha256
    byte_length: Annotated[int, Field(ge=1, strict=True)]


class SourceCandidate(StrictModel):
    kind: CandidateKind
    source_id: NonEmptyText
    status: CandidateStatus
    target_id: Identifier | None = None
    reason: NonEmptyText | None = None

    @model_validator(mode="after")
    def validate_status(self) -> SourceCandidate:
        if self.status is CandidateStatus.INCLUDED:
            if self.target_id is None or self.reason is not None:
                raise ValueError("INCLUDED candidates require target_id and no reason")
        elif self.target_id is not None or self.reason is None:
            raise ValueError("EXCLUDED candidates require reason and no target_id")
        return self


class SourceManifest(StrictModel):
    schema_version: Literal[SOURCE_MANIFEST_SCHEMA_VERSION]
    source_type: Identifier
    source_sha256: Sha256
    generated_file_sha256: dict[str, Sha256]
    asset_sha256: dict[str, Sha256]
    sources: list[SourceRecord] = Field(default_factory=list)

    @field_validator("generated_file_sha256", "asset_sha256")
    @classmethod
    def validate_hashed_paths(cls, value: dict[str, str]) -> dict[str, str]:
        for path in value:
            validate_relative_path(path)
        return value

    @model_validator(mode="after")
    def validate_source_ids(self) -> SourceManifest:
        source_ids = [record.id for record in self.sources]
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("sources must not contain duplicate IDs")
        return self


class LocalSetSpec(StrictModel):
    """Offline source specification used by the deterministic Set builder."""

    schema_version: Literal[SOURCE_SPEC_SCHEMA_VERSION]
    manifest: SetManifest
    champions: list[ChampionDefinition]
    items: list[ItemDefinition] = Field(default_factory=list)
    traits: list[TraitDefinition]
    dynamic_traits: list[DynamicTraitDefinition] = Field(default_factory=list)
    team_planner: TeamPlannerData = Field(default_factory=TeamPlannerData)
    source_inventory: list[SourceCandidate] = Field(default_factory=list)
    review: SetReviewPolicy | None = None
    sources: list[SourceRecord] = Field(default_factory=list)
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
        if (self.manifest.review_file is None) != (self.review is None):
            raise ValueError(
                "manifest.review_file and review data must either both be set or both be absent"
            )

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
        required_name_keys.update(item.name_key for item in self.items)
        required_name_keys.update(trait.name_key for trait in self.traits)
        required_name_keys.update(
            key
            for key in (
                *(item.description_key for item in self.items),
                *(trait.description_key for trait in self.traits),
            )
            if key is not None
        )
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
        referenced_assets.update(item.icon for item in self.items)
        referenced_assets.update(trait.icon for trait in self.traits)
        referenced_assets.update(
            image
            for dynamic_trait in self.dynamic_traits
            for image in dynamic_trait.choice_images.values()
        )
        mapped_assets = set(self.assets)
        missing_assets = sorted(referenced_assets - mapped_assets)
        unexpected_assets = sorted(mapped_assets - referenced_assets)
        if missing_assets:
            raise ValueError(f"source spec has no asset mapping for: {missing_assets}")
        if unexpected_assets:
            raise ValueError(f"source spec maps unreferenced runtime assets: {unexpected_assets}")

        return self
