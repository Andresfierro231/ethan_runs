---
provenance:
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/refit_coefficients.csv
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/holdout_external_score_old_vs_new.csv
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/train_fit_quality.csv
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/best_model_recommendation.csv
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_1/summary.csv
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_2/summary.csv
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_3/summary.csv
  - work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_4/summary.csv
  - work_products/2026-07/2026-07-17/2026-07-17_predict_salt2_pm5_holdout_extraction_repair/salt2_pm5_admission_table.csv
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
tags: [forward-model, combined-model, temperature-correction, mass-flow-correction, empirical-bias, friction-closure, root-cause, evidentiary-tiering]
related:
  - .agent/status/2026-07-23_TODO-COMBINED-BEST-CURRENT-MODEL-TEMP-MDOT-CORRECTION-2026-07-23.md
  - .agent/journal/2026-07-23/combined-best-current-model-temp-mdot-correction.md
  - imports/2026-07-23_combined_best_current_model_temp_mdot_correction.json
  - operational_notes/07-26/23/2026-07-23_COMBINED_BEST_CURRENT_MODEL_TEMP_MDOT_CORRECTION.md
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/README.md
task: TODO-COMBINED-BEST-CURRENT-MODEL-TEMP-MDOT-CORRECTION-2026-07-23
date: 2026-07-23
role: Forward-pred/Implementer/Tester/Writer/Reviewer
type: work_product
status: complete
temperature_component_scope: off_scope_experiment_basis
temperature_component_superseded_by: work_products/2026-07/2026-07-23/2026-07-23_salt2_pm5_holdout_inputs_and_f2_score
mdot_component_scope: cfd_basis_in_sample_retained
---
# Combined Best-Current Model: Temperature + Mass-Flow Correction

> **PARTIAL RELABEL (2026-07-23, user-directed): temperature component is
> OFF-SCOPE for the CFD-only main body.**
> The temperature correction here was fit against the **experimental thermocouple**
> (experiment basis) and must NOT be cited as CFD-validated. Use the CFD-basis
> temperature model form + holdout/external scores in
> `work_products/2026-07/2026-07-23/2026-07-23_salt2_pm5_holdout_inputs_and_f2_score/`
> instead (global all-4 CFD affine a=0.7669693, b=29.8909; Salt2+/-5Q CFD holdout
> MAE 7.04 K). The **mass-flow correction** (a=0.7504) was fit on CFD mdot ground
> truth and remains CFD-basis (in-sample only) — retained.

Decision: `combined_model_temp_holdout_validated_mdot_train_only_not_a_physical_closure_not_a_freeze_score`.

## EVIDENTIARY TIER CALLOUT (read first)

This package combines TWO corrections with **very different evidentiary
strength**, and they must never be described with the same confidence:

- **Temperature correction (F2_global_affine, Salt1-4 refit): HOLDOUT/EXTERNAL
  VALIDATED.** It is scored against genuinely never-seen data: the real
  Salt2 +/-5Q holdout runs (`salt2_lo5q`, `salt2_hi5q`) and the independent
  `val_salt2` external-test case (different property set). MAE = 3.502 K
  (salt2_lo5q), 3.169 K (salt2_hi5q), 5.868 K (val_salt2, n=15).
- **Mass-flow correction (1-DOF multiplicative, a=0.7504257967710826): TRAIN-ONLY,
  NOT VALIDATED OUT-OF-SAMPLE.** It is fit AND scored on the SAME 4 Salt1-4
  nominal points -- the only 4 points in the whole dataset with a measured
  mass-flow ground truth. There is no measured mdot for salt2_lo5q,
  salt2_hi5q, or val_salt2.
- A Re-based back-calculation of an approximate mdot from the CFD probe
  stations in `salt2_pm5_admission_table.csv` was considered and **explicitly
  rejected**: those stations show 37-79% local reverse-flow area fraction and
  are labeled `recirculation_status == recirculating_section_effective`
  (non-single-stream) per the project's own admission criteria. Using them
  would silently launder a bad number into what should be an honest gap in
  the evidence, so the mass-flow correction is reported strictly as
  train-only and not holdout-validated.

**Never report these two corrections as if they carried the same evidentiary
weight.** See `evidentiary_tier_table.csv` and `claim_boundary_table.csv`.

## What this package is

The final combined-model deliverable requested by the user: the current best
temperature correction (holdout/external-validated F2_global_affine, Salt1-4
refit) plus the current best mass-flow correction (train-only 1-DOF
multiplicative fit) reported together as one honest "best current model"
statement, with future work named separately (`future_work_sequence.csv`).
It also documents the friction root-cause finding for the mdot overprediction
(`friction_root_cause.csv`) and an ablation answering "does a pure multiplier
(no offset) do as well for temperature?" (`f6_pure_multiplier_ablation.csv`;
answer: no, the additive offset is load-bearing).

## What this package is NOT

- Not a physical closure. Neither the temperature nor the mass-flow
  correction is an admitted physical heat-transfer or friction coefficient.
- Not a legitimate single-use protected-split freeze score for the mass-flow
  correction (no held-out mdot data exists at all) or for the temperature
  correction (it is a cited, already-second-exposure score from the upstream
  refit package, not a fresh single-use exposure).
- Not a new curve-fit exercise beyond the already-established mdot 1-DOF
  multiplicative correction (recomputed here from the same 4 read-only
  source pairs, not re-derived with any new methodology).
- Does not run OpenFOAM, the 1D `solve_case()` solver, or mutate any
  case_stage tree; does not touch any other board row's files.

## Headline numbers

### Temperature correction (F2_global_affine, Salt1-4 refit) -- HOLDOUT/EXTERNAL VALIDATED

- `T_corrected = 0.5746889644933884 * T_1D + 138.28222646893295`
- Holdout MAE: salt2_lo5q = 3.502 K, salt2_hi5q = 3.169 K
- External MAE: val_salt2 = 5.868 K (n=15)

### Mass-flow correction (1-DOF multiplicative) -- TRAIN-ONLY, NOT VALIDATED

- `mdot_corrected = 0.7504257967710826 * mdot_1D`
- Raw mean relative error (Salt1-4 nominal): 32.57%
- Corrected mean relative error: 3.17%
- Corrected MAE: 0.000529 kg/s
- Rejected alternative (2-DOF affine, in-sample mean rel err 2.20%):
  not adopted because 2 free parameters fit to only 4 data points leaves too
  little residual degrees of freedom to trust the improvement.

### Friction root-cause (why mdot is overpredicted)

`f * Re = 64.0` exactly for all four Salt1-4 nominal cases -- the solver's
`friction_form` default is `"F1"` (plain fully-developed-laminar 64/Re, no
entrance-length or buoyancy correction), even though `F3_hagenbach`,
`F4_leg_class`, and `F5_ri_corrected` are already implemented in
`friction_closures.py` but not wired into this candidate. This is the most
likely direct cause of the mdot overprediction and the cheapest, most
physically-grounded next fix (see `future_work_sequence.csv`, step 1).

### F6 pure-multiplier temperature ablation

A pure multiplier (no offset) is NOT robust: under either fit basis it does
well on one +/-5%Q direction and poorly on the other, unlike F2 (affine),
which is stable across both directions and both fit bases. This shows the
additive offset term is load-bearing, not a redundant extra parameter.
Recommend AGAINST the pure-multiplier form for temperature.

## Open first

- `combined_model_spec.csv`
- `evidentiary_tier_table.csv`
- `mdot_correction_fit.csv`
- `temp_correction_holdout_scores.csv`
- `friction_root_cause.csv`
- `f6_pure_multiplier_ablation.csv`
- `claim_boundary_table.csv`
- `future_work_sequence.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
