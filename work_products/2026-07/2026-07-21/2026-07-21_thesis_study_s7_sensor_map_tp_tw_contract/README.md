---
provenance:
  task: TODO-THESIS-STUDY-S7-SENSOR-MAP-TP-TW-CONTRACT-2026-07-21
  generated_by: work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s7_sensor_map_tp_tw_contract/build_s7_sensor_map_tp_tw_contract.py
tags:
  - thesis
  - sensor-map
  - runtime-leakage
related:
  - work_products/2026-07/2026-07-15/2026-07-15_sensor_tp2_restore_tw10_exclude/sensor_tp2_tw10_policy_refresh.csv
  - work_products/2026-07/2026-07-16/2026-07-16_tp2_1d_model_evidence/tp2_projected_sensor_registry.csv
---
# S7 TP/TW Sensor-Map Contract

This package turns the existing TP/TW sensor-map evidence into a thesis-facing contract. It is a documentation and policy package, not a model-fit or closure-admission package.

## Results

- Sensor policy rows reviewed: 17.
- Coordinate ledger rows: 17.
- 1D path-position rows: 17.
- Acceptance classes: `1` mapped, `15` bounded, `1` excluded.
- Runtime target-temperature permissions: `0` allowed.
- Fit permissions: `0` allowed.
- Model-selection permissions: `0` allowed.

## Artifacts

- `sensor_coordinate_ledger.csv` records provisional registry coordinates and staged native probe-coordinate centroids without upgrading them to exact experimental measurements.
- `one_d_path_position_map.csv` maps each scoreable TP/TW sensor to a 1D segment or junction state; TW10 is excluded because the current model has no active heat-exchanger shell state.
- `bounded_or_excluded_sensor_rationale.csv` records the reason each sensor is mapped, bounded, or excluded.
- `score_only_target_policy.csv` makes TP/TW rows score targets only and keeps fit/model-selection permissions false.
- `runtime_input_leakage_audit.csv` records the leakage gates used by downstream thesis sections.
- `source_manifest.csv` lists the exact source paths used.

## Claim Boundary

TP/TW residuals can be used as post-solve score targets and diagnostic evidence. They must not become runtime features, closure fit targets, or model-selection criteria. Temperature-probe claims stay secondary to energy balance and branch heat parity until a later row explicitly admits stronger evidence.
