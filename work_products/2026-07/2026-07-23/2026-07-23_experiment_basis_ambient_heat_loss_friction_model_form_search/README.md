---
provenance:
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/refit_coefficients.csv
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/train_fit_quality.csv
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/holdout_external_score_old_vs_new.csv
  - work_products/2026-07/2026-07-22/2026-07-22_thesis_master_model_form_scoreboard/master_model_form_scoreboard.csv
  - .agent/BLOCKERS.md
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/friction_closures.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/tamu_loop_model_v2/solver.py
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/joint_htc_friction_calibration_weekend_focused_v1/trial_grid__salt.csv
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/practical_reduced_order_broadened_v1/analysis/scenario_rankings.csv
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/practical_reduced_order_broadened_v1/scenario_plan.csv
  - ../cfd-modeling-tools/tamu_first_order_model/Fluid/results/diagnostics/practical_reduced_order_broadened_v1/RUN_SUMMARY.md
tags: [forward-model, experiment-basis, measured-K, ambient-heat-loss, insulation, friction-closure, internal-nu-ablation, model-form-search, off-scope-cfd-main-body]
related:
  - .agent/status/2026-07-23_TODO-EXPERIMENT-BASIS-AMBIENT-HEAT-LOSS-FRICTION-MODEL-FORM-SEARCH-2026-07-23.md
  - .agent/journal/2026-07-23/experiment-basis-ambient-heat-loss-friction-model-form-search.md
  - imports/2026-07-23_experiment_basis_ambient_heat_loss_friction_model_form_search.json
  - operational_notes/07-26/23/2026-07-23_EXPERIMENT_BASIS_AMBIENT_HEAT_LOSS_FRICTION_MODEL_FORM_SEARCH.md
  - work_products/2026-07/2026-07-23/2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score/README.md
  - work_products/2026-07/2026-07-23/2026-07-23_combined_best_current_model_temp_mdot_correction/README.md
task: TODO-EXPERIMENT-BASIS-AMBIENT-HEAT-LOSS-FRICTION-MODEL-FORM-SEARCH-2026-07-23
date: 2026-07-23
role: Forward-pred/Hydraulics/Thermal-modeling/Implementer/Tester/Writer/Reviewer
type: work_product
status: complete
main_body_scope: off_scope_experiment_basis
parallel_main_body_track: work_products/2026-07/2026-07-23/2026-07-23_salt2_pm5_holdout_inputs_and_f2_score (CFD-basis, different reference data, NOT superseded/superseding -- this content has no CFD-basis equivalent yet)
---
# Experiment-Basis Ambient Heat-Loss + Friction Model-Form Search

> **OFF-SCOPE FOR THE CFD-ONLY THESIS MAIN BODY (2026-07-23, user-directed).**
> This package is validated against **experimental `measured_K`**
> (`validation_table.csv`'s `measured_K` column), NOT CFD `reference_k`. The
> thesis main body is purely computational (CFD `reference_k` is the reference
> truth), so this experiment-basis result must NOT be cited as the CFD-validated
> model. It is retained as the experiment-anchored (measured_K) secondary track,
> exactly like its two sibling packages
> (`2026-07-23_empirical_bias_salt1_4_refit_holdout_external_score`,
> `2026-07-23_combined_best_current_model_temp_mdot_correction`).
>
> Unlike those two siblings, this package's content (real solver-level
> ambient-heat-loss/friction model-form search, not a post-hoc statistical
> correction) has **no CFD-basis equivalent yet** -- it is genuinely new
> physics-finding content not previously done in either basis. It is therefore
> cross-referenced as **"the parallel main-body track using different
> reference data"**
> (`work_products/2026-07/2026-07-23/2026-07-23_salt2_pm5_holdout_inputs_and_f2_score/`),
> not claimed as superseded by or superseding it.

## Terminology note: "validation" not "holdout"

Per explicit user instruction this session, `salt2_lo5q`, `salt2_hi5q`, and
`val_salt2` are called **validation** cases throughout this package (not
"holdout"). See `validation_terminology_crosswalk.csv` for a footnote
crosswalk to the repo's internal split-policy labels (holdout =
`blind_holdout_pm5q` for Salt2 +/-5Q, external_test = `val_salt2`) so nothing
breaks for readers of other packages using the older terminology.

Decision: `experiment_basis_ambient_heat_loss_friction_model_form_search_complete_measured_K_track_not_a_physical_closure_not_a_freeze_score`.

## PROVENANCE CALLOUT (read first)

ALL solver-level numbers in this package (friction-closure comparison,
insulation/friction sweeps, internal-Nu ablation, validation-case scores,
residual correction fit) were computed **in-conversation this session** via
direct, ad hoc `solve_case()` calls that were never written to the repo as
reusable tools. They are cited here with an explicit provenance tag and are
**reproducible only by re-running the solver** with the stated
`ScenarioConfig` settings -- this script does not re-run the solver, only
organizes/tabulates/cross-checks the numbers. Wherever a number could be
independently checked against an existing repo file (the F1-based F2
temperature-correction coefficients, the M3 comparator, the
`friction_closures.py` F4 docstring line and F3_hagenbach/Shah(1978)
citation, the `.agent/BLOCKERS.md` internal-Nu guardrail phrase, and the two
prior undocumented sweep CSVs), this script reads that file directly and
asserts the match -- see `tools/analyze/build_experiment_basis_ambient_heat_loss_friction_model_form_search.py`'s
`verify_*` functions and the accompanying test suite.

## What this package is

A real solver-level model-form search for reducing TP/TW error on the TSWFC2
candidate `tswfc2_smoke_salt2_four_node_v1` -- friction-closure form,
ambient heat-loss (insulation) magnitude, and internal-Nu magnitude -- scored
against **experimental measured_K**, as requested when the user asked for the
best model form using real solver-level search (not just post-hoc empirical
correction). It documents twelve findings: a friction-closure comparison; an
mdot/temperature decoupling check; two undocumented prior sweeps found in the
Fluid repo; a sign-error correction (methodological lesson); a corrected-
direction insulation screening sweep with a genuine non-monotonic optimum; a
fine mdot-zero-crossing refinement; full Salt1-4 train validation at the
recommended combo; validation-case scores with zero fitted parameters; an
optional residual affine correction on top of the physics baseline; a
decisive internal-Nu ablation up to 500x; physical-plausibility caveats; and
a validation-exposure count.

## What this package is NOT

- Not the CFD-validated thesis main-body model (see off-scope banner above).
- Not a physical closure. The insulation_multiplier~=0.08 value is a
  calibrated finding, NOT an independently-verified physical measurement of
  the rig's actual insulation condition.
- Not a legitimate single-use protected-split score. `salt2_lo5q`,
  `salt2_hi5q`, and `val_salt2` have now been scored at least a 3rd-4th time
  this session across this package and its two siblings (see
  `validation_exposure_count.csv`).
- Not superseded by or superseding the CFD-basis main-body track -- this is
  new physics-finding content with no CFD-basis equivalent yet.
- Does not run OpenFOAM or the 1D `solve_case()` solver (all solver-level
  numbers were computed earlier in this session, not by this script); does
  not mutate any case_stage tree; does not touch any other board row's files.

## What this proves vs. what remains a hypothesis

- **Decisive / rigorous (proves a negative, not just deference to a
  guardrail):** the internal-Nu ablation (finding 10) sweeps internal HTC
  across 500x -- a physically implausible magnitude -- and shows the gap
  closes by only 2.36 K of ~96 K before asymptoting. This is quantitative,
  falsifiable evidence that no internal-Nu value can close the residual gap,
  because the series thermal-resistance network (R_i + R_wall + R_ins + R_o)
  is dominated by the non-internal terms. This directly and numerically
  justifies this repo's own standing guardrail
  ("do not tune Nu to absorb heater, cooler/HX, passive wall, radiation, storage, or branch-mixing residuals") rather than merely deferring to it.
- **Calibrated / needs rig verification (a hypothesis, not a proof):** the
  insulation_multiplier~=0.08 (effective insulation ~8% of nameplate
  thickness) finding is a curve-matching result against experimental
  `measured_K`. It is physically plausible (gaps at supports/instrumentation
  ports, degraded/aged insulation, uninsulated fittings, thermal bridging)
  but has NOT been checked against the rig's actual as-built insulation
  condition. Treat it as a calibrated hypothesis pending independent
  physical verification (see `physical_plausibility_caveats.csv`).

## Headline numbers (see CSVs for full detail and provenance)

### 1. Friction closure comparison (Salt1-4 nominal, TSWFC2 candidate)

F3_hagenbach wins: mean pct error 11.8% vs F3_shah_apparent's 15.8% and F1's
32.6%, with zero fitting. This reverses the 2026-07-07 historical benchmark
(`work_products/2026-07/2026-07-07/2026-07-07_friction_forms_comparison/mdot_comparison.csv`), where F3_shah_apparent won on a
DIFFERENT case config -- closure performance is candidate-specific, not
universally transferable. See `friction_closure_comparison.csv`.

### 2. mdot/temperature decoupling check

Refitting the F2-style affine T-correction on F3_hagenbach-based 1D
predictions gives train MAE ~9.25 K and validation MAE ~3.48/3.35/5.83 K --
essentially identical to the F1-based refit's 9.29 K / 3.50/3.17/5.87 K.
Mdot-correction and T-correction are decoupled for this model. See
`mdot_temperature_decoupling_check.csv`.

### 3. Two undocumented prior sweeps found

`joint_htc_friction_calibration_weekend_focused_v1`
(64 data rows) shows TP RMSE stuck at
67.64-68.57 K and
TW RMSE stuck at 64.92-65.51 K
across its entire grid regardless of HTC-shape/profile-descriptor tuning.
`practical_reduced_order_broadened_v1` (12
rows) found best TP RMSE 59.99 K but
overall mean TW-excl-TW10 RMSE 65.897 K
(std 13.146). Neither sweep varied
`friction_form`, and the insulation multiplier range actually tested in the
second sweep was 0.85-
1.50x nameplate --
never approaching this package's found optimum of ~0.08x.
See `prior_undocumented_sweeps_found.csv` (includes an honest caveat: the file
paths DO appear in two prior exploration/read-list contexts, just never
analyzed for this finding or entered into CLAUDE.md/the thesis scoreboard).

### 4. Sign-error correction (methodological lesson)

`outer_insulation_multiplier_by_parent_segment` scales insulation THICKNESS
directly, so increasing it means MORE insulation and a HOTTER model -- the
opposite of the initial wrong hypothesis. `outer_rad_multiplier_by_parent_segment`
was inert (this candidate has `radiation_on=False`). `major_loss_multiplier`
direction also flipped once real ambient heat loss was added. See
`sign_convention_corrections.csv`.

### 5-6. Insulation screening sweep and zero-crossing refinement

A genuine non-monotonic optimum near insulation_multiplier~=0.08 (TP~4.4-4.8
K), with major_loss_multiplier=0.60 giving the best combined mdot/TP result
(mdot_err=-0.67%, TP=4.43 K, TW=19.50 K, Salt2). See
`insulation_screening_sweep.csv` and
`insulation_friction_zero_crossing_refinement.csv`.

### 7. Full Salt1-4 train validation at the recommended combo

(friction_form=F3_hagenbach, insulation_multiplier=0.08 uniform,
major_loss_multiplier=0.6): mean |mdot_err|=4.48%, TP=5.73 K, TW=20.69 K
across all four Salt1-4 train cases (Salt1 is the outlier at TP=11.04 K,
consistent with this repo's documented "Salt1 weakly converged" caveat).
Compare to the F1/ins=1.0 baseline (mean |mdot_err|=32.6%, TP~90-100 K) and to
the M3 comparator (`13.558` K TP, `18.9775` K TW,
diagnostic_not_admitted). See `salt1_4_train_validation_at_recommended_combo.csv`.

### 8. Validation-case scores, RAW physics (zero fitted parameters)

salt2_lo5q MAE=5.387 K, salt2_hi5q MAE=2.398 K, val_salt2 MAE=7.418 K
(val_salt2 carries a property-basis caveat -- see below). Comparable overall
to the earlier empirical F1-based F2 correction's 3.50/3.17/5.87 K, with ZERO
fitted parameters instead of 2. See `validation_case_scores_raw_physics.csv`.

**val_salt2 property-basis caveat:** this package used the `salt_current`
property override for val_salt2 per this session's earlier convention. The
PARALLEL CFD-basis session found this was methodologically inconsistent for
the CFD comparison and that val_salt2's correct operating point should use
`salt_jin` default properties matching Salt2 nominal. This experiment-basis
package has NOT been re-verified against that correction -- flagged as a
known limitation needing follow-up, not silently claimed consistent.

### 9. Optional residual affine correction on top of the physics baseline

a=0.7915691091053846, b=97.05201417937809, train MAE=9.2199 K -- essentially
the SAME ~9.2 K training ceiling as every other affine-correction attempt
this session regardless of underlying physics, suggesting a genuine
local/segment-level structure a global affine correction cannot capture. With
this correction: mean validation MAE=4.13 K (best mean found this session),
but it is a genuine tradeoff (helps lo5q, slightly hurts hi5q vs raw-physics-
only), not a strict win, and is OPTIONAL, not required. See
`residual_correction_on_physics_baseline.csv`.

### 10. Internal-Nu ablation -- decisive ruling-out

See "What this proves vs. what remains a hypothesis" above and
`internal_nu_ablation.csv` for the full 9-row htc_mult sweep.

### 11. Physical plausibility caveats

See `physical_plausibility_caveats.csv`: insulation_multiplier~=0.08 is a
calibrated hypothesis needing rig verification; major_loss_multiplier~=0.6
sits within the already-documented F4 calibrated-multiplier tier of
`friction_closures.py`'s own hierarchy.

### 12. Validation-exposure count

`salt2_lo5q`/`salt2_hi5q`/`val_salt2` have now been scored at least a
3rd-4th time this session (across this package and its two siblings). See
`validation_exposure_count.csv`. None of this constitutes a legitimate
single-use protected-split score.

## Open first

- `friction_closure_comparison.csv`
- `mdot_temperature_decoupling_check.csv`
- `prior_undocumented_sweeps_found.csv`
- `sign_convention_corrections.csv`
- `insulation_screening_sweep.csv`
- `insulation_friction_zero_crossing_refinement.csv`
- `salt1_4_train_validation_at_recommended_combo.csv`
- `validation_case_scores_raw_physics.csv`
- `residual_correction_on_physics_baseline.csv`
- `internal_nu_ablation.csv`
- `physical_plausibility_caveats.csv`
- `claim_boundary_table.csv`
- `validation_exposure_count.csv`
- `validation_terminology_crosswalk.csv`
- `source_manifest.csv`
- `no_mutation_guardrails.csv`
