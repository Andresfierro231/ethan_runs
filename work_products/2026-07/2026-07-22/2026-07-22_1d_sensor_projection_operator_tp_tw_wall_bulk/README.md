---
provenance:
  task_id: TODO-1D-SENSOR-PROJECTION-OPERATOR-TP-TW-WALL-BULK-2026-07-22
  generated_at_utc: 2026-07-22T14:29:10.769373+00:00
tags:
  - sensor-map
  - projection-operator
  - tp
  - tw
related:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table
  - work_products/2026-07/2026-07-22/2026-07-22_mf_d2_tp_tw_qoi_projection_gate
---

# 1D Sensor Projection Operator: TP/TW Wall/Bulk

This package defines the score-only measurement operator from 1D bulk and wall
states to TP/TW observations. It does not release observed validation
temperatures as runtime inputs and does not release a bulk-to-TP thermal
development correction.

Open `sensor_projection_operator_table.csv` first. TP sensors use
`bulk_fluid_projection`; TW sensors use `wall_state_projection`; TW10 is
excluded because the active-HX shell state is absent.

Decision: `projection_operator_defined_diagnostic_only_no_runtime_temperature_release`.
