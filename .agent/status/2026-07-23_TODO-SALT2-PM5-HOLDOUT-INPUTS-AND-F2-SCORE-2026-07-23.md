# TODO-SALT2-PM5-HOLDOUT-INPUTS-AND-F2-SCORE-2026-07-23 Status

Date: `2026-07-23`
Role: Implementer / cfd-pp / Tester / Writer / Reviewer
Owner: claude

## Scope
Produce the CFD-basis holdout inputs and score for the empirical affine ROM on
Salt2 +/-5Q: blind 1D +/-5Q predictions, CFD reference_k extraction (TP/TW),
all-4 nominal CFD-affine fit, and a score-once on the Salt2 +/-5Q CFD holdout.

## Completed
- Registered pm5 profiles in `tools/case_analysis_profiles.py` (user-authorized;
  mesh byte-identical to nominal Salt2, md5 5e17f598...; reuses SALT2_MAJOR_SPANS).
- Fixed numpy-2.0 `np.trapz` removal in `tools/extract/sample_streamwise_boundary_layer_landmarks.py` (`_trapz` shim).
- Blind 1D +/-5Q predictions (heater 252.415 / 278.985 W; mdot 0.0212 / 0.0231).
- OF13 reconstruction (non-mutating staging mirrors) + TP/TW sampling of CFD
  reference_k for Salt2 lo5q (10275 s), hi5q (9780 s), and nominal Salt1-4.
- All-4 CFD-affine fit: **a = 0.7669693, b = 29.8909 K** (60 paired TP/TW sensors).
- Score-once (CFD basis, 15 TP/TW sensors/case): Salt2+/-5Q combined **MAE 7.04 K,
  RMSE 9.27 K** vs raw 1D **95.1 K** -> **92.6% reduction**. 5 tests pass.

## Current State
A genuine, purely-CFD, holdout-validated empirical-ROM number exists for the main
body. KEY RECONCILIATION: the parallel `2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score`
package was fit against the EXPERIMENTAL thermocouple (reference_K = 453.26 =
measured_K), which is off-scope for the CFD-only main body; this package
supersedes it for the CFD-basis claim. Nuance: the global all-4 affine (7.0 K) is
slightly worse locally at Salt2 than a Salt2-local fit (6.0 K).

## Follow-up
1. val_salt2 external CFD score: resolve val_salt2's own 1D operating point
   (distinct from Salt2 nominal), then score against its existing CFD reference_k.
2. Reconcile/relabel the experiment-basis refit + combined packages as off-scope
   for the CFD-only main body (or move to an experiment-appendix if desired).
3. Decide global-all-4 vs Salt2-local affine for the thesis (report both honestly).
4. Package the CFD-basis result into the thesis evidence-packet + transfer.
