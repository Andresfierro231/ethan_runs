---
provenance:
  - work_products/2026-07/2026-07-14/2026-07-14_final_forward_v1_scorecard_gate/summary.json
  - work_products/2026-07/2026-07-14/2026-07-14_fluid_reset_development_api/summary.json
  - work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/summary.json
  - work_products/2026-07/2026-07-14/2026-07-14_salt1_terminal_bc_and_pm5_upcomer_harvest/summary.json
  - work_products/2026-07/2026-07-14/2026-07-14_forward_v1_pm5_hydraulic_delta/summary.json
tags: [forward-model, forward-v1, scorecard, hydraulics, boundary-conditions]
related:
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-366
date: 2026-07-14
role: Forward-pred/Scientific-closure/Implementer/Tester/Writer
type: work_product
status: complete
---
# Forward-v1 Gate Refresh After Fluid API And Audits

## Decision

Final forward-v1 remains `blocked_no_go_final_forward_v1_not_admitted`.

This package refreshes the final-gate state after three gate-moving updates:
Fluid reset/development API support landed, the mdot/TP/TW audit landed, and
Salt1 terminal BC conflict evidence landed. These are real progress, but none
admits final forward-v1.

## What Changed

- Fluid can now accept `MinorLosses.reset_development_k_by_segment`, but H1 is
  still blocked by missing admitted pressure/reset-development evidence.
- The mdot/temperature audit adds residual-attribution evidence:
  `16` model result rows and
  `204` sensor error rows.
- Salt1 hi10q's stale conflict is resolved as perturbed-Q training evidence,
  but Salt1 does not silently enter the current Salt2/Salt3/Salt4 final split.
- PM5 matched pressure/upcomer metrics remain pending because job `3295901` is
  `PENDING` with `0`
  parsed metric files present.

## Current Blocking State

- Gate rows refreshed: `10`.
- Blocking rows: `7`.
- Final forward-v1 admitted: `false`.
- Current split: `salt_2=train;salt_3=validation;salt_4=holdout`.

## Runtime Input Rules

- No CFD mdot as a model input.
- No realized CFD `wallHeatFlux` as a predictive runtime input.
- No imposed CFD cooler duty as final predictive HX evidence.
- No validation or holdout temperatures used for fitting.
- No diagnostic internal Nu row consumed as trainable closure data.

## Files

- `forward_v1_gate_checklist_refreshed.csv`
- `forward_v1_scorecard_input_contract_next.csv`
- `forward_v1_blocking_gate_burndown.csv`
- `forward_v1_residual_attribution_skeleton.csv`
- `perturbation_split_policy_next.csv`
- `math_assumptions_theory.md`
- `source_manifest.csv`
- `summary.json`

## Documentation Note

The forward-model map and thesis README are intentionally not edited here
because AGENT-365 currently owns those additive link paths. Add cross-links
after that lane closes.
