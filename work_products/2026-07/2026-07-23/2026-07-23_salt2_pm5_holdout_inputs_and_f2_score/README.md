---
provenance:
  - work_products/2026-07/2026-07-23/2026-07-23_salt2_pm5_holdout_inputs_and_f2_score/cfd_extraction/salt2_jin_lo5q_corrected/raw_extraction/boundary_layer_landmark_summary.csv
  - work_products/2026-07/2026-07-23/2026-07-23_salt2_pm5_holdout_inputs_and_f2_score/cfd_extraction/salt2_jin_hi5q_corrected/raw_extraction/boundary_layer_landmark_summary.csv
  - work_products/2026-07/2026-07-23/2026-07-23_salt2_pm5_holdout_inputs_and_f2_score/cfd_extraction/nominal_salt{1,2,3,4}_jin/raw_extraction/boundary_layer_landmark_summary.csv
  - work_products/2026-07/2026-07-23/2026-07-23_salt2_pm5_holdout_inputs_and_f2_score/frozen_1d_predictions_salt2_pm5.csv
tags: [track-a, empirical-rom, cfd-basis, holdout, salt2-pm5, affine, cfd-reference, diagnostic-only]
related:
  - .agent/status/2026-07-23_TODO-SALT2-PM5-HOLDOUT-INPUTS-AND-F2-SCORE-2026-07-23.md
  - .agent/journal/2026-07-23/salt2-pm5-holdout-inputs-and-f2-score.md
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/README.md
task: TODO-SALT2-PM5-HOLDOUT-INPUTS-AND-F2-SCORE-2026-07-23
date: 2026-07-23
role: Implementer / cfd-pp / Tester / Writer / Reviewer
owner: claude
type: work_product
status: complete
---

# Salt2 +/-5Q CFD holdout inputs + CFD-basis affine score

Empirical discrepancy ROM (Track A), CFD-basis. NOT a physical closure.

## BASIS CALLOUT (read first)

The thesis main body is purely computational: the reference truth is the **CFD**
sensor value (`reference_k` = TP core `t_core_k`, TW wall `t_wall_area_avg_k`),
NOT the experimental thermocouple. This package is fit AND scored entirely on CFD.

**A separate parallel package
(`2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score`) was fit against
the EXPERIMENTAL thermocouple** (`reference_K = 453.26 K` for Salt2 TP1 = the
`measured_K` thermocouple), then scored on a smaller (~6-row upcomer-plane) target
set. That is an experiment-basis result and is off-scope for the CFD-only main
body; it should not be cited as the CFD-validated model. This package supersedes
it for the main-body CFD-basis claim.

## Pipeline (all this session)

1. **Blind 1D +/-5Q predictions** (`frozen_1d_predictions_salt2_pm5.csv`): Salt2 at
   heater 252.415 W (lo5q) / 278.985 W (hi5q), same TSWFC2 scenario, TP/TW
   projection. mdot 0.0212 / 0.0231 kg/s.
2. **CFD reference_k extraction** (`cfd_extraction/`): OF13 reconstruct
   (`libRCWallBC.so`, non-mutating `staging/` mirrors) of the terminal state
   (lo5q 10275 s, hi5q 9780 s) + nominal Salt1-4, then `foamPostProcess` sampling
   at the mesh-true TP/TW centerlines (mesh byte-identical to nominal Salt2,
   md5 `5e17f598...`). TP -> `t_core_k`, TW -> `t_wall_area_avg_k`.
3. **All-4 CFD-affine fit** (`cfd_affine_freeze_manifest.csv`): OLS
   `T_CFD = a*T_1D + b` on Salt1-4 nominal (60 paired TP/TW sensors, TP2/TW10
   excluded): **a = 0.7669693, b = 29.8909 K**.
4. **Score-once on the CFD holdout** (`holdout_external_scores.csv`).

## Result (CFD-basis, 15 TP/TW sensors per case)

| target | model | n | corrected MAE (K) | corrected RMSE (K) | raw 1D MAE (K) |
|--------|-------|---|-------------------|--------------------|----------------|
| salt2_lo5q | all-4 CFD affine | 15 | 7.25 | 9.84 | 89.7 |
| salt2_hi5q | all-4 CFD affine | 15 | 6.83 | 8.67 | 100.5 |
| **salt2_pm5 combined** | **all-4 CFD affine** | **30** | **7.04** | **9.27** | **95.1** |
| salt2_pm5 combined | orig Salt1/2 F2 (exp-fit coeffs) | 30 | 6.01 | 8.13 | 95.1 |

| **val_salt2 (external)** | **all-4 CFD affine** | **15** | **7.62** | **10.25** | 91.0 |

**The all-4 CFD affine (global) cuts the Salt2+/-5Q CFD holdout error from ~95 K
(raw 1D) to 7.04 K (MAE, 92.6% reduction), and the val_salt2 CFD external error
from ~91 K to 7.62 K (91.6% reduction) — a coherent ~7-8 K on a genuine,
purely-CFD holdout AND external test.** Model form chosen: GLOBAL all-4 affine
(per user; local Salt2-only fit not pursued).

## val_salt2 external — method consistency (important)

val_salt2's 1D prediction uses the CFD-matching **salt_jin default** (mdot 0.02219,
= Salt2 nominal operating point), NOT the parallel refit's `salt_current`
(mdot 0.0196). Its CFD `reference_k` target was **re-extracted with this session's
same pipeline** as the nominal/±5Q cases. That matters: scoring against the prior
**2026-06-23** frozen-state extraction gave MAE 29.3 K, but that was an
**extraction-vintage artifact** — the method-consistent 2026-07-23 extraction gives
**7.62 K**. Always score fit and target on the same extraction pipeline.

Caveat: this is a *partial* external test — val_salt2 shares Salt2 nominal's
operating point (identical salt_jin 1D input, which is in the training fit); the
novelty is the independent val CFD realization (validation mesh/laminar) as the
target. It tests affine transfer across CFD realizations, not operating-point
extrapolation.

## Caveats (non-negotiable)
Empirical discrepancy ROM only; `a,b` are NOT admitted heat-transfer coefficients;
NOT a physical closure; NOT a legitimate single-use protected-split freeze
(Salt2+/-5Q used more than once this session for model comparison). Do not conflate
with the strict physical Track-B model.

## Reproduce
```
python3.11 work_products/2026-07/.../scripts/generate_1d_pm5_predictions.py   # 1D preds
# CFD extraction: source tools/ofenv/of13_env.sh; python3.11 tools/extract/stage_latest_time_field_reconstruction.py --source-id salt2_jin_lo5q_corrected --field T --field U --field p_rgh --field rho ; then build_ethan_case_analysis_package.py --source-id <id> --time-selector <t>
python3.11 tools/analyze/build_salt2_pm5_holdout_inputs_and_f2_score.py       # fit + score
```
