---
provenance:
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/fit_and_transfer_sensor_rows.csv
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/frozen_coefficients.csv
  - work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/salt2_pm5_admission_table.csv
  - work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress/val_salt2_external_score_targets.csv
tags: [forward-model, empirical-bias, reduced-dof, refit, holdout, external-test, second-exposure]
related:
  - .agent/status/2026-07-23_TODO-EMPIRICAL-BIAS-SALT1-4-REFIT-HOLDOUT-EXTERNAL-SCORE-2026-07-23.md
  - .agent/journal/2026-07-23/empirical-bias-salt1-4-refit-holdout-external-score.md
  - imports/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score.json
  - operational_notes/07-26/23/2026-07-23_EMPIRICAL_BIAS_SALT1_4_REFIT_HOLDOUT_EXTERNAL_SCORE.md
task: TODO-EMPIRICAL-BIAS-SALT1-4-REFIT-HOLDOUT-EXTERNAL-SCORE-2026-07-23
date: 2026-07-23
role: Forward-pred/Implementer/Tester/Writer
type: work_product
status: complete
main_body_scope: off_scope_experiment_basis
superseded_for_cfd_main_body_by: work_products/2026-07/2026-07-23/2026-07-23_salt2_pm5_holdout_inputs_and_f2_score
---
# Empirical Bias Salt1-4 Refit Holdout/External Score

> **OFF-SCOPE FOR THE CFD-ONLY THESIS MAIN BODY (relabel 2026-07-23, user-directed).**
> This package was fit against the **experimental thermocouple** target
> (`reference_K` = `measured_K`, e.g. Salt2 TP1 = 453.26 K). The thesis main body
> is purely computational (CFD `reference_k` is the reference truth), so this
> experiment-basis result must NOT be cited as the CFD-validated model. It is
> retained only as an experiment-anchored reference. The CFD-basis model form and
> holdout/external scores live in
> `work_products/2026-07/2026-07-23/2026-07-23_salt2_pm5_holdout_inputs_and_f2_score/`.

Decision: `salt1_4_refit_diagnostic_complete_f2_global_affine_recommended_not_a_physical_closure_not_a_legal_freeze_score`.

## SECOND EXPOSURE CALLOUT (read first)

`salt2_lo5q`, `salt2_hi5q`, and `val_salt2` have now been scored TWICE within
this session:

1. An ad hoc, in-conversation-only pass (never written to the repo) scored
   the ORIGINAL Salt1/Salt2-fit F0-F5 family against these targets.
2. THIS package refits F0-F5 on all four Salt1-4 nominal cases and scores the
   refit coefficients against the SAME targets, for direct comparison.

This is an explicit user-directed override of the normal "score once, then
freeze" discipline, done to compare fit-set size, not to produce a legitimate
single-use protected-split score. It does not modify, supersede, or compete
with the separate, concurrent `TODO-F2-EMPIRICAL-HOLDOUT-FREEZE-AND-SCORE-HARNESS-2026-07-23`
/ `2026-07-23_salt2_pm5_holdout_inputs_and_f2_score` effort, which keeps the
ORIGINAL Salt1/2-fit F2 frozen and untouched.

## What this package is

A refit of the F0-F5 reduced-DOF empirical bias-correction family (same exact
fitting methodology as
`work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/`)
using ALL FOUR Salt1-4 nominal train sensor rows (64 usable rows) instead of
Salt1/Salt2 only (32 rows), then scored against the real Salt2 +/-5Q holdout
(`salt2_lo5q`, `salt2_hi5q`) and the `val_salt2` external-test case, with a
direct old-fit-vs-new-fit comparison.

## What this package is NOT

- Not a physical closure. Coefficients are mathematical discrepancy
  parameters, not admitted heat-transfer coefficients.
- Not a legitimate single-use protected-split freeze score (second exposure,
  see callout above).
- Not a candidate freeze, source/property release, or admission decision
  change.
- Does not run OpenFOAM/native solver, mutate any case_stage tree, or touch
  the concurrent F2-freeze package's files.

## Headline numbers

- Train rows (Salt1-4 nominal): `64`.
- Best train family (refit, in-sample): `F2_global_affine`.
- Best holdout family (refit, mean of salt2_lo5q/hi5q): `F2_global_affine`.
- Best external family (refit, val_salt2 n=15): `F2_global_affine`.
- Most robust family (refit, smallest range across all 3 splits): `F2_global_affine`.
- Overall recommendation: `F2_global_affine`.

## Open first

- `refit_coefficients.csv`
- `train_fit_quality.csv`
- `holdout_external_score_old_vs_new.csv`
- `best_model_recommendation.csv`
- `claim_boundary_table.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
