---
provenance:
  - /scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/tamu_first_order_model/Fluid/docs/provisional_sensor_locations.csv
  - work_products/2026-07/2026-07-15/2026-07-15_sensor_tp2_restore_tw10_exclude/sensor_tp2_tw10_policy_refresh.csv
  - work_products/2026-07/2026-07-14/2026-07-14_mdot_temperature_probe_error_audit/sensor_level_errors.csv
  - operational_notes/07-26/15/2026-07-15_sensor_and_sophisticated_modeling_decisions.md
tags: [TP2, sensor-map, forward-v1, validation-only, one-dimensional-model]
task: AGENT-463
date: 2026-07-16
type: work_product_readme
status: complete
---
# TP2 1D Model Evidence

This package makes TP2 usable as validation-only 1D evidence. It reruns the
existing TP/TW score path with a generated projected TP2 registry that keeps the
original provisional coordinate in provenance columns while placing TP2 on the
1D bottom-horizontal/right-downcomer junction for scoring.

## Result

- TP2 canonical scorecard segment: `right_downcomer_bottom_horizontal_junction`.
- TP2 Fluid computational parent: either `right_vertical` at its end or `bottom_horizontal_inlet` at fraction `0.0`; these are the same physical junction in the current segment order.
- TP2 finite prediction gate: `pass`.
- Current aggregate count: `5` TP + `10` TW.
- Restored aggregate count: `6` TP + `10` TW.
- Current aggregate RMSE: `163.5887589218957` K.
- Restored aggregate RMSE: `163.7606479786714` K.

TP2 is now validation-only score evidence when these gates pass. It is still not
a runtime temperature input, fit target, sensor-wise correction, or closure
calibration row. The replay model rows consumed here remain diagnostic-only for
final forward-v1 because they are not the final setup-only predictive model.

## Outputs

- `tp2_projected_sensor_registry.csv`
- `tp2_sensor_level_evidence.csv`
- `sensor_policy_gate_evidence.csv`
- `aggregate_rmse_before_after.csv`
- `tp2_gate_status.csv`
- `admission_status_scorecard.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

Native CFD outputs, registry/admission state, scheduler state, generated docs
indexes, and external Fluid source files were not mutated.
