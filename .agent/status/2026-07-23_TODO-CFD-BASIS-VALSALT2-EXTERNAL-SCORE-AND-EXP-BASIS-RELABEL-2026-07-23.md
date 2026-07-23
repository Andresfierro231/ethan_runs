# TODO-CFD-BASIS-VALSALT2-EXTERNAL-SCORE-AND-EXP-BASIS-RELABEL-2026-07-23 Status

Date: `2026-07-23`
Role: Forward-pred / cfd-pp / Writer / Implementer / Tester / Reviewer
Owner: claude

## Scope
Global-only per user. Score the frozen all-4 CFD affine on val_salt2 CFD
reference_k as an external test; relabel the experiment-basis packages off-scope
for the CFD-only main body.

## Completed
- Resolved val_salt2's 1D operating point: Salt2 nominal (265.7 W) on the
  CFD-matching **salt_jin default** (mdot 0.02219), NOT the parallel refit's
  salt_current (0.0196). Generated `frozen_1d_prediction_valsalt2.csv`.
- Re-extracted val_salt2 CFD reference_k with THIS session's pipeline
  (method-consistent with nominal + pm5).
- External score (global all-4 CFD affine, 15 sensors): **MAE 7.62 K, RMSE 10.25 K**
  vs raw 1D 91.0 K (91.6% reduction). Method-consistency mattered: the prior
  2026-06-23 extraction gave 29.3 K (vintage artifact); consistent extraction gives 7.62 K.
- Relabeled `2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score`
  (fully off-scope experiment-basis) and `2026-07-23_combined_best_current_model_temp_mdot_correction`
  (partial: temp component off-scope/superseded, mdot component CFD-basis retained).
- 5 builder tests pass.

## Current State
Coherent purely-CFD, global-only empirical ROM result: holdout (Salt2+/-5Q)
MAE 7.04 K and external (val_salt2) MAE 7.62 K, both ~92% reduction vs raw 1D.
Experiment-basis packages are marked off-scope for the CFD-only main body.

## Follow-up
1. Package the CFD-basis result into the thesis evidence-packet (19-field) and
   transfer to the papers LaTeX repo.
2. Note the partial-external caveat (val_salt2 shares Salt2 nominal operating
   point) in the thesis; a true operating-point-novel external needs a new CFD case.
3. Optional: fold the CFD-basis mdot correction (a=0.7504, in-sample) into a
   combined CFD-basis model statement.
