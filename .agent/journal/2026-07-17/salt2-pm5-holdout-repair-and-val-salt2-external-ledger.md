---
provenance:
  - work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair/resampled_pm5_matched_plane_metrics.csv
  - work_products/2026-07/2026-07-15/2026-07-15_pm5_wall_band_vtk_and_f6_unlock_repair/resampled_vtk_field_validation.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/val_salt2_patch_heat_ledger.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_training_readiness_and_corner_k_unlock/val_salt2_pressure_map.csv
  - work_products/2026-07/2026-07-15/2026-07-15_forward_v1_hydraulic_unblock_plan_execution/sensor_map_policy_refresh.csv
tags: [salt2, pm5, holdout, val-salt2, external-test, heat-audit, pressure-map]
related:
  - .agent/status/2026-07-17_AGENT-486.md
  - imports/2026-07-17_predict_salt2_pm5_holdout_extraction_repair.json
  - imports/2026-07-17_predict_val_salt2_external_ledger.json
task: AGENT-486
date: 2026-07-17
role: Implementer/Tester/Writer
type: journal
status: complete
---
# Salt2 PM5 Holdout Repair and val_salt2 External Ledger

## Why this exists

The user asked to implement the plan for
`TODO-PREDICT-SALT2-PM5-HOLDOUT-EXTRACTION-REPAIR` and
`TODO-PREDICT-VAL-SALT2-EXTERNAL-LEDGER`, using reusable scripts where possible.
The important constraint was to use completed July 15/17 postprocessing and not
submit more duplicate pressure or PM5 jobs.

## Observed output

The Salt2 PM5 package validates AGENT-406 repaired staged-copy outputs. The
Salt2 +/-5Q rows have all three upcomer planes per case, all required
wall/core/`wallHeatFlux` fields, and passing VTK field validation. The repair
decision for both `salt2_lo5q` and `salt2_hi5q` is
`reuse_agent406_repaired_artifacts`; the old July 14 broken PM5 path is not
relaunched.

The Salt2 PM5 admission table is intentionally conservative: all `6` rows are
holdout diagnostics, `0` are fit admitted, and every row carries recirculation
blockers. The two upcomer-mid rows have nonpositive `wallHeatFlux / delta_T`
proxy signs and are marked for thermal sign review.

The `val_salt2` external ledger normalizes AGENT-483 and AGENT-393 evidence:

- `69` patch heat rows.
- `10` section heat rows with maximum latest reconciliation residual
  `3.45099996857e-07 W`.
- `4` physical junction/stub split rows, summing to `40.9260865692 W`.
- `30` streamwise pressure-map targets.
- `17` TP/TW sensor-policy rows.

## Interpretation

Salt2 +/-5Q PM5 is repaired enough for holdout diagnostic evidence, especially
for recirculation/onset and PM5 wall/core review. It is not training evidence.
The current PM5 wallHeatFlux rows should not be used for F6/Internal-Nu fitting
because the plane statistics still show large reverse-flow fractions and no
final mesh/GCI fit admission.

`val_salt2` is now packaged as main external-test evidence and a
training-quality audit artifact. It should support blind scoring of pressure,
section heat, junction/stub heat, and sensor-policy coverage. It still must not
train, tune, or select the model unless a later split-policy package explicitly
reclassifies it.

Sensor rows in this package are policy targets only. They preserve AGENT-393
runtime-input guardrails and score/validation eligibility, but this task did not
join case-specific val_salt2 numeric sensor temperatures.

## Reusable commands

- `python3.11 tools/extract/repair_salt2_pm5_holdout_matched_plane_sampling.py`
- `python3.11 tools/analyze/build_salt2_pm5_holdout_admission.py`
- `python3.11 tools/analyze/build_val_salt2_external_test_ledger.py`
- `python3.11 -m unittest tools.extract.test_repair_salt2_pm5_holdout_matched_plane_sampling tools.analyze.test_salt2_pm5_holdout_admission tools.analyze.test_val_salt2_external_test_ledger`

## Next task sequence

1. Use the Salt2 PM5 package only as holdout diagnostics in final predictive
   evaluation.
2. Use the `val_salt2` external ledger for blind external scoring after the
   predictive model is frozen.
3. If numeric TP/TW `val_salt2` sensor temperatures are needed in the same
   ledger, add a separate case-specific sensor-value join that preserves the
   current runtime-input-forbidden policy.
4. Do not regenerate repo-wide indexes until the active generated-index owner
   releases that scope.

## Do-not-do guardrails

- Do not mutate native solver outputs or registry state.
- Do not submit duplicate pressure/PM5 jobs for these TODOs.
- Do not fit, tune, or select model form on Salt2 +/-5Q or `val_salt2`.
- Do not use realized `wallHeatFlux`, section heat, pressure targets, or TP/TW
  sensor targets as runtime predictors.
