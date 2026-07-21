---
provenance:
  - work_products/2026-07/2026-07-16/2026-07-16_predictive_test_section_heat_loss_model/README.md
  - work_products/2026-07/2026-07-16/2026-07-16_predictive_test_section_heat_loss_model/blocker_decision.json
tags: [forward-model, test-section, heat-loss, admission]
related:
  - .agent/status/2026-07-16_AGENT-458.md
  - .agent/blockers.yml
task: AGENT-458
date: 2026-07-16
role: Coordinator/BC-modeling/Forward-pred/Implementer/Tester/Writer
type: journal
status: complete
---
# Predictive Test-Section Heat-Loss Model

## Observed

The package fit two setup-only physical candidates on Salt2 and scored Salt3
and Salt4 as held-out cases. Both use allowed runtime inputs after Salt2
training: setup geometry/hA and a Salt2-trained scalar.

The held-out result is not admissible. The hA constant-drive model underpredicts
Salt3 and Salt4 test-section heat loss by `45.43%` and `65.13%`. The constant-W
model underpredicts by `46.14%` and `66.13%`. The zero-loss, legacy 37 W source,
and realized-loss rows are retained as diagnostics or upper bounds only.

## Inferred

The current evidence does not support removing
`predictive-wall-test-section-submodels`. A scientifically sound resolution
needs a segment external-boundary or resistance-network M3+TS implementation
that actually couples the predicted test-section loss into the pressure/thermal
solve and scores mdot plus TP/TW against M2 and M3.

## Blocker Action

`.agent/blockers.yml` now points `predictive-wall-test-section-submodels` at
the AGENT-458 package and keeps the blocker open.

## Next Action

Implement or run the solver-coupled M3+TS path using setup h/Ta/Tsur/emissivity,
coverage, wall/layer resistance, and a permitted drive selector. Do not use
realized CFD wallHeatFlux, realized CFD test-section loss, CFD mdot, imposed
CFD cooler duty, or validation/holdout temperatures as runtime inputs.
