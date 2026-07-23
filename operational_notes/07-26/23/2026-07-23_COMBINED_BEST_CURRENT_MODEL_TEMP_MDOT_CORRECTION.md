---
provenance:
  - work_products/2026-07/2026-07-23/2026-07-23_combined_best_current_model_temp_mdot_correction/summary.json
tags: [combined-model, empirical-rom, F2, mass-flow-correction, friction-closure, root-cause, evidentiary-tiering, thesis]
related:
  - work_products/2026-07/2026-07-23/2026-07-23_combined_best_current_model_temp_mdot_correction/README.md
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/README.md
  - operational_notes/07-26/23/2026-07-23_EMPIRICAL_BIAS_SALT1_4_REFIT_HOLDOUT_EXTERNAL_SCORE.md
task: TODO-COMBINED-BEST-CURRENT-MODEL-TEMP-MDOT-CORRECTION-2026-07-23
date: 2026-07-23
role: Forward-pred / Writer
owner: claude
type: operational_note
status: current
---

# Start-here: Combined best-current model, temperature + mass-flow correction (2026-07-23)

## Why this exists

The user asked, explicitly, for the final best-current combined empirical-ROM
model: a temperature correction AND a mass-flow correction together, shared
now with future work named separately. This note is the start-here for that
combined deliverable.

## EVIDENTIARY TIER CAVEAT (read before citing any number here)

The two corrections in this combined model carry **very different**
evidentiary strength and must never be described with the same confidence:

- **Temperature (`F2_global_affine`, Salt1-4 refit): HOLDOUT/EXTERNAL
  VALIDATED.** Scored against real never-seen data (`salt2_lo5q`,
  `salt2_hi5q` +/-5Q holdout runs; `val_salt2` external-test case).
- **Mass-flow (1-DOF multiplicative, `a=0.7504257967710826`): TRAIN-ONLY.**
  Fit AND scored on the same 4 Salt1-4 nominal points — the only 4 points
  with a measured mass-flow ground truth in the whole dataset. No held-out
  mdot data exists. A Re-based back-calculation from the pm5 probe stations
  was considered and rejected (those stations show 37-79% local reverse-flow
  area fraction and are non-single-stream per the project's own admission
  criteria).

## Headline result

- Temperature: `T_corrected = 0.5746889644933884 * T_1D + 138.28222646893295`.
  Holdout MAE: 3.50 K (salt2_lo5q), 3.17 K (salt2_hi5q). External MAE: 5.87 K
  (val_salt2, n=15).
- Mass-flow: `mdot_corrected = 0.7504257967710826 * mdot_1D`. Raw mean
  relative error 32.57% -> corrected 3.17% (in-sample, Salt1-4 nominal only).
- Friction root-cause: `f * Re = 64.0` exactly for all four Salt1-4 nominal
  cases -> the solver's `friction_form` default (`"F1"`, plain 64/Re, no
  entrance-length or buoyancy correction) is confirmed in use, while
  `F3_hagenbach`/`F4_leg_class`/`F5_ri_corrected` are already implemented in
  `friction_closures.py` but not wired into this candidate. This is the most
  likely direct cause of the mdot overprediction and the cheapest next fix.
- F6 pure-multiplier temperature ablation: NOT robust (good on one +/-5%Q
  direction, poor on the other, under either fit basis) -> the additive
  offset in F2 is load-bearing, not redundant. Recommend against a
  pure-multiplier temperature form.

## Recommendation

Report the combined model with the two-tier framing above. Do not claim the
mass-flow correction is validated. Do not claim either correction is a
physical closure. Do not treat this package as a legitimate single-use
protected-split freeze score.

## Open first

- `work_products/2026-07/2026-07-23/2026-07-23_combined_best_current_model_temp_mdot_correction/README.md`
- `.../combined_model_spec.csv`
- `.../evidentiary_tier_table.csv`
- `.../mdot_correction_fit.csv`
- `.../friction_root_cause.csv`
- `.../claim_boundary_table.csv`
- `.../future_work_sequence.csv`

## Trusted packages

- `work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/`
  (source of the F2 temperature correction; not modified by this task).
- `work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_{1,2,3,4}/summary.csv`
  (source of the 4 Salt1-4 nominal mdot ground-truth pairs).
- `work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/salt2_pm5_admission_table.csv`
  (source of the reverse-flow-fraction rejection evidence).
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`
  (source of the F3_hagenbach/F4_leg_class/F5_ri_corrected closure names,
  read/run-only, not edited).

## Unresolved blockers

- No held-out mass-flow ground truth exists for salt2_lo5q/salt2_hi5q/val_salt2
  today; the mass-flow correction's evidentiary tier cannot be upgraded until
  one is obtained (see future_work_sequence.csv, step 4).
- The friction-closure swap (future_work_sequence.csv step 1) has not been
  run; this note and the package document it as the next concrete action
  only.

## Active board rows

- `TODO-COMBINED-BEST-CURRENT-MODEL-TEMP-MDOT-CORRECTION-2026-07-23` (this
  task; STATUS: COMPLETE 2026-07-23).

## Next task sequence

1. Swap `friction_form` to `F3_hagenbach`/`F4_leg_class`/`F5_ri_corrected` and
   re-run the existing Salt1-4 nominal solver pass.
2. Re-check whether F2's 138.28 K offset shrinks once mdot is fixed.
3. Continue the separate, active PASSIVE-H2 outer-insulation/radiation
   heat-loss admission track (not part of this package).
4. Obtain a genuine non-recirculating held-out mdot readout before claiming a
   validated mass-flow correction.
5. Treat salt2_lo5q/salt2_hi5q/val_salt2 as spent for any future single-use
   freeze score; use Salt4 +/-5Q or +/-10Q rows instead.

## Output contract

Every headline number in this note and in the linked work_products package
was independently re-verified against its cited source file before being
written (see the task's journal entry and status file for the full
verification list). No number differed from its source.

## Do-not-do

No physical-closure claim for either correction. No claiming the mass-flow
correction is holdout- or externally-validated. No treating this package as a
legitimate single-use protected-split freeze score. No native/registry/
scheduler/Fluid/thesis mutation, no S11/S15/S6 trigger, no solver run, no
commit/push without explicit request, no touching any other board row's
files.
