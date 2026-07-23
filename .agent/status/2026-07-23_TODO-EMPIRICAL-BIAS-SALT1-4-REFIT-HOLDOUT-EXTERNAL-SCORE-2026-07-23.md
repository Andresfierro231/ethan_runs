# TODO-EMPIRICAL-BIAS-SALT1-4-REFIT-HOLDOUT-EXTERNAL-SCORE-2026-07-23 Status

Date: `2026-07-23`
Role: Forward-pred / Implementer / Tester / Writer / Reviewer
Owner: claude

## Scope

Refit the F0-F5 reduced-DOF empirical bias-correction family (same fitting
methodology as `tools/analyze/build_fluid_reduced_dof_bias_transfer_screen.py`)
using ALL FOUR Salt1-4 nominal train sensor rows (the canonical train set)
instead of Salt1/Salt2 only, then re-score against the real Salt2 +/-5Q
holdout (`salt2_lo5q`, `salt2_hi5q`) and the `val_salt2` external-test case,
compare old-fit vs new-fit performance directly, and document this as an
explicit SECOND scoring exposure of these rows within this session (the first
was an ad hoc, in-conversation-only pass, never written to the repo).

## Completed

- Refit F0-F5 on all 64 usable Salt1-4 nominal sensor rows (up from 32 for
  Salt1/2 only). New F2 coefficients: `a=0.5746889644933884`,
  `b=138.28222646893295` (OLS affine, 2 DOF, 64 fit rows).
- Reproduced raw (uncorrected) 1D `T_1D` predictions for `salt2_lo5q`
  (heater_power_W=252.415), `salt2_hi5q` (heater_power_W=278.985, both
  confirmed against `corrected_case_manifest.csv`), and `val_salt2`
  (`property_set_name="salt_current"`, heater_power_W=265.7) by running
  `solve_case()` with the exact `tswfc2_smoke_salt2_four_node_v1`
  ScenarioConfig. Reproduction matched the task's sanity-check numbers and
  independently reproduced the cited prior-pass old-fit F0/F2/F5 MAE values
  to within floating-point rounding (lo5q F0=89.44/F2=3.47, hi5q
  F0=100.34/F5=2.89, val_salt2 F0=90.65/F2=6.45) — a strong cross-check that
  the raw predictions, station-extraction convention, and target join are all
  correct.
- Applied OLD (Salt1/2, read from `frozen_coefficients.csv`) and NEW
  (Salt1-4 refit) coefficients to the same raw predictions; built the full
  old-fit-vs-new-fit comparison table for all 6 families x 3 cases.
- Found and documented: under the Salt1-4 refit, `F2_global_affine` wins
  holdout (3.34 K mean MAE), external (5.87 K MAE, n=15), AND robustness
  (2.70 K MAE range across all 3 splits) simultaneously — unlike the
  Salt1/2-only fit, where different families won different splits.
  Recommended `F2_global_affine` as the single family to carry forward for
  thesis use, as an empirical discrepancy/digital-twin-ROM layer only.
- Wrote the full work_products package (README, summary.json,
  refit_coefficients.csv, train_fit_quality.csv,
  holdout_external_score_old_vs_new.csv, best_model_recommendation.csv,
  claim_boundary_table.csv, source_manifest.csv, no_mutation_guardrails.csv),
  the build script, and the test script. All 7 tests pass.

## Current State

Package complete. `tools/analyze/build_empirical_bias_salt1_4_refit_holdout_external_score.py`
is deterministic and re-runnable (no `Date.now()`/random; reads
read-only source CSVs and runs the existing 1D `solve_case()`, no OpenFOAM,
no case_stage mutation). `tools/analyze/test_empirical_bias_salt1_4_refit_holdout_external_score.py`
passes all 7 checks, including an independent recomputation of F0 train MAE
from the raw source rows and a cross-check of the recomputed old-fit MAE
against the cited prior-pass numbers.

This package explicitly documents (in `claim_boundary_table.csv`,
`no_mutation_guardrails.csv`, this status file, the README, and the journal
entry) that `salt2_lo5q`/`salt2_hi5q`/`val_salt2` have now been scored twice
within this session and that neither pass is a legitimate single-use
protected-split freeze score. The separate, concurrent
`TODO-F2-EMPIRICAL-HOLDOUT-FREEZE-AND-SCORE-HARNESS-2026-07-23` /
`2026-07-23_salt2_pm5_holdout_inputs_and_f2_score` effort (original Salt1/2-fit
F2 freeze) was not touched, modified, or superseded.

## Follow-up

1. If the thesis narrative adopts the Salt1-4 refit as the reported empirical
   ROM, `F2_global_affine` (a=0.5747, b=138.28) is the recommended coefficient
   set — but this must be re-labeled as a genuine single-use score (one more
   fresh exposure of the holdout/external rows, or a policy decision to accept
   this session's second exposure as final) before any thesis claim cites a
   specific MAE number as "the" result.
2. Consider whether the wall-side (`T_pipe_outer_wall_K`) proxy used for the
   pm5 lo5q/hi5q "wall" rows should be replaced with a CFD-plane-exact
   extraction if/when TP/TW sensor-level Salt2 +/-5Q targets are ever
   extracted (per the F2-freeze effort's stated blocker) — that would let both
   efforts score against the same TP/TW sensor definition F2 was originally
   fit on, rather than this package's upcomer-plane bulk/wall proxy.
3. No further action required from this task; hand off to whichever agent
   owns the final thesis model-selection decision.
