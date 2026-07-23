# TODO-EXPERIMENT-BASIS-AMBIENT-HEAT-LOSS-FRICTION-MODEL-FORM-SEARCH-2026-07-23 Status

Date: `2026-07-23`
Role: Forward-pred / Hydraulics / Thermal-modeling / Implementer / Tester / Writer / Reviewer
Owner: claude

## Scope

Document a real solver-level model-form search (friction-closure form,
ambient heat-loss/insulation magnitude, internal-Nu magnitude) for reducing
TP/TW error on the TSWFC2 candidate `tswfc2_smoke_salt2_four_node_v1`, scored
against EXPERIMENTAL `measured_K` (NOT CFD `reference_k`). This is explicitly
the experiment-anchored secondary track, off-scope for the CFD-only thesis
main body, per the same user decision that relabeled this session's two prior
packages. All twelve numbered findings supplied were computed in-conversation
this session via ad hoc `solve_case()` calls; this task's job is to verify
what is independently checkable and organize/document everything with
explicit provenance, not to re-run the solver.

## Completed

- Read the two prior sibling packages
  (`2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score`,
  `2026-07-23_combined_best_current_model_temp_mdot_correction`) fully as
  style/banner templates, plus their status file, journal entry, imports
  manifest, and operational note as format templates.
- Independently verified every number that could be checked against a
  reachable repo file (see `verify_*` functions in the build script and the
  parallel checks in the test script):
  - F1-based `F2_global_affine` (Salt1-4 refit) coefficients
    (`a=0.5746889644933884`, `b=138.28222646893295`,
    `train_MAE=9.291089110109809`) confirmed in
    `2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/refit_coefficients.csv`
    and `train_fit_quality.csv`.
  - M3 comparator (`segment_only_fluid_walls`) TP=13.558 K, TW=18.9775 K
    confirmed in
    `work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/master_model_form_scoreboard.csv`.
  - The internal-Nu guardrail phrase ("do not tune Nu to absorb heater,
    cooler/HX, passive wall, radiation, storage, or branch-mixing residuals")
    confirmed verbatim in `.agent/BLOCKERS.md`'s resolved
    `thermal-cfd-1d-parity` entry.
  - The F4 docstring line ("F4  calibrated global multiplier — existing
    major_loss_multiplier in MinorLosses") and the F3_hagenbach/Shah(1978)
    citation confirmed verbatim in `friction_closures.py`.
  - The `t_ins_m = insulation_thickness_in * INCH_TO_M * insulation_multiplier`
    formula and `major_loss_multiplier: float = 1.0` default confirmed
    verbatim in `solver.py`.
  - Both prior undocumented sweeps
    (`joint_htc_friction_calibration_weekend_focused_v1`,
    `practical_reduced_order_broadened_v1`) independently re-derived from
    their own CSVs: 64/12 data rows, TP RMSE stuck 67.64-68.57 K, TW RMSE
    stuck 64.92-65.51 K (joint_htc); best TP RMSE 59.99 K, mean TW-excl-TW10
    RMSE 65.897 K (std 13.146) per the practical-ROM `RUN_SUMMARY.md`;
    neither sweep's trial grid has a `friction_form` column; the practical-ROM
    `scenario_plan.csv` per-segment `outer_insulation_multiplier_by_parent_segment`
    values range 0.85-1.5x, never below 0.85x. Also confirmed neither sweep
    name appears in `CLAUDE.md` or the master scoreboard -- though both file
    paths DO appear in two prior exploration/read-list contexts
    (`.agent/status/2026-06-19_AGENT-090.md`'s command list;
    `reports/2026-06/2026-06-19/.../dual_path_execution_report.md`'s anchor
    list), just never analyzed for the TP/TW-stuck finding itself. Documented
    this honest nuance rather than an unqualified "never referenced" claim.
  - Confirmed `validation_table.csv`'s `measured_K` column exists as the
    scoring basis for this package (spot-checked
    `work_products/2026-07/2026-07-20/2026-07-20_tswfc2_bounded_nominal_scorecard/case_outputs/Salt_2/validation_table.csv`).
- All other numbers (friction-closure comparison percentages, F3_hagenbach
  T-refit, insulation/friction sweeps, validation-case raw-physics scores,
  residual correction fit, internal-Nu ablation) are session-only ad hoc
  `solve_case()` results with no upstream CSV to check against. These are
  hard-coded in the build script with an explicit
  `SESSION_SOLVE_PROVENANCE` tag and are NOT re-run by this script or its
  tests; the tests instead check internal self-consistency (e.g. the stated
  4.48% mean |mdot_err| across Salt1-4 equals `mean()` of the 4 stored
  per-case values; the internal-Nu TP series is monotonic and the stated
  2.36 K gap-closed matches the first/last row difference; the friction-form
  means match the per-case values).
- Built
  `tools/analyze/build_experiment_basis_ambient_heat_loss_friction_model_form_search.py`
  (writes all 16 CSVs + `README.md` + `summary.json`; runs no solver, no
  OpenFOAM, no case_stage mutation).
- Wrote the full work_products package: `README.md` (off-scope-for-CFD-main-body
  banner, "validation" terminology footnote crosswalk, all 12 findings, a
  "what this proves vs. what remains a hypothesis" section), `summary.json`,
  `friction_closure_comparison.csv`, `mdot_temperature_decoupling_check.csv`,
  `prior_undocumented_sweeps_found.csv`, `sign_convention_corrections.csv`,
  `insulation_screening_sweep.csv`,
  `insulation_friction_zero_crossing_refinement.csv`,
  `salt1_4_train_validation_at_recommended_combo.csv`,
  `validation_case_scores_raw_physics.csv`,
  `residual_correction_on_physics_baseline.csv`, `internal_nu_ablation.csv`,
  `physical_plausibility_caveats.csv`, `claim_boundary_table.csv`,
  `validation_exposure_count.csv`, `validation_terminology_crosswalk.csv`,
  `source_manifest.csv`, `no_mutation_guardrails.csv`.
- Wrote
  `tools/analyze/test_experiment_basis_ambient_heat_loss_friction_model_form_search.py`
  (13 checks: required outputs exist; summary flags including
  `main_body_scope`/`validated_against`/no-solver-run declarations; friction
  closure comparison internal consistency and F3_hagenbach-wins ordering;
  F1-based F2 coefficients match upstream file exactly; M3 comparator matches
  master scoreboard and this package's own comparator row; guardrail phrase
  cited verbatim in `.agent/BLOCKERS.md`, `summary.json`, and `README.md`; F4
  docstring line and Shah(1978) citation present in `friction_closures.py`;
  Salt1-4 mean-at-recommended-combo internal consistency (4.48%/5.73K); the
  internal-Nu TP series is monotonic non-increasing with the stated 2.36 K
  gap and the htc_mult=1 mdot error matches finding 1's Salt2/F3_hagenbach
  value; both prior sweeps confirmed absent from CLAUDE.md/scoreboard with
  `friction_form_varied=False`; claim-boundary table has the required
  allowed/forbidden rows; validation-exposure-count documents the 3rd-4th
  pass and the "not a legitimate...score" statement; no-mutation guardrails
  all False; source manifest entries are read-only or explicitly
  session-only). All 13 checks pass.

## Current State

Package complete. Build script is deterministic and re-runnable (reads only
read-only upstream files plus hard-coded, provenance-tagged session-only
numbers; no `Date.now()`/random; no OpenFOAM run; no 1D `solve_case()` run;
no case_stage mutation). Test suite passes:
`python3 tools/analyze/test_experiment_basis_ambient_heat_loss_friction_model_form_search.py`
prints "Experiment-basis ambient heat-loss + friction model-form search
checks passed."

The package explicitly and repeatedly documents (README off-scope banner,
provenance callout, claim boundary table, no-mutation guardrails, this status
file, the journal entry) that: (1) this is the experiment-basis (measured_K)
secondary track, not the CFD-only thesis main body; (2) the insulation~8%
finding is a calibrated hypothesis, not a verified physical measurement; (3)
the internal-Nu ablation is a decisive/rigorous finding, numerically
justifying the repo's own guardrail; (4) this is at least a 3rd-4th scoring
exposure of `salt2_lo5q`/`salt2_hi5q`/`val_salt2` this session and does not
constitute a legitimate single-use protected-split score; (5) this package
has no CFD-basis equivalent and is cross-referenced as a parallel track, not
claimed as superseding/superseded.

## Follow-up

1. If a genuine physical inspection of the rig's insulation condition becomes
   available, use it to either confirm or refute the ~8%-of-nameplate
   effective insulation hypothesis found here.
2. Whichever agent next touches the 1D solver / friction closures should
   consider wiring `friction_form="F3_hagenbach"` as the new default for this
   candidate, given the zero-fitting mdot-error improvement found here.
3. The val_salt2 property-basis discrepancy flagged in finding 8 (this
   package used `salt_current`; the parallel CFD-basis session found
   `salt_jin` is the methodologically consistent choice) should be resolved
   in a future pass, not silently carried forward as consistent.
4. Treat `salt2_lo5q`/`salt2_hi5q`/`val_salt2` as further spent for any
   future single-use freeze score (now a 3rd-4th exposure); use Salt4 +/-5Q
   or +/-10Q rows instead for the next genuine single-use protected-split
   evaluation.
5. This package's ambient-heat-loss/friction physics-finding content has no
   CFD-basis equivalent yet; a future CFD-basis session could investigate
   whether an analogous insulation/friction-form search against CFD
   `reference_k` produces a comparable optimum.

No further action required from this task itself; board row marked COMPLETE.
