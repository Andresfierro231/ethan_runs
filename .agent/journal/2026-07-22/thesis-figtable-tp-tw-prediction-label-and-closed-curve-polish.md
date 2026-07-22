---
provenance:
  - tools/analyze/build_thesis_figtable_model_form_and_blocked_scorecard_panels.py
  - tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/figures/png/m3_tp_tw_temperature_vs_elevation_salt_2.png
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/figures/png/m3_tp_tw_temperature_vs_elevation_salt_4.png
tags: [thesis, figures, tp-tw, prediction-labels, closed-curve]
related:
  - .agent/status/2026-07-22_TODO-THESIS-FIGTABLE-TP-TW-PREDICTION-LABEL-AND-CLOSED-CURVE-POLISH-2026-07-22.md
  - imports/2026-07-22_thesis_figtable_tp_tw_prediction_label_and_closed_curve_polish.json
task: TODO-THESIS-FIGTABLE-TP-TW-PREDICTION-LABEL-AND-CLOSED-CURVE-POLISH-2026-07-22
date: 2026-07-22
role: Figures / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# Journal

## Attempted

Applied the requested figure polish after the target/elevation basis correction:
ensure TP5 connects to TP6, close TW11 back to TW1, and label M3 TP/TW
prediction markers.

## Observed

The TP curve already used the ordered TP1-TP6 sensor sequence, but the plot did
not expose this topology in the CSV. The TW target order was TW1-TW9/TW11 and
therefore stopped at TW11 instead of returning to TW1 like the reference plot.
M3 prediction markers were differentiated by style and legend but were not
directly labeled.

## Inferred

The right contract is to preserve TW10 as an unplotted shell-state row, close
the visible TW loop from TW11 back to TW1, and label all available prediction
markers without changing target values, elevations, predictions, or admission
state.

## Changed

Added curve-topology columns and prediction labels to the TP/TW point table.
Updated plotting to draw TW rows as `TW1..TW9,TW11,TW1` for both target and M3
prediction curves. Added visible `M3 TP*`/`M3 TW*` marker labels and moved the
legend below the plot area.

## Validation

The regression test passed and now asserts TP5->TP6, TW11->TW1, and 45 labeled
prediction markers. Salt2 and Salt4 PNGs were visually inspected after
regeneration.

## Next Useful Actions

Use the corrected temperature-elevation panels as the preferred thesis figure
for target-vs-M3 diagnostic shape. Further polish should focus on label
collision tuning only; the scientific basis should remain experimental targets
plus reference-geometry elevation.
