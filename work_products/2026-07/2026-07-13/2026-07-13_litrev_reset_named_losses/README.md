# Lit-Rev Reset Map And Named Losses

Date: `2026-07-13`

Task: `TODO-LITREV-RESET-NAMED-LOSSES`

## Source Context

- Lit-rev synthesis: `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways`
- Research pathways: `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/research_pathways.csv`

## Observed Output

Built 33 reset rows and 33 named pressure-loss rows from the pressure ledger and two-tap minor-loss package.

## Inferred Interpretation

Pressure residuals near bends, clusters, or recirculating sections should be carried as named component/cluster/branch-apparent rows, not hidden in one loop friction multiplier.

## Blockers

Some tap lengths remain proxy lengths from preserved reductions. Thermal reset status is conservative until wall material and heat-path reset locations are explicitly mapped.

## Recommended Next Action

Use `named_pressure_loss_table.csv` with CFD validity naming limits before any section coefficient is exported to the 1D model.
