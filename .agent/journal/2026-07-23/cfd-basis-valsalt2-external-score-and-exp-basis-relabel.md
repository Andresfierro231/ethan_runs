# Journal: CFD-basis val_salt2 external score + experiment-basis relabel

Date: `2026-07-23`
Role: Forward-pred / cfd-pp / Writer / Implementer / Tester / Reviewer
Task ID: `TODO-CFD-BASIS-VALSALT2-EXTERNAL-SCORE-AND-EXP-BASIS-RELABEL-2026-07-23`

## What / why
User: global-only model form; test on val_salt2; relabel experiment-basis
packages off-scope (CFD is main focus); work in parallel.

## Files changed
- `tools/analyze/build_salt2_pm5_holdout_inputs_and_f2_score.py` (+ val_salt2
  external scoring, method-consistent CFD target rollup) + test (external assert).
- NEW `.../scripts/generate_1d_valsalt2_prediction.py`, `frozen_1d_prediction_valsalt2.csv`,
  `cfd_extraction/val_salt2/**`.
- Relabel (user-authorized, additive): `.../2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/README.md`
  (off-scope experiment-basis), `.../2026-07-23_combined_best_current_model_temp_mdot_correction/README.md`
  (partial: temp off-scope, mdot retained).
- Updated package README + summary.json; status/journal/import; board row.

## Commands
```
python3.11 .../scripts/generate_1d_valsalt2_prediction.py
python3.11 tools/analyze/build_ethan_case_analysis_package.py --source-id val_salt_test_2_coarse_mesh_laminar --last-n-times 1 --output-dir .../cfd_extraction/val_salt2
python3.11 tools/analyze/build_salt2_pm5_holdout_inputs_and_f2_score.py
python3.11 -m pytest tools/analyze/test_salt2_pm5_holdout_inputs_and_f2_score.py -q
```

## Results
- Default salt property = salt_jin (materials.py:383) confirmed; val_salt2 salt_jin
  mdot 0.02219 (refit's salt_current gave 0.0196 -- off-basis).
- Global all-4 CFD affine a=0.7669693 b=29.8909.
- Holdout Salt2+/-5Q: MAE 7.04 K (92.6% vs raw 95.1).
- External val_salt2: MAE 7.62 K, RMSE 10.25 K (91.6% vs raw 91.0), n=15,
  method-consistent (2026-07-23) extraction.
- METHOD-CONSISTENCY FINDING: prior 2026-06-23 val extraction gave 29.3 K; the
  same-pipeline 2026-07-23 extraction gives 7.62 K -> the 29 K was an extraction-
  vintage artifact. Score fit and target on the same pipeline.

## Caveats / incomplete
- val_salt2 is a PARTIAL external test (same operating point as Salt2 nominal
  train; identical salt_jin 1D input). A true operating-point-novel external needs
  a new CFD case.
- Repeated-exposure caveat stands (Salt2 +/-5Q / val_salt2 used >1x this session).

## Next
Package CFD-basis result into thesis evidence-packet + transfer to papers repo.
