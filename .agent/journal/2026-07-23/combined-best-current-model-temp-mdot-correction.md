# Journal: Combined best-current model (temperature + mass-flow correction)

Date: 2026-07-23
Agent role: Forward-pred / Implementer / Tester / Writer / Reviewer
Task ID: TODO-COMBINED-BEST-CURRENT-MODEL-TEMP-MDOT-CORRECTION-2026-07-23
Branch/worktree: main (no branch/worktree switch)

## Files inspected

- `.agent/BOARD.md` (own row only)
- `work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/README.md`
  (style template) and its `summary.json`, `refit_coefficients.csv`,
  `holdout_external_score_old_vs_new.csv`, `best_model_recommendation.csv`,
  `claim_boundary_table.csv`, `source_manifest.csv`,
  `no_mutation_guardrails.csv`, `train_fit_quality.csv`
- `.agent/status/2026-07-23_TODO-EMPIRICAL-BIAS-SALT1-4-REFIT-HOLDOUT-EXTERNAL-SCORE-2026-07-23.md`
  (status style template)
- `imports/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score.json`
  (manifest style template)
- `operational_notes/07-26/23/2026-07-23_EMPIRICAL_BIAS_SALT1_4_REFIT_HOLDOUT_EXTERNAL_SCORE.md`
  (operational-note style template)
- `tools/analyze/build_empirical_bias_salt1_4_refit_holdout_external_score.py`
  and `tools/analyze/test_empirical_bias_salt1_4_refit_holdout_external_score.py`
  (build/test script style templates)
- `work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_{1,2,3,4}/summary.csv`
  (read-only; `mdot_kg_s`, `measured_mass_flow_rate_kg_s`, `friction_factor_main`,
  `reynolds_main` columns)
- `work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/salt2_pm5_admission_table.csv`
  (read-only; `reverse_area_fraction`/`reverse_mass_fraction`/`recirculation_status`
  columns)
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`
  (read-only; confirmed `dp_F1`, `dp_F3_hagenbach`, `dp_F4_leg_class`,
  `dp_F5_ri_corrected` function names)
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`
  (read-only; confirmed `friction_form: str = "F1"` default)

## Files changed

- `tools/analyze/build_combined_best_current_model_temp_mdot_correction.py` (new)
- `tools/analyze/test_combined_best_current_model_temp_mdot_correction.py` (new)
- `work_products/2026-07/2026-07-23/2026-07-23_combined_best_current_model_temp_mdot_correction/`
  (new package: README.md, summary.json, combined_model_spec.csv,
  mdot_correction_fit.csv, temp_correction_holdout_scores.csv,
  f6_pure_multiplier_ablation.csv, friction_root_cause.csv,
  claim_boundary_table.csv, evidentiary_tier_table.csv,
  future_work_sequence.csv, source_manifest.csv, no_mutation_guardrails.csv)
- `.agent/status/2026-07-23_TODO-COMBINED-BEST-CURRENT-MODEL-TEMP-MDOT-CORRECTION-2026-07-23.md` (new)
- `.agent/journal/2026-07-23/combined-best-current-model-temp-mdot-correction.md` (this file)
- `imports/2026-07-23_combined_best_current_model_temp_mdot_correction.json` (new)
- `operational_notes/07-26/23/2026-07-23_COMBINED_BEST_CURRENT_MODEL_TEMP_MDOT_CORRECTION.md` (new)
- `.agent/BOARD.md` (own row status only)

## Commands run

```
python3 -m py_compile tools/analyze/build_combined_best_current_model_temp_mdot_correction.py \
  tools/analyze/test_combined_best_current_model_temp_mdot_correction.py
python3 tools/analyze/build_combined_best_current_model_temp_mdot_correction.py
python3 tools/analyze/test_combined_best_current_model_temp_mdot_correction.py
```

Prior to writing the build script, ad hoc scratch computations (session
scratchpad, not committed) independently recomputed every cited number
against its stated source file:

- `f * Re` for each of Salt1-4 nominal `friction_factor_main`/`reynolds_main`
  -> exactly `64.0` in all four cases.
- `a = sum(pred*meas)/sum(pred**2)` over the 4 Salt1-4 nominal
  `mdot_kg_s`/`measured_mass_flow_rate_kg_s` pairs -> `0.7504257967710826`,
  matching the cited value exactly; corrected MAE `0.0005292970724547924`
  kg/s and mean relative error `3.1658220088627402%`, matching the cited
  ~0.000529 kg/s / ~3.17%.
- Raw mean relative error over the same 4 pairs -> `32.57455114068148%`,
  matching the cited ~32.57%.
- Rejected 2-DOF affine fit -> `a=0.5688041864582456`, `b=0.0042901970515859065`,
  mean relative error `2.2021438385811214%`, matching the cited numbers
  exactly (the build script's own least-squares implementation, using the
  same mean/covariance formulation as the upstream F2 refit script,
  reproduced these bit-for-bit).
- `reverse_area_fraction` values at the six salt2_lo5q/hi5q pm5 upcomer-plane
  stations range `0.369-0.790` (37-79%), and `recirculation_status` is
  `recirculating_section_effective` for all six, confirming the rejection
  rationale for a Re-based mdot back-calculation.

## Results / observations

- Every number in the task prompt was verified against its cited source file
  and matched exactly (to float precision); none required correction.
- The combined package cites the F2_global_affine temperature correction
  verbatim from the read-only upstream refit package (no re-fitting) and
  recomputes the mdot multiplicative/affine fits in the open from the
  read-only Salt1-4 nominal summary.csv files using the identical
  already-verified least-squares methodology (not a new modeling choice).
- The F6 pure-multiplier ablation and friction-root-cause numbers were
  hard-coded with an explicit in-file provenance comment, since those exact
  scoring passes were run ad hoc in-conversation earlier this session and are
  not yet materialized as their own upstream work_products CSVs, per the task
  instruction.
- The evidentiary-tier asymmetry (temperature: holdout/external validated;
  mass-flow: train-only, not validated) is stated prominently and repeatedly:
  in the README's EVIDENTIARY TIER CALLOUT, `evidentiary_tier_table.csv`, and
  `claim_boundary_table.csv`, including the explicit reasoning for rejecting
  the Re-based mdot back-calculation (37-79% local reverse-flow area
  fraction, non-single-stream per the project's own admission criteria).
- `friction_form: str = "F1"` (plain 64/Re, no entrance-length or buoyancy
  correction) is confirmed as the solver default, while `F3_hagenbach`,
  `F4_leg_class`, and `F5_ri_corrected` are implemented in
  `friction_closures.py` but not wired into this candidate -- documented as
  the most likely direct cause of the mdot overprediction and the first item
  in `future_work_sequence.csv`.
- All 9 tests in the new test script pass, including an independent
  recomputation of the mdot least-squares multiplier and the friction f*Re
  check, and a cross-check that the temperature coefficients in this
  package's spec exactly match the upstream refit file.

## Incomplete lines of investigation

- The friction-closure swap (future_work_sequence.csv step 1) has not been
  run; this package documents it as the next concrete action but does not
  execute it (no solver runs performed by this task, per its board-row
  guardrails).
- No genuine held-out mdot ground truth exists yet for
  salt2_lo5q/salt2_hi5q/val_salt2; the mass-flow correction's evidentiary
  tier cannot be upgraded until one is obtained (future_work_sequence.csv
  step 4).

## Next steps

1. Whichever agent next touches the 1D solver / friction closures should
   attempt future_work_sequence.csv step 1 (swap `friction_form`) as the
   cheapest test of the root-cause hypothesis.
2. Whichever agent owns the final thesis model-selection decision should
   decide whether/how to present this combined package's two-tier
   temperature/mass-flow claim in the thesis narrative.
3. No further action required from this task itself; board row marked
   COMPLETE.
