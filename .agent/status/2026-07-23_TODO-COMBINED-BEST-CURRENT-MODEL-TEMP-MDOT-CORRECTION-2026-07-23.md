# TODO-COMBINED-BEST-CURRENT-MODEL-TEMP-MDOT-CORRECTION-2026-07-23 Status

Date: `2026-07-23`
Role: Forward-pred / Implementer / Tester / Writer / Reviewer
Owner: claude

## Scope

Assemble the final "best current model" deliverable the user explicitly
requested: combine the holdout/external-validated temperature correction
(`F2_global_affine`, Salt1-4 refit) with a train-only mass-flow multiplicative
correction into one honestly-tiered combined-model package, document the
friction root-cause finding for the mdot overprediction, document the F6
pure-multiplier temperature ablation, and name concrete future work
separately. No new curve-fitting beyond the already-established mdot 1-DOF
multiplier; no new solver runs.

## Completed

- Verified every cited number against its source file before writing anything:
  - `F2_global_affine` (Salt1-4 refit) coefficients `a=0.5746889644933884`,
    `b=138.28222646893295` — confirmed in
    `2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/refit_coefficients.csv`.
  - Holdout/external MAE (Salt1_4_refit fit_basis): salt2_lo5q=3.5017398572680727 K,
    salt2_hi5q=3.1694407461151193 K, val_salt2=5.868112800214832 K — confirmed
    in `holdout_external_score_old_vs_new.csv`.
  - Train MAE 9.291089110109809 K — confirmed in `train_fit_quality.csv`.
  - Raw mdot pred/measured pairs for Salt1-4 — confirmed in
    `2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_{1,2,3,4}/summary.csv`
    (`mdot_kg_s`, `measured_mass_flow_rate_kg_s`, `friction_factor_main`,
    `reynolds_main` columns).
  - `f * Re = 64.0` exactly for all four Salt1-4 nominal cases (recomputed).
  - Independently recomputed the 1-DOF multiplicative fit
    `a = sum(pred*meas)/sum(pred**2) = 0.7504257967710826`, in-sample
    MAE=0.0005292970724547924 kg/s, mean relative error=3.1658220088627402%
    (matches cited ~0.000529 / ~3.17%); raw mean relative error
    32.57455114068148% (matches cited ~32.57%).
  - Independently recomputed the rejected 2-DOF affine alternative
    (`a=0.5688041864582456`, `b=0.0042901970515859065`, mean relative error
    2.2021438385811214%) — matches cited numbers exactly.
  - Confirmed `reverse_area_fraction` values 0.37-0.79 and
    `recirculation_status == recirculating_section_effective` for all six
    salt2_lo5q/hi5q pm5 upcomer-plane stations in
    `2026-07-17_predict_salt2_pm5_holdout_extraction_repair/salt2_pm5_admission_table.csv`,
    confirming the rejection rationale for the Re-based mdot back-calculation.
  - Confirmed `friction_form: str = "F1"` is the solver default in
    `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py`,
    and that `dp_F1`, `dp_F3_hagenbach`, `dp_F4_leg_class`, `dp_F5_ri_corrected`
    all exist in `friction_closures.py` but are not wired into this
    candidate's `friction_form`.
  - No number was found to mismatch its cited source.
- Built `tools/analyze/build_combined_best_current_model_temp_mdot_correction.py`,
  which cites the F2 temperature correction verbatim from the upstream
  read-only refit package, recomputes the mdot multiplicative/affine fits in
  the open from the read-only Salt1-4 nominal `summary.csv` files (same
  methodology already verified this session, not a new fitting exercise), and
  hard-codes the F6 ablation and friction-root-cause numbers with an in-file
  provenance comment (these exact scoring passes were run ad hoc
  in-conversation this session and are not yet materialized as upstream
  CSVs).
- Wrote the full work_products package: `README.md` (with a prominent
  EVIDENTIARY TIER CALLOUT), `summary.json`, `combined_model_spec.csv`,
  `mdot_correction_fit.csv` (both the recommended multiplicative and the
  rejected affine fit, for transparency), `temp_correction_holdout_scores.csv`,
  `f6_pure_multiplier_ablation.csv`, `friction_root_cause.csv`,
  `claim_boundary_table.csv`, `evidentiary_tier_table.csv`,
  `future_work_sequence.csv` (5 ordered steps), `source_manifest.csv`,
  `no_mutation_guardrails.csv`.
- Wrote `tools/analyze/test_combined_best_current_model_temp_mdot_correction.py`
  (9 checks: required outputs exist; summary flags; mdot correction reduces
  error vs raw baseline on all 4 known pairs; mdot multiplier matches an
  independent least-squares recomputation; friction f*Re=64.0 for all 4
  cases with the correct closure-form labels; F2 temp coefficients match the
  upstream refit file exactly; claim-boundary table contains the required
  forbidden-claim rows (holdout-validated mdot, physical closure,
  final/frozen score) and an allowed combined-model claim; evidentiary tier
  table matches the spec; F6 ablation shows the offset is load-bearing; all
  guardrails False and all sources read-only). All 9 checks pass.

## Current State

Package complete. Script is deterministic and re-runnable (reads only
read-only upstream CSVs plus hard-coded, provenance-commented ad hoc numbers;
no `Date.now()`/random; no OpenFOAM run; no 1D `solve_case()` run; no
case_stage mutation). Test suite passes:
`python3 tools/analyze/test_combined_best_current_model_temp_mdot_correction.py`
prints "Combined best-current model temp/mdot correction checks passed."

The package explicitly and repeatedly documents (README EVIDENTIARY TIER
CALLOUT, `evidentiary_tier_table.csv`, `claim_boundary_table.csv`,
`no_mutation_guardrails.csv`, this status file, the journal entry) that the
temperature correction is holdout/external validated while the mass-flow
correction is train-only and has never been evaluated out-of-sample, and that
the two must never be described with the same evidentiary confidence.

## Follow-up

1. Swap `friction_form` to `F3_hagenbach`/`F4_leg_class`/`F5_ri_corrected` and
   re-run the existing Salt1-4 nominal solver pass to test whether the mdot
   overprediction shrinks (cheapest, most physically-grounded next fix).
2. Re-check whether F2's 138.28 K offset shrinks once mdot is fixed, to
   separate mdot-driven bias from a genuine heat-transfer/thermal-BC gap
   (Q = mdot * cp * deltaT coupling).
3. Continue the separate, active PASSIVE-H2 outer-insulation/radiation
   heat-loss admission track (not conflated with this package).
4. Obtain a genuine non-recirculating held-out mdot readout before ever
   claiming a validated mass-flow correction.
5. Treat salt2_lo5q/salt2_hi5q/val_salt2 as spent for any future single-use
   freeze score; use Salt4 +/-5Q or +/-10Q rows instead.

No further action required from this task; hand off to whichever agent owns
the friction-closure re-run or the next thesis model-selection decision.
