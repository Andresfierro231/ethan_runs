---
provenance:
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/tp_temperature_elevation_panel_points.csv
  - tools/analyze/build_thesis_figtable_model_form_and_blocked_scorecard_panels.py
tags: [thesis, figures, tp-elevation, m3, no-admission]
related:
  - .agent/journal/2026-07-22/thesis-figtable-tp-elevation-panel-revision.md
  - imports/2026-07-22_thesis_figtable_tp_elevation_panel_revision.json
task: TODO-THESIS-FIGTABLE-TP-ELEVATION-PANEL-REVISION-2026-07-22
date: 2026-07-22
role: Figures / Writer / Reviewer / Tester
type: status
status: complete
---
# Status: TODO-THESIS-FIGTABLE-TP-ELEVATION-PANEL-REVISION-2026-07-22

## Objective

Replace the cramped signed-error-first visual with a thesis-usable TP
temperature-vs-elevation figure set. The revision must show TP1-TP6, preserve
the physical elevation coordinate, and explicitly mark the missing M3 TP2
prediction rather than silently dropping the sensor.

## Changes Made

Updated
`tools/analyze/build_thesis_figtable_model_form_and_blocked_scorecard_panels.py`
to generate three primary TP temperature-vs-elevation figures, one each for
Salt2, Salt3, and Salt4. Updated the package README, caption ledger, source
manifest, summary, and regression test so the TP elevation panels are the first
insertion targets and the signed-error plot is secondary diagnostic material.

Generated outputs:

- `figures/svg/m3_tp_temperature_vs_elevation_salt_2.svg`
- `figures/png/m3_tp_temperature_vs_elevation_salt_2.png`
- `figures/svg/m3_tp_temperature_vs_elevation_salt_3.svg`
- `figures/png/m3_tp_temperature_vs_elevation_salt_3.png`
- `figures/svg/m3_tp_temperature_vs_elevation_salt_4.svg`
- `figures/png/m3_tp_temperature_vs_elevation_salt_4.png`
- `tp_temperature_elevation_panel_points.csv`

## Outcome

The revised package reports:

- figure panels: `6`
- TP temperature-elevation rows: `18`
- TP sensors shown per case: `TP1` through `TP6`
- missing M3 TP predictions marked: `3` (`TP2` for Salt2, Salt3, Salt4)
- final score values: `0`
- decision: `thesis_figure_panels_ready_no_closure_admission`

## Validation

- `python3.11 -m py_compile tools/analyze/build_thesis_figtable_model_form_and_blocked_scorecard_panels.py tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py` passed.
- `python3.11 tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py` passed.
- Visual inspection passed for `m3_tp_temperature_vs_elevation_salt_2.png`, `m3_tp_temperature_vs_elevation_salt_3.png`, and `m3_tp_temperature_vs_elevation_salt_4.png`: all TP1-TP6 targets are visible, TP2 missing M3 prediction is labeled, and the layout is no longer cramped.

## Guardrails

- Native CFD/OpenFOAM outputs: read-only, not mutated.
- Registry/admission state: read-only, not mutated.
- Scheduler/solver/sampler/harvest/UQ: not launched.
- Fluid/external repositories: not edited.
- Thesis current/LaTeX files: not edited.
- Validation/holdout/external-test scoring: not performed.
- Fitting/tuning/model selection: not performed.
- Source/property release and Qwall release: not performed.
- Coefficient admission and final score claims: not made.
- S11/S12/S13/S15/S6 triggers: not fired.
- Blocker register: not changed.
- Residual absorption into internal Nu: not performed.

## Next Useful Actions

Use the TP elevation SVGs as the thesis-facing figures. Keep
`m3_signed_sensor_error_shape.svg` only as a secondary diagnostic/audit figure
unless it receives a separate redesign.
