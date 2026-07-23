# TODO-F2-EMPIRICAL-HOLDOUT-FREEZE-AND-SCORE-HARNESS-2026-07-23 Status

Date: `2026-07-23`
Role: Implementer / Tester / Writer / Reviewer
Owner: claude

## Scope
Advance Track A (empirical bias-corrected ROM, `F2_global_affine`) toward its
first legal protected-holdout score by freezing F2 (pre-registration) and
building + validating the score-once harness, without scoring any protected row.

## Completed
- Froze F2 into an immutable manifest: `T_corrected = 0.3729829182408737*T_1D +
  246.55192842685844`, 2 DOF, fit on Salt1/Salt2 train-support only (32 rows),
  with a `content_sha256` over the frozen-coefficients source + builder.
- Built the score-once harness (`score_rows`, pure) and dry-run-validated it on
  Salt_2 nominal (corrected RMSE 16.46 K vs raw ~90 K; affine-identity check
  passed). 6 tests pass.
- Emitted a holdout-score readiness ledger; scored 0 protected rows.

## Current State
F2 is frozen and the scorer is built + proven correct. The protected-holdout
score is NOT computable yet: the primary-holdout number (Salt2 ±5Q) is blocked
on (i) 1D ±5Q predictions at TP/TW sensors [cheap 1D] and (ii) TP/TW CFD sensor
target extraction from the existing corrected Salt2 ±5Q runs [CFD postprocessing,
no new solve — the controlling blocker]. `val_salt2` external additionally lacks
a compatible sensor-level external artifact. No physical-closure claim.

## Follow-up
1. Generate frozen 1D `T_1D` predictions for `salt2_lo5q`/`salt2_hi5q` at TP/TW
   placements (run `tamu_loop_model_v2` at ±5Q BC; blind, no target contact).
2. Extract TP/TW CFD sensor targets for Salt2 ±5Q from the corrected runs
   (CFD postprocessing) — the single controlling blocker to the number.
3. Fire the harness once; report as empirical-ROM holdout performance.
4. Package this + the two-track writeup + mesh-GCI + PASSIVE-H2 strict envelope
   into evidence packets and transfer to the LaTeX repo (external writer).
