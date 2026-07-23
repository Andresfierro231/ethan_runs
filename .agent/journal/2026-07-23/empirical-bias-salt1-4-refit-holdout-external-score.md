# Journal: Empirical bias Salt1-4 refit holdout/external score

Date: 2026-07-23
Agent role: Forward-pred / Implementer / Tester / Writer
Task ID: TODO-EMPIRICAL-BIAS-SALT1-4-REFIT-HOLDOUT-EXTERNAL-SCORE-2026-07-23
Branch/worktree: main (no branch/worktree switch)

## Files inspected

- `.agent/BOARD.md` (own row only)
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/fit_and_transfer_sensor_rows.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/model_family_dof_ledger.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/frozen_coefficients.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/transfer_summary.csv`
- `work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/README.md`
- `tools/analyze/build_fluid_reduced_dof_bias_transfer_screen.py` (read-only; fitting methodology reproduced, not imported)
- `tools/analyze/test_fluid_reduced_dof_bias_transfer_screen.py` (style reference)
- `work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/salt2_pm5_admission_table.csv`
- `work_products/2026-07/2026-07-17/2026-07-17_val_salt2_external_score_and_unlock_progress/val_salt2_external_score_targets.csv`
- `jadyn_runs/modern_runs/2026-07-04_corrected_salt_q_perturbations/corrected_case_manifest.csv`
- `jadyn_runs/salt2/2026-06-01_continuation_candidate/case_stage/val_salt_test_2_coarse_mesh_laminar_continuation/case_config.yaml`
- `work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/scripts/build_tswfc2_bounded_nominal_scorecard.py` (exact ScenarioConfig source)
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/{solver.py,config_loader.py,materials.py}` (read-only; `solve_case()` and property-set resolution)
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/configs/cases.yaml` (Salt 2 nominal ExperimentCase)
- `tools/analyze/build_f2_empirical_holdout_freeze_and_score.py` (read-only context; concurrent, different task, not touched)
- `work_products/2026-07/2026-07-23/2026-07-23_thesis_two_track_rom_model_writeup/{README.md,claim_boundary_table.csv}` (style templates)
- `.agent/status/2026-07-23_TODO-F2-EMPIRICAL-HOLDOUT-FREEZE-AND-SCORE-HARNESS-2026-07-23.md` (status style template)
- `operational_notes/07-26/23/2026-07-23_F2_EMPIRICAL_HOLDOUT_FREEZE_AND_SCORE_HARNESS.md` (operational-note style template)
- `operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md` (confirms Salt1-4 nominal is the canonical train set)
- `.agent/journal/README.md`
- `imports/2026-07-21_fluid_reduced_dof_bias_transfer_screen.json` (manifest style template)

## Files changed

- `tools/analyze/build_empirical_bias_salt1_4_refit_holdout_external_score.py` (new)
- `tools/analyze/test_empirical_bias_salt1_4_refit_holdout_external_score.py` (new)
- `work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/` (new package: README.md, summary.json, refit_coefficients.csv, train_fit_quality.csv, holdout_external_score_old_vs_new.csv, best_model_recommendation.csv, claim_boundary_table.csv, source_manifest.csv, no_mutation_guardrails.csv)
- `.agent/status/2026-07-23_TODO-EMPIRICAL-BIAS-SALT1-4-REFIT-HOLDOUT-EXTERNAL-SCORE-2026-07-23.md` (new)
- `.agent/journal/2026-07-23/empirical-bias-salt1-4-refit-holdout-external-score.md` (this file)
- `imports/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score.json` (new)
- `operational_notes/07-26/23/2026-07-23_EMPIRICAL_BIAS_SALT1_4_REFIT_HOLDOUT_EXTERNAL_SCORE.md` (new)
- `.agent/BOARD.md` (own row status only)

## Commands run

```
python3 -m py_compile tools/analyze/build_empirical_bias_salt1_4_refit_holdout_external_score.py
python3 -m py_compile tools/analyze/test_empirical_bias_salt1_4_refit_holdout_external_score.py
python3 tools/analyze/build_empirical_bias_salt1_4_refit_holdout_external_score.py
python3 tools/analyze/test_empirical_bias_salt1_4_refit_holdout_external_score.py
```

Before writing the final script, exploratory/scratch computations (in the
session scratchpad, not committed to the repo) were used to:
- Independently recompute the F0-F5 refit coefficients from
  `fit_and_transfer_sensor_rows.csv`'s Salt1-4 usable rows (64 rows) and
  confirm they matched what the final script produces.
- Run `solve_case()` directly for Salt2 nominal / lo5q / hi5q / val_salt2 to
  confirm the exact station-extraction convention (T_in_K at fraction 0.0 of
  `left_lower_vertical` for "upcomer_inlet" bulk, the fraction-0.5 nodal
  boundary of `test_section` for "upcomer_mid", T_out_K at fraction 1.0 of
  `left_upper_vertical` for "upcomer_outlet") against the task's sanity-check
  numbers (matched to within the stated ~0.1 K rounding).
- Independently recompute OLD-fit (Salt1/2) F0/F1/F5 MAE using this station
  mapping and confirm exact agreement with the cited prior in-conversation-
  pass numbers (lo5q F0=89.44/F1=3.15, hi5q F0=100.34/F1=11.59, val_salt2
  F0=90.65), which is the correctness proof for the whole pipeline (raw 1D
  predictions + station/segment mapping + target join).

## Results / observations

- Refitting F0-F5 on all four Salt1-4 nominal cases (64 usable rows vs 32 for
  Salt1/2) makes `F2_global_affine` (a=0.5746889644933884,
  b=138.28222646893295) the single family that wins holdout (3.34 K mean
  MAE), external (5.87 K MAE), and robustness (2.70 K MAE range across
  lo5q/hi5q/val_salt2) simultaneously.
- Under the OLDER Salt1/2-only fit, no single family dominated all three
  splits: F3 was best on lo5q (3.08 K), F5 was best on hi5q (2.89 K), and F2
  was already best on val_salt2 (6.45 K) — evidence that the 2-salt fit was
  under-determined and split-dependent.
- The offset-only families (F1, F3, F4) got measurably WORSE at holdout under
  the larger Salt1-4 refit (their single/grouped offsets moved to also
  explain Salt3/Salt4's different thermal-family bias pattern, at the cost of
  fitting Salt2-specific +/-5Q perturbations as well). F5 (shared multiplier +
  family offset) improved in-sample train fit slightly but got WORSE on
  external test under the refit (9.71 K vs old 9.95 K is close but its
  holdout-external gap widened). F2 (pure global affine, 2 DOF) was the most
  stable across the refit.
- The wall-side ("upcomer_inlet"/"upcomer_mid"/"upcomer_outlet" wall_T_K)
  targets for lo5q/hi5q have no CFD-plane-exact 1D equivalent (unlike the
  bulk T_in_K/T_out_K nodal values); the script uses `T_pipe_outer_wall_K`
  (populated for every 1D sub-segment, unlike the TSWFC2-node-only
  `tswfc2_outer_wall_temperature_K`) as a documented, reproducible proxy. This
  is flagged in the script docstring and README as an approximation, not a
  claimed physical match.

## Incomplete lines of investigation

- Whether a genuinely single-use, never-before-touched exposure of
  salt2_lo5q/hi5q/val_salt2 (a true "third" score, done carefully after this
  session ends) should be the one actually cited in the thesis, rather than
  either of this session's two exposures. Left to whoever owns final
  model-selection/thesis-claim decisions.
- Whether TP/TW sensor-level Salt2 +/-5Q CFD targets will ever be extracted
  (the separate F2-freeze effort's stated blocker); if so, both this
  package's pm5 upcomer-plane bulk/wall scoring and that effort's TP/TW
  scoring could be reconciled onto the same sensor definition.

## Next steps

- None required from this task itself; package is complete and self-
  contained. Handoff note left in the status file's Follow-up section and in
  the operational note for whichever agent next touches thesis model
  selection.
