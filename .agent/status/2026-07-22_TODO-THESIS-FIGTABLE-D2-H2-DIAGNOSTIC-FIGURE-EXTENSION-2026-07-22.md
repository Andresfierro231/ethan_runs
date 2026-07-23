---
provenance:
  - tools/analyze/build_thesis_figtable_model_form_and_blocked_scorecard_panels.py
  - tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/model_form_summary.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/summary.json
tags: [thesis, figures, d2, passive-h2, diagnostic-only, no-admission]
related:
  - .agent/journal/2026-07-22/thesis-figtable-d2-h2-diagnostic-figure-extension.md
  - imports/2026-07-22_thesis_figtable_d2_h2_diagnostic_figure_extension.json
task: TODO-THESIS-FIGTABLE-D2-H2-DIAGNOSTIC-FIGURE-EXTENSION-2026-07-22
date: 2026-07-22
role: Figures / Thermal-modeling / Forward-pred / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# Status

## Objective

Extend the thesis figure package beyond the current master-scoreboard model
forms by adding D2 diagnostic TP/TW panels and PASSIVE-H2 operator-only panels,
without changing admission, scoring, release, or freeze state.

## Changes Made

- Added `D2_M3_sensor_kind_offsets_train` to the reusable TP/TW elevation and
  signed-error pipelines using completed diagnostic addendum rows.
- Generated D2 TP/TW elevation panels, TP-only panels, and signed-error panels
  under `figures/D2_M3_sensor_kind_offsets_train/...`.
- Added `PASSIVE-H2-CAND001` as an operator-only model-form folder with three
  figures under `figures/PASSIVE-H2-CAND001/operator/{svg,png}/`.
- Added PASSIVE-H2 operator CSVs:
  `passive_h2_operator_case_points.csv`,
  `passive_h2_operator_family_points.csv`, and
  `passive_h2_operator_global_patch_points.csv`.
- Updated `model_form_summary.csv`, `caption_ledger.csv`, source manifest,
  README text, and regression tests for the expanded contract.
- Shortened on-plot D2 labels to `D2 TP*` and `D2 TW*` while preserving full
  provenance IDs in CSV/readme/caption paths.

## Results

- Total figure panels: `40`.
- TP/TW elevation panels: `15`.
- TP-only elevation panels: `15`.
- Signed-error diagnostic panels: `5`.
- PASSIVE-H2 operator panels: `3`.
- D2 experimental-basis TP/TW RMSE: `8.10959406187 K`.
- M3 remains the best current legacy numeric comparator with RMSE
  `19.5676078164 K`.
- PASSIVE-H2 corrected operator total range: `38.6073163603066` to
  `44.677058690827764 W`.

## Validation

- `python3.11 -m py_compile tools/analyze/build_thesis_figtable_model_form_and_blocked_scorecard_panels.py tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py`
  passed.
- `python3.11 tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py`
  passed.
- Visual spot checks inspected:
  `figures/D2_M3_sensor_kind_offsets_train/tp_tw_vs_elevation/png/d2_m3_sensor_kind_offsets_train_tp_tw_temperature_vs_elevation_salt_2.png`
  and
  `figures/PASSIVE-H2-CAND001/operator/png/passive_h2_case_heat_path_operator.png`.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry or admission state mutated: no.
- Scheduler, solver, sampler, harvest, or UQ launched: no.
- Fluid source or external repo edited: no.
- Thesis current/LaTeX files edited: no.
- Validation/holdout/external-test new scoring performed: no.
- New fitting, tuning, or model selection performed: no. D2 rows were consumed
  from an already-completed diagnostic packet only.
- Source/property release, Qwall release, numeric q-loss release, coefficient
  admission, candidate freeze, or final-score claim made: no.
- S11/S12/S13/S15/S6 trigger changed: no.
- Runtime-temperature input release, hidden multiplier, or residual absorption
  into internal Nu: no.

## Remaining Caveats

D2 is the best numeric diagnostic addendum in this package, but it uses
Salt2-trained TP/TW offsets and is not admitted or protected-scoreable.
PASSIVE-H2 is an operator/heat-path development figure family, not a per-sensor
TP/TW predictive model.
