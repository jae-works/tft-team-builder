"""Generic reviewed-Set verification and human-readable dataset reporting."""

from __future__ import annotations

import hashlib
import math
import re
import struct
from collections import Counter, defaultdict
from pathlib import Path

from .set_loader import LoadedSet
from .set_schema import ItemCategory

_MARKUP_PATTERN = re.compile(r"@[^@]+@|<[^>]+>|%i:[^%]+%")
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _markdown_cell(value: str) -> str:
    """Keep generated tables readable without allowing cell-breaking content."""

    return value.replace("|", "\\|").replace("\n", " ").strip()


def _item_cell(name: str, icon: str) -> str:
    return f"![{_markdown_cell(name)}]({icon})<br>{_markdown_cell(name)}"


def _runtime_png_inventory(
    loaded: LoadedSet,
) -> tuple[Counter[tuple[int, int]], set[frozenset[str]], list[str]]:
    """Read PNG headers once and return dimensions, duplicate groups and structural issues."""

    asset_root = loaded.root / loaded.manifest.assets_dir
    dimensions: Counter[tuple[int, int]] = Counter()
    paths_by_hash: defaultdict[str, list[str]] = defaultdict(list)
    issues: list[str] = []

    for path in sorted(asset_root.rglob("*.png")):
        if not path.is_file():
            continue
        relative = path.relative_to(loaded.root).as_posix()
        payload = path.read_bytes()
        if len(payload) < 24 or payload[:8] != _PNG_SIGNATURE:
            issues.append(f"runtime asset is not a structurally valid PNG: {relative}")
            continue
        width, height = struct.unpack(">II", payload[16:24])
        if width <= 0 or height <= 0:
            issues.append(f"runtime PNG has invalid dimensions: {relative}")
            continue
        dimensions[(width, height)] += 1
        paths_by_hash[hashlib.sha256(payload).hexdigest()].append(relative)

    duplicate_groups = {
        frozenset(paths) for paths in paths_by_hash.values() if len(paths) > 1
    }
    return dimensions, duplicate_groups, issues


def verify_review_policy(loaded: LoadedSet) -> list[str]:
    """Compare a validated runtime Set with its own declared review expectations."""

    policy = loaded.review
    if policy is None:
        return ["Set package does not declare a review policy"]

    issues: list[str] = []
    manifest = loaded.manifest
    if manifest.set_id != policy.expected_set_id:
        issues.append(
            f"Set ID differs: expected {policy.expected_set_id}, got {manifest.set_id}"
        )
    if manifest.revision != policy.expected_revision:
        issues.append(
            f"Set revision differs: expected {policy.expected_revision}, got {manifest.revision}"
        )

    actual_counts = {
        "Champions": len(loaded.champions),
        "Traits": len(loaded.traits),
        "Items": len(loaded.items),
        "dynamic Trait rules": len(loaded.dynamic_traits),
    }
    expected_counts = {
        "Champions": policy.champion_count,
        "Traits": policy.trait_count,
        "Items": policy.item_count,
        "dynamic Trait rules": policy.dynamic_trait_count,
    }
    for label, expected in expected_counts.items():
        if actual_counts[label] != expected:
            issues.append(f"{label} count differs: expected {expected}, got {actual_counts[label]}")

    expected_costs = {entry.cost: entry.count for entry in policy.champion_cost_counts}
    actual_costs = dict(sorted(Counter(item.cost for item in loaded.champions).items()))
    if actual_costs != expected_costs:
        issues.append(f"Champion cost counts differ: expected {expected_costs}, got {actual_costs}")

    expected_categories = {
        entry.category: entry.count for entry in policy.item_category_counts
    }
    actual_categories = Counter(item.category for item in loaded.items)
    if any(actual_categories[key] != value for key, value in expected_categories.items()) or sum(
        actual_categories.values()
    ) != sum(expected_categories.values()):
        printable = {key.value: value for key, value in actual_categories.items()}
        expected_printable = {key.value: value for key, value in expected_categories.items()}
        issues.append(
            f"Item category counts differ: expected {expected_printable}, got {printable}"
        )

    for expectation in policy.champion_expectations:
        champion = loaded.champions_by_id.get(expectation.champion_id)
        if champion is None:
            issues.append(f"reviewed Champion is missing: {expectation.champion_id}")
            continue
        if expectation.board_slots is not None and champion.board_slots != expectation.board_slots:
            issues.append(
                f"Champion {champion.id} board_slots differs: expected "
                f"{expectation.board_slots}, got {champion.board_slots}"
            )
        if champion.trait_points != expectation.trait_points:
            issues.append(
                f"Champion {champion.id} trait_points differ: expected "
                f"{expectation.trait_points}, got {champion.trait_points}"
            )

    for expectation in policy.trait_expectations:
        trait = loaded.traits_by_id.get(expectation.trait_id)
        if trait is None:
            issues.append(f"reviewed Trait is missing: {expectation.trait_id}")
            continue
        if (
            expectation.activation_mode is not None
            and trait.activation_mode is not expectation.activation_mode
        ):
            issues.append(
                f"Trait {trait.id} activation_mode differs: expected "
                f"{expectation.activation_mode.value}, got {trait.activation_mode.value}"
            )
        if trait.derived_requirements != expectation.derived_requirements:
            issues.append(
                f"Trait {trait.id} derived_requirements differ: expected "
                f"{expectation.derived_requirements}, got {trait.derived_requirements}"
            )

    dynamic_by_champion = {rule.champion_id: rule for rule in loaded.dynamic_traits}
    for expectation in policy.dynamic_trait_expectations:
        rule = dynamic_by_champion.get(expectation.champion_id)
        if rule is None:
            issues.append(f"reviewed dynamic Trait rule is missing: {expectation.champion_id}")
            continue
        if rule.selection_rule is not expectation.selection_rule:
            issues.append(
                f"Dynamic rule {rule.champion_id} selection_rule differs: expected "
                f"{expectation.selection_rule.value}, got {rule.selection_rule.value}"
            )
        if rule.selection_scope is not expectation.selection_scope:
            issues.append(
                f"Dynamic rule {rule.champion_id} selection_scope differs: expected "
                f"{expectation.selection_scope.value}, got {rule.selection_scope.value}"
            )
        if rule.exact_count != expectation.exact_count:
            issues.append(
                f"Dynamic rule {rule.champion_id} exact_count differs: expected "
                f"{expectation.exact_count}, got {rule.exact_count}"
            )
        if rule.choices != expectation.choices:
            issues.append(f"Dynamic rule {rule.champion_id} choices differ")
        if rule.choice_points != expectation.choice_points:
            issues.append(f"Dynamic rule {rule.champion_id} choice_points differ")
        if expectation.choice_images == "NONE" and rule.choice_images:
            issues.append(f"Dynamic rule {rule.champion_id} must not define choice images")
        if expectation.choice_images == "ALL" and set(rule.choice_images) != set(rule.choices):
            issues.append(f"Dynamic rule {rule.champion_id} must define an image for every choice")

    if (
        policy.team_planner_codec is not None
        and loaded.team_planner.codec != policy.team_planner_codec
    ):
        issues.append(
            f"Team Planner codec differs: expected {policy.team_planner_codec}, "
            f"got {loaded.team_planner.codec}"
        )
    if (
        policy.team_planner_champion_count is not None
        and len(loaded.team_planner.champion_ids) != policy.team_planner_champion_count
    ):
        issues.append(
            "Team Planner Champion count differs: expected "
            f"{policy.team_planner_champion_count}, got {len(loaded.team_planner.champion_ids)}"
        )

    expected_source_counts = {
        (entry.kind, entry.status): entry.count for entry in policy.source_candidate_counts
    }
    actual_source_counts = Counter((item.kind, item.status) for item in loaded.source_inventory)
    if actual_source_counts != expected_source_counts:
        issues.append("source candidate accounting differs from review policy")

    asset_root = loaded.root / manifest.assets_dir
    png_count = sum(1 for path in asset_root.rglob("*.png") if path.is_file())
    if png_count != policy.png_count:
        issues.append(f"runtime PNG count differs: expected {policy.png_count}, got {png_count}")
    if len(loaded.source_manifest.asset_sha256) != policy.source_manifest_asset_count:
        issues.append(
            "source-manifest asset count differs: expected "
            f"{policy.source_manifest_asset_count}, got {len(loaded.source_manifest.asset_sha256)}"
        )
    if len(loaded.source_manifest.sources) != policy.provenance_source_count:
        issues.append(
            "provenance source count differs: expected "
            f"{policy.provenance_source_count}, got {len(loaded.source_manifest.sources)}"
        )

    dimensions, duplicate_groups, png_issues = _runtime_png_inventory(loaded)
    issues.extend(png_issues)
    expected_dimensions = Counter(
        {(entry.width, entry.height): entry.count for entry in policy.png_dimensions}
    )
    if dimensions != expected_dimensions:
        issues.append(
            f"runtime PNG dimension inventory differs: expected {dict(expected_dimensions)}, "
            f"got {dict(dimensions)}"
        )
    expected_duplicate_groups = {
        frozenset(group) for group in policy.allowed_duplicate_asset_groups
    }
    if duplicate_groups != expected_duplicate_groups:
        issues.append("runtime PNG duplicate groups differ from review policy")

    if policy.reject_locale_markup:
        for locale, catalog in loaded.locales.items():
            bad_keys = sorted(
                key for key, value in catalog.items() if _MARKUP_PATTERN.search(value)
            )
            if bad_keys:
                issues.append(
                    f"locale {locale} still contains source markup in: {', '.join(bad_keys[:5])}"
                )

    for expectation in policy.locale_expectations:
        actual = loaded.locales.get(expectation.locale, {}).get(expectation.key)
        if actual != expectation.value:
            issues.append(
                f"locale value differs for {expectation.locale}:{expectation.key}: "
                f"expected {expectation.value!r}, got {actual!r}"
            )

    max_traits = max((len(champion.traits) for champion in loaded.champions), default=0)
    if max_traits < policy.minimum_max_champion_traits:
        issues.append(
            "maximum Champion Trait count is below review minimum: expected at least "
            f"{policy.minimum_max_champion_traits}, got {max_traits}"
        )
    max_breakpoints = max((len(trait.breakpoints) for trait in loaded.traits), default=0)
    if max_breakpoints < policy.minimum_max_trait_breakpoints:
        issues.append(
            "maximum Trait breakpoint count is below review minimum: expected at least "
            f"{policy.minimum_max_trait_breakpoints}, got {max_breakpoints}"
        )

    return issues


def render_set_review(loaded: LoadedSet) -> str:
    """Render a compact but complete Markdown inspection document from runtime Set data."""

    catalog = loaded.locales[loaded.manifest.default_locale]
    trait_names = {trait.id: catalog[trait.name_key] for trait in loaded.traits}
    item_names = {item.id: catalog[item.name_key] for item in loaded.items}
    dynamic_by_champion = {rule.champion_id: rule for rule in loaded.dynamic_traits}

    lines = [
        f"# {catalog[loaded.manifest.display_name_key]} - dataset review",
        "",
        "Generated automatically from the validated runtime Set package. Edit the JSON data or",
        "the Set source configuration, not this report; the checker regenerates this file.",
        "",
        f"- Set ID: `{loaded.manifest.set_id}`",
        f"- Revision: `{loaded.manifest.revision}`",
        f"- Champions: {len(loaded.champions)}",
        f"- Traits: {len(loaded.traits)}",
        f"- Items: {len(loaded.items)}",
        f"- Dynamic Trait rules: {len(loaded.dynamic_traits)}",
        "",
        "## Traits and breakpoints",
        "",
        "| Icon | Trait | Breakpoints and effects | Activation | Derived requirements |",
        "| --- | --- | --- | --- | --- |",
    ]
    for trait in loaded.traits:
        breakpoint_parts = []
        for breakpoint in trait.breakpoints:
            effect = (
                catalog[breakpoint.description_key]
                if breakpoint.description_key is not None
                else "-"
            )
            breakpoint_parts.append(
                f"**{breakpoint.count}** [{breakpoint.style}] - {_markdown_cell(effect)}"
            )
        derived = ", ".join(
            f"{trait_names.get(trait_id, trait_id)} >= {count}"
            for trait_id, count in sorted(trait.derived_requirements.items())
        ) or "-"
        lines.append(
            f"| ![{_markdown_cell(trait_names[trait.id])}]({trait.icon}) | "
            f"{_markdown_cell(trait_names[trait.id])} | {'<br>'.join(breakpoint_parts)} | "
            f"{trait.activation_mode.value} | {_markdown_cell(derived)} |"
        )

    lines.extend(
        [
            "",
            "## Champions",
            "",
            "| Portrait | Champion | Cost | Traits / points | Dynamic choices | Slots |",
            "| --- | --- | ---: | --- | --- | ---: |",
        ]
    )
    for champion in loaded.champions:
        trait_text = ", ".join(
            f"{trait_names[trait_id]} ({champion.trait_points.get(trait_id, 1)})"
            for trait_id in champion.traits
        ) or "-"
        rule = dynamic_by_champion.get(champion.id)
        if rule is None:
            dynamic_text = "-"
        else:
            choices = ", ".join(
                f"{trait_names[trait_id]} ({rule.choice_points.get(trait_id, 1)})"
                for trait_id in rule.choices
            )
            dynamic_text = f"{rule.selection_rule.value} / {rule.selection_scope.value}: {choices}"
        lines.append(
            f"| ![{_markdown_cell(catalog[champion.name_key])}]({champion.image}) | "
            f"{_markdown_cell(catalog[champion.name_key])} | {champion.cost} | "
            f"{_markdown_cell(trait_text)} | {_markdown_cell(dynamic_text)} | "
            f"{champion.board_slots} |"
        )

    components = [item for item in loaded.items if item.category is ItemCategory.COMPONENT]
    recipes = {
        tuple(sorted(item.composition)): item for item in loaded.items if len(item.composition) == 2
    }
    lines.extend(["", "## Component recipe matrix", ""])
    if components:
        headers = [_item_cell(item_names[item.id], item.icon) for item in components]
        lines.append("| Component | " + " | ".join(headers) + " |")
        lines.append("| --- | " + " | ".join("---" for _ in headers) + " |")
        for row in components:
            cells = []
            for column in components:
                item = recipes.get(tuple(sorted((row.id, column.id))))
                cells.append("-" if item is None else _item_cell(item_names[item.id], item.icon))
            lines.append(
                f"| {_item_cell(item_names[row.id], row.icon)} | " + " | ".join(cells) + " |"
            )
    else:
        lines.append("No components are defined for this Set.")

    non_recipe_items = [
        item
        for item in loaded.items
        if item.category not in {ItemCategory.COMPONENT, ItemCategory.RADIANT}
        and not item.composition
    ]
    lines.extend(["", "## Non-recipe items (excluding Radiant)", ""])
    for category in ItemCategory:
        category_items = [item for item in non_recipe_items if item.category is category]
        if not category_items:
            continue
        lines.extend(
            [
                f"### {category.value.title()}",
                "",
                "| Icon | Item | Description | Associated Traits |",
                "| --- | --- | --- | --- |",
            ]
        )
        for item in category_items:
            description = catalog.get(item.description_key, "-") if item.description_key else "-"
            associated = ", ".join(
                trait_names.get(trait_id, trait_id) for trait_id in item.associated_traits
            ) or "-"
            lines.append(
                f"| ![{_markdown_cell(item_names[item.id])}]({item.icon}) | "
                f"{_markdown_cell(item_names[item.id])} | {_markdown_cell(description)} | "
                f"{_markdown_cell(associated)} |"
            )
        lines.append("")

    radiant = [item for item in loaded.items if item.category is ItemCategory.RADIANT]
    lines.extend(["", "## Radiant items", ""])
    if radiant:
        columns = max(1, math.ceil(math.sqrt(len(radiant))))
        lines.append("| " + " | ".join(f"Item {index + 1}" for index in range(columns)) + " |")
        lines.append("| " + " | ".join("---" for _ in range(columns)) + " |")
        for offset in range(0, len(radiant), columns):
            row = radiant[offset : offset + columns]
            cells = [_item_cell(item_names[item.id], item.icon) for item in row]
            cells.extend("" for _ in range(columns - len(cells)))
            lines.append("| " + " | ".join(cells) + " |")
    else:
        lines.append("No Radiant items are defined for this Set.")

    lines.extend(
        [
            "",
            "## Provenance and package inventory",
            "",
            "- Runtime assets hashed by source manifest: "
            f"{len(loaded.source_manifest.asset_sha256)}",
            f"- Pinned provenance sources: {len(loaded.source_manifest.sources)}",
            f"- Source candidates reviewed: {len(loaded.source_inventory)}",
            "",
        ]
    )
    return "\n".join(lines)


def write_set_review_report(loaded: LoadedSet) -> Path:
    """Regenerate the declared review report beside the Set data."""

    path = loaded.root.joinpath(*loaded.manifest.review_report_file.split("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_set_review(loaded), encoding="utf-8", newline="\n")
    return path
