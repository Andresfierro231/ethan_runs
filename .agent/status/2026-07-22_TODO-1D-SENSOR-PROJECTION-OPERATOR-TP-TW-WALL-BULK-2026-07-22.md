---
provenance:
  - tools/analyze/build_1d_sensor_projection_operator_tp_tw_wall_bulk.py
  - tools/analyze/test_1d_sensor_projection_operator_tp_tw_wall_bulk.py
  - work_products/2026-07/2026-07-22/2026-07-22_1d_sensor_projection_operator_tp_tw_wall_bulk/summary.json
task: TODO-1D-SENSOR-PROJECTION-OPERATOR-TP-TW-WALL-BULK-2026-07-22
date: 2026-07-22
role: Sensor-map / Thermal-modeling / Forward-pred / Writer / Tester
type: status
status: complete
tags: [status, sensor-map, projection-operator, tp, tw, thermal-development]
related:
  - work_products/2026-07/2026-07-22/2026-07-22_1d_sensor_projection_operator_tp_tw_wall_bulk
---

# TODO-1D-SENSOR-PROJECTION-OPERATOR-TP-TW-WALL-BULK-2026-07-22

## Objective

Define the score-only measurement/projection operator from 1D bulk and wall
states to TP/TW observations, while preserving the guardrail that observed
validation temperatures are not runtime inputs.

## Outcome

Decision: `projection_operator_defined_diagnostic_only_no_runtime_temperature_release`.

The package defines `17` sensor rows: `6` TP rows use a bulk/fluid projection
operator, `10` TW rows use a wall-state projection operator, and `1` row
(`TW10`) remains excluded because the active-HX shell state is absent. D2
remains promising diagnostic context: TP RMSE improved from `13.5673279702 K`
to `4.38159298515 K`, but no bulk-to-TP correction is released.

## Changes Made

- Added task-owned projection-operator builder and unit test.
- Wrote `sensor_projection_operator_table.csv`.
- Wrote `runtime_legality_matrix.csv`.
- Wrote `writer_ready_projection_equations.csv`.
- Wrote `bulk_to_tp_release_status.csv`.
- Wrote `figures/svg/1d_sensor_projection_operator_map.svg`.
- Wrote README, source manifest, no-mutation guardrails, summary, status,
  journal, and import manifest.

## Validation

- `python3.11 tools/analyze/build_1d_sensor_projection_operator_tp_tw_wall_bulk.py`: passed; decision `projection_operator_defined_diagnostic_only_no_runtime_temperature_release`.
- `python3.11 -m unittest tools.analyze.test_1d_sensor_projection_operator_tp_tw_wall_bulk`: passed, 4 tests.

## Guardrails

- Runtime temperature release: false.
- Validation/holdout/external scoring: false.
- Source/property release, coefficient admission, final score, and S11/S12/S13/S15/S6
  trigger: false.
- Native-output, registry/admission, scheduler, solver/sampler/harvest/UQ,
  Fluid/external, and thesis-current mutation: false.
- Residual absorption into internal `Nu`: false.
