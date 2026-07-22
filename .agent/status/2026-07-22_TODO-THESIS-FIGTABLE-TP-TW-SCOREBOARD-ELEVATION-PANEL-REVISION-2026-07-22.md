---
provenance:
  - tools/analyze/build_thesis_figtable_model_form_and_blocked_scorecard_panels.py
  - tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/summary.json
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/tp_tw_temperature_elevation_panel_points.csv
tags: [thesis, figures, model-form-scoreboard, tp-tw-elevation, no-admission]
related:
  - .agent/journal/2026-07-22/thesis-figtable-tp-tw-scoreboard-elevation-panel-revision.md
  - imports/2026-07-22_thesis_figtable_tp_tw_scoreboard_elevation_panel_revision.json
task: TODO-THESIS-FIGTABLE-TP-TW-SCOREBOARD-ELEVATION-PANEL-REVISION-2026-07-22
date: 2026-07-22
role: Figures / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# TODO-THESIS-FIGTABLE-TP-TW-SCOREBOARD-ELEVATION-PANEL-REVISION-2026-07-22

## Objective

Revise the thesis temperature-vs-elevation figure package so the primary panels
use master-scoreboard temperatures rather than the placeholder values from the
old reference script, include TP1-TP6 and TW1-TW9/TW11, and explicitly identify
missing M3 TP2 and excluded/missing TW10.

## Outcome

Completed. The builder now writes `tp_tw_temperature_elevation_panel_points.csv`
with `51` rows: `17` TP/TW sensors per Salt2/Salt3/Salt4 case. Target and M3
temperature values come from
`work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/signed_sensor_errors.csv`.
Elevation coordinates come from the S7 sensor coordinate ledger
`native_centroid_y_m` with fallback to `registry_y_m`; the CSV records the
coordinate field, claim level, placement class, caveat, and one-dimensional
projection metadata.

The regenerated primary figures are:

- `work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/figures/svg/m3_tp_tw_temperature_vs_elevation_salt_2.svg`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/figures/svg/m3_tp_tw_temperature_vs_elevation_salt_3.svg`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/figures/svg/m3_tp_tw_temperature_vs_elevation_salt_4.svg`

PNG companions were also regenerated. The previous signed-error, model-form
ladder, and blocked-scorecard panels remain diagnostic-only supporting outputs.

## Changes Made

- Replaced the TP-only panel generator with a TP/TW scoreboard-backed generator.
- Added S7 sensor coordinate and N4 sensor projection metadata to the panel CSV.
- Regenerated Salt2/Salt3/Salt4 TP/TW SVG and PNG panels.
- Updated the caption ledger, source manifest, summary, README, and regression
  test for the new TP/TW output contract.

## Validation

- `python3.11 tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py` passed.
- Visual spot-check performed on Salt2 and Salt4 PNGs. Both show TP1-TP6,
  TW1-TW9/TW11, M3 TP/TW prediction overlays, TP2 missing-M3 annotation, and
  TW10 excluded/no-M3 annotation.

## Guardrails

- Native CFD/OpenFOAM output mutation: none.
- Registry/admission mutation: none.
- Scheduler action: none.
- Solver/postprocessing/sampler/harvest/UQ launch: none.
- Validation/holdout/external-test new scoring or tuning: none.
- Fitting/model selection: none.
- Source/property release or coefficient admission: none.
- Closure admission or final predictive score claim: none.
- S11/S12/S13/S15/S6 trigger: none.
- Thesis current/LaTeX edit: none.
- Blocker-register or generated-index refresh before closeout: none.
