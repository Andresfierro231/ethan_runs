# Journal: Salt2 +/-5Q CFD holdout inputs + CFD-basis affine score

Date: `2026-07-23`
Role: Implementer / cfd-pp / Tester / Writer / Reviewer
Task ID: `TODO-SALT2-PM5-HOLDOUT-INPUTS-AND-F2-SCORE-2026-07-23`

## What / why
User: put evaluated model forms into the (purely CFD) thesis. Empirical Track-A
ROM `T_corr = a*T_1D + b`. This task produced the CFD-basis holdout inputs +
score for Salt2 +/-5Q.

## Files inspected / changed
- Edited (user-authorized): `tools/case_analysis_profiles.py` (+2 pm5 profiles).
- Edited (numpy-2.0 bug): `tools/extract/sample_streamwise_boundary_layer_landmarks.py` (`np.trapz`->`_trapz`).
- New: `tools/analyze/build_salt2_pm5_holdout_inputs_and_f2_score.py` + test.
- New: `work_products/2026-07/2026-07-23/2026-07-23_salt2_pm5_holdout_inputs_and_f2_score/**`
  (scripts/generate_1d_pm5_predictions.py, frozen_1d_predictions_salt2_pm5.csv,
  cfd_extraction/{salt2_jin_lo5q,salt2_jin_hi5q,nominal_salt1..4}, cfd_affine_freeze_manifest.csv,
  holdout_external_scores.csv, nominal_fit_coverage.csv, score_decision.csv, README, summary).
- Staging (non-mutating): `staging/render_inputs/salt2_jin_{lo5q,hi5q}_corrected/reconstructed_case`.

## Commands (reproducible)
```
python3.11 .../scripts/generate_1d_pm5_predictions.py
source tools/ofenv/of13_env.sh; python3.11 tools/extract/stage_latest_time_field_reconstruction.py --source-id salt2_jin_lo5q_corrected --field T --field U --field p_rgh --field rho
python3.11 tools/analyze/build_ethan_case_analysis_package.py --source-id <id> --time-selector <t>   # reconstruct+sample
python3.11 tools/analyze/build_ethan_case_analysis_package.py --source-id viscosity_screening_salt_test_{1..4}_jin_coarse_mesh --last-n-times 1
python3.11 tools/analyze/build_salt2_pm5_holdout_inputs_and_f2_score.py
python3.11 -m pytest tools/analyze/test_salt2_pm5_holdout_inputs_and_f2_score.py -q
```

## Results
- 1D +/-5Q: mdot 0.0212 (lo5q) / 0.0231 (hi5q) kg/s.
- CFD reference_k extracted for lo5q/hi5q + nominal Salt1-4 (TP=t_core_k, TW=t_wall_area_avg_k).
- All-4 CFD affine: a=0.7669693, b=29.8909; ±5Q holdout MAE 7.04 K / RMSE 9.27 K
  (15 TP/TW sensors/case, 30 combined), raw 1D 95.1 K -> 92.6% reduction.
- orig Salt1/2 F2 (exp-fit coeffs) on same CFD holdout: 6.01 K (locally better).

## Critical reconciliation (basis)
`measured_K`/`reference_K` in the transfer-screen data = EXPERIMENTAL thermocouple
(Salt2 TP1 = 453.26). The parallel `2026-07-23_empirical_bias_salt1_4_refit...`
package fit against that (experiment), off-scope for the CFD-only main body. This
package is fit AND scored on CFD reference_k -> the correct main-body basis. The
nominal CFD reference (e.g. salt_2 TP1 = 449.9) is close to experiment (453.26),
which is why the two bases give similar-magnitude scores despite different coeffs.

## Incomplete / next
- val_salt2 external needs its own 1D operating point (distinct; not in cases.yaml).
- Choose global-all-4 vs Salt2-local affine for the thesis (both reported).
- Relabel experiment-basis packages as off-scope; package CFD-basis for transfer.
