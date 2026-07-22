---
provenance:
  - tools/analyze/build_thesis_figtable_model_form_and_blocked_scorecard_panels.py
  - tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/signed_sensor_errors.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/model_form_summary.csv
tags: [thesis, figures, model-form-scoreboard, tp-tw-elevation, predictive-triage]
related:
  - .agent/status/2026-07-22_TODO-THESIS-FIGTABLE-MODEL-FORM-FOLDER-AND-SCOREBOARD-READER-2026-07-22.md
  - imports/2026-07-22_thesis_figtable_model_form_folder_and_scoreboard_reader.json
task: TODO-THESIS-FIGTABLE-MODEL-FORM-FOLDER-AND-SCOREBOARD-READER-2026-07-22
date: 2026-07-22
role: Figures / Forward-pred / Implementer / Tester / Writer / Reviewer
type: journal
status: complete
---
# Journal

## Attempted

Extended the thesis model-form figure/table package from an M3-centered figure
set to a reusable master-scoreboard reader that emits comparable TP/TW,
TP-only, and signed-error panels for every current scoreboard model form. The
folder structure was changed to put the model form before the figure type.

## Observed

The scoreboard currently has finite TP/TW prediction rows for `M1`, `M1b`,
`M2`, and `M3`. All four forms lack TP2 predictions, and TW10 remains excluded
from plotted curves because it represents the active heat-exchanger shell state
that current model forms do not emit.

Against experimental TP/TW targets, `M3` is the closest current numeric
comparator with RMSE `19.5676078164 K`. `M2` is second with RMSE
`29.0171223641 K`. `M1b` and `M1` remain far worse historical CFD-boundary
replay forms with RMSE values above `165 K`.

## Inferred

`M3` is the current best legacy numeric comparator for thesis figure discussion,
but it should not be described as the predictive model. The stronger future
predictive direction is still the `M5 / MF-04` throughflow-plus-recirculation
exchange-cell family, because it is the path most aligned with the active
source/Qwall/UQ/freeze blocker line. That family remains diagnostic only until
the relevant gates release it.

## Changed

- Reworked figure writing to `figures/<model_form>/<category>/{svg,png}/` for
  model-specific categories.
- Kept non-scoring progress figures under `figures/progress/{svg,png}/`.
- Added model-form discovery from the master scoreboard rather than hardcoding
  M3.
- Added per-model README generation with the model definition, numeric rank,
  RMSE values, source paths, and claim boundary.
- Added `model_form_summary.csv` with model-level ranking and disposition.
- Updated regression tests to assert the full folder contract and generated
  counts.

## Validation

`python3.11 -m py_compile tools/analyze/build_thesis_figtable_model_form_and_blocked_scorecard_panels.py`
passed.

`python3.11 tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py`
passed after regenerating the package.

## Next Useful Actions

Use `figures/M3/tp_tw_vs_elevation/{svg,png}/` as the current best numeric
comparison for thesis narrative figures, with `figures/M2/...` as the closest
alternative. Keep `M1` and `M1b` available mainly as historical ladder context.
Do not promote any of these to final predictive status. Continue the predictive
science line through the source/Qwall/UQ/freeze gates for `M5 / MF-04`.
