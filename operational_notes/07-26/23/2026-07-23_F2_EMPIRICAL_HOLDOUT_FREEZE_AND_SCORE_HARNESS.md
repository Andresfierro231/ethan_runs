---
provenance:
  - work_products/2026-07/2026-07-23/2026-07-23_f2_empirical_holdout_freeze_and_score/summary.json
tags: [track-a, empirical-rom, F2, freeze, holdout, thesis, start-here]
related:
  - work_products/2026-07/2026-07-23/2026-07-23_f2_empirical_holdout_freeze_and_score/README.md
  - work_products/2026-07/2026-07-23/2026-07-23_thesis_two_track_rom_model_writeup/README.md
  - operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md
task: TODO-F2-EMPIRICAL-HOLDOUT-FREEZE-AND-SCORE-HARNESS-2026-07-23
date: 2026-07-23
role: Coordinator / Writer
owner: claude
type: operational_note
status: current
---

# Start-here: F2 empirical holdout freeze + the path to the first real score (2026-07-23)

## Why this exists
Toward putting final model forms in the thesis, the two-track plan makes Track A
(empirical bias-corrected ROM, `F2_global_affine`) the fastest route to a genuine
protected-holdout number. This note records that F2 is now frozen and the
score-once harness is built + validated, and pins the ONE compute step that
unlocks the actual number.

## State
- **F2 frozen** (immutable, pre-registration): `T_corrected = 0.37298*T_1D +
  246.552`, 2 DOF, fit on Salt1/Salt2 only, content-hashed. No refit/selection
  after freeze.
- **Score-once harness built + dry-run-validated** on Salt2 nominal (corrected
  RMSE 16.46 K vs ~90 K raw; affine identity check passed). Ready to fire.
- **0 protected rows scored.** F2 is an empirical discrepancy ROM, NOT a physical
  closure (mf11).

## The path to the first real holdout number (corrected)
The empirical score is NOT analysis-only. To score the primary blind holdout
(Salt2 +/-5Q):
1. Generate frozen 1D `T_1D` predictions at TP/TW placements for `salt2_lo5q` /
   `salt2_hi5q` (run `tamu_loop_model_v2` at the +/-5Q BC; blind, cheap 1D).
2. **Extract TP/TW CFD sensor targets for Salt2 +/-5Q** from the existing
   corrected runs (CFD postprocessing, NO new solve). The pm5 targets on disk are
   upcomer-plane bulk/wall, not the TP/TW sensor rows F2 was fit on -- this is the
   controlling blocker.
3. Fire `score_rows()` once; report pass/fail as empirical-ROM holdout error.
`val_salt2` external additionally needs a compatible sensor-level external
artifact that does not exist.

## How this fits the thesis
- Track A gets a real number once step 2 lands -> Chapter 7 predictive results.
- Track B (physical) stays a defensible blocked scorecard, strengthened by the
  Q_wall mesh-GCI (<=0.51%) and PASSIVE-H2 strict source-envelope work.
- "Into LaTeX" = evidence packets, not prose: package this + two-track writeup +
  mesh-GCI + strict envelope, transfer via the gated import scripts to
  `../papers/UTexas_Research/csem-Masters_dissertation/`, external writer composes.

## Do-not-do
No refit/model-selection after freeze, no physical-closure claim for F2/F5, no
protected/final score before the inputs land, no source/property/Qwall release,
no physical candidate freeze, no native/registry/scheduler/Fluid/thesis mutation,
no S11/S15/S6 trigger, no commit/push without explicit request.
