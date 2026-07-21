---
provenance:
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/sensor_map_contract.csv
  - /scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/tamu_first_order_model/Fluid/docs/sensor_location_status.md
  - /scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/cross_model_comparison/campaigns/2026-05-29_ethan_salt_test_2_v1/reports/sensor_location_reference.md
tags: [forward-model, predictive-1d, sensor-prediction, validation-targets]
related:
  - .agent/status/2026-07-13_AGENT-302.md
  - imports/2026-07-13_predictive_sensor_map_contract.json
task: AGENT-302
date: 2026-07-13
role: Writer / Implementer
type: journal
status: complete
---
# Predictive Sensor Map Contract

Date: 2026-07-13

Agent role: Writer / Implementer

Task ID: AGENT-302

Branch/worktree: `/scratch/09748/andresfierro231/projects_scratch/ethan_runs`

## Files Inspected

- `AGENTS.md`
- `.agent/BOARD.md`
- `.agent/FILE_OWNERSHIP.md`
- `.agent/ROLES.md`
- `.agent/DOC_FRONTMATTER_SCHEMA.md`
- `.agent/JOURNAL_POLICY.md`
- `operational_notes/maps/forward-predictive-model.md`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_input_contract/**`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_imposed_cooler/**`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_validation_split/**`
- `/scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/tamu_first_order_model/AGENTS.md`
- `/scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/tamu_first_order_model/Fluid/AGENTS.override.md`
- `/scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/tamu_first_order_model/Fluid/README.md`
- `/scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/tamu_first_order_model/Fluid/docs/sensor_location_status.md`
- `/scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/tamu_first_order_model/Fluid/docs/provisional_sensor_locations.csv`
- `/scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/tamu_first_order_model/Fluid/docs/provisional_sensor_locations.md`
- `/scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/tamu_first_order_model/Fluid/docs/ethan_probe_location_reference.md`
- `/scratch/09748/andresfierro231/projects_scratch/cfd-modeling-tools/cross_model_comparison/campaigns/2026-05-29_ethan_salt_test_2_v1/reports/sensor_location_reference.md`

## Files Changed

- `work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/build_sensor_map_contract.py`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/README.md`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/sensor_map_contract.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/native_cfd_probe_family_contract.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/runtime_target_policy.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/sensor_map_blockers.csv`
- `work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/summary.json`
- `.agent/status/2026-07-13_AGENT-302.md`
- `.agent/journal/2026-07-13/predictive-sensor-map-contract.md`
- `imports/2026-07-13_predictive_sensor_map_contract.json`

## Commands Run

- `python3 work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/build_sensor_map_contract.py`
- `python3 -m py_compile work_products/2026-07/2026-07-13/2026-07-13_predictive_sensor_map_contract/build_sensor_map_contract.py`

## Observations

- Fluid documentation explicitly marks current TP/TW coordinates as provisional
  first-model coordinates, not exact experimental measurements.
- Native Ethan CFD TP channels are single nominal points, while TW channels are
  four-probe families (`back`, `bottom`, `front`, `top`). A one-coordinate TW
  score therefore needs an explicit aggregation policy.
- Forward-v0 emits finite predictions for 15 of 17 current TP/TW labels. `TP2`
  and `TW10` are the current exceptions.
- `TP2` is a coordinate-contract issue: current Fluid provisional `TP2` is
  off the current 1D path, while native CFD TP2 and notes bound it to the right
  downcomer/bottom-horizontal junction.
- `TW10` is a model-output issue: it is a cooling-jacket shell surrogate, and
  imposed-cooler forward-v0 does not emit finite active-HX shell temperature.

## Result

Sensor-temperature claims can be scored now only as partial, provisional,
diagnostic targets: 15 mapped sensors have finite forward-v0 predictions.
They cannot yet be used for thesis-grade exact-coordinate claims, and they
cannot be runtime inputs or fit anchors.

## Incomplete Lines / Next Steps

- Register or route the four sensor-map blockers through the coordinator if
  `.agent/blockers.yml` needs a curated global blocker entry; AGENT-302 did not
  edit that coordinator-owned path.
- Correct or supersede `TP2` in the Fluid registry, then rerun forward-v0 sensor
  outputs.
- Add a declared TW native-probe aggregation policy before claiming native CFD
  TW coordinate parity.
- Decide whether `TW10` is excluded from imposed-cooler forward-v0 scoring or
  supplied by a forward mode that emits finite active-HX shell temperature.

