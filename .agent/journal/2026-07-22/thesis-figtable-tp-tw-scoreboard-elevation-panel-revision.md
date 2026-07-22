---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/signed_sensor_errors.csv
  - work_products/2026-07/2026-07-21/2026-07-21_thesis_study_s7_sensor_map_tp_tw_contract/sensor_coordinate_ledger.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_n4_sensor_qoi_projection_uncertainty_table/sensor_qoi_projection_table.csv
  - tools/analyze/build_thesis_figtable_model_form_and_blocked_scorecard_panels.py
tags: [thesis, figures, scoreboard, sensors, diagnostic-only]
related:
  - .agent/status/2026-07-22_TODO-THESIS-FIGTABLE-TP-TW-SCOREBOARD-ELEVATION-PANEL-REVISION-2026-07-22.md
  - imports/2026-07-22_thesis_figtable_tp_tw_scoreboard_elevation_panel_revision.json
task: TODO-THESIS-FIGTABLE-TP-TW-SCOREBOARD-ELEVATION-PANEL-REVISION-2026-07-22
date: 2026-07-22
role: Figures / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# TP/TW Scoreboard Elevation Panel Revision

## Attempted

The earlier figure package contained a TP-only temperature-vs-elevation panel
derived from the reference plot style, but its coordinate constants came from
the reference script and were not an acceptable evidence source. I replaced the
primary panel generator with a scoreboard-backed TP/TW generator.

## Observed

The master scoreboard has M3 target rows for TP1-TP6 and TW1-TW11 in
Salt2/Salt3/Salt4. M3 finite predictions are available for TP1 and TP3-TP6,
but not TP2. M3 finite predictions are available for TW1-TW9 and TW11, but not
TW10. N4 marks TW10 excluded because the active heat-exchanger shell state is
absent.

The S7 sensor coordinate ledger provides `native_centroid_y_m` and
`registry_y_m` values plus coordinate caveats. The revised panel table records
that coordinate basis instead of hiding it in plotting constants.

## Inferred

The right correction is to keep TP2 and TW10 visible but distinct:

- TP2 remains a plotted TP target because it is a validation-only projected
  target, while the missing M3 prediction is annotated.
- TW10 is preserved in the output table and marked on the panel as excluded/no
  M3, but it is not connected into the TW target curve because the active HX
  shell state is not emitted.

This makes the figure scientifically honest: it shows M3's cold trend and shape
context without claiming a complete TP/TW predictive curve.

## Caveats

The y-axis is an S7 sensor-ledger elevation coordinate, not an exact experimental
measurement. The output CSV carries `coordinate_claim_level`, `placement_class`,
and `coordinate_caveat` for each sensor so the thesis caption can describe the
coordinate uncertainty.

M3 remains legacy numeric context only. These panels do not admit a closure, do
not release any source/property coefficient, and do not publish final predictive
accuracy.

## Next Useful Actions

Use the three `m3_tp_tw_temperature_vs_elevation_salt_*` panels as the preferred
thesis insertion figures for the M3 diagnostic profile. If mentor feedback wants
less line crossing, the next purely visual row can split each Salt case into
side-by-side TP and TW axes while preserving the same
`tp_tw_temperature_elevation_panel_points.csv` source table.
