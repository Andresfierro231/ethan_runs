# Lit-Rev Property Sensitivity

Date: `2026-07-13`

Task: `TODO-LITREV-PROPERTY-SENSITIVITY`

## Source Context

- Lit-rev synthesis: `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways`
- Research pathways: `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/research_pathways.csv`

## Observed Output

Built 90 property-mode branch rows and 15 case/mode summary rows.

## Inferred Interpretation

Property choices move Re, Pr, and Gz enough that pressure or heat residuals should not be fitted until the property mode is declared.

## Blockers

This pass does not rerun Fluid or recompute pressure-rooted mdot. It quantifies first-order nondimensional and residual sensitivity from existing CFD/postprocessing artifacts.

## Recommended Next Action

Use `property_sensitivity_summary.csv` to choose replication versus updated-property lanes before fitting friction, heat-loss, or Nu residuals.
