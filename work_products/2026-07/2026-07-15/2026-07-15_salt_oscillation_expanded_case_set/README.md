# Expanded Salt Oscillation Case Set

Task: AGENT-415
Generated: 2026-07-15

## Why This Exists

The first AGENT-411 package followed the July 15 thermal-fit table and therefore omitted
nominal Salt2 and Salt3 from the plotted case set. This package corrects that scope:
it keeps the original eight Salt rows and adds canonical Salt2 nominal, canonical
Salt3 nominal, native `val_salt_test_2_coarse_mesh_laminar`, and a Salt1 Jin
diagnostic reference row.

No `val_salt_test_1*`/`salt1_val` case was found in the case matrix or bounded
directory search. The Salt1 Jin reference is included only as diagnostic context;
it is not relabeled as a validation case.

## Requested Case Resolution

| requested | status | resolved case |
| --- | --- | --- |
| salt2_jin_nominal | resolved | salt2_jin |
| salt3_jin_nominal | resolved | salt3_jin |
| salt2_native_val | resolved | salt_test_2 |
| salt1_jin_reference_not_val | resolved | salt1_jin |
| val_salt_test_1 / salt1_val | not_found |  |

## Results

- Selected cases: `12`.
- Resolved postProcessing directories: `12`.
- Statistics rows: `684`.
- SVG figures: `144`.

Representative verdicts:

| case | split role | steady reps | quasi reps | drifting reps | verdicts |
| --- | --- | ---: | ---: | ---: | --- |
| salt1_hi10q | training_perturbation | 3 | 0 | 0 | steady |
| salt1_jin_reference_not_val | diagnostic_reference_not_val | 3 | 0 | 0 | steady |
| salt1_lo10q | training_perturbation | 3 | 0 | 0 | steady |
| salt1_nominal | training | 3 | 0 | 0 | steady |
| salt2_hi5q | holdout_perturbation | 3 | 0 | 0 | steady |
| salt2_jin_nominal | canonical_forward_train | 3 | 0 | 0 | steady |
| salt2_lo5q | holdout_perturbation | 3 | 0 | 0 | steady |
| salt2_native_val | diagnostic_validation_comparison | 3 | 0 | 0 | steady |
| salt3_jin_nominal | canonical_forward_validation | 3 | 0 | 0 | steady |
| salt4_hi5q | training_perturbation | 3 | 0 | 0 | steady |
| salt4_lo5q | training_perturbation | 3 | 0 | 0 | steady |
| salt4_nominal | training | 3 | 0 | 0 | steady |

Representative RMS/variance/SEM metrics are in `representative_metrics.csv`; all
per-series values are in `oscillation_stats.csv`. Figures are under `figures/` and
are indexed by `figure_manifest.csv`.

The math is unchanged from AGENT-411: last-window RMS and variance are computed
about the last-window mean; SEM follows the independent-sample CLT `sigma/sqrt(N)`
and the tables also include autocorrelation-corrected SEM using `N_eff=N/tau_int`.
