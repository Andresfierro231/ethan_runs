# Salt Oscillation User Train Scope

Task: AGENT-416
Generated: 2026-07-15

## Scope

This package applies the requested reporting split: Salt1 Jin nominal, Salt2 Jin
nominal, and Salt3 Jin nominal are labeled `canonical_forward_train`. Native
`val_salt_test_2_coarse_mesh_laminar` is included as `diagnostic_validation_comparison`.
The original Salt1/Salt4/Salt2 perturbation rows from the July 15 thermal table remain
in the package for continuity.

This is a reporting/plotting scope update only. It does not mutate registry/admission
state and does not consume validation temperatures as predictive runtime inputs.

## Requested Case Resolution

| requested | status | resolved case |
| --- | --- | --- |
| salt1_jin_nominal | resolved | salt1_jin |
| salt2_jin_nominal | resolved | salt2_jin |
| salt3_jin_nominal | resolved | salt3_jin |
| salt2_native_val | resolved | salt_test_2 |

## Results

- Selected cases: `12`.
- Resolved postProcessing directories: `12`.
- Statistics rows: `684`.
- SVG figures: `144`.
- Canonical/user-requested train rows: `salt1_nominal, salt1_jin_nominal, salt2_jin_nominal, salt3_jin_nominal`.
- Validation comparison rows: `salt2_native_val`.

Representative verdicts:

| case | split role | steady reps | quasi reps | drifting reps | verdicts |
| --- | --- | ---: | ---: | ---: | --- |
| salt1_hi10q | training_perturbation | 3 | 0 | 0 | steady |
| salt1_jin_nominal | canonical_forward_train | 3 | 0 | 0 | steady |
| salt1_lo10q | training_perturbation | 3 | 0 | 0 | steady |
| salt1_nominal | canonical_forward_train | 3 | 0 | 0 | steady |
| salt2_hi5q | holdout_perturbation | 3 | 0 | 0 | steady |
| salt2_jin_nominal | canonical_forward_train | 3 | 0 | 0 | steady |
| salt2_lo5q | holdout_perturbation | 3 | 0 | 0 | steady |
| salt2_native_val | diagnostic_validation_comparison | 3 | 0 | 0 | steady |
| salt3_jin_nominal | canonical_forward_train | 3 | 0 | 0 | steady |
| salt4_hi5q | training_perturbation | 3 | 0 | 0 | steady |
| salt4_lo5q | training_perturbation | 3 | 0 | 0 | steady |
| salt4_nominal | training | 3 | 0 | 0 | steady |

RMS, variance, naive CLT SEM, and autocorrelation-corrected SEM are in
`representative_metrics.csv` and `oscillation_stats.csv`; plots are indexed by
`figure_manifest.csv`.
