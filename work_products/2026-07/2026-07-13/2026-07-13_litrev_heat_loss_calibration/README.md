# Lit-Rev Heat-Loss Calibration Ledger

Date: `2026-07-13`

Task: `TODO-LITREV-HEAT-LOSS-CALIBRATION`

## Source Context

- Lit-rev synthesis: `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways`
- Research pathways: `reports/2026-07/2026-07-13/2026-07-13_litrev_lessons_and_research_pathways/research_pathways.csv`

## Observed Output

Built 207 heat-path rows and 18 segment admission rows from thermal boundary and predictive heat-loss packages.

## Inferred Interpretation

The ledger keeps cooler/jacket removal, passive losses, heater input, radiation metadata, wall/storage unknowns, and residuals separate. Internal Nu remains blocked from absorbing external heat-loss terms.

## Blockers

The current CFD wallHeatFlux integrates the rcExternalTemperature effect; radiation is metadata-bounded but not a separately observed heat term in this package.

## Recommended Next Action

Use `heat_closure_admission.csv` before any internal HTC/Nu calibration. Add a later radiation-specific row only if a distinct `qr` term or independent surface-radiation estimate is available.
