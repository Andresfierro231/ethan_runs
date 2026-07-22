# Lit-Rev CFD Validity Diagnostics

Date: `2026-07-13`

Task: `TODO-LITREV-CFD-VALIDITY-DIAGNOSTICS`

## Source Context

- Lit-rev synthesis: `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways`
- Research pathways: `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/research_pathways.csv`

## Observed Output

Built 18 pressure-section validity rows and 54 coefficient naming rows.

## Inferred Interpretation

Sections with recirculation or material reverse-flow proxies must be named as section-effective or diagnostic coefficients, not universal `f_D`, `K`, or `Nu` closures.

## Blockers

Secondary velocity fraction and exact reverse-flow area/mass fractions are unavailable in existing package form for some sections; those rows are marked for bounded plane-vector extraction if needed.

## Recommended Next Action

Feed `coefficient_naming_limits.csv` into the reset/named-loss package and reject universal coefficient names wherever the validity gate is section-effective only.
