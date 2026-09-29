"""Shared read-only presentation helpers for validated Set data."""

from __future__ import annotations

from pathlib import Path

from .models import TraitSelection
from .search import normalize_search_text
from .set_loader import LoadedSet
from .set_schema import ChampionDefinition, DynamicTraitDefinition


def localized_text(loaded_set: LoadedSet, key: str) -> str:
    """Return default-locale text, falling back to the stable localization key."""

    locale = loaded_set.locales.get(loaded_set.manifest.default_locale, {})
    return locale.get(key, key)


def set_display_name(loaded_set: LoadedSet) -> str:
    """Return the localized user-facing name for a validated Set."""

    return localized_text(loaded_set, loaded_set.manifest.display_name_key)


def asset_source(loaded_set: LoadedSet, assets_dir: Path, relative_path: str) -> str:
    """Return a Flet asset path relative to the configured application assets root."""

    absolute = (loaded_set.root / relative_path).resolve()
    try:
        return absolute.relative_to(assets_dir.resolve()).as_posix()
    except ValueError as error:
        raise ValueError(
            "Set asset is outside the configured application assets directory"
        ) from error


def _dynamic_rule(
    loaded_set: LoadedSet, champion: ChampionDefinition
) -> DynamicTraitDefinition | None:
    """Return the optional data-driven dynamic Trait rule for one Champion."""

    return next(
        (rule for rule in loaded_set.dynamic_traits if rule.champion_id == champion.id),
        None,
    )


def champion_trait_ids(loaded_set: LoadedSet, champion: ChampionDefinition) -> tuple[str, ...]:
    """Return native and possible dynamic Trait IDs for one Champion without duplicates."""

    dynamic = _dynamic_rule(loaded_set, champion)
    dynamic_choices = () if dynamic is None else tuple(dynamic.choices)
    return tuple(dict.fromkeys((*champion.traits, *dynamic_choices)))


def champion_portrait_path(
    loaded_set: LoadedSet,
    champion: ChampionDefinition,
    selection: TraitSelection,
) -> str:
    """Return a selected dynamic portrait or the logical Champion's base portrait."""

    dynamic = _dynamic_rule(loaded_set, champion)
    if dynamic is None or len(selection.trait_ids) != 1:
        return champion.image
    return dynamic.choice_images.get(selection.trait_ids[0], champion.image)


def dynamic_selection_text(
    loaded_set: LoadedSet,
    champion: ChampionDefinition,
    selection: TraitSelection,
) -> str:
    """Return localized selected dynamic Trait names in the rule's stable choice order."""

    dynamic = _dynamic_rule(loaded_set, champion)
    if dynamic is None or not selection.trait_ids:
        return ""
    selected = set(selection.trait_ids)
    traits_by_id = loaded_set.traits_by_id
    return ", ".join(
        localized_text(loaded_set, traits_by_id[trait_id].name_key)
        for trait_id in dynamic.choices
        if trait_id in selected
    )


def champion_details_text(loaded_set: LoadedSet, champion: ChampionDefinition) -> str:
    """Return compact hover details from Set data without inventing game-specific prose."""

    traits_by_id = loaded_set.traits_by_id
    traits = [
        localized_text(loaded_set, traits_by_id[trait_id].name_key)
        for trait_id in champion_trait_ids(loaded_set, champion)
    ]
    trait_text = ", ".join(traits) if traits else "No Traits"
    return (
        f"{localized_text(loaded_set, champion.name_key)} | "
        f"Cost {champion.cost} | Traits: {trait_text}"
    )


def champion_matches_query(loaded_set: LoadedSet, champion: ChampionDefinition, query: str) -> bool:
    """Return whether one Champion matches normalized name, alias or Trait text."""

    needle = normalize_search_text(query)
    if not needle:
        return True
    traits_by_id = loaded_set.traits_by_id
    terms = [
        localized_text(loaded_set, champion.name_key),
        *champion.search_aliases,
        *(
            localized_text(loaded_set, traits_by_id[trait_id].name_key)
            for trait_id in champion_trait_ids(loaded_set, champion)
        ),
    ]
    return any(needle in normalize_search_text(term) for term in terms)
