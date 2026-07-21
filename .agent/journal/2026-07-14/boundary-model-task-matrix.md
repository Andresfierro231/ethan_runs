---
provenance:
  - operational_notes/07-26/14/2026-07-14_PROJECT_MISSION_AND_SCIENTIFIC_QUESTIONS.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hx_fit/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract/README.md
tags: [journal, boundary-modeling, heat-loss, radiation, fluid-api]
related:
  - .agent/status/2026-07-14_AGENT-327.md
  - imports/2026-07-14_boundary_model_task_matrix.json
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_model_task_matrix/README.md
task: AGENT-327
date: 2026-07-14
role: Coordinator/Writer
type: journal
status: complete
---
# Boundary Model Task Matrix

## Observed

The boundary/HX decision package requires heater, cooler/HX, wall/external
convection, and radiation semantics to stay separate. The heater/test-section
contract recommends `C1_heater_only_predictive_setup`: `eta_heater = 1`,
`test_section_fluid_fraction = 0`, and `test_section_external_loss_W = 0` until
a validation split admits a correction. The predictive HX package already has a
repo-local `HX1` post-solve duty multiplier, but the cleaner `HX2` direct Fluid
UA multiplier remains blocked by external Fluid API work.

## Interpretation

The next executable boundary task should be heater fraction/source-contract
work because it is repo-local and can be scored without CFD-duty runtime
leakage. The next high-impact external Fluid task is direct HX UA/effectiveness
support. Wall/external convection and predictive radiation require first-class
boundary dictionaries and explicit replay-vs-predictive radiation modes.

## Output

Created:

- `work_products/2026-07/2026-07-14/2026-07-14_boundary_model_task_matrix/boundary_model_task_matrix.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_boundary_model_task_matrix/fluid_api_gap_for_external_bc.csv`
- `work_products/2026-07/2026-07-14/2026-07-14_boundary_model_task_matrix/README.md`
- `work_products/2026-07/2026-07-14/2026-07-14_boundary_model_task_matrix/summary.json`

## Guardrails

- No CFD `wallHeatFlux`, CFD cooler duty, CFD `mdot`, or validation temperature
  may enter runtime configuration.
- CFD cooler duty may be used only on declared training rows for a fitted
  cooler scalar and only as validation scoring evidence elsewhere.
- Current CFD `rcExternalTemperature` already embeds radiative exchange in
  total wallHeatFlux; no separate `qr` is exported.
- Replay modes must not add separate radiation on top of realized CFD
  wallHeatFlux.

## Validation

CSV/JSON parse check passed: 5 matrix rows and 5 API-gap rows.

No native CFD solver outputs were modified.
