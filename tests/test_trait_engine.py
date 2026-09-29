from __future__ import annotations

from pathlib import Path

import pytest

from tft_builder.models import ChampionInstance, Slot, TeamList, TraitSelection
from tft_builder.set_loader import LoadedSet
from tft_builder.set_schema import (
    ChampionDefinition,
    DynamicSelectionRule,
    DynamicSelectionScope,
    DynamicTraitDefinition,
    SetManifest,
    SourceManifest,
    TeamPlannerData,
    TraitActivationMode,
    TraitBreakpoint,
    TraitCountingMode,
    TraitDefinition,
)
from tft_builder.trait_engine import calculate_traits, validate_dynamic_selection


def trait(
    trait_id: str,
    *,
    order: int,
    mode: TraitCountingMode = TraitCountingMode.UNIQUE_CHAMPION,
    activation: TraitActivationMode = TraitActivationMode.AT_LEAST,
    breakpoints: tuple[int, ...] = (1, 2, 4),
    derived_requirements: dict[str, int] | None = None,
) -> TraitDefinition:
    return TraitDefinition(
        id=trait_id,
        name_key=f"trait.{trait_id}.name",
        icon=f"assets/traits/{trait_id}.png",
        display_order=order,
        counting_mode=mode,
        activation_mode=activation,
        derived_requirements={} if derived_requirements is None else derived_requirements,
        breakpoints=[TraitBreakpoint(count=count, style=f"tier_{count}") for count in breakpoints],
    )


def champion(champion_id: str, *trait_ids: str, order: int = 0) -> ChampionDefinition:
    return ChampionDefinition(
        id=champion_id,
        name_key=f"champion.{champion_id}.name",
        cost=1,
        traits=list(trait_ids),
        image=f"assets/champions/{champion_id}.png",
        display_order=order,
    )


def dynamic(
    champion_id: str,
    rule: DynamicSelectionRule,
    choices: tuple[str, ...] = (),
    *,
    scope: DynamicSelectionScope = DynamicSelectionScope.PER_INSTANCE,
    exact_count: int | None = None,
) -> DynamicTraitDefinition:
    return DynamicTraitDefinition(
        champion_id=champion_id,
        selection_rule=rule,
        choices=list(choices),
        selection_scope=scope,
        exact_count=exact_count,
    )


def loaded_set(
    *,
    champions: tuple[ChampionDefinition, ...],
    traits: tuple[TraitDefinition, ...],
    dynamic_traits: tuple[DynamicTraitDefinition, ...] = (),
) -> LoadedSet:
    return LoadedSet(
        root=Path(),
        manifest=SetManifest(
            schema_version=5,
            set_id="test_set",
            display_name_key="set.name",
            revision="1.0.0",
            default_locale="en_US",
            supported_locales=["en_US"],
        ),
        champions=champions,
        traits=traits,
        dynamic_traits=dynamic_traits,
        items=(),
        source_inventory=(),
        team_planner=TeamPlannerData(),
        locales={"en_US": {}},
        source_manifest=SourceManifest(
            schema_version=2,
            source_type="test",
            source_sha256="0" * 64,
            generated_file_sha256={},
            asset_sha256={},
        ),
    )


def team_list(*items: tuple[str, tuple[str, ...]] | None) -> TeamList:
    slots: list[Slot] = []
    for index, item in enumerate(items):
        if item is None:
            slots.append(Slot(index))
            continue
        champion_id, selected = item
        slots.append(
            Slot(
                index,
                ChampionInstance(
                    champion_id,
                    trait_selection=TraitSelection(selected),
                ),
            )
        )
    return TeamList(name="Main", slots=slots)


def result_by_id(result) -> dict[str, object]:
    return {item.trait_id: item for item in result.traits}


def test_calculate_traits_requires_loaded_set_and_team_list() -> None:
    set_data = loaded_set(champions=(champion("a", "x"),), traits=(trait("x", order=0),))
    with pytest.raises(TypeError, match="LoadedSet"):
        calculate_traits(object(), team_list(("a", ())))  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="TeamList"):
        calculate_traits(set_data, object())  # type: ignore[arg-type]


def test_calculate_traits_revalidates_list_invariants() -> None:
    set_data = loaded_set(champions=(champion("a", "x"),), traits=(trait("x", order=0),))
    current = team_list(("a", ()))
    current.slots[0].index = 1
    with pytest.raises(ValueError, match="contiguously"):
        calculate_traits(set_data, current)


def test_unknown_champion_id_is_reported_clearly() -> None:
    set_data = loaded_set(champions=(champion("a", "x"),), traits=(trait("x", order=0),))
    with pytest.raises(ValueError, match=r"unknown Champion ID.*missing"):
        calculate_traits(set_data, team_list(("missing", ())))


def test_zero_contribution_traits_are_hidden() -> None:
    set_data = loaded_set(champions=(champion("a", "x"),), traits=(trait("x", order=0),))
    result = calculate_traits(set_data, team_list(None))
    assert result.traits == ()
    assert result.dynamic_issues == ()


def test_native_unique_champion_deduplicates_duplicate_definitions() -> None:
    set_data = loaded_set(champions=(champion("a", "x"),), traits=(trait("x", order=0),))
    result = calculate_traits(set_data, team_list(("a", ()), ("a", ())))
    assert result.traits[0].count == 1


def test_native_unique_instance_counts_duplicate_instances() -> None:
    set_data = loaded_set(
        champions=(champion("a", "x"),),
        traits=(trait("x", order=0, mode=TraitCountingMode.UNIQUE_INSTANCE),),
    )
    result = calculate_traits(set_data, team_list(("a", ()), ("a", ())))
    assert result.traits[0].count == 2


def test_unique_champion_counts_distinct_champion_definitions() -> None:
    set_data = loaded_set(
        champions=(champion("a", "x"), champion("b", "x")),
        traits=(trait("x", order=0),),
    )
    result = calculate_traits(set_data, team_list(("a", ()), ("b", ())))
    assert result.traits[0].count == 2


def test_breakpoint_state_below_first_exact_middle_and_above_highest() -> None:
    set_data = loaded_set(
        champions=tuple(champion(letter, "x", order=index) for index, letter in enumerate("abcde")),
        traits=(trait("x", order=0, breakpoints=(2, 4)),),
    )
    below = calculate_traits(set_data, team_list(("a", ())))
    at_first = calculate_traits(set_data, team_list(("a", ()), ("b", ())))
    middle = calculate_traits(set_data, team_list(("a", ()), ("b", ()), ("c", ())))
    above = calculate_traits(
        set_data,
        team_list(("a", ()), ("b", ()), ("c", ()), ("d", ()), ("e", ())),
    )
    assert below.traits[0].active_breakpoint is None
    assert below.traits[0].next_breakpoint.count == 2
    assert below.traits[0].needed_for_next_breakpoint == 1
    assert at_first.traits[0].active_breakpoint.count == 2
    assert at_first.traits[0].next_breakpoint.count == 4
    assert at_first.traits[0].needed_for_next_breakpoint == 2
    assert middle.traits[0].active_breakpoint.count == 2
    assert middle.traits[0].next_breakpoint.count == 4
    assert middle.traits[0].needed_for_next_breakpoint == 1
    assert above.traits[0].active_breakpoint.count == 4
    assert above.traits[0].next_breakpoint is None
    assert above.traits[0].needed_for_next_breakpoint is None


def test_trait_results_are_deterministically_sorted_by_display_order_then_id() -> None:
    set_data = loaded_set(
        champions=(champion("a", "z", "a", "m"),),
        traits=(trait("z", order=10), trait("m", order=5), trait("a", order=10)),
    )
    result = calculate_traits(set_data, team_list(("a", ())))
    assert [item.trait_id for item in result.traits] == ["m", "a", "z"]


def test_champion_without_dynamic_rule_ignores_stored_selection_for_counting() -> None:
    set_data = loaded_set(
        champions=(champion("a", "native"),),
        traits=(trait("native", order=0), trait("choice", order=1)),
    )
    result = calculate_traits(set_data, team_list(("a", ("choice",))))
    assert [item.trait_id for item in result.traits] == ["native"]
    assert result.dynamic_issues == ()


def test_exactly_one_valid_selection_contributes_selected_trait() -> None:
    set_data = loaded_set(
        champions=(champion("a"),),
        traits=(trait("x", order=0), trait("y", order=1)),
        dynamic_traits=(dynamic("a", DynamicSelectionRule.EXACTLY_ONE, ("x", "y")),),
    )
    result = calculate_traits(set_data, team_list(("a", ("y",))))
    assert [item.trait_id for item in result.traits] == ["y"]
    assert result.dynamic_issues == ()


def test_exactly_one_missing_selection_is_reported_and_does_not_count() -> None:
    set_data = loaded_set(
        champions=(champion("a", "x"),),
        traits=(trait("x", order=0), trait("y", order=1)),
        dynamic_traits=(dynamic("a", DynamicSelectionRule.EXACTLY_ONE, ("x", "y")),),
    )
    result = calculate_traits(set_data, team_list(("a", ())))
    assert result.traits[0].trait_id == "x"
    assert result.traits[0].count == 1
    assert result.traits[0].has_invalid_dynamic_selection is True
    assert result.dynamic_issues[0].code == "missing_selection"
    assert result.dynamic_issues[0].affected_trait_ids == ("x", "y")


def test_exactly_one_too_many_choices_is_reported() -> None:
    set_data = loaded_set(
        champions=(champion("a"),),
        traits=(trait("x", order=0), trait("y", order=1)),
        dynamic_traits=(dynamic("a", DynamicSelectionRule.EXACTLY_ONE, ("x", "y")),),
    )
    result = calculate_traits(set_data, team_list(("a", ("x", "y"))))
    assert result.traits == ()
    assert result.dynamic_issues[0].code == "invalid_selection_count"
    assert result.dynamic_issues[0].selected_trait_ids == ("x", "y")
    assert "received 2" in result.dynamic_issues[0].message


def test_invalid_dynamic_choice_is_reported_and_included_in_affected_ids() -> None:
    set_data = loaded_set(
        champions=(champion("a"),),
        traits=(trait("x", order=0), trait("other", order=1)),
        dynamic_traits=(dynamic("a", DynamicSelectionRule.EXACTLY_ONE, ("x",)),),
    )
    result = calculate_traits(set_data, team_list(("a", ("other",))))
    issue = result.dynamic_issues[0]
    assert issue.code == "invalid_choice"
    assert issue.selected_trait_ids == ("other",)
    assert issue.affected_trait_ids == ("x", "other")
    assert "not allowed" in issue.message


def test_none_rule_accepts_empty_selection_and_rejects_any_choice() -> None:
    set_data = loaded_set(
        champions=(champion("a", "x"),),
        traits=(trait("x", order=0),),
        dynamic_traits=(dynamic("a", DynamicSelectionRule.NONE),),
    )
    valid = calculate_traits(set_data, team_list(("a", ())))
    invalid = calculate_traits(set_data, team_list(("a", ("x",))))
    assert valid.dynamic_issues == ()
    assert invalid.dynamic_issues[0].code == "invalid_selection_count"
    assert "no choices" in invalid.dynamic_issues[0].message


def test_zero_or_one_accepts_zero_and_one_but_rejects_two() -> None:
    set_data = loaded_set(
        champions=(champion("a"),),
        traits=(trait("x", order=0), trait("y", order=1)),
        dynamic_traits=(dynamic("a", DynamicSelectionRule.ZERO_OR_ONE, ("x", "y")),),
    )
    zero = calculate_traits(set_data, team_list(("a", ())))
    one = calculate_traits(set_data, team_list(("a", ("x",))))
    two = calculate_traits(set_data, team_list(("a", ("x", "y"))))
    assert zero.dynamic_issues == ()
    assert one.traits[0].trait_id == "x"
    assert two.traits == ()
    assert two.dynamic_issues[0].code == "invalid_selection_count"


def test_any_number_accepts_empty_and_multiple_allowed_choices() -> None:
    set_data = loaded_set(
        champions=(champion("a"),),
        traits=(trait("x", order=0), trait("y", order=1)),
        dynamic_traits=(dynamic("a", DynamicSelectionRule.ANY_NUMBER, ("x", "y")),),
    )
    empty = calculate_traits(set_data, team_list(("a", ())))
    multiple = calculate_traits(set_data, team_list(("a", ("x", "y"))))
    assert empty.traits == ()
    assert empty.dynamic_issues == ()
    assert [item.trait_id for item in multiple.traits] == ["x", "y"]


def test_exactly_n_accepts_exact_count_and_rejects_missing_or_wrong_nonzero_count() -> None:
    set_data = loaded_set(
        champions=(champion("a"),),
        traits=(trait("x", order=0), trait("y", order=1), trait("z", order=2)),
        dynamic_traits=(
            dynamic(
                "a",
                DynamicSelectionRule.EXACTLY_N,
                ("x", "y", "z"),
                exact_count=2,
            ),
        ),
    )
    exact = calculate_traits(set_data, team_list(("a", ("x", "z"))))
    missing = calculate_traits(set_data, team_list(("a", ())))
    wrong = calculate_traits(set_data, team_list(("a", ("x",))))
    assert [item.trait_id for item in exact.traits] == ["x", "z"]
    assert missing.dynamic_issues[0].code == "missing_selection"
    assert wrong.dynamic_issues[0].code == "invalid_selection_count"
    assert "exactly 2" in wrong.dynamic_issues[0].message


def test_per_instance_evaluates_duplicate_instances_independently() -> None:
    set_data = loaded_set(
        champions=(champion("a"),),
        traits=(trait("x", order=0, mode=TraitCountingMode.UNIQUE_INSTANCE),),
        dynamic_traits=(dynamic("a", DynamicSelectionRule.EXACTLY_ONE, ("x",)),),
    )
    result = calculate_traits(set_data, team_list(("a", ("x",)), ("a", ())))
    assert result.traits[0].count == 1
    assert result.traits[0].has_invalid_dynamic_selection is True
    assert len(result.dynamic_issues) == 1
    assert len(result.dynamic_issues[0].instance_ids) == 1


def test_per_champion_matching_selection_is_shared_and_uses_selected_trait_count_mode() -> None:
    set_data = loaded_set(
        champions=(champion("a"),),
        traits=(
            trait("unique_champion", order=0),
            trait("unique_instance", order=1, mode=TraitCountingMode.UNIQUE_INSTANCE),
        ),
        dynamic_traits=(
            dynamic(
                "a",
                DynamicSelectionRule.ANY_NUMBER,
                ("unique_champion", "unique_instance"),
                scope=DynamicSelectionScope.PER_CHAMPION,
            ),
        ),
    )
    result = calculate_traits(
        set_data,
        team_list(
            ("a", ("unique_champion", "unique_instance")),
            ("a", ("unique_champion", "unique_instance")),
        ),
    )
    by_id = result_by_id(result)
    assert by_id["unique_champion"].count == 1
    assert by_id["unique_instance"].count == 2
    assert result.dynamic_issues == ()


def test_per_champion_conflict_is_reported_as_one_group_and_contributes_nothing() -> None:
    set_data = loaded_set(
        champions=(champion("a", "x"),),
        traits=(trait("x", order=0), trait("y", order=1)),
        dynamic_traits=(
            dynamic(
                "a",
                DynamicSelectionRule.EXACTLY_ONE,
                ("x", "y"),
                scope=DynamicSelectionScope.PER_CHAMPION,
            ),
        ),
    )
    current = team_list(("a", ("x",)), ("a", ("y",)))
    result = calculate_traits(set_data, current)
    issue = result.dynamic_issues[0]
    assert issue.code == "per_champion_conflict"
    assert len(issue.instance_ids) == 2
    assert issue.selected_trait_ids == ("x", "y")
    assert issue.affected_trait_ids == ("x", "y")
    assert "must match" in issue.message
    assert result.traits[0].trait_id == "x"
    assert result.traits[0].count == 1
    assert result.traits[0].has_invalid_dynamic_selection is True


def test_per_champion_individual_invalid_selection_blocks_entire_shared_selection() -> None:
    set_data = loaded_set(
        champions=(champion("a"),),
        traits=(trait("x", order=0, mode=TraitCountingMode.UNIQUE_INSTANCE),),
        dynamic_traits=(
            dynamic(
                "a",
                DynamicSelectionRule.EXACTLY_ONE,
                ("x",),
                scope=DynamicSelectionScope.PER_CHAMPION,
            ),
        ),
    )
    result = calculate_traits(set_data, team_list(("a", ("x",)), ("a", ())))
    assert result.traits == ()
    assert len(result.dynamic_issues) == 1
    assert result.dynamic_issues[0].code == "missing_selection"


def test_invalid_dynamic_flag_is_false_for_unaffected_positive_trait() -> None:
    set_data = loaded_set(
        champions=(champion("a", "native"),),
        traits=(trait("native", order=0), trait("choice", order=1)),
        dynamic_traits=(dynamic("a", DynamicSelectionRule.EXACTLY_ONE, ("choice",)),),
    )
    result = calculate_traits(set_data, team_list(("a", ())))
    assert result.traits[0].trait_id == "native"
    assert result.traits[0].has_invalid_dynamic_selection is False
    assert result.dynamic_issues[0].affected_trait_ids == ("choice",)


def test_sample_set_integration_calculates_native_and_dynamic_traits(valid_set_dir: Path) -> None:
    from tft_builder.set_loader import load_set_directory

    set_data = load_set_directory(valid_set_dir)
    current = team_list(
        ("sample_guardian", ()),
        ("sample_flex", ("sample_arcane",)),
        ("sample_mage", ()),
    )
    result = calculate_traits(set_data, current)
    by_id = result_by_id(result)
    assert by_id["sample_guard"].count == 2
    assert by_id["sample_guard"].active_breakpoint.count == 2
    assert by_id["sample_arcane"].count == 2
    assert by_id["sample_arcane"].active_breakpoint.count == 2
    assert result.dynamic_issues == ()


def test_large_realistic_list_keeps_linear_counting_semantics() -> None:
    set_data = loaded_set(
        champions=tuple(champion(f"c{index}", "x", order=index) for index in range(50)),
        traits=(
            trait("x", order=0, mode=TraitCountingMode.UNIQUE_INSTANCE, breakpoints=(10, 100)),
        ),
    )
    current = team_list(*[(f"c{index % 50}", ()) for index in range(500)])
    result = calculate_traits(set_data, current)
    assert result.traits[0].count == 500
    assert result.traits[0].active_breakpoint.count == 100
    assert result.traits[0].next_breakpoint is None


def test_per_champion_selection_order_does_not_create_false_conflict() -> None:
    set_data = loaded_set(
        champions=(champion("a"),),
        traits=(trait("x", order=0), trait("y", order=1)),
        dynamic_traits=(
            dynamic(
                "a",
                DynamicSelectionRule.EXACTLY_N,
                ("x", "y"),
                scope=DynamicSelectionScope.PER_CHAMPION,
                exact_count=2,
            ),
        ),
    )
    result = calculate_traits(set_data, team_list(("a", ("x", "y")), ("a", ("y", "x"))))
    assert [item.trait_id for item in result.traits] == ["x", "y"]
    assert [item.count for item in result.traits] == [1, 1]
    assert result.dynamic_issues == ()


def test_native_and_dynamic_same_trait_do_not_double_count_one_instance() -> None:
    set_data = loaded_set(
        champions=(champion("a", "x"),),
        traits=(trait("x", order=0, mode=TraitCountingMode.UNIQUE_INSTANCE),),
        dynamic_traits=(dynamic("a", DynamicSelectionRule.EXACTLY_ONE, ("x",)),),
    )
    result = calculate_traits(set_data, team_list(("a", ("x",))))
    assert result.traits[0].count == 1
    assert result.dynamic_issues == ()


def test_distinct_dynamic_champion_definitions_count_for_unique_champion_trait() -> None:
    set_data = loaded_set(
        champions=(champion("a"), champion("b")),
        traits=(trait("x", order=0),),
        dynamic_traits=(
            dynamic("a", DynamicSelectionRule.EXACTLY_ONE, ("x",)),
            dynamic("b", DynamicSelectionRule.EXACTLY_ONE, ("x",)),
        ),
    )
    result = calculate_traits(set_data, team_list(("a", ("x",)), ("b", ("x",))))
    assert result.traits[0].count == 2
    assert result.dynamic_issues == ()


def test_any_number_still_rejects_traits_outside_allowed_choices() -> None:
    set_data = loaded_set(
        champions=(champion("a"),),
        traits=(trait("x", order=0), trait("other", order=1)),
        dynamic_traits=(dynamic("a", DynamicSelectionRule.ANY_NUMBER, ("x",)),),
    )
    result = calculate_traits(set_data, team_list(("a", ("other",))))
    assert result.traits == ()
    assert result.dynamic_issues[0].code == "invalid_choice"
    assert result.dynamic_issues[0].selected_trait_ids == ("other",)


def test_public_dynamic_selection_validation_matches_engine_rules() -> None:
    rule = dynamic("a", DynamicSelectionRule.EXACTLY_ONE, ("x", "y"))
    assert validate_dynamic_selection(rule, TraitSelection(("x",))) is None
    issue = validate_dynamic_selection(rule, TraitSelection())
    assert issue is not None
    assert issue.code == "missing_selection"
    assert issue.instance_ids == ()


def test_public_dynamic_selection_validation_rejects_wrong_types() -> None:
    rule = dynamic("a", DynamicSelectionRule.EXACTLY_ONE, ("x",))
    with pytest.raises(TypeError, match="rule"):
        validate_dynamic_selection(object(), TraitSelection())
    with pytest.raises(TypeError, match="selection"):
        validate_dynamic_selection(rule, object())
    with pytest.raises(TypeError, match="instance_ids"):
        validate_dynamic_selection(rule, TraitSelection(), [ChampionInstance("a").instance_id])
    with pytest.raises(TypeError, match="instance_ids"):
        validate_dynamic_selection(rule, TraitSelection(), ("not-a-uuid",))


def test_exact_activation_trait_deactivates_above_its_only_breakpoint() -> None:
    set_data = loaded_set(
        champions=(champion("a", "rival"), champion("b", "rival")),
        traits=(
            trait(
                "rival",
                order=0,
                activation=TraitActivationMode.EXACT,
                breakpoints=(1,),
            ),
        ),
    )
    one = result_by_id(calculate_traits(set_data, team_list(("a", ()))))
    assert one["rival"].active_breakpoint is not None

    two = result_by_id(calculate_traits(set_data, team_list(("a", ()), ("b", ()))))
    assert two["rival"].count == 2
    assert two["rival"].active_breakpoint is None
    assert two["rival"].next_breakpoint is None


def test_derived_trait_activates_from_required_trait_counts() -> None:
    champions = tuple(
        champion(f"solar_{index}", "solar", order=index) for index in range(3)
    ) + tuple(champion(f"lunar_{index}", "lunar", order=index + 3) for index in range(3))
    set_data = loaded_set(
        champions=champions,
        traits=(
            trait("solar", order=0, breakpoints=(3,)),
            trait("lunar", order=1, breakpoints=(3,)),
            trait(
                "eclipse",
                order=2,
                breakpoints=(1,),
                derived_requirements={"solar": 3, "lunar": 3},
            ),
        ),
    )
    incomplete = team_list(
        ("solar_0", ()),
        ("solar_1", ()),
        ("solar_2", ()),
        ("lunar_0", ()),
        ("lunar_1", ()),
    )
    assert "eclipse" not in result_by_id(calculate_traits(set_data, incomplete))

    complete = team_list(
        ("solar_0", ()),
        ("solar_1", ()),
        ("solar_2", ()),
        ("lunar_0", ()),
        ("lunar_1", ()),
        ("lunar_2", ()),
    )
    eclipse = result_by_id(calculate_traits(set_data, complete))["eclipse"]
    assert eclipse.count == 1
    assert eclipse.active_breakpoint is not None


def test_exact_activation_reports_a_future_exact_breakpoint() -> None:
    set_data = loaded_set(
        champions=(champion("a", "rival"), champion("b", "rival")),
        traits=(
            trait(
                "rival",
                order=0,
                activation=TraitActivationMode.EXACT,
                breakpoints=(1, 3),
            ),
        ),
    )
    result = result_by_id(calculate_traits(set_data, team_list(("a", ()), ("b", ()))))["rival"]
    assert result.active_breakpoint is None
    assert result.next_breakpoint is not None
    assert result.next_breakpoint.count == 3
    assert result.needed_for_next_breakpoint == 1
