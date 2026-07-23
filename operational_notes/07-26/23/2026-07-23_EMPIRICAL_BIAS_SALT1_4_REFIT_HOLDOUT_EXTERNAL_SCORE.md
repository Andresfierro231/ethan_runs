---
provenance:
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/summary.json
tags: [track-a, empirical-rom, F2, refit, holdout, external-test, second-exposure, thesis]
related:
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/README.md
  - work_products/2026-07/2026-07-21/2026-07-21_fluid_reduced_dof_bias_transfer_screen/README.md
  - operational_notes/07-26/23/2026-07-23_F2_EMPIRICAL_HOLDOUT_FREEZE_AND_SCORE_HARNESS.md
  - operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md
task: TODO-EMPIRICAL-BIAS-SALT1-4-REFIT-HOLDOUT-EXTERNAL-SCORE-2026-07-23
date: 2026-07-23
role: Forward-pred / Writer
owner: claude
type: operational_note
status: current
---

# Start-here: Salt1-4 refit of the empirical bias family (2026-07-23)

## Why this exists

The user asked, explicitly, for a stronger version of the F0-F5 empirical
bias-correction screen: refit the same low-DOF families on ALL FOUR Salt1-4
nominal cases (the canonical train set per
`operational_notes/07-26/17/2026-07-17_CANONICAL_FINAL_PREDICTIVE_SPLIT_POLICY.md`)
instead of Salt1/Salt2 only, then re-score against the same Salt2 +/-5Q
holdout and val_salt2 external targets, and compare old-fit vs new-fit
performance directly.

## SECOND EXPOSURE CAVEAT (read before citing any number here)

`salt2_lo5q`, `salt2_hi5q`, `val_salt2` have now been scored TWICE within this
session: once ad hoc/in-conversation (never written to the repo, cited here
verbatim for comparison only), and once by this package's refit. This is an
explicit, user-directed override of "score once, then freeze." **Neither
scoring pass here is a legitimate single-use protected-split freeze score.**
This does not modify or supersede the separate, concurrent
`TODO-F2-EMPIRICAL-HOLDOUT-FREEZE-AND-SCORE-HARNESS-2026-07-23` /
`2026-07-23_salt2_pm5_holdout_inputs_and_f2_score` effort, which keeps the
ORIGINAL Salt1/2-fit F2 frozen and untouched.

## Headline result

Refitting on Salt1-4 (64 rows, vs 32 for Salt1/2) makes `F2_global_affine`
the family that wins ALL THREE evaluation dimensions simultaneously:

- Holdout (mean of salt2_lo5q + salt2_hi5q refit-corrected MAE): **3.34 K**
- External (val_salt2 refit-corrected MAE, n=15): **5.87 K**
- Robustness (smallest MAE range across all three splits): **2.70 K**

Under the OLDER Salt1/2-only fit, no single family won all three splits (F3
best on lo5q at 3.08 K, F5 best on hi5q at 2.89 K, F2 best on val_salt2 at
6.45 K) — a symptom of an under-determined 2-salt fit. The offset-only
families (F1/F3/F4) got noticeably WORSE at holdout under the larger refit
(their offsets moved to also fit Salt3/Salt4, which no longer matches
Salt2-specific perturbations as well), while F2's affine form stayed stable
or improved across all three splits.

## Recommendation

Carry forward `F2_global_affine`, refit on Salt1-4
(`a=0.5746889644933884`, `b=138.28222646893295`), as the single empirical-ROM
family for thesis use — reported strictly as an empirical
discrepancy/digital-twin-ROM layer, never as a physical closure, and never as
a legitimate single-use protected-split score.

## Open first

- `work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/README.md`
- `.../refit_coefficients.csv`
- `.../holdout_external_score_old_vs_new.csv`
- `.../best_model_recommendation.csv`
- `.../claim_boundary_table.csv`

## Do-not-do

No physical-closure claim for any F0-F5 family. No treating either scoring
pass here as a legitimate single-use protected-split score. No modification
of the separate F2 single-use freeze effort's files. No refit-after-freeze
confusion — this is a distinct, explicitly-labeled second exposure, not a
freeze update. No native/registry/scheduler/Fluid/thesis mutation, no
S11/S15/S6 trigger, no commit/push without explicit request.
