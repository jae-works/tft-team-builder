"""Deterministic Trait calculation for one validated Set and one Team List."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from .models import ChampionInstance, TeamList, TraitSelection
from .set_loader import LoadedSet
from .set_schema import (
    DynamicSelectionRule,
    DynamicSelectionScope,
    DynamicTraitDefinition,
    TraitActivationMode,
    TraitBreakpoint,
    TraitCountingMode,
)


@dataclass(frozen=True, slots=True)
class DynamicSelectionIssue:
    """One invalid or conflicting dynamic Trait selection."""

    code: str
    champion_id: str
    instance_ids: tuple[UUID, ...]
    selected_trait_ids: tuple[str, ...]
    affected_trait_ids: tuple[str, ...]
    message: str


@dataclass(frozen=True, slots=True)
class TraitResult:
    """UI-independent calculated state for one Trait with positive contribution."""

    trait_id: str
    count: int
    active_breakpoint: TraitBreakpoint | None
    next_breakpoint: TraitBreakpoint | None
    needed_for_next_breakpoint: int | None
    has_invalid_dynamic_selection: bool


@dataclass(frozen=True, slots=True)
class TraitCalculationResult:
    """Ordered positive Trait results plus dynamic-selection problems."""

    traits: tuple[TraitResult, ...]
    dynamic_issues: tuple[DynamicSelectionIssue, ...]


@dataclass(slots=True)
class _TraitContributors:
    champion_points: dict[str, int]
    instance_points: dict[UUID, int]


def calculate_traits(loaded_set: LoadedSet, team_list: TeamList) -> TraitCalculationResult:
    """Calculate Trait state for one List using only validated Set metadata."""

    if not isinstance(loaded_set, LoadedSet):
        raise TypeError("loaded_set must be a LoadedSet")
    if not isinstance(team_list, TeamList):
        raise TypeError("team_list must be a TeamList")
    team_list.validate_invariants()

    champions_by_id = loaded_set.champions_by_id
    dynamic_by_champion = {item.champion_id: item for item in loaded_set.dynamic_traits}
    contributors = {
        trait.id: _TraitContributors(champion_points={}, instance_points={})
        for trait in loaded_set.traits
    }
    placed_by_champion: dict[str, list[ChampionInstance]] = {}

    for slot in team_list.slots:
        champion = slot.champion
        if champion is None:
            continue
        definition = champions_by_id.get(champion.champion_id)
        if definition is None:
            raise ValueError(f"unknown Champion ID in List: {champion.champion_id}")
        placed_by_champion.setdefault(champion.champion_id, []).append(champion)
        for trait_id in definition.traits:
            _add_contribution(
                contributors[trait_id], champion, definition.trait_points.get(trait_id, 1)
            )

    issues: list[DynamicSelectionIssue] = []
    for champion_id, instances in placed_by_champion.items():
        rule = dynamic_by_champion.get(champion_id)
        if rule is None:
            continue
        if rule.selection_scope is DynamicSelectionScope.PER_INSTANCE:
            _apply_per_instance_rule(rule, instances, contributors, issues)
        else:
            _apply_per_champion_rule(rule, instances, contributors, issues)

    invalid_trait_ids = {
        trait_id
        for issue in issues
        for trait_id in issue.affected_trait_ids
        if trait_id in contributors
    }
    base_counts: dict[str, int] = {}
    for trait in loaded_set.traits:
        trait_contributors = contributors[trait.id]
        if trait.counting_mode is TraitCountingMode.UNIQUE_CHAMPION:
            base_counts[trait.id] = sum(trait_contributors.champion_points.values())
        else:
            base_counts[trait.id] = sum(trait_contributors.instance_points.values())

    results: list[TraitResult] = []
    for trait in sorted(loaded_set.traits, key=lambda item: (item.display_order, item.id)):
        count = base_counts[trait.id]
        if trait.derived_requirements:
            count = int(
                all(
                    base_counts.get(required_trait_id, 0) >= required_count
                    for required_trait_id, required_count in trait.derived_requirements.items()
                )
            )
        if count == 0:
            continue

        active = None
        next_breakpoint = None
        for breakpoint in trait.breakpoints:
            if trait.activation_mode is TraitActivationMode.EXACT:
                if breakpoint.count == count:
                    active = breakpoint
                elif breakpoint.count > count and next_breakpoint is None:
                    next_breakpoint = breakpoint
            elif breakpoint.count <= count:
                active = breakpoint
            elif next_breakpoint is None:
                next_breakpoint = breakpoint

        results.append(
            TraitResult(
                trait_id=trait.id,
                count=count,
                active_breakpoint=active,
                next_breakpoint=next_breakpoint,
                needed_for_next_breakpoint=(
                    None if next_breakpoint is None else next_breakpoint.count - count
                ),
                has_invalid_dynamic_selection=trait.id in invalid_trait_ids,
            )
        )

    return TraitCalculationResult(traits=tuple(results), dynamic_issues=tuple(issues))


def _add_contribution(
    contributors: _TraitContributors, champion: ChampionInstance, points: int = 1
) -> None:
    # UNIQUE_CHAMPION semantics use the strongest contribution for duplicate copies of one unit.
    contributors.champion_points[champion.champion_id] = max(
        points, contributors.champion_points.get(champion.champion_id, 0)
    )
    contributors.instance_points[champion.instance_id] = points


def _apply_per_instance_rule(
    rule: DynamicTraitDefinition,
    instances: list[ChampionInstance],
    contributors: dict[str, _TraitContributors],
    issues: list[DynamicSelectionIssue],
) -> None:
    for champion in instances:
        issue = validate_dynamic_selection(rule, champion.trait_selection, (champion.instance_id,))
        if issue is not None:
            issues.append(issue)
            continue
        for trait_id in champion.trait_selection.trait_ids:
            _add_contribution(contributors[trait_id], champion, rule.choice_points.get(trait_id, 1))


def _apply_per_champion_rule(
    rule: DynamicTraitDefinition,
    instances: list[ChampionInstance],
    contributors: dict[str, _TraitContributors],
    issues: list[DynamicSelectionIssue],
) -> None:
    individual_issues = [
        issue
        for champion in instances
        if (
            issue := validate_dynamic_selection(
                rule, champion.trait_selection, (champion.instance_id,)
            )
        )
        is not None
    ]
    if individual_issues:
        issues.extend(individual_issues)
        return

    # Selection order is persisted for stable round-trips, but dynamic Trait semantics are set-like.
    # Duplicate instances therefore agree when they choose the same Traits in a different order.
    selections = {frozenset(champion.trait_selection.trait_ids) for champion in instances}
    if len(selections) != 1:
        selected = tuple(sorted({trait_id for selection in selections for trait_id in selection}))
        issues.append(
            DynamicSelectionIssue(
                code="per_champion_conflict",
                champion_id=rule.champion_id,
                instance_ids=tuple(champion.instance_id for champion in instances),
                selected_trait_ids=selected,
                affected_trait_ids=tuple(rule.choices),
                message=(
                    "PER_CHAMPION dynamic Trait selections must match across duplicate Champions"
                ),
            )
        )
        return

    selected = next(iter(selections))
    for champion in instances:
        for trait_id in selected:
            _add_contribution(contributors[trait_id], champion, rule.choice_points.get(trait_id, 1))


def validate_dynamic_selection(
    rule: DynamicTraitDefinition,
    selection: TraitSelection,
    instance_ids: tuple[UUID, ...] = (),
) -> DynamicSelectionIssue | None:
    """Validate one dynamic Trait selection using the same rules as Trait calculation."""

    if not isinstance(rule, DynamicTraitDefinition):
        raise TypeError("rule must be a DynamicTraitDefinition")
    if not isinstance(selection, TraitSelection):
        raise TypeError("selection must be a TraitSelection")
    if not isinstance(instance_ids, tuple) or any(
        not isinstance(item, UUID) for item in instance_ids
    ):
        raise TypeError("instance_ids must be a tuple of UUID values")
    selected = selection.trait_ids
    count = len(selected)
    if rule.selection_rule is DynamicSelectionRule.NONE:
        if count == 0:
            return None
        return _issue(
            rule,
            instance_ids,
            selected,
            "invalid_selection_count",
            f"dynamic Trait selection requires no choices; received {count}",
        )

    unknown = tuple(trait_id for trait_id in selected if trait_id not in rule.choices)
    if unknown:
        return _issue(
            rule,
            instance_ids,
            selected,
            "invalid_choice",
            f"selection contains choices not allowed by the dynamic Trait rule: {unknown}",
        )

    valid = False
    expected = ""
    if rule.selection_rule is DynamicSelectionRule.EXACTLY_ONE:
        valid = count == 1
        expected = "exactly one choice"
    elif rule.selection_rule is DynamicSelectionRule.ZERO_OR_ONE:
        valid = count <= 1
        expected = "zero or one choice"
    elif rule.selection_rule is DynamicSelectionRule.ANY_NUMBER:
        valid = True
        expected = "any number of allowed choices"
    else:
        valid = count == rule.exact_count
        expected = f"exactly {rule.exact_count} choices"

    if valid:
        return None
    code = "missing_selection" if count == 0 else "invalid_selection_count"
    return _issue(
        rule,
        instance_ids,
        selected,
        code,
        f"dynamic Trait selection requires {expected}; received {count}",
    )


def _issue(
    rule: DynamicTraitDefinition,
    instance_ids: tuple[UUID, ...],
    selected: tuple[str, ...],
    code: str,
    message: str,
) -> DynamicSelectionIssue:
    affected = tuple(dict.fromkeys((*rule.choices, *selected)))
    return DynamicSelectionIssue(
        code=code,
        champion_id=rule.champion_id,
        instance_ids=instance_ids,
        selected_trait_ids=selected,
        affected_trait_ids=affected,
        message=message,
    )
