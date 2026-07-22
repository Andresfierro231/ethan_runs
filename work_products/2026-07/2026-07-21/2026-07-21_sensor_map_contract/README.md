---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s7_sensor_map_tp_tw_contract/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s7_sensor_map_tp_tw_contract/sensor_coordinate_ledger.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s7_sensor_map_tp_tw_contract/one_d_path_position_map.csv
tags: [sensor-map, thesis, runtime-leakage, score-only]
related:
  - .agent/status/2026-07-21_TODO-PRED-SENSOR-MAP.md
task: TODO-PRED-SENSOR-MAP
date: 2026-07-21
role: Writer/Implementer/Reviewer
type: work_product
status: complete
---
# Sensor Map Contract Consolidation

This package closes the canonical `TODO-PRED-SENSOR-MAP` row by consolidating
the completed S7 TP/TW sensor-map contract. It does not reopen sensor
extraction, Fluid code, model scoring, fitting, or closure admission.

## Decision

- TP/TW sensors reviewed: `17`
- mapped exactly enough for score-only 1D comparison: `1` (`TP2`)
- bounded/provisional sensors: `15`
- excluded sensors: `1` (`TW10`, no active heat-exchanger shell state)
- runtime target-temperature permissions: `0`
- fit/model-selection permissions: `0`

## Outputs

- `sensor_map_consolidation.csv`
- `score_only_policy.csv`
- `remaining_coordinate_caveats.csv`
- `summary.json`

## Guardrails

Temperature sensors remain score-only and diagnostic. They are not runtime
inputs, closure-fit targets, model-selection criteria, or final predictive
claims. Temperature-probe discussion stays secondary to energy and branch heat
parity.
