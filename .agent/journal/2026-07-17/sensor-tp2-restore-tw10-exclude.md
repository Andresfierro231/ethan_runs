---
provenance:
  - work_products/2026-07/2026-07-15/2026-07-15_sensor_policy_gate_opening_and_hydraulic_node_run/sensor_map_policy_refresh.csv
  - work_products/2026-07/2026-07-16/2026-07-16_tp2_1d_model_evidence/README.md
  - work_products/2026-07/2026-07-17/2026-07-17_sensor_tp2_restore_tw10_exclude/README.md
tags: [journal, sensor-map, TP2, TW10]
related:
  - .agent/status/2026-07-17_TODO-SENSOR-TP2-RESTORE-TW10-EXCLUDE.md
  - imports/2026-07-17_sensor_tp2_restore_tw10_exclude.json
task: TODO-SENSOR-TP2-RESTORE-TW10-EXCLUDE
date: 2026-07-17
role: Sensor-map/Forward-pred/Implementer/Tester/Writer
type: journal
status: complete
---
# TP2 Restore / TW10 Exclude Journal

## Files Inspected

- `work_products/2026-07/2026-07-15/2026-07-15_sensor_policy_gate_opening_and_hydraulic_node_run/sensor_map_policy_refresh.csv`
- `work_products/2026-07/2026-07-16/2026-07-16_tp2_1d_model_evidence/tp2_projected_sensor_registry.csv`
- `work_products/2026-07/2026-07-16/2026-07-16_tp2_1d_model_evidence/tp2_sensor_level_evidence.csv`
- `work_products/2026-07/2026-07-16/2026-07-16_tp2_1d_model_evidence/aggregate_rmse_before_after.csv`
- `work_products/2026-07/2026-07-16/2026-07-16_tp2_1d_model_evidence/tp2_gate_status.csv`

## Files Changed

- `tools/analyze/build_sensor_tp2_restore_scorecard.py`
- `tools/analyze/test_sensor_tp2_restore_scorecard.py`
- `work_products/2026-07/2026-07-17/2026-07-17_sensor_tp2_restore_tw10_exclude/`
- `.agent/status/2026-07-17_TODO-SENSOR-TP2-RESTORE-TW10-EXCLUDE.md`
- `.agent/journal/2026-07-17/sensor-tp2-restore-tw10-exclude.md`
- `imports/2026-07-17_sensor_tp2_restore_tw10_exclude.json`
- `.agent/BOARD.md` own row status

## Interpretation

TP2 is now usable as validation-only 1D aggregate evidence. TW10 remains correctly blocked rather than silently scored.

## Recommended Next Action

Make future TP/TW scorecards consume `sensor_policy_scorecard.csv` and keep TP/TW out of runtime inputs.
