---
provenance:
  - .agent/BOARD.md
  - operational_notes/maps/forward-predictive-model.md
  - operational_notes/07-26/15/2026-07-15_m3_successor_test_section_heat_loss_requirement.md
  - reports/thesis_dossier/2026-07-15_integrated_weekly_powerpoint_outline_definitions_first.md
tags: [journal, forward-predictive-model, m3, test-section, heat-loss, todo]
related:
  - .agent/status/2026-07-15_AGENT-430.md
  - imports/2026-07-15_m3_successor_test_section_loss_todo.json
task: AGENT-430
date: 2026-07-15
role: Coordinator/Writer
type: journal
status: complete
---
# M3 Successor Test-Section Loss TODO

## Observed Facts

- The setup/BC model error synthesis reports diagnostic M2 as the best current
  combined mdot/temperature mode and diagnostic M3 as the lowest TP/TW RMSE
  mode.
- Diagnostic M3 removes the CFD test-section net term, but mdot error worsens.
- The user explicitly requested that M3 should not delete the test section; it
  should model heat lost at the test section.
- Fluid now has setup-only external-boundary hooks through
  `outer_closure_mode: external_boundary_table`, including h/Ta/Tsur/emissivity,
  coverage multipliers, and drive selectors.

## Inferred Interpretation

The old M3 is an ablation that identifies a bad or overcorrecting
test-section compatibility term. It is not a physical claim that
test-section heat loss is absent. The next predictive target should be
`M3+TS`: heater model + cooler/HX model + distributed setup-only
test-section heat-loss model + pressure-root mdot solve.

## Changes Made

- Added active coordination row `AGENT-430`.
- Added future implementation row `TODO-PREDICT-TEST-SECTION-HEAT-LOSS`.
- Updated `operational_notes/maps/forward-predictive-model.md` with the M3
  successor policy and current blocker wording.
- Updated the definitions-first presentation outline so `M3 diagnostic` and
  `M3+TS successor` are defined separately.
- Added a dated operational note with math, allowed inputs, and do-not-do
  guardrails.

## Blockers

No new blocker was opened. The relevant existing blocker remains
`predictive-heater-cooler-wall-submodels`, with dependencies on
`thermal-cfd-1d-parity` and admission/scorecard gates.

## Recommended Next Action

Claim `TODO-PREDICT-TEST-SECTION-HEAT-LOSS` after cooler/HX and heater scorecard
inputs are ready enough to evaluate `M3+TS` end-to-end.
