---
provenance:
  - tools/analyze/build_thesis_figtable_model_form_and_blocked_scorecard_panels.py
  - tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/tp_tw_temperature_elevation_panel_points.csv
tags: [thesis, figures, tp-tw, prediction-labels, closed-curve, no-admission]
related:
  - .agent/journal/2026-07-22/thesis-figtable-tp-tw-prediction-label-and-closed-curve-polish.md
  - imports/2026-07-22_thesis_figtable_tp_tw_prediction_label_and_closed_curve_polish.json
task: TODO-THESIS-FIGTABLE-TP-TW-PREDICTION-LABEL-AND-CLOSED-CURVE-POLISH-2026-07-22
date: 2026-07-22
role: Figures / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# Status

## Objective

Polish the corrected TP/TW temperature-elevation thesis panels so TP5 connects
to TP6, TW11 closes back to TW1, and the available M3 TP/TW prediction markers
are labeled directly on the figure.

## Changes Made

- Added explicit curve-topology fields to
  `tp_tw_temperature_elevation_panel_points.csv`:
  `target_next_sensor_in_plot`, `prediction_next_sensor_in_plot`, and
  `prediction_label`.
- Kept TP target and prediction ordering continuous through TP5->TP6.
- Closed the TW target and prediction curves from TW11 back to TW1, matching the
  reference-plot convention that omits TW10 but closes the wall loop.
- Added direct `M3 TP*` and `M3 TW*` labels to available prediction markers.
- Moved the legend below the data region so prediction labels remain visible.
- Updated README/captions/summary metrics to document the closed-curve and
  prediction-label choices.

## Validation

- `python3.11 tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py`
  passed.
- Data checks after regeneration:
  - Salt2 TP5 target next sensor: `TP6`.
  - Salt2 TP5 prediction next sensor: `TP6`.
  - Salt2 TW11 target next sensor: `TW1`.
  - Salt2 TW11 prediction next sensor: `TW1`.
  - Prediction marker label rows: `45`.
- Visual checks inspected regenerated Salt2 and Salt4 PNG panels.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry/admission state mutated: no.
- Scheduler, solver, sampler, harvest, or UQ launched: no.
- Fluid source or external repo edited: no.
- Thesis current/LaTeX files edited: no.
- Validation/holdout/external-test new scoring performed: no.
- Fitting, tuning, model selection, source/property release, coefficient
  admission, or final score claim made: no.
- S11/S12/S13/S15/S6 trigger changed: no.
- Blocker register changed before closeout: no.

## Remaining Caveats

These are figure-polish changes only. M3 remains a legacy diagnostic comparator,
not an admitted closure or frozen predictive candidate.
