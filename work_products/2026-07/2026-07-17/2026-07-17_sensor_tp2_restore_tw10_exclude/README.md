---
provenance:
  - work_products/2026-07/2026-07-15/2026-07-15_sensor_policy_gate_opening_and_hydraulic_node_run/sensor_map_policy_refresh.csv
  - work_products/2026-07/2026-07-16/2026-07-16_tp2_1d_model_evidence/tp2_projected_sensor_registry.csv
  - work_products/2026-07/2026-07-16/2026-07-16_tp2_1d_model_evidence/aggregate_rmse_before_after.csv
tags: [sensor-map, TP2, TW10, forward-v1, validation-only]
related:
  - .agent/status/2026-07-17_TODO-SENSOR-TP2-RESTORE-TW10-EXCLUDE.md
  - .agent/journal/2026-07-17/sensor-tp2-restore-tw10-exclude.md
task: TODO-SENSOR-TP2-RESTORE-TW10-EXCLUDE
date: 2026-07-17
role: Sensor-map/Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
---
# TP2 Restore / TW10 Exclude Final Scorecard

## Decision

TP2 is restored as a post-solve validation/scoring target on the 1D path. TW10 remains excluded from aggregate scoring because the current model does not emit an active-HX shell-state temperature.

## Results

- TP2 source segment: `right_downcomer_bottom_horizontal_junction`.
- TP2 finite rows: `3` of `3`.
- Current aggregate: `5` TP + `10` TW, RMSE `163.588758922` K.
- Restored aggregate: `6` TP + `10` TW, RMSE `163.760647979` K.
- TP2 and TW10 both remain `runtime_temperature_allowed=false` and `fit_allowed=false`.

## Outputs

- `sensor_policy_scorecard.csv`
- `aggregate_rmse_before_after.csv`
- `tp2_tw10_gate_status.csv`
- `admission_status_scorecard.csv`
- `source_manifest.csv`
- `summary.json`

## Guardrails

This package changes score/admission status only. It does not mutate Fluid, native CFD outputs, registry state, scheduler state, or generated docs indexes.
