---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/sensor_map_contract.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/native_cfd_probe_family_contract.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/runtime_target_policy.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/sensor_map_blockers.csv
  - /scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/tamu_first_order_model/Fluid/docs/sensor_location_status.md
  - /scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/tamu_first_order_model/Fluid/docs/provisional_sensor_locations.csv
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler/forward_v0_sensor_predictions_experimental.csv
tags: [forward-model, predictive-1d, sensor-prediction, validation-targets]
related:
  - .agent/journal/2026-07-13/predictive-sensor-map-contract.md
  - .agent/status/2026-07-13_AGENT-302.md
  - imports/2026-07-13_predictive_sensor_map_contract.json
  - operational_notes/maps/forward-predictive-model.md
task: AGENT-302
date: 2026-07-13
role: Writer / Implementer
type: work_product
status: complete
---
# Predictive Sensor Map Contract

Generated package for `AGENT-302`.

## Start Here

Read in this order:

1. `sensor_map_contract.csv`
2. `runtime_target_policy.csv`
3. `sensor_map_blockers.csv`
4. `native_cfd_probe_family_contract.csv`
5. `summary.json`

## Why This Exists

Forward predictive scoring needs a clean split between runtime inputs and score
targets. TP/TW temperatures are score targets only. They may be joined after the
forward solve, but measured experimental temperatures and CFD sensor references
must not be consumed as runtime anchors, fit targets, or sensor-wise correction
tables.

## Current Result

The package maps all 17 current Fluid TP/TW labels to the best available sensor
contract.

- `15` sensors are provisionally scoreable for diagnostic forward-v0 sensor
  tables using the current Fluid point registry and finite forward-v0
  predictions.
- `TP2` is blocked in the current Fluid registry because its provisional point
  is off the current 1D path; native CFD TP2 and Fluid notes bound it to the
  right-downcomer/bottom-horizontal junction.
- `TW10` is blocked for imposed-cooler forward-v0 scoring because it is a
  cooling-jacket shell surrogate and that mode does not emit finite active-HX
  shell temperature for the sensor.
- No sensor-temperature claim is survey-grade. Fluid's own status note says the
  current coordinates are provisional first-model coordinates, not exact
  experimental measurements.

## Output Contract

- `sensor_map_contract.csv`: one row per TP/TW label with runtime role,
  provisional Fluid coordinates, 1D path projection, native CFD coordinate
  evidence, forward-v0 prediction availability, score status, and blockers.
- `native_cfd_probe_family_contract.csv`: native Ethan CFD probe-family summary.
  TP channels are single nominal points; TW channels are four-probe families
  and must not be silently flattened without an explicit aggregation rule.
- `runtime_target_policy.csv`: machine-readable guardrail separating runtime
  setup inputs from validation targets and mapping metadata.
- `sensor_map_blockers.csv`: open blockers and next data needed.
- `build_sensor_map_contract.py`: reproducible package generator.
- `summary.json`: counts, blocked sensors, and source paths.

## Trusted Inputs

- Fluid sensor status and provisional registry:
  `/scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/tamu_first_order_model/Fluid/docs/sensor_location_status.md`
  and `docs/provisional_sensor_locations.csv`.
- Native Ethan CFD probe-family reference:
  `/scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/cross_model_comparison/campaigns/2026-05-29_ethan_salt_test_2_v1/`.
- Forward-v0 sensor streams:
  `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler/`.
- Predictive input and validation-split contracts:
  `work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/`
  and `work_products/2026-07/2026-07-13/2026-07-13_predictive_validation_split/`.

## Do Not Do

- Do not use TP/TW measured values as runtime inputs.
- Do not fit thermal corrections to TP/TW residuals.
- Do not claim exact experimental coordinates from the current Fluid registry.
- Do not flatten native CFD TW four-probe families into one coordinate without a
  declared aggregation policy.
- Do not include `TP2` or `TW10` in current forward-v0 sensor score claims until
  their blockers clear or an explicit exclusion policy is declared.

