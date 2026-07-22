---
provenance:
  - tools/analyze/build_thesis_figtable_model_form_and_blocked_scorecard_panels.py
  - tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/README.md
  - work_products/2026-07/2026-07-13/2026-07-13_predictive_forward_v0_solve_case_confirmation/solve_case_full/forward_v0_sensor_predictions_experimental.csv
  - reference/geometry_reference.md
tags: [thesis, figures, tp-tw, reference-geometry, experimental-targets, no-admission]
related:
  - .agent/journal/2026-07-22/thesis-figtable-reference-geometry-experimental-target-panel-correction.md
  - imports/2026-07-22_thesis_figtable_reference_geometry_experimental_target_panel_correction.json
task: TODO-THESIS-FIGTABLE-REFERENCE-GEOMETRY-EXPERIMENTAL-TARGET-PANEL-CORRECTION-2026-07-22
date: 2026-07-22
role: Figures / Implementer / Tester / Writer / Reviewer
type: status
status: complete
---
# Status

## Objective

Correct the TP/TW thesis figure package so the temperature-vs-elevation panels
use experimental validation target temperatures and the reference-geometry
elevation convention, while retaining the master scoreboard as the source of M3
predictions and audit-only scoreboard targets.

## Outcome

Complete. The regenerated package now uses:

- `target_K`: experimental validation target temperatures from
  `forward_v0_sensor_predictions_experimental.csv` with
  `variant_id=F0_current_fluid_sources`.
- `elevation_m`: reference-geometry `Y_ABSOLUTE_M - TP2_DATUM_M`, making TP2
  exactly `0.0 m`.
- `scoreboard_reference_target_K`: the prior master-scoreboard target values,
  retained only for audit and disagreement detection.
- `target_delta_experimental_minus_scoreboard_K`: explicit delta showing where
  the prior plotted target basis differed from the experimental target basis.

TW10 remains in the CSV with its experimental target and reference elevation, but
is omitted from plotted curves and x-limits because it is the active
heat-exchanger shell state and M3 does not emit a prediction.

## Changes Made

- `tools/analyze/build_thesis_figtable_model_form_and_blocked_scorecard_panels.py`
- `tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/README.md`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/tp_tw_temperature_elevation_panel_points.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/signed_error_panel_points.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/caption_ledger.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/source_manifest.csv`
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_figtable_model_form_and_blocked_scorecard_panels/summary.json`
- regenerated SVG/PNG figures under the package `figures/` tree.

## Validation

- `python3.11 tools/analyze/test_thesis_figtable_model_form_and_blocked_scorecard_panels.py`
  passed.
- Spot checks after regeneration:
  - Salt2 TP1 target `453.26 K`, elevation `0.9144 m`.
  - Salt2 TP2 target `446.63 K`, elevation `0.0 m`, M3 prediction missing.
  - Salt2 TW5 target `471.69 K`, elevation `0.156371609528495 m`.
  - Salt2 TW10 target `389.74 K`, preserved in CSV and unplotted.

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
- Blocker register or generated documentation index changed by this task before
  closeout: no.

## Remaining Caveats

M3 remains a legacy diagnostic comparator and is not a frozen predictive
candidate. The figures show that the M3 temperature shape is still cold relative
to experimental targets, especially near TW5/TW6, and do not admit a closure.
