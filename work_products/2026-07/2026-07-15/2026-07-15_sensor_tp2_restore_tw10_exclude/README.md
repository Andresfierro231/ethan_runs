---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/sensor_map_contract.csv
  - work_products/2026-07/2026-07-15/2026-07-15_sensor_policy_gate_opening_and_hydraulic_node_run/sensor_map_policy_refresh.csv
  - operational_notes/07-26/15/2026-07-15_sensor_and_sophisticated_modeling_decisions.md
tags: [sensor-map, TP2, TW10, forward-v1, validation-only]
task: AGENT-442
date: 2026-07-15
type: work_product_readme
status: complete
---
# TP2 Restore / TW10 Exclude Sensor-Map Refresh

This package refreshes the sensor-map policy requested for overnight work.
It does not use TP2 or TW10 as runtime model inputs or fit targets.

## Result

- TP2 source segment after refresh: `right_downcomer_bottom_horizontal_junction`.
- Current aggregate count: `5` TP +
  `10` TW.
- Aggregate count after TP2 finite/projection gates: `6` TP +
  `10` TW.
- TW10 after refresh: `excluded`.

TP2 is restored as a gated post-solve scoring candidate. It enters aggregate
RMSE only after projection, source-segment, and finite prediction gates pass.
TW10 remains excluded until the model emits an active-HX shell-state
temperature. Before/after RMSE impact is therefore pending finite TP2
prediction rows from the next scoring model.

## Outputs

- `sensor_tp2_tw10_policy_refresh.csv`
- `aggregate_sensor_count_delta.csv`
- `tp2_tw10_gate_status.csv`
- `summary.json`

## Guardrails

Native CFD outputs, registry/admission state, generated indexes, and external
`../cfd-modeling-tools/**` were not mutated.
