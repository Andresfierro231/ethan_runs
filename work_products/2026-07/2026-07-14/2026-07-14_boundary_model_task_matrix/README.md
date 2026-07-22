---
provenance:
  - operational_notes/07-26/14/2026-07-14_PROJECT_MISSION_AND_SCIENTIFIC_QUESTIONS.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_hx_wall_radiation_model_form_decision/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_hx_fit/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_heater_test_section_contract/README.md
tags: [boundary-modeling, forward-model, heat-loss, radiation, fluid-api]
related:
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_model_task_matrix/boundary_model_task_matrix.csv
  - work_products/2026-07/2026-07-14/2026-07-14_boundary_model_task_matrix/fluid_api_gap_for_external_bc.csv
task: AGENT-327
date: 2026-07-14
role: Coordinator/Writer
type: work_product
status: complete
---
# Boundary Model Task Matrix

## Purpose

This package converts the boundary/HX/wall-layer/radiation decisions into
setup-only predictive model tasks. It separates heater realized fraction,
cooler/HX removal, passive wall/external convection, and radiation semantics so
future forward runs do not hide one error inside another coefficient.

## Files

- `boundary_model_task_matrix.csv`: concrete task rows with setup-only inputs,
  fitted parameters, validation targets, diagnostic-only CFD quantities, split
  policy, and acceptance gates.
- `fluid_api_gap_for_external_bc.csv`: Fluid API gaps that block clean
  setup-only external boundary/HX/wall/radiation modeling.
- `summary.json`: compact decision summary.

## Next Executable Recommendation

Run `BCM-HEATER-FRACTION-V1` first as a repo-local task.

Reason: the heater/test-section contract already shows that `C1_heater_only`
reduces mean absolute CFD Tmean error from `34.374 K` to `4.609 K` without a
fitted thermal parameter and without using realized CFD wallHeatFlux at runtime.
The next executable task should run/score this source contract under the locked
Salt2/Salt3/Salt4 split and, if calibration is attempted, fit exactly one scalar
on Salt2 only:

- either `eta_heater`; or
- `test_section_external_loss_W`;
- not both on the current three-row split.

Validation targets are Salt3/Salt4 branch/sensor/Tmean errors, with mdot kept as
a coupled hydraulic guardrail. Realized CFD heater/test-section wallHeatFlux is
diagnostic-only and may not enter runtime config.

## Next Fluid API Recommendation

After the heater source task, run `BCM-COOLER-HX-UA-V1` as the first external
Fluid API task. It should implement a direct UA/effectiveness multiplier inside
Fluid's predictive HX calculation. The current HX1 global duty multiplier is
useful screening evidence but is not the clean final form because it sits around
the computed duty rather than inside the physical HX model.

## Radiation Rule

Do not double-count radiation. Current CFD `rcExternalTemperature` includes
radiative exchange inside total `wallHeatFlux`, and no separate `qr` term is
exported. Replay modes must treat radiation as embedded in realized wallHeatFlux.
Predictive setup-only modes may compute radiation explicitly only when they are
not also replaying realized CFD wallHeatFlux.
