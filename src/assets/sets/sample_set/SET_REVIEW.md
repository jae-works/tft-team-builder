# Development Sample Set - dataset review

Generated automatically from the validated runtime Set package. Edit the JSON data or
the Set source configuration, not this report; the checker regenerates this file.

- Set ID: `sample_set`
- Revision: `0.1.0`
- Champions: 3
- Traits: 3
- Items: 1
- Dynamic Trait rules: 1

## Traits and breakpoints

| Icon | Trait | Breakpoints and effects | Activation | Derived requirements |
| --- | --- | --- | --- | --- |
| ![Sample Guard](assets/traits/sample_guard.png) | Sample Guard | **2** [bronze] - Gain a basic defensive bonus.<br>**4** [silver] - Gain an improved defensive bonus. | AT_LEAST | - |
| ![Sample Arcane](assets/traits/sample_arcane.png) | Sample Arcane | **2** [bronze] - -<br>**3** [gold] - - | AT_LEAST | - |
| ![Sample Wildcard](assets/traits/sample_wildcard.png) | Sample Wildcard | **1** [unique] - - | AT_LEAST | - |

## Champions

| Portrait | Champion | Cost | Traits / points | Dynamic choices | Slots |
| --- | --- | ---: | --- | --- | ---: |
| ![Sample Guardian](assets/champions/sample_guardian.png) | Sample Guardian | 1 | Sample Guard (1) | - | 1 |
| ![Sample Mage](assets/champions/sample_mage.png) | Sample Mage | 3 | Sample Arcane (1) | - | 1 |
| ![Sample Flex](assets/champions/sample_flex.png) | Sample Flex | 7 | Sample Guard (1) | EXACTLY_ONE / PER_INSTANCE: Sample Arcane (1), Sample Wildcard (1) | 1 |

## Component recipe matrix

| Component | ![Sample Blade](assets/items/sample_blade.png)<br>Sample Blade |
| --- | --- |
| ![Sample Blade](assets/items/sample_blade.png)<br>Sample Blade | - |

## Non-recipe items (excluding Radiant)


## Radiant items

No Radiant items are defined for this Set.

## Provenance and package inventory

- Runtime assets hashed by source manifest: 9
- Pinned provenance sources: 0
- Source candidates reviewed: 0
