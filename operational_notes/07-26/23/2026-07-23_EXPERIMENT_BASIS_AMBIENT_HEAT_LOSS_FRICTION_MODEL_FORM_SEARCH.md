---
provenance:
  - work_products/2026-07/2026-07-23/2026-07-23_experiment_basis_ambient_heat_loss_friction_model_form_search/summary.json
tags: [experiment-basis, measured-K, ambient-heat-loss, insulation, friction-closure, internal-nu-ablation, model-form-search, off-scope-cfd-main-body]
related:
  - work_products/2026-07/2026-07-23/2026-07-23_experiment_basis_ambient_heat_loss_friction_model_form_search/README.md
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/README.md
  - work_products/2026-07/2026-07-23/2026-07-23_combined_best_current_model_temp_mdot_correction/README.md
  - operational_notes/07-26/23/2026-07-23_EMPIRICAL_BIAS_SALT1_4_REFIT_HOLDOUT_EXTERNAL_SCORE.md
  - operational_notes/07-26/23/2026-07-23_COMBINED_BEST_CURRENT_MODEL_TEMP_MDOT_CORRECTION.md
  - operational_notes/maps/friction-closures.md
  - operational_notes/maps/thermal-boundary-and-radiation.md
task: TODO-EXPERIMENT-BASIS-AMBIENT-HEAT-LOSS-FRICTION-MODEL-FORM-SEARCH-2026-07-23
date: 2026-07-23
role: Forward-pred / Hydraulics / Thermal-modeling / Writer
owner: claude
type: operational_note
status: current
---

# Start-here: Experiment-basis ambient heat-loss + friction model-form search (2026-07-23)

## Why this exists

The user asked for the best model form for reducing TP/TW error via a real
solver-level model-form search (friction closure, ambient heat-loss/
insulation magnitude, internal-Nu magnitude) rather than a post-hoc empirical
correction, scored against experimental `measured_K`. This note is the
start-here for that search's twelve findings.

## OFF-SCOPE CAVEAT (read before citing any number here)

This entire track is validated against **experimental `measured_K`**
(`validation_table.csv`), NOT CFD `reference_k`. The thesis main body is
CFD-only. This note and its package are the experiment-anchored secondary
track, exactly like its two siblings
(`operational_notes/07-26/23/2026-07-23_EMPIRICAL_BIAS_SALT1_4_REFIT_HOLDOUT_EXTERNAL_SCORE.md`,
`operational_notes/07-26/23/2026-07-23_COMBINED_BEST_CURRENT_MODEL_TEMP_MDOT_CORRECTION.md`).

Unlike those two siblings, this package's content (real solver-level
ambient-heat-loss/friction model-form search) has **no CFD-basis equivalent
yet**. It is cross-referenced as **"the parallel main-body track using
different reference data"**
(`work_products/2026-07/2026-07-23/2026-07-23_salt2_pm5_holdout_inputs_and_f2_score/`),
not claimed as superseded by or superseding it.

## Headline result

- **Friction closure comparison** (Salt1-4 nominal, TSWFC2 candidate
  `tswfc2_smoke_salt2_four_node_v1`): F3_hagenbach wins (mean pct error
  11.8%) over F3_shah_apparent (15.8%) and F1 (32.6%), zero fitting. Reverses
  the 2026-07-07 historical benchmark on a different candidate config --
  closure performance is candidate-specific.
- **mdot/temperature decoupling:** refitting the F2-style affine T-correction
  on F3_hagenbach-based predictions gives essentially the same train/
  validation MAE as the F1-based refit -- mdot-correction and T-correction
  are decoupled for this model.
- **Two undocumented prior sweeps found**
  (`joint_htc_friction_calibration_weekend_focused_v1`,
  `practical_reduced_order_broadened_v1`) show the friction/HTC-shape space
  is exhausted (TP/TW RMSE stuck 65-68 K across both grids) and neither
  tested insulation multipliers below 0.85x -- confirming the ambient
  heat-loss MAGNITUDE direction was genuinely untested before this package.
- **Sign-error correction (methodological lesson):** insulation_multiplier
  scales thickness UP, not down -- increasing it makes the model HOTTER, the
  opposite of the initial wrong hypothesis.
- **Corrected-direction insulation sweep:** a genuine non-monotonic optimum
  near insulation_multiplier~=0.08 (8% of nameplate thickness), with
  major_loss_multiplier=0.6, gives the best combined mdot/TP result.
- **Full Salt1-4 train validation at the recommended combo**
  (F3_hagenbach, insulation_multiplier=0.08, major_loss_multiplier=0.6): mean
  |mdot_err|=4.48%, TP=5.73 K, TW=20.69 K -- down from the F1/ins=1.0
  baseline's ~32.6%/~90-100 K, and better on TP than the M3 comparator
  (13.558 K TP, 18.9775 K TW, diagnostic_not_admitted).
- **Validation-case scores (zero fitted parameters):** salt2_lo5q MAE=5.387
  K, salt2_hi5q MAE=2.398 K, val_salt2 MAE=7.418 K (val_salt2 carries an
  unresolved property-basis caveat -- see package README).
- **Optional residual correction:** a small affine fit on top of the physics
  baseline reaches train MAE=9.22 K, essentially the same ~9.2-9.3 K floor as
  every other affine-correction attempt this session -- a genuine tradeoff,
  not a strict win, and optional.
- **Internal-Nu ablation, decisive:** sweeping internal HTC across 500x
  closes only 2.36 K of the ~96 K gap before asymptoting -- numerically
  proves the wall/insulation/ambient resistances dominate, justifying this
  repo's own guardrail against tuning Nu to absorb heat-loss residuals rather
  than merely deferring to it.

## What this proves vs. what remains a hypothesis

- **Decisive:** internal-Nu ruling-out (finding 10).
- **Calibrated hypothesis, needs rig verification:** insulation~=8% of
  nameplate thickness (findings 5-7, 11).

## Recommendation

Report this track's friction-closure and internal-Nu findings as decisive
physics-level evidence. Report the insulation~8% finding as a calibrated
hypothesis pending independent physical verification of the rig. Do not cite
any number here as the CFD-validated thesis main-body model. Do not treat
`salt2_lo5q`/`salt2_hi5q`/`val_salt2` scores here as a legitimate single-use
protected-split score (this is at least a 3rd-4th exposure this session).

## Open first

- `work_products/2026-07/2026-07-23/2026-07-23_experiment_basis_ambient_heat_loss_friction_model_form_search/README.md`
- `.../friction_closure_comparison.csv`
- `.../salt1_4_train_validation_at_recommended_combo.csv`
- `.../internal_nu_ablation.csv`
- `.../claim_boundary_table.csv`
- `.../physical_plausibility_caveats.csv`

## Trusted packages

- `work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/`
  (source of the F1-based F2 temperature correction cited for comparison; not
  modified by this task).
- `work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/`
  (source of the M3 comparator).
- `.agent/BLOCKERS.md` (source of the internal-Nu guardrail phrase).
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py`
  (source of the F3_hagenbach/F4 closure-hierarchy citations, read/run-only,
  not edited).
- `../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/joint_htc_friction_calibration_weekend_focused_v1/`
  and `.../practical_reduced_order_broadened_v1/` (source of the two prior
  undocumented sweeps, read-only, no edits).

## Unresolved blockers

- The recommended combo (F3_hagenbach, insulation_multiplier=0.08,
  major_loss_multiplier=0.6) has not been re-run as a real, tool-tracked
  solver campaign outside this session's ad hoc exploration.
- The val_salt2 property-basis discrepancy (this package used
  `salt_current`; the parallel CFD-basis session found `salt_jin` is
  methodologically consistent) is flagged, not resolved.
- The insulation~=8%-of-nameplate hypothesis has no independent physical
  verification against the rig's actual as-built insulation condition.

## Active board rows

- `TODO-EXPERIMENT-BASIS-AMBIENT-HEAT-LOSS-FRICTION-MODEL-FORM-SEARCH-2026-07-23`
  (this task; STATUS: COMPLETE 2026-07-23).

## Next task sequence

1. Wire `friction_form="F3_hagenbach"` as the default for this candidate in
   a real, tool-tracked solver run (not ad hoc), given the zero-fitting mdot
   improvement found here.
2. Resolve the val_salt2 property-basis discrepancy before citing this
   package's validation scores again.
3. Seek independent physical verification (photos/inspection) of the rig's
   insulation condition to test the insulation~8% hypothesis.
4. Treat `salt2_lo5q`/`salt2_hi5q`/`val_salt2` as further spent for any
   future single-use freeze score; use Salt4 +/-5Q or +/-10Q rows instead.
5. Consider whether an analogous insulation/friction-form search against CFD
   `reference_k` (the parallel main-body track) would find a comparable
   optimum.

## Output contract

Every headline number in this note and in the linked work_products package
that could be independently checked against a reachable repo file was
verified before being written (see the task's journal entry, status file,
and the build script's `verify_*` functions for the full list). Numbers that
could not be independently checked are explicitly tagged as session-only,
ad hoc `solve_case()` results, not re-run by this task.

## Do-not-do

No physical-closure claim. No claiming insulation~8% is a verified physical
measurement. No claiming this is the CFD-validated thesis main-body model. No
claiming this is a legitimate single-use protected-split freeze score. No
native/registry/scheduler/Fluid/thesis mutation, no S11/S15/S6 trigger, no
solver run by this task, no commit/push without explicit request, no
touching any other board row's files.
