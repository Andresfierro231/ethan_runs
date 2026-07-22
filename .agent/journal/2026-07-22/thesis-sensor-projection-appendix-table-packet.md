---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table/sensor_qoi_projection_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table/sensor_runtime_input_audit.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table/sensor_uncertainty_caveat_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_sensor_projection_operator_tp_tw_wall_bulk/sensor_projection_operator_table.csv
tags: [journal, thesis, sensors, qoi-projection]
related:
  - .agent/status/2026-07-22_TODO-THESIS-SENSOR-PROJECTION-APPENDIX-TABLE-PACKET-2026-07-22.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_sensor_projection_appendix_table_packet/README.md
task: TODO-THESIS-SENSOR-PROJECTION-APPENDIX-TABLE-PACKET-2026-07-22
date: 2026-07-22
role: Writer / Reviewer / Tester
type: journal
status: complete
---
# Thesis Sensor Projection Appendix Table Packet

## Attempted

Claimed the sensor projection appendix row and joined the N4 sensor/QOI projection tables with the 1D projection-operator evidence. Wrote a small appendix-ready packet under `work_products/2026-07/2026-07-22/2026-07-22_thesis_sensor_projection_appendix_table_packet`.

## Observed

There are 17 TP/TW sensor rows: 15 bounded, 1 mapped, and 1 excluded. TP2 is the mapped row. TW10 is excluded. Every runtime-audit row has `runtime_temperature_allowed=false`, `fit_allowed=false`, and `model_selection_allowed=false`.

## Inferred

The sensor material is ready for appendix/table transfer as a score-target projection contract, not as a runtime-temperature release. It supports thesis clarity around TP/TW scoring, projection caveats, and why exact-coordinate or thermal-development correction claims remain bounded.

## Caveats

This packet does not admit a coefficient, release source/property inputs, score validation/holdout/external rows, or edit the thesis body.

## Next Useful Actions

Use `appendix_sensor_projection_table.csv` and `runtime_temperature_input_audit.csv` in a later exact thesis transfer row. Keep TP2 and TW10 caveats visible in any caption or table note.
