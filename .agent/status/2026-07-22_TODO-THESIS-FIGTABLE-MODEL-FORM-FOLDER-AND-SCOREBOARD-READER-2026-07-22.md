---
provenance:
  - tools/analyze/build_thesis_figtable_model_form_and_blocked_scorecard_panels.py
  - tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/README.md
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/model_form_summary.csv
tags: [thesis, figures, model-form-scoreboard, tp-tw-elevation, no-admission]
related:
  - .agent/journal/2026-07-22/thesis-figtable-model-form-folder-and-scoreboard-reader.md
  - imports/2026-07-22_thesis_figtable_model_form_folder_and_scoreboard_reader.json
task: TODO-THESIS-FIGTABLE-MODEL-FORM-FOLDER-AND-SCOREBOARD-READER-2026-07-22
date: 2026-07-22
role: Figures / Forward-pred / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# Status

## Objective

Reorganize the thesis model-form figure package so TP/TW elevation figures are
generated from the master scoreboard for every current model form and written
under `figures/<model_form>/{tp_tw_vs_elevation,tp_vs_elevation,diagnostics}/{svg,png}`.
Add per-model README files and a model-form summary that answers which current
numeric comparator is closest to the experimental TP/TW targets without
freezing or admitting any predictive closure.

## Changes Made

- Regenerated `30` figure panels: `12` TP/TW elevation panels, `12` TP-only
  elevation panels, `4` signed-error diagnostic panels, and `2` progress panels.
- Added per-model folders and README definitions for `M1`, `M1b`, `M2`, and
  `M3`.
- Added `model_form_summary.csv` ranking current scoreboard model forms against
  experimental TP/TW targets.
- Preserved `figures/progress/{svg,png}` for the model-form ladder and blocked
  scorecard waterfall.
- Removed stale model-agnostic figure-category outputs during regeneration.

## Model-Form Finding

Current experimental-basis TP/TW RMSE ranking:

- `M3`: `19.5676078164 K`, best current legacy numeric comparator, not frozen.
- `M2`: `29.0171223641 K`, secondary numeric candidate, still blocked pending a
  defensible passive/source basis.
- `M1b`: `165.441006624 K`, historical CFD-boundary replay sensitivity.
- `M1`: `172.191708447 K`, historical CFD-boundary replay.

The most likely future predictive family remains `M5 / MF-04
throughflow-plus-recirculation exchange cell`, but only after Qwall, UQ,
source/property, and freeze gates release it.

## Validation

- `python3.11 -m py_compile tools/analyze/build_thesis_figtable_model_form_and_blocked_scorecard_panels.py`
  passed.
- `python3.11 tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py`
  passed.

## Guardrails

- Native CFD/OpenFOAM outputs mutated: no.
- Registry or admission state mutated: no.
- Scheduler action, solver, sampler, harvest, or UQ launched: no.
- Fluid source or external repo edited: no.
- Thesis current/LaTeX files edited: no.
- Validation/holdout/external-test new scoring performed: no.
- Fitting, tuning, model selection, source/property release, Qwall release,
  coefficient admission, or final-score claim made: no.
- S11/S12/S13/S15/S6 trigger changed: no.
- Runtime-temperature input release or residual absorption into internal Nu: no.

## Remaining Caveats

This package supports thesis figures and model-form triage. `M3` is the best
current numeric comparator in the legacy scoreboard, but it is not the final
predictive model. `M5 / MF-04` remains a future candidate family, not an
admitted model.
