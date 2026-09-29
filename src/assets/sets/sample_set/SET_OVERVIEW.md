# Development Sample Set - Set package overview

Generated from the validated Set source specification. Images use local package paths.

- Champions: 3
- Traits: 3
- Items: 1

## Champions

| Image | Champion | Cost | Traits | Trait points | Slots |
| --- | --- | ---: | --- | --- | ---: |
| ![Sample Guardian](assets/champions/sample_guardian.png) | Sample Guardian | 1 | Sample Guard | sample_guard=1 | 1 |
| ![Sample Mage](assets/champions/sample_mage.png) | Sample Mage | 3 | Sample Arcane | sample_arcane=1 | 1 |
| ![Sample Flex](assets/champions/sample_flex.png) | Sample Flex | 7 | Sample Guard | sample_guard=1 | 1 |

## Dynamic Trait choices

| Champion | Rule | Scope | Choice | Points | Choice image |
| --- | --- | --- | --- | ---: | --- |
| Sample Flex | EXACTLY_ONE | PER_INSTANCE | Sample Arcane | 1 | ![Sample Arcane](assets/champions/variants/sample_flex_arcane.png) |
| Sample Flex | EXACTLY_ONE | PER_INSTANCE | Sample Wildcard | 1 | ![Sample Wildcard](assets/champions/variants/sample_flex_wildcard.png) |

## Traits

| Icon | Trait | Breakpoints | Activation | Derived from | Description |
| --- | --- | --- | --- | --- | --- |
| ![Sample Guard](assets/traits/sample_guard.png) | Sample Guard | 2 (bronze): Gain a basic defensive bonus. / 4 (silver): Gain an improved defensive bonus. | AT_LEAST | - | Sample Guard grants defensive bonuses at each breakpoint. |
| ![Sample Arcane](assets/traits/sample_arcane.png) | Sample Arcane | 2 (bronze) / 3 (gold) | AT_LEAST | - | - |
| ![Sample Wildcard](assets/traits/sample_wildcard.png) | Sample Wildcard | 1 (unique) | AT_LEAST | - | - |

## Items

| Icon | Item | Category | Components | Associated Traits | Description |
| --- | --- | --- | --- | --- | --- |
| ![Sample Blade](assets/items/sample_blade.png) | Sample Blade | COMPONENT | - | - | Development-only sample item. |

## Source candidate accounting

Included/excluded source candidates: 0
