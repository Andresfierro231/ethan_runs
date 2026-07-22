---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table/sensor_qoi_projection_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table/sensor_runtime_input_audit.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table/sensor_uncertainty_caveat_table.csv
  - work_products/2026-07/2026-07-22/2026-07-22_1d_sensor_projection_operator_tp_tw_wall_bulk/sensor_projection_operator_table.csv
tags: [thesis, sensors, projection, qoi, no-runtime-temperature]
related:
  - .agent/status/2026-07-22_TODO-THESIS-SENSOR-PROJECTION-APPENDIX-TABLE-PACKET-2026-07-22.md
  - .agent/journal/2026-07-22/thesis-sensor-projection-appendix-table-packet.md
task: TODO-THESIS-SENSOR-PROJECTION-APPENDIX-TABLE-PACKET-2026-07-22
date: 2026-07-22
role: Writer/Reviewer/Tester
type: work_product
status: complete
supersedes: []
superseded_by:
---
# Thesis Sensor Projection Appendix Table Packet

Decision: `sensor_projection_appendix_ready_no_runtime_temperature_release`.

This packet converts the N4 sensor/QOI projection evidence and the 1D projection-operator table into appendix-ready CSVs. The table set keeps TP/TW temperatures as post-solve score targets only: `0` rows allow runtime temperature inputs, `0` rows allow fitting, and `0` rows allow model selection.

Outputs:
- `appendix_sensor_projection_table.csv`: 17 TP/TW rows with segment/state, marker, elevation, projection equation, release status, and caveat.
- `uncertainty_caveat_table.csv`: bounded/mapped/excluded coordinate caveats and publication language.
- `score_table_effect_matrix.csv`: score inclusion effect; TW10 remains excluded.
- `runtime_temperature_input_audit.csv`: row-level no-runtime-temperature audit.
- `tp_tw_panel_caption_source_table.csv`: caption/source links for TP/TW panel import.
- `summary.json`: compact counts and guardrail flags.

Key boundary: TP2 is mapped to the bottom-horizontal/right-downcomer junction for score-only projection, most sensors are bounded rather than exact-coordinate claims, and TW10 is excluded because the active HX shell state is not emitted.

Guardrails preserved: no runtime temperature release, no fit or model-selection release, no coefficient admission, no final score, no thesis body edit, no solver output mutation, and no registry mutation.
